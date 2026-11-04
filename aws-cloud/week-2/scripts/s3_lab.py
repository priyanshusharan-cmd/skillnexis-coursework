"""S3 hands-on: a private, encrypted, versioned bucket with a lifecycle policy, uploads and time-limited sharing.

    python scripts/s3_lab.py                      # offline: an in-process AWS emulator (moto), costs nothing
    AWS_PROFILE=sandbox python scripts/s3_lab.py --real --bucket <globally-unique-name>
"""
import argparse
import json

import boto3


def setup_bucket(s3, bucket, region, tls_only=True):
    kw = {} if region == "us-east-1" else {"CreateBucketConfiguration": {"LocationConstraint": region}}
    s3.create_bucket(Bucket=bucket, **kw)
    s3.put_bucket_ownership_controls(Bucket=bucket, OwnershipControls={"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]})
    s3.put_public_access_block(Bucket=bucket, PublicAccessBlockConfiguration={
        "BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True})
    s3.put_bucket_encryption(Bucket=bucket, ServerSideEncryptionConfiguration={
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]})
    s3.put_bucket_versioning(Bucket=bucket, VersioningConfiguration={"Status": "Enabled"})
    s3.put_bucket_lifecycle_configuration(Bucket=bucket, LifecycleConfiguration={"Rules": [
        {"ID": "logs-to-cheaper-storage", "Status": "Enabled", "Filter": {"Prefix": "logs/"},
         "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}, {"Days": 90, "StorageClass": "GLACIER"}],
         "Expiration": {"Days": 365}},
        {"ID": "old-versions", "Status": "Enabled", "Filter": {"Prefix": ""},
         "NoncurrentVersionExpiration": {"NoncurrentDays": 30}}]})
    if tls_only:
        require_tls(s3, bucket)


def require_tls(s3, bucket):
    """Refuse any request that doesn't arrive over HTTPS."""
    s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps({"Version": "2012-10-17", "Statement": [{
        "Sid": "DenyInsecureTransport", "Effect": "Deny", "Principal": "*", "Action": "s3:*",
        "Resource": [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"],
        "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}))


def demo(s3, bucket):
    report = {}
    s3.put_object(Bucket=bucket, Key="notes/week2.txt", Body=b"version 1")
    s3.put_object(Bucket=bucket, Key="notes/week2.txt", Body=b"version 2")
    versions = s3.list_object_versions(Bucket=bucket, Prefix="notes/week2.txt")["Versions"]
    report["versions_kept"] = len(versions)
    oldest = next(v for v in versions if not v["IsLatest"])           # read back the overwritten version
    report["restored_body"] = s3.get_object(Bucket=bucket, Key="notes/week2.txt", VersionId=oldest["VersionId"])["Body"].read().decode()
    head = s3.head_object(Bucket=bucket, Key="notes/week2.txt")
    report["encryption"] = head.get("ServerSideEncryption")
    report["share_link"] = s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": "notes/week2.txt"}, ExpiresIn=600)
    # ACLs disabled (real S3 then rejects any public-read ACL; the emulator doesn't enforce this, so we report the setting)
    report["object_ownership"] = s3.get_bucket_ownership_controls(Bucket=bucket)["OwnershipControls"]["Rules"][0]["ObjectOwnership"]
    report["public_access_block"] = s3.get_public_access_block(Bucket=bucket)["PublicAccessBlockConfiguration"]
    report["lifecycle_rules"] = [r["ID"] for r in s3.get_bucket_lifecycle_configuration(Bucket=bucket)["Rules"]]
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--bucket", default="week2-s3-lab")
    ap.add_argument("--region", default="ap-south-1")
    a = ap.parse_args()
    if not a.real:
        import os

        from moto import mock_aws
        os.environ.update(AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test")
        mock_aws().start()
    s3 = boto3.client("s3", region_name=a.region)
    setup_bucket(s3, a.bucket, a.region, tls_only=a.real)     # the emulator speaks plain HTTP
    print(json.dumps(demo(s3, a.bucket), indent=2, default=str))
