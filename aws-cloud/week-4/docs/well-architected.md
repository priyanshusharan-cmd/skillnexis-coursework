# AWS Well-Architected review of the study-links system (weeks 2–4)

Each pillar: what the design does, the evidence in this repository, and the risks still open, ranked.

## 1. Operational excellence
| Practice | Implementation | Evidence |
|---|---|---|
| Everything as code | 9 CloudFormation/SAM templates, no console clicking | `cfn-lint` clean in CI for weeks 2–4 |
| Deploy safely | ASG rolling updates (1 at a time, min 1 healthy); CI deploys via OIDC | [week-3/infra/web-tier.yaml](../../week-3/infra/web-tier.yaml) |
| Know when it breaks | Dashboard of the 4 golden signals; composite alarm pages once | [infra/observability.yaml](../infra/observability.yaml), tests |
| Practise failure | Scripted DR drill | [results/dr_drill.md](../results/dr_drill.md) |
| **Open** | No runbook links in alarm descriptions; no deployment canary for Lambda (SAM `AutoPublishAlias` + `DeploymentPreference: Canary10Percent5Minutes` would add one) | |

## 2. Security
| Practice | Implementation |
|---|---|
| Identity | Cognito JWTs checked at API Gateway; IAM roles everywhere, no long-lived keys (GitHub OIDC); MFA enforced in the developer policy; root alerts |
| Least privilege | Lambda: one table, one bucket; deploy role: one bucket prefix and invalidations; Parliament-linted policies |
| Network | Instances reachable only from the ALB; no SSH (SSM); private subnets with no internet route; DB SG only from the web SG |
| Data protection | Encryption at rest everywhere (S3 SSE, DynamoDB SSE, encrypted EBS); TLS-only bucket policies; versioning; Block Public Access; CloudFront OAC |
| Detection | Multi-region CloudTrail with log file validation; EventBridge alerts for root login, console login without MFA, IAM and security group changes (tested against sample events) |
| **Open** | HTTP only on the ALB until a domain and ACM certificate exist; no WAF (the managed rules cost ~$5/month); GuardDuty left off after its 30-day trial (cost) |

## 3. Reliability
| Practice | Implementation |
|---|---|
| Multi-AZ | ALB and ASG across 2 AZs; Lambda, DynamoDB, S3 and CloudFront are multi-AZ by design |
| Self-healing | ELB health checks replace instances whose app stops answering |
| Scale | Target tracking 50 % CPU; API throttling (10 req/s, burst 20) protects the backend; on-demand DynamoDB |
| Backup and restore | PITR (any second in 35 days) + daily AWS Backup in a deletion-protected vault; restore drill passes (1,000/1,000 items) |
| **Open** | Single region (acceptable: RTO 30 min, RPO seconds, see [dr.md](dr.md)); the web tier has no data tier yet |

## 4. Performance efficiency
* Serverless for spiky student traffic; arm64 Lambda; CloudFront edge caching with HTTP/3 and compression.
* DynamoDB key design makes "my items, newest first" a single `Query`.
* Scaling model: target tracking plus scheduled scaling gives 0 overloaded minutes on results day ([week 3](../../week-3/results/scaling.md)).
* **Open**: per-instance capacity (120 req/s) is assumed; measure it with a load test (k6 or JMeter, as in the QA course).

## 5. Cost optimisation
* Free-tier-first design ([week 2 cost table](../../week-2/docs/cost.md)): no NAT gateway (free gateway endpoints instead), no RDS, on-demand everything.
* Auto Scaling saves 63 % of instance-hours compared with a fixed fleet of 3.
* Budgets alert at the first cent; log retention 14 days; S3 lifecycle to IA/Glacier; old object versions expire.
* **Open**: the ALB (≈ $16/month after the first year) is the largest steady cost. For this traffic, CloudFront + API Gateway alone could replace the EC2 tier.

## 6. Sustainability
* Graviton (arm64) Lambda uses less energy per request; scale-to-zero serverless; Auto Scaling runs 1 instance most of the day instead of 3.
* Region ap-south-1 is close to users (less network transfer). S3 lifecycle rules and log expiry avoid storing data nobody needs.

## Top 3 improvements, in order
1. **Domain + ACM certificate → HTTPS on the ALB and a custom domain on CloudFront** (security; free with ACM).
2. **Lambda canary deployments with automatic rollback on the 5xx alarm** (operational excellence; free).
3. **Load test to replace the assumed instance capacity**, then re-tune the scaling target (performance).
