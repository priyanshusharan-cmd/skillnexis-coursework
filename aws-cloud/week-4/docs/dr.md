# Disaster recovery runbook

| Component | Failure | Protection | RPO (data lost) | RTO (time to recover) |
|---|---|---|---|---|
| DynamoDB table | Bad deploy or bug corrupts items | Point-in-time recovery | ~seconds (restore to just before the bad deploy) | 30 min |
| DynamoDB table | Table deleted, or corruption found days later | AWS Backup daily, 35 days, vault denies early deletion | ≤ 24 h | 30 min |
| S3 attachments | Overwrite or delete | Versioning (non-current kept 30 days) | 0 | minutes |
| Lambda / API | Bad code | Redeploy the previous commit (CloudFormation) | n/a | 10 min |
| Web tier | Instance or AZ failure | ALB + ASG across 2 AZs, ELB health checks | n/a | ~3 min (automatic) |
| Region | ap-south-1 outage | Not covered: IaC can redeploy to ap-south-2 (Hyderabad), but data would be ≤ 24 h old unless backups are copied cross-region (~₹ per GB) | ≤ 24 h | hours |

## Restore the table (drilled in [scripts/dr_drill.py](../scripts/dr_drill.py))
1. Find the recovery point: AWS Backup vault `study-links-vault`, or a PITR timestamp just before the incident.
2. Restore to a **new** table (`study-links-restored`); restores never overwrite the original.
3. Verify item counts and spot-check (the drill compares every item).
4. Point the Lambda at it: `sam deploy ... --parameter-overrides` or update the `TABLE_NAME` environment variable.
5. Once happy, re-enable PITR and the `backup=daily` tag on the restored table (they are not copied by a restore).

Latest drill: **passed**, 1,000 / 1,000 items identical ([results](../results/dr_drill.md)).
