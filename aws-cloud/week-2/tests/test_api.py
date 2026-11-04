"""The Lambda handler against moto's DynamoDB and S3: CRUD, validation, owner isolation, presigned uploads."""
import json

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def api():
    with mock_aws():
        ddb = boto3.client("dynamodb")
        ddb.create_table(TableName="study-links", BillingMode="PAY_PER_REQUEST",
                         AttributeDefinitions=[{"AttributeName": "owner", "AttributeType": "S"}, {"AttributeName": "id", "AttributeType": "S"}],
                         KeySchema=[{"AttributeName": "owner", "KeyType": "HASH"}, {"AttributeName": "id", "KeyType": "RANGE"}])
        boto3.client("s3").create_bucket(Bucket="study-links-attachments", CreateBucketConfiguration={"LocationConstraint": "ap-south-1"})
        import handler
        handler._ddb = handler._s3 = None

        def call(method, path, body=None, user="alice", jwt=False):
            ev = {"rawPath": path, "requestContext": {"http": {"method": method}}, "headers": {},
                  "body": json.dumps(body) if body is not None else None}
            if jwt:
                ev["requestContext"]["authorizer"] = {"jwt": {"claims": {"sub": user}}}
            elif user:
                ev["headers"]["x-user"] = user
            r = handler.lambda_handler(ev)
            return r["statusCode"], json.loads(r["body"]) if r["body"] else None
        yield call


GOOD = {"title": "Week 2: VPC basics", "url": "https://docs.aws.amazon.com/vpc/", "tags": ["vpc", "networking"]}


def test_create_list_read_update_delete(api):
    code, item = api("POST", "/items", GOOD)
    assert code == 201 and item["title"] == GOOD["title"] and "owner" not in item
    code, body = api("GET", "/items")
    assert code == 200 and [i["id"] for i in body["items"]] == [item["id"]]
    assert api("GET", f"/items/{item['id']}")[1]["url"] == GOOD["url"]
    code, upd = api("PUT", f"/items/{item['id']}", {"title": "VPC and subnets"})
    assert code == 200 and upd["title"] == "VPC and subnets" and upd["url"] == GOOD["url"]
    assert api("DELETE", f"/items/{item['id']}")[0] == 204
    assert api("GET", f"/items/{item['id']}")[0] == 404


def test_newest_first(api):
    ids = [api("POST", "/items", {**GOOD, "title": f"t{i}"})[1]["id"] for i in range(3)]
    assert [i["id"] for i in api("GET", "/items")[1]["items"]] == ids[::-1]


@pytest.mark.parametrize("bad, field", [({"url": "https://x.y"}, "title"), ({"title": "x", "url": "http://insecure.example"}, "url"),
                                        ({"title": "x", "url": "javascript:alert(1)"}, "url"),
                                        ({**GOOD, "tags": ["a"] * 11}, "tags"), ({**GOOD, "title": "x" * 201}, "title")])
def test_validation(api, bad, field):
    code, body = api("POST", "/items", bad)
    assert code == 422 and field in body["errors"]


def test_users_cannot_see_each_others_items(api):
    _, item = api("POST", "/items", GOOD, user="alice")
    assert api("GET", "/items", user="bob")[1]["items"] == []
    assert api("GET", f"/items/{item['id']}", user="bob")[0] == 404          # same answer as "doesn't exist"
    assert api("DELETE", f"/items/{item['id']}", user="bob")[0] == 404
    assert api("GET", f"/items/{item['id']}", user="alice")[0] == 200


def test_jwt_identity_and_unauthenticated(api):
    api("POST", "/items", GOOD, user="cognito-sub-123", jwt=True)
    assert len(api("GET", "/items", user="cognito-sub-123", jwt=True)[1]["items"]) == 1
    assert api("GET", "/items", user=None)[0] == 401


def test_presigned_upload_and_cleanup(api):
    _, item = api("POST", "/items", GOOD)
    code, up = api("POST", f"/items/{item['id']}/upload-url")
    assert code == 200 and up["expires_in"] == 300 and "X-Amz-Signature" in up["upload_url"] and up["key"].startswith("alice/")
    s3 = boto3.client("s3")
    s3.put_object(Bucket="study-links-attachments", Key=up["key"], Body=b"%PDF-1.4")
    api("DELETE", f"/items/{item['id']}")
    assert s3.list_objects_v2(Bucket="study-links-attachments").get("KeyCount", 0) == 0


def test_bad_json_and_unknown_route(api):
    import handler
    r = handler.lambda_handler({"rawPath": "/items", "requestContext": {"http": {"method": "POST"}}, "headers": {"x-user": "a"}, "body": "{"})
    assert r["statusCode"] == 400
    assert api("PATCH", "/nothing")[0] == 404
