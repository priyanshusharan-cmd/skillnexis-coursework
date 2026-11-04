"""Serverless "study links" API: Lambda behind an API Gateway HTTP API, data in DynamoDB, files in a private S3 bucket.

Routes
  GET    /items            list the caller's items (newest first)
  POST   /items            create   {"title": str, "url": "https://...", "tags": [str]}
  GET    /items/{id}       read one
  PUT    /items/{id}       update title/url/tags
  DELETE /items/{id}       delete (and its attachment)
  POST   /items/{id}/upload-url   presigned S3 PUT URL (5 min) for an attachment, e.g. a PDF of the notes

The owner comes from the JWT authorizer claims (Cognito) when present, else the "x-user" header for local tests.
"""
import json
import os
import re
import time
import uuid

import boto3
from boto3.dynamodb.conditions import Key

TABLE = os.environ.get("TABLE_NAME", "study-links")
BUCKET = os.environ.get("BUCKET_NAME", "study-links-attachments")
URL_RE = re.compile(r"^https://[^\s/$.?#].[^\s]*$")
MAX_TAGS, MAX_TITLE = 10, 200

_ddb = _s3 = None


def ddb():
    global _ddb
    if _ddb is None:
        _ddb = boto3.resource("dynamodb").Table(TABLE)
    return _ddb


def s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3")
    return _s3


def reply(status, body=None):
    return {"statusCode": status, "headers": {"content-type": "application/json"},
            "body": json.dumps(body) if body is not None else ""}


def owner_of(event):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    return claims.get("sub") or (event.get("headers") or {}).get("x-user")


def validate(d, partial=False):
    errors = {}
    if not partial or "title" in d:
        t = d.get("title")
        if not isinstance(t, str) or not t.strip() or len(t) > MAX_TITLE:
            errors["title"] = f"required, 1-{MAX_TITLE} characters"
    if not partial or "url" in d:
        if not isinstance(d.get("url"), str) or not URL_RE.match(d["url"]):
            errors["url"] = "must be an https:// URL"
    if "tags" in d:
        tags = d["tags"]
        if not isinstance(tags, list) or len(tags) > MAX_TAGS or not all(isinstance(x, str) and 0 < len(x) <= 30 for x in tags):
            errors["tags"] = f"up to {MAX_TAGS} strings of 1-30 characters"
    return errors


def lambda_handler(event, context=None):
    user = owner_of(event)
    if not user:
        return reply(401, {"error": "unauthenticated"})
    method = event.get("requestContext", {}).get("http", {}).get("method", event.get("httpMethod", "GET"))
    path = event.get("rawPath", event.get("path", "/"))
    parts = [p for p in path.split("/") if p]
    try:
        body = json.loads(event.get("body") or "{}")
    except ValueError:
        return reply(400, {"error": "body must be JSON"})

    if parts == ["items"] and method == "GET":
        r = ddb().query(KeyConditionExpression=Key("owner").eq(user), ScanIndexForward=False, Limit=100)
        return reply(200, {"items": [clean(i) for i in r["Items"]]})
    if parts == ["items"] and method == "POST":
        if errs := validate(body):
            return reply(422, {"errors": errs})
        item = {"owner": user, "id": f"{int(time.time() * 1000):013d}-{uuid.uuid4().hex[:8]}", "title": body["title"].strip(),
                "url": body["url"], "tags": sorted(set(body.get("tags", []))), "created": int(time.time())}
        ddb().put_item(Item=item)
        return reply(201, clean(item))
    if len(parts) >= 2 and parts[0] == "items":
        key = {"owner": user, "id": parts[1]}
        current = ddb().get_item(Key=key).get("Item")
        if not current:
            return reply(404, {"error": "not found"})        # also for other users' items: no existence leak
        if len(parts) == 2 and method == "GET":
            return reply(200, clean(current))
        if len(parts) == 2 and method == "PUT":
            if errs := validate(body, partial=True):
                return reply(422, {"errors": errs})
            current.update({k: body[k] for k in ("title", "url", "tags") if k in body})
            ddb().put_item(Item=current)
            return reply(200, clean(current))
        if len(parts) == 2 and method == "DELETE":
            ddb().delete_item(Key=key)
            if current.get("attachment"):
                s3().delete_object(Bucket=BUCKET, Key=current["attachment"])
            return reply(204)
        if parts[2:] == ["upload-url"] and method == "POST":
            obj = f"{user}/{parts[1]}.pdf"
            url = s3().generate_presigned_url("put_object", ExpiresIn=300,
                                              Params={"Bucket": BUCKET, "Key": obj, "ContentType": "application/pdf"})
            current["attachment"] = obj
            ddb().put_item(Item=current)
            return reply(200, {"upload_url": url, "expires_in": 300, "key": obj})
    return reply(404, {"error": "no such route"})


def clean(item):
    out = {k: v for k, v in item.items() if k != "owner"}
    if "created" in out:
        out["created"] = int(out["created"])
    return out
