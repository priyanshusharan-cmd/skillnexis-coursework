"""Search tools for the research agent. Each returns a list of {title, url, snippet, facts} so answers can cite
sources. All are free and need no key (a GITHUB_TOKEN only raises GitHub's rate limit).
  github_search   GitHub repository search API (stars, description, last push, licence)
  pypi_package    PyPI JSON API (latest version, release date, summary, licence, required Python)
  wikipedia       Wikipedia search + REST summary
  web_search      DuckDuckGo HTML results
  read_page       fetch and extract a page's main text
Where a host is unreachable (this sandbox only reaches GitHub and PyPI) the tool returns an error the agent can see
and route around."""
import datetime, os, re
import requests
from bs4 import BeautifulSoup
UA = {"User-Agent": "skillnexis-research-agent/1.0 (+https://github.com/priyanshusharan-cmd/skillnexis-coursework)"}
def _get(url, **kw):
    h = dict(UA); h.update(kw.pop("headers", {})); r = requests.get(url, headers=h, timeout=15, **kw); r.raise_for_status(); return r
def github_search(query, n=5):
    h = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"): h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    items = _get("https://api.github.com/search/repositories", params={"q": query, "sort": "stars", "order": "desc", "per_page": n}, headers=h).json().get("items", [])
    return [dict(title=i["full_name"], url=i["html_url"], snippet=i.get("description") or "", facts=dict(stars=i["stargazers_count"], forks=i["forks_count"], language=i.get("language"),
                 last_push=i["pushed_at"][:10], licence=(i.get("license") or {}).get("spdx_id"), topics=i.get("topics", [])[:6])) for i in items]
def pypi_package(name):
    d = _get(f"https://pypi.org/pypi/{name}/json").json(); info = d["info"]; rel = d["releases"].get(info["version"], [])
    up = rel[0]["upload_time"][:10] if rel else None
    first = min((f["upload_time"][:10] for v in d["releases"].values() for f in v), default=None)
    proj = dict(info.get("project_urls") or {}); proj["home_page"] = info.get("home_page") or ""
    repos = sorted({re.sub(r"^https?://(www\.)?github\.com/([^/#?]+/[^/#?]+).*$", r"\2", u).removesuffix(".git").lower() for u in proj.values() if u and "github.com/" in u})
    repo = repos[0] if repos else None
    return [dict(title=f"{info['name']} on PyPI", url=f"https://pypi.org/project/{info['name']}/", snippet=info.get("summary") or "",
                 facts=dict(latest=info["version"], released=up, first_release=first, requires_python=info.get("requires_python"), licence=info.get("license_expression") or (info.get("license") or "")[:40], repo=repo, repos=repos, releases=len(d["releases"])))]
def wikipedia(query, n=3):
    s = _get("https://en.wikipedia.org/w/api.php", params={"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": n}).json()["query"]["search"]
    out = []
    for r in s:
        t = r["title"]; sm = _get("https://en.wikipedia.org/api/rest_v1/page/summary/" + t.replace(" ", "_")).json()
        out.append(dict(title=t + " (Wikipedia)", url=sm.get("content_urls", {}).get("desktop", {}).get("page", ""), snippet=sm.get("extract", ""), facts={}))
    return out
def web_search(query, n=5):
    soup = BeautifulSoup(_get("https://html.duckduckgo.com/html/", params={"q": query}).text, "lxml"); out = []
    for r in soup.select(".result")[:n]:
        a = r.select_one(".result__a"); s = r.select_one(".result__snippet")
        if a: out.append(dict(title=a.get_text(" ", strip=True), url=a.get("href"), snippet=s.get_text(" ", strip=True) if s else "", facts={}))
    return out
def read_page(url):
    from extract import article  # noqa
    a = article(url); return [dict(title=a["title"] or url, url=url, snippet=a["text"][:1500], facts=dict(words=a["words"]))]
TOOLS = {"github_search": (github_search, "search GitHub repositories, sorted by stars. arg: query"), "pypi_package": (pypi_package, "facts about a Python package from PyPI. arg: exact package name"),
         "wikipedia": (wikipedia, "encyclopedia summaries. arg: query"), "web_search": (web_search, "general web search (DuckDuckGo). arg: query"), "read_page": (read_page, "read one web page. arg: url")}
def run(tool, arg):
    try: return dict(ok=True, results=TOOLS[tool][0](arg))
    except Exception as e: return dict(ok=False, error=f"{type(e).__name__}: {str(e)[:160]}")
