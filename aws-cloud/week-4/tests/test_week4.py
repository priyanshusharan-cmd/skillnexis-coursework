import glob
import json
import os
import re
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


def load(name):
    class L(yaml.SafeLoader):
        pass
    for tag in ("!Ref", "!Sub", "!GetAtt", "!Join", "!Select"):
        L.add_constructor(tag, lambda lo, n: lo.construct_scalar(n) if isinstance(n, yaml.ScalarNode) else lo.construct_sequence(n))
    return yaml.load(open(os.path.join(ROOT, "infra", name)), Loader=L)


@pytest.mark.parametrize("tpl", sorted(glob.glob(os.path.join(ROOT, "infra", "*.yaml"))))
def test_cfn_lint(tpl):
    r = subprocess.run(["cfn-lint", tpl], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_dashboard_is_valid_json_and_covers_the_service():
    body = load("observability.yaml")["Resources"]["Dashboard"]["Properties"]["DashboardBody"]
    body = re.sub(r"\$\{[^}]+\}", "x", body)                 # what !Sub produces, with placeholder values
    widgets = json.loads(body)["widgets"]
    namespaces = {m[0] for w in widgets if w["type"] == "metric" for m in w["properties"]["metrics"] if not m[0].startswith(".")}
    assert namespaces == {"AWS/ApiGateway", "AWS/Lambda", "AWS/DynamoDB"}
    assert any(w["type"] == "log" for w in widgets)


def test_composite_alarm_covers_every_alarm():
    t = load("observability.yaml")["Resources"]
    alarms = [k for k, v in t.items() if v["Type"] == "AWS::CloudWatch::Alarm"]
    rule = t["ServiceUnhealthy"]["Properties"]["AlarmRule"]
    assert all(f"${{{a}}}" in rule for a in alarms) and t["ServiceUnhealthy"]["Properties"]["AlarmActions"]


ROOT_LOGIN = {"id": "1", "account": "123456789012", "source": "aws.signin", "time": "2026-11-04T00:00:00Z", "region": "us-east-1",
              "resources": [], "detail-type": "AWS Console Sign In via CloudTrail",
              "detail": {"userIdentity": {"type": "Root"}, "responseElements": {"ConsoleLogin": "Success"}, "additionalEventData": {"MFAUsed": "Yes"}}}
USER_NO_MFA = {**ROOT_LOGIN, "detail": {"userIdentity": {"type": "IAMUser"}, "responseElements": {"ConsoleLogin": "Success"},
                                         "additionalEventData": {"MFAUsed": "No"}}}
SG_OPENED = {**ROOT_LOGIN, "source": "aws.ec2", "detail-type": "AWS API Call via CloudTrail",
             "detail": {"eventName": "AuthorizeSecurityGroupIngress", "userIdentity": {"type": "IAMUser"}}}
NORMAL = {**ROOT_LOGIN, "source": "aws.ec2", "detail-type": "AWS API Call via CloudTrail", "detail": {"eventName": "DescribeInstances"}}


@pytest.mark.parametrize("rule, event, fires", [("RootLogin", ROOT_LOGIN, True), ("RootLogin", USER_NO_MFA, False),
                                                 ("LoginWithoutMfa", USER_NO_MFA, True), ("LoginWithoutMfa", ROOT_LOGIN, False),
                                                 ("RiskyChanges", SG_OPENED, True), ("RiskyChanges", NORMAL, False)])
def test_security_alert_rules_match_the_right_events(rule, event, fires):
    pattern = load("security-baseline.yaml")["Resources"][rule]["Properties"]["EventPattern"]
    from moto.events.models import EventPattern        # EventBridge's matching rules, as implemented by moto
    assert EventPattern.load(json.dumps(pattern)).matches_event(event) is fires


def test_backup_vault_forbids_early_deletion_and_keeps_35_days():
    t = load("backup.yaml")["Resources"]
    deny = t["Vault"]["Properties"]["AccessPolicy"]["Statement"][0]
    assert deny["Effect"] == "Deny" and "backup:DeleteRecoveryPoint" in deny["Action"]
    assert t["Plan"]["Properties"]["BackupPlan"]["BackupPlanRule"][0]["Lifecycle"]["DeleteAfterDays"] == 35


def test_disaster_recovery_drill_restores_every_item():
    import dr_drill
    with mock_aws():
        before, after, steps = dr_drill.drill(boto3.client("dynamodb", region_name="ap-south-1"), n_users=5, per_user=10)
    assert len(before) == 50 and before == after
