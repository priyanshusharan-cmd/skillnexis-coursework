"""Repo-health check: the automation script deployed as a cloud function. Standard library only, so the deployment
package is a few KB and cold starts are fast. For each GitHub repo it fetches the public API data and scores
maintenance health from 0 to 100:
  recency of the last push (40) + the last release (20) + an issue-to-star ratio (20) + licence present (10) + not archived (10)."""
import datetime, json, os, urllib.parse, urllib.request, urllib.error
API = "https://api.github.com/repos/"
def _get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "repo-health-function/1.0",
                                               **({"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"]} if os.environ.get("GITHUB_TOKEN") else {})})
    with urllib.request.urlopen(req, timeout=10) as r: return json.loads(r.read())
def check(repo, today=None):
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    source = "repos-api"
    try: d = _get(API + repo)
    except urllib.error.HTTPError as e:
        if e.code != 403: return dict(repo=repo, error=f"HTTP {e.code}")
        # some networks/proxies only allow the search API: the same fields are in a repo: search (releases aren't)
        try: items = _get("https://api.github.com/search/repositories?q=repo:" + urllib.parse.quote(repo))["items"]
        except urllib.error.HTTPError as e2: return dict(repo=repo, error=f"HTTP {e2.code}")
        if not items: return dict(repo=repo, error="HTTP 404 (not found)")
        d, source = items[0], "search-api"
    except Exception as e: return dict(repo=repo, error=type(e).__name__)
    rel_date = rel_tag = None
    if source == "repos-api":
        try: rel = _get(API + repo + "/releases/latest"); rel_date = rel["published_at"][:10]; rel_tag = rel["tag_name"]
        except Exception: pass
    push_days = (today - datetime.date.fromisoformat(d["pushed_at"][:10])).days
    rel_days = (today - datetime.date.fromisoformat(rel_date)).days if rel_date else None
    ratio = d["open_issues_count"] / max(d["stargazers_count"], 1)
    parts = dict(recent_push=round(40 * max(0, 1 - push_days / 180)), recent_release=round(20 * max(0, 1 - rel_days / 365)) if rel_days is not None else 0,
                 issue_ratio=round(20 * max(0, 1 - ratio / .1)), licence=10 if d.get("license") else 0, not_archived=0 if d["archived"] else 10)
    score = sum(parts.values())
    if source == "search-api": parts.pop("recent_release"); score = round(sum(parts.values()) * 100 / 80)     # release data unavailable: rescale the other 80 points
    return dict(repo=repo, score=score, grade="healthy" if score >= 70 else "watch" if score >= 45 else "at risk", stars=d["stargazers_count"], open_issues=d["open_issues_count"],
                last_push=d["pushed_at"][:10], last_release=rel_tag, last_release_date=rel_date, licence=(d.get("license") or {}).get("spdx_id"), archived=d["archived"], parts=parts, data_source=source)
def run(repos):
    res = [check(r.strip()) for r in repos if r.strip()][:20]                # cap work per invocation
    return dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), results=sorted(res, key=lambda r: r.get("score", -1)))
