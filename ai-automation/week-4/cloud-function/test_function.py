"""Invokes both entry points locally with real events (calls the live GitHub API).   python -m pytest -q test_function.py"""
import json
from lambda_function import lambda_handler
def test_http_get():
    r = lambda_handler({"rawPath": "/", "requestContext": {}, "queryStringParameters": {"repos": "encode/httpx,psf/requests"}}, None)
    b = json.loads(r["body"]); assert r["statusCode"] == 200 and len(b["results"]) == 2 and all(0 <= x["score"] <= 100 for x in b["results"])
def test_http_errors():
    assert lambda_handler({"rawPath": "/", "requestContext": {}, "body": "not json"}, None)["statusCode"] == 400
    assert lambda_handler({"rawPath": "/", "requestContext": {}}, None)["statusCode"] == 400
def test_missing_repo_is_reported_not_raised():
    r = lambda_handler({"repos": ["this-owner-does-not-exist-xyz/nope"]}, None); assert r["results"][0]["error"].startswith(("HTTP 404", "HTTP 422"))
def test_gcf_entry():
    import main
    class Req:
        args = {"repos": "scrapy/scrapy"}
        def get_json(self, silent=True): return None
    body, code, _ = main.repo_health(Req()); assert code == 200 and json.loads(body)["results"][0]["repo"] == "scrapy/scrapy"
