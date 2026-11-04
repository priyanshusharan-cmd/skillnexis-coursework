"""Disaster-recovery drill for the study-links table, run against the AWS emulator (or a real sandbox with --real).

Scenario: a bad deploy wipes the table. We (1) seed data, (2) take an on-demand backup (what AWS Backup does nightly),
(3) "lose" the table, (4) restore it from the backup under a new name, (5) verify every item came back, and
(6) time each step. The output is the evidence for the RTO/RPO table in docs/dr.md.

    python scripts/dr_drill.py         -> results/dr_drill.md
"""
import argparse
import os
import time

import boto3

TABLE = "study-links"


def make_table(ddb, name):
    ddb.create_table(TableName=name, BillingMode="PAY_PER_REQUEST",
                     AttributeDefinitions=[{"AttributeName": "owner", "AttributeType": "S"}, {"AttributeName": "id", "AttributeType": "S"}],
                     KeySchema=[{"AttributeName": "owner", "KeyType": "HASH"}, {"AttributeName": "id", "KeyType": "RANGE"}],
                     Tags=[{"Key": "backup", "Value": "daily"}])
    ddb.get_waiter("table_exists").wait(TableName=name)


def scan_all(ddb, name):
    items, kw = [], {}
    while True:
        r = ddb.scan(TableName=name, **kw)
        items += r["Items"]
        if "LastEvaluatedKey" not in r:
            return items
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]


def drill(ddb, n_users=40, per_user=25):
    t, steps = time.perf_counter(), []

    def step(name):
        nonlocal t
        now = time.perf_counter()
        steps.append((name, now - t))
        t = now

    make_table(ddb, TABLE)
    with boto3.resource("dynamodb", region_name=ddb.meta.region_name, endpoint_url=ddb.meta.endpoint_url).Table(TABLE).batch_writer() as w:
        for u in range(n_users):
            for i in range(per_user):
                w.put_item(Item={"owner": f"user-{u:03d}", "id": f"{i:05d}", "title": f"link {i}", "url": f"https://example.org/{u}/{i}"})
    before = sorted((i["owner"]["S"], i["id"]["S"], i["url"]["S"]) for i in scan_all(ddb, TABLE))
    step("seed data")
    arn = ddb.create_backup(TableName=TABLE, BackupName=f"{TABLE}-drill")["BackupDetails"]["BackupArn"]
    step("take backup")
    ddb.delete_table(TableName=TABLE)                     # the "incident"
    ddb.get_waiter("table_not_exists").wait(TableName=TABLE)
    step("incident: table deleted")
    restored = f"{TABLE}-restored"
    ddb.restore_table_from_backup(TargetTableName=restored, BackupArn=arn)
    ddb.get_waiter("table_exists").wait(TableName=restored)
    step("restore from backup")
    after = sorted((i["owner"]["S"], i["id"]["S"], i["url"]["S"]) for i in scan_all(ddb, restored))
    step("verify")
    return before, after, steps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    a = ap.parse_args()
    if not a.real:
        from moto import mock_aws
        os.environ.update(AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test")
        mock_aws().start()
    ddb = boto3.client("dynamodb", region_name="ap-south-1")
    before, after, steps = drill(ddb)
    ok = before == after
    lines = [f"Drill {'PASSED' if ok else 'FAILED'}: {len(before):,} items before the incident, {len(after):,} after restore, "
             f"{'identical' if ok else 'DIFFERENT'} (owner, id and url compared item by item).", "",
             "| Step | Time (emulator) |", "|---|---:|"] + [f"| {n} | {s * 1000:.0f} ms |" for n, s in steps] + ["",
             "Emulator timings show the procedure works, not real durations: on AWS a restore of a small table takes "
             "minutes, so the documented RTO is 30 minutes including switching the Lambda's TABLE_NAME to the restored table."]
    os.makedirs("results", exist_ok=True)
    open("results/dr_drill.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
