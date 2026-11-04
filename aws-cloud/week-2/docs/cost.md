# Cost: why this costs ₹0

Verified locally with an AWS emulator (moto), so building and testing this week cost nothing and needed no AWS account.
If deployed to a real **new AWS account in ap-south-1 (Mumbai)**, a class-sized workload stays inside the Free Tier:

| Service | What we use | Free tier | Our usage (100 students, 50 requests/day each) |
|---|---|---|---|
| Lambda | 256 MB arm64, ~50 ms per request | 1 M requests + 400,000 GB-s per month, always free | 150,000 requests, ~1,900 GB-s |
| API Gateway HTTP API | 6 routes | 1 M calls/month for 12 months | 150,000 calls |
| DynamoDB on-demand | 1 table, ~1 KB items | 25 GB storage always free (on-demand requests: a few rupees per million) | < 50 MB; ~₹0.30/month of requests |
| S3 | private bucket, PDFs | 5 GB for 12 months | < 1 GB |
| Cognito | user pool | 10,000 monthly active users free (Lite tier) | 100 |
| CloudWatch | 1 alarm, 14-day logs | 10 alarms, 5 GB logs | 1 alarm, < 100 MB |
| EC2 (network stack) | 1 × t3.micro, 8 GB gp3 | 750 h/month for 12 months, 30 GB EBS | 720 h, 8 GB |
| VPC | 2 AZs, gateway endpoints | free (gateway endpoints are free) | – |
| Public IPv4 address | the web server's | **not free: ~$3.6/month** since Feb 2024 (750 h free for 12 months on new accounts) | covered for 12 months |

Deliberately **left out** because they would cost money: NAT gateway (~$32/month; replaced by free S3/DynamoDB
gateway endpoints), RDS (the DB security group is ready for it; free tier is db.t3.micro for 12 months, but it
is the easiest service to leave running by mistake), Application Load Balancer, interface VPC endpoints.

**Guard rails:** `infra/budget.yaml` emails at the first cent of actual spend and at 80 % of a $1 forecast
(two budgets are free). Always `aws cloudformation delete-stack` after a lab.
