"""Google Cloud Functions (2nd gen) entry point, same core:
    gcloud functions deploy repo-health --gen2 --runtime=python312 --region=asia-south1 --source=. \
      --entry-point=repo_health --trigger-http --allow-unauthenticated --memory=256Mi"""
import json
from core import run
def repo_health(request):
    data = request.get_json(silent=True) or {}
    repos = data.get("repos") or [r for r in (request.args.get("repos") or "").split(",") if r]
    if not repos: return (json.dumps({"error": "give repos"}), 400, {"Content-Type": "application/json"})
    return (json.dumps(run(repos)), 200, {"Content-Type": "application/json"})
