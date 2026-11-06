"""AWS Lambda entry point. Works for both triggers in template.yaml:
  * Function URL / API Gateway (HTTP):  GET ?repos=owner/a,owner/b   or  POST {"repos": [...]}
  * EventBridge schedule (weekly):      the event's "repos", else the REPOS environment variable"""
import json, os
from core import run
def lambda_handler(event, context):
    event = event or {}
    if "requestContext" in event or "rawPath" in event:                     # HTTP invocation
        qs = event.get("queryStringParameters") or {}; body = event.get("body") or ""
        try: data = json.loads(body) if body else {}
        except json.JSONDecodeError: return _resp(400, {"error": "body must be JSON"})
        repos = data.get("repos") or [r for r in qs.get("repos", "").split(",") if r]
        if not repos: return _resp(400, {"error": "give repos: ?repos=owner/name,owner/name or {\"repos\": [...]}"})
        return _resp(200, run(repos))
    repos = event.get("repos") or os.environ.get("REPOS", "").split(",")    # scheduled invocation
    out = run(repos); print(json.dumps({"summary": [(r["repo"], r.get("score"), r.get("grade")) for r in out["results"]]}))   # -> CloudWatch Logs
    return out
def _resp(code, body): return {"statusCode": code, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}
