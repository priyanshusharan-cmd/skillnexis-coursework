# Cloud Computing with AWS — Week 2: core services hands-on

Week 1 was the theory (EC2, S3, RDS, Lambda, service models). This week builds with them, as **infrastructure as
code**, and tests everything with an AWS emulator ([moto](https://github.com/getmoto/moto)), so it cost ₹0 and needed
no AWS login. The same templates deploy to a real free-tier account unchanged ([how](#deploy-to-a-real-account-optional)).

| Part | Files | Verified by |
|---|---|---|
| Serverless REST API: HTTP API + Lambda + DynamoDB + S3 + Cognito | [infra/serverless.yaml](infra/serverless.yaml), [app/handler.py](app/handler.py) | 11 API tests against emulated DynamoDB/S3 |
| Networking: 2-AZ VPC, public/private subnets, EC2 web server | [infra/network.yaml](infra/network.yaml) | stack deployed into emulated CloudFormation, then inspected |
| S3: private, encrypted, versioned bucket, lifecycle, presigned sharing | [scripts/s3_lab.py](scripts/s3_lab.py) | [results/s3_lab_output.json](results/s3_lab_output.json) + test |
| IAM: least-privilege policies | [iam/](iam/) | Parliament IAM linter: no findings |
| Cost control | [infra/budget.yaml](infra/budget.yaml), [docs/cost.md](docs/cost.md) | cfn-lint |

`pytest -q tests` → **17 passed**, and all three CloudFormation templates pass `cfn-lint`. GitHub Actions runs both on every push.

## 1. Serverless API (Lambda, API Gateway, DynamoDB, S3, Cognito)
A "study links" service: each student saves useful links with tags and can attach a PDF of their notes.
* **Routes**: `GET/POST /items`, `GET/PUT/DELETE /items/{id}`, `POST /items/{id}/upload-url`.
* **Identity**: a Cognito user pool issues JWTs, and the HTTP API checks them before Lambda runs. The handler
  uses the token's `sub` as the owner. Passwords are at least 12 characters, with optional TOTP MFA.
* **Data model**: DynamoDB with partition key `owner` and sort key `id`, where the id starts with a timestamp.
  "My items, newest first" is then a single `Query`, never a `Scan`, and one user's data can't be reached
  with another user's key. Another user's item returns 404, not 403, so its existence isn't revealed.
* **Files**: the client gets a 5-minute **presigned PUT URL**, so PDFs go straight to S3 instead of through
  Lambda. The bucket blocks all public access, is encrypted and versioned, refuses non-HTTPS requests, and
  has ACLs disabled.
* **Least privilege**: the function can only CRUD *its* table and put/delete in *its* bucket.
* **Operations**: X-Ray tracing, 14-day log retention, and a CloudWatch alarm on errors that emails through SNS.
  The API is throttled to 10 req/s (burst 20), which caps any bill.
* **Validation**: title 1–200 characters, `https://` URLs only (the tests reject `javascript:` and `http:`),
  at most 10 tags.

## 2. VPC and EC2
```
VPC 10.20.0.0/16 ──┬─ AZ a: public 10.20.0.0/24  (web server, nginx)   private 10.20.10.0/24
                   └─ AZ b: public 10.20.1.0/24                          private 10.20.11.0/24
public route table: 0.0.0.0/0 → Internet Gateway     private route table: no internet route
S3 + DynamoDB gateway endpoints (free) instead of a NAT gateway (~$32/month)
```
* The web security group opens only 80/443. **There is no SSH port and no key pair**: the instance is reached
  with SSM Session Manager through its IAM role.
* The database security group admits PostgreSQL only from the web security group.
* The instance requires IMDSv2 tokens (blocks the SSRF-to-credentials attack), has an encrypted gp3 root
  disk, and gets the latest Amazon Linux 2023 AMI from SSM.
* The test deploys the stack into emulated CloudFormation, then checks it:
  * 4 subnets across 2 AZs, 2 of them public;
  * only the public subnets route to the internet gateway;
  * the only world-open ports are 80 and 443;
  * the instance is a free-tier t3.micro in a public subnet.

## 3. S3 lab ([output](results/s3_lab_output.json))
`python scripts/s3_lab.py` creates a bucket with:
* Block Public Access (all four settings on);
* SSE-S3 encryption and versioning;
* bucket-owner-enforced ownership (ACLs off);
* lifecycle: `logs/` moves to Standard-IA after 30 days and Glacier after 90, and expires at 365; old versions
  are removed after 30 days;
* a TLS-only bucket policy.

It then overwrites a file and reads the previous version back (an accidental overwrite is recoverable), and makes
a 10-minute presigned share link. The test also shows the TLS-only policy refusing a plain-HTTP request.
`--real --bucket <name>` runs the same thing against a real account.

## 4. IAM ([iam/](iam/))
* `developer.json`:
  * can deploy only `week2-*` stacks in `ap-south-1`;
  * every action is denied without MFA (except setting up MFA);
  * other regions are denied, except for global services.
* `auditor.json`: reads configuration (security groups, bucket policies, MFA status, CloudTrail), never data.
* `s3-uploader.json`: each user can read and write only their own `${aws:username}/` prefix.

All three pass the Parliament linter with no medium or high findings. The root user is not used for anything.

## Deploy to a real account (optional)
Only if you want to see it live, on a new free-tier account, after setting up the budget first:
```bash
aws cloudformation deploy --template-file infra/budget.yaml --stack-name week2-budget --parameter-overrides Email=you@example.com
sam deploy --template-file infra/serverless.yaml --stack-name week2-api --capabilities CAPABILITY_IAM --resolve-s3 \
  --parameter-overrides AlertEmail=you@example.com --region ap-south-1
aws cloudformation deploy --template-file infra/network.yaml --stack-name week2-network --capabilities CAPABILITY_IAM
# ...and when done:
aws cloudformation delete-stack --stack-name week2-network && aws cloudformation delete-stack --stack-name week2-api
```

## Limitations
* Verified with an emulator, not a live account: moto implements the API behaviour but not every guard rail.
  For example it doesn't refuse a public ACL on an ACL-disabled bucket, so that is reported as a setting, not
  claimed as a tested refusal.
* Cognito JWT checks happen in API Gateway, which the tests don't emulate. The handler is tested with the
  claims API Gateway would pass on.
