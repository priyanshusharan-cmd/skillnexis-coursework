# Cloud Computing with AWS — Week 1

## Service summary

- **EC2:** virtual compute instances.
- **S3:** object storage for files and static assets.
- **RDS:** managed relational databases.
- **Lambda:** event-driven functions without managing servers.

Cloud service models: IaaS gives control over virtual infrastructure, PaaS provides a managed application platform, and SaaS delivers a finished application. Public, private, and hybrid describe deployment arrangements. Regions contain separate Availability Zones.

## Safe mini-project plan

Use a dedicated sandbox account only after reviewing current pricing and account controls. Create a least-privilege IAM role for one named task; enable MFA for human admins; do not use root credentials for daily work. For an S3 static asset exercise, keep Block Public Access enabled and use a private test bucket. The brief asks to expose a public bucket; this repository documents the safer design and does not create an AWS account, IAM identity, or public resource.

This is a written service report and implementation plan, not evidence of AWS console activity.
