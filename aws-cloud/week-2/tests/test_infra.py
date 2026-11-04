"""Infrastructure as code: lint every template, deploy the network into moto's CloudFormation and inspect it,
lint the IAM policies, and run the S3 lab."""
import glob
import os
import subprocess

import boto3
import pytest
from moto import mock_aws

ROOT = os.path.join(os.path.dirname(__file__), "..")


@pytest.mark.parametrize("tpl", sorted(glob.glob(os.path.join(ROOT, "infra", "*.yaml"))))
def test_templates_pass_cfn_lint(tpl):
    r = subprocess.run(["cfn-lint", tpl], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_network_stack_deploys_with_expected_shape():
    body = open(os.path.join(ROOT, "infra", "network.yaml")).read()
    with mock_aws():
        cf = boto3.client("cloudformation")
        cf.create_stack(StackName="week2-network", TemplateBody=body, Capabilities=["CAPABILITY_IAM"])
        assert cf.describe_stacks(StackName="week2-network")["Stacks"][0]["StackStatus"] == "CREATE_COMPLETE"
        ec2 = boto3.client("ec2")
        vpc = [v for v in ec2.describe_vpcs()["Vpcs"] if v["CidrBlock"] == "10.20.0.0/16"][0]
        subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc["VpcId"]]}])["Subnets"]
        assert len(subnets) == 4 and len({s["AvailabilityZone"] for s in subnets}) == 2
        public = {s["SubnetId"] for s in subnets if s["MapPublicIpOnLaunch"]}
        assert len(public) == 2
        tables = ec2.describe_route_tables(Filters=[{"Name": "vpc-id", "Values": [vpc["VpcId"]]}])["RouteTables"]
        for t in tables:
            subs = {a.get("SubnetId") for a in t["Associations"]} - {None}
            internet = any(r.get("GatewayId", "").startswith("igw-") for r in t["Routes"])
            if subs:
                assert internet == bool(subs & public), "only public subnets may route to the internet"
        sgs = ec2.describe_security_groups(Filters=[{"Name": "vpc-id", "Values": [vpc["VpcId"]]}])["SecurityGroups"]
        ports = {p["FromPort"] for g in sgs for p in g["IpPermissions"] if any(r["CidrIp"] == "0.0.0.0/0" for r in p.get("IpRanges", []))}
        assert ports == {80, 443}, "only web ports open to the world: no SSH, no database"
        inst = ec2.describe_instances()["Reservations"][0]["Instances"][0]
        assert inst["InstanceType"] == "t3.micro" and inst["SubnetId"] in public


def test_iam_policies_have_no_findings():
    from parliament import analyze_policy_string
    for f in glob.glob(os.path.join(ROOT, "iam", "*.json")):
        findings = [x for x in analyze_policy_string(open(f).read()).findings if x.severity in ("HIGH", "MEDIUM")]
        assert not findings, (f, [(x.issue, x.detail) for x in findings])


def test_s3_lab_secure_bucket():
    import s3_lab
    with mock_aws():
        s3 = boto3.client("s3")
        s3_lab.setup_bucket(s3, "week2-s3-lab", "ap-south-1", tls_only=False)
        r = s3_lab.demo(s3, "week2-s3-lab")
        s3_lab.require_tls(s3, "week2-s3-lab")
        with pytest.raises(s3.exceptions.ClientError):      # moto serves plain HTTP, which the policy now refuses
            s3.put_object(Bucket="week2-s3-lab", Key="x", Body=b"x")
    assert r["versions_kept"] == 2 and r["restored_body"] == "version 1"
    assert r["encryption"] == "AES256"
    assert all(r["public_access_block"].values())
    assert "X-Amz-Expires=600" in r["share_link"]
    assert r["lifecycle_rules"] == ["logs-to-cheaper-storage", "old-versions"]
