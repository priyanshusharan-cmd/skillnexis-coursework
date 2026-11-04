"""Lint all templates; deploy week 2's network and this week's web tier into emulated CloudFormation and check
the high-availability properties; check the deploy role's trust policy and the scaling model."""
import glob
import os
import subprocess
import sys

import boto3
import pytest
import yaml
from moto import mock_aws

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))


@pytest.fixture(autouse=True)
def creds(monkeypatch):
    for k, v in {"AWS_ACCESS_KEY_ID": "t", "AWS_SECRET_ACCESS_KEY": "t", "AWS_DEFAULT_REGION": "ap-south-1"}.items():
        monkeypatch.setenv(k, v)


@pytest.mark.parametrize("tpl", sorted(glob.glob(os.path.join(ROOT, "infra", "*.yaml"))))
def test_cfn_lint(tpl):
    r = subprocess.run(["cfn-lint", tpl], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def outputs(cf, name):
    return {o["OutputKey"]: o["OutputValue"] for o in cf.describe_stacks(StackName=name)["Stacks"][0].get("Outputs", [])}


def test_web_tier_is_highly_available():
    with mock_aws():
        cf = boto3.client("cloudformation")
        cf.create_stack(StackName="week2-network", TemplateBody=open(os.path.join(ROOT, "..", "week-2", "infra", "network.yaml")).read(),
                        Capabilities=["CAPABILITY_IAM"])
        ec2 = boto3.client("ec2")
        vpc = outputs(cf, "week2-network")["VpcId"]
        public = [s["SubnetId"] for s in ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc]}])["Subnets"] if s["MapPublicIpOnLaunch"]]
        cf.create_stack(StackName="week3-web", TemplateBody=open(os.path.join(ROOT, "infra", "web-tier.yaml")).read(),
                        Capabilities=["CAPABILITY_IAM"],
                        Parameters=[{"ParameterKey": "VpcId", "ParameterValue": vpc},
                                    {"ParameterKey": "PublicSubnets", "ParameterValue": ",".join(public)}])
        assert cf.describe_stacks(StackName="week3-web")["Stacks"][0]["StackStatus"] == "CREATE_COMPLETE"
        asg = boto3.client("autoscaling").describe_auto_scaling_groups()["AutoScalingGroups"][0]
        assert (asg["MinSize"], asg["MaxSize"]) == (1, 3)
        assert asg["HealthCheckType"] == "ELB" and len(asg["TargetGroupARNs"]) == 1
        azs = {s["AvailabilityZone"] for s in ec2.describe_subnets(SubnetIds=asg["VPCZoneIdentifier"].split(","))["Subnets"]}
        assert len(azs) == 2, "instances can land in two AZs"
        # moto doesn't create scaling policies from CloudFormation, so check that resource in the template
        policy = _template("web-tier.yaml")["Resources"]["CpuTarget"]["Properties"]
        assert policy["PolicyType"] == "TargetTrackingScaling" and policy["TargetTrackingConfiguration"]["TargetValue"] == 50
        elb = boto3.client("elbv2")
        lb = elb.describe_load_balancers()["LoadBalancers"][0]
        assert len(lb["AvailabilityZones"]) == 2 and lb["Scheme"] == "internet-facing"
        tg = elb.describe_target_groups()["TargetGroups"][0]
        assert tg["HealthCheckPath"] == "/health"
        app_sg = [g for g in ec2.describe_security_groups()["SecurityGroups"] if g["Description"].startswith("Instances accept")][0]
        assert all(not p.get("IpRanges") for p in app_sg["IpPermissions"]), "instances are not reachable from the internet directly"


def _template(name):
    class L(yaml.SafeLoader):
        pass
    for tag in ("!Ref", "!Sub", "!GetAtt", "!Join", "!Select", "!GetAZs", "!If", "!Equals"):
        L.add_constructor(tag, lambda loader, node: loader.construct_scalar(node) if isinstance(node, yaml.ScalarNode) else loader.construct_sequence(node))
    return yaml.load(open(os.path.join(ROOT, "infra", name)), Loader=L)


def test_github_deploy_role_trusts_only_main_branch_of_this_repo():
    t = _template("github-oidc.yaml")
    cond = t["Resources"]["DeployRole"]["Properties"]["AssumeRolePolicyDocument"]["Statement"][0]["Condition"]["StringEquals"]
    assert cond["token.actions.githubusercontent.com:sub"] == "repo:${Repo}:ref:refs/heads/main"
    assert cond["token.actions.githubusercontent.com:aud"] == "sts.amazonaws.com"
    actions = {a for s in t["Resources"]["DeployRole"]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"] for a in s["Action"]}
    assert not any(a.endswith(":*") or a == "*" for a in actions)


def test_static_site_bucket_is_private_and_cdn_https_only():
    t = _template("static-site.yaml")["Resources"]
    assert all(t["SiteBucket"]["Properties"]["PublicAccessBlockConfiguration"].values())
    assert t["Cdn"]["Properties"]["DistributionConfig"]["DefaultCacheBehavior"]["ViewerProtocolPolicy"] == "redirect-to-https"
    stmt = t["SiteBucketPolicy"]["Properties"]["PolicyDocument"]["Statement"][0]
    assert stmt["Principal"] == {"Service": "cloudfront.amazonaws.com"} and "AWS:SourceArn" in stmt["Condition"]["StringEquals"]


def test_autoscaling_beats_a_fixed_fleet():
    import numpy as np
    import scaling_sim as s
    load = s.traffic(np.random.default_rng(3))
    auto, fixed1, fixed3 = s.simulate(load), s.simulate(load, fixed=1), s.simulate(load, fixed=3)
    assert auto[:, 1].sum() < 0.5 * fixed3[:, 1].sum()          # far fewer instance-hours than over-provisioning
    assert auto[:, 3].sum() < 0.01 * fixed1[:, 3].sum()         # and almost none of the drops of under-provisioning
    assert (s.simulate_scheduled(load)[:, 2] > 80).sum() == 0    # scheduled scaling removes the warm-up gap
