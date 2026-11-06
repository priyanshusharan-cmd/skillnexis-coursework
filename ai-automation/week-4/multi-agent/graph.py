"""Multi-agent workflow (LangGraph, LangChain's agent-orchestration library) for one specific task: writing a
**library selection brief**. Given a need such as "HTTP client for an async web scraper", four agents collaborate
over a shared state:

  Planner    -> turns the need into candidate packages and evaluation criteria
  Researcher -> gathers facts with real tools (PyPI JSON API, GitHub API) for every candidate
  Analyst    -> scores the candidates on maintenance, maturity, popularity and fit (a transparent formula)
  Writer     -> drafts the brief with a recommendation and citations
  Reviewer   -> checks every number in the draft against the research data and that every candidate is covered;
               sends the draft back to the Writer with notes if a check fails (at most 2 revisions)

With an LLM configured (llm.py: Gemini / OpenAI-compatible / Ollama), the Planner and Writer use it; without one they
fall back to rules and templates. Research, analysis and review are always deterministic, so their numbers can be
trusted and re-checked.   python graph.py "HTTP client for an async web scraper" """
import datetime, json, math, operator, os, re, sys
from typing import Annotated, TypedDict
from langgraph.graph import END, StateGraph
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "research-agent"))
import llm, tools
class State(TypedDict, total=False):
    need: str; candidates: list; criteria: dict; facts: dict; scores: list; draft: str; review: dict; revisions: int
    log: Annotated[list, operator.add]                                     # every agent appends its messages
KNOWN = {"http": ["httpx", "aiohttp", "requests"], "scrap": ["scrapy", "beautifulsoup4", "selectolax"], "dataframe": ["pandas", "polars", "duckdb"],
         "web framework": ["fastapi", "flask", "django"], "api": ["fastapi", "flask", "litestar"], "test": ["pytest", "hypothesis", "nose2"], "pdf": ["pypdf", "pdfplumber", "pymupdf"],
         "task queue": ["celery", "rq", "dramatiq"], "cli": ["typer", "click", "argparse-manpage"], "orm": ["sqlalchemy", "peewee", "tortoise-orm"]}
def planner(s):
    need = s["need"].lower(); cands = None
    try:
        out, eng = llm.chat(f'Need: {s["need"]}\nReturn JSON {{"candidates": [3 exact PyPI package names]}}.', json_mode=True); cands = llm.parse_json(out)["candidates"][:3]; how = eng
    except RuntimeError:
        hits = [v for k, v in KNOWN.items() if k in need]; cands = (hits[0] if hits else ["requests", "httpx", "aiohttp"]); how = "rules"
    async_need = bool(re.search(r"\basync|asyncio|concurren", need))
    crit = dict(maintenance=.35, maturity=.2, popularity=.25, fit=.2, async_required=async_need)
    return dict(candidates=cands, criteria=crit, revisions=0, log=[dict(agent="Planner", msg=f"candidates {cands} via {how}; criteria {crit}")])
def researcher(s):
    facts = {}
    for c in s["candidates"]:
        p = tools.run("pypi_package", c); f = dict(pypi=p["results"][0] if p["ok"] else None, github=None, error=None if p["ok"] else p["error"])
        if p["ok"] and p["results"][0]["facts"].get("repo"):
            repo = p["results"][0]["facts"]["repo"]; g = tools.run("github_search", f"repo:{repo}")
            if g["ok"] and g["results"]: f["github"] = g["results"][0]
        facts[c] = f
    return dict(facts=facts, log=[dict(agent="Researcher", msg=f"PyPI + GitHub facts for {', '.join(c for c in facts if facts[c]['pypi'])}; failed: {[c for c in facts if not facts[c]['pypi']]}")])
def analyst(s):
    today = datetime.date.today(); rows = []
    for c, f in s["facts"].items():
        if not f["pypi"]: continue
        p = f["pypi"]["facts"]; g = (f["github"] or {}).get("facts", {})
        days = (today - datetime.date.fromisoformat(p["released"])).days if p.get("released") else 9999
        years = (today - datetime.date.fromisoformat(p["first_release"])).days / 365 if p.get("first_release") else 0
        stars = g.get("stars", 0); summary = (f["pypi"]["snippet"] + " " + " ".join(g.get("topics", []))).lower()
        sc = dict(maintenance=max(0, 1 - days / 540), maturity=min(1, years / 8), popularity=min(1, math.log10(stars + 1) / 5),
                  fit=1.0 if not s["criteria"]["async_required"] else (1.0 if re.search(r"async", summary) else .25))
        total = sum(s["criteria"][k] * v for k, v in sc.items())
        if s["criteria"]["async_required"] and sc["fit"] < 1: total *= .6           # a hard requirement the package doesn't meet
        rows.append(dict(package=c, total=round(total, 3), **{k: round(v, 2) for k, v in sc.items()}, latest=p["latest"], released=p["released"], days_since_release=days,
                         first_release=p["first_release"], stars=stars, url=f["pypi"]["url"], repo_url=(f["github"] or {}).get("url")))
    rows.sort(key=lambda r: -r["total"])
    return dict(scores=rows, log=[dict(agent="Analyst", msg="ranking " + ", ".join(f"{r['package']} {r['total']:.2f}" for r in rows))])
def writer(s):
    r = s["scores"]; notes = (s.get("review") or {}).get("notes", []); best = r[0]
    try:
        out, eng = llm.chat("Write a 200-word library selection brief in markdown with a recommendation. Use ONLY these numbers and cite urls:\n" + json.dumps(r) + "\nNeed: " + s["need"] + ("\nFix: " + "; ".join(notes) if notes else ""))
        draft = out
    except RuntimeError:
        eng = "template"
        why = []
        if best["maintenance"] >= max(x["maintenance"] for x in r): why.append(f"the most recent release ({best['latest']}, {best['released']})")
        if best["fit"] == 1 and s["criteria"]["async_required"]: why.append("native async support, which the need requires")
        if best["stars"] >= max(x["stars"] for x in r): why.append(f"the largest community ({best['stars']:,} GitHub stars)")
        lines = [f"# Library brief: {s['need']}", "", f"**Recommendation: `{best['package']}`** (score {best['total']:.2f} of 1), chosen for " + (", ".join(why) or "the best overall balance") + ".", "",
                 "| Package | Score | Latest | Released | First release | GitHub stars | Meets requirements |", "|---|---|---|---|---|---|---|"]
        lines += [f"| [{x['package']}]({x['url']}) | {x['total']:.2f} | {x['latest']} | {x['released']} | {x['first_release']} | {x['stars']:,} | {'yes' if x['fit'] == 1 else 'partial'} |" for x in r]
        lines += ["", f"**Runner-up:** `{r[1]['package']}` ({r[1]['total']:.2f})." if len(r) > 1 else "", "",
                  ("*Async is a hard requirement here, so packages without native async support get a 40 % penalty.*  \n" if s["criteria"]["async_required"] else "") + f"*Scoring:* maintenance {s['criteria']['maintenance']:.0%} (days since last release), popularity {s['criteria']['popularity']:.0%} (log GitHub stars), maturity {s['criteria']['maturity']:.0%} (years since first release), fit {s['criteria']['fit']:.0%}. Data from PyPI and GitHub on {datetime.date.today()}."]
        draft = "\n".join(lines)
    return dict(draft=draft, revisions=s.get("revisions", 0) + (1 if notes else 0), log=[dict(agent="Writer", msg=f"draft {len(draft)} chars via {eng}" + (f", revised for: {notes}" if notes else ""))])
def reviewer(s):
    """Fact check: every version number, date and star count in the draft must come from the research data."""
    known = set()
    for x in s["scores"]: known |= {x["latest"], x["released"], x["first_release"], f"{x['stars']:,}", str(x["stars"]), f"{x['total']:.2f}"}
    known |= {str(datetime.date.today())}
    found = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b|\b\d+\.\d+(?:\.\d+)*\b|\b\d{1,3}(?:,\d{3})+\b", s["draft"]))
    allowed_small = {f"{v:.2f}" for v in (0, 1)} | {"1"}
    unknown = sorted(n for n in found - known - allowed_small if not re.fullmatch(r"0\.\d{2}", n) or n not in {f"{x['total']:.2f}" for x in s["scores"]})
    unknown = [n for n in unknown if n not in known]
    missing = [x["package"] for x in s["scores"] if x["package"] not in s["draft"]]
    notes = ([f"numbers not in the research data: {unknown}"] if unknown else []) + ([f"candidates not covered: {missing}"] if missing else [])
    ok = not notes
    return dict(review=dict(ok=ok, notes=notes, numbers_checked=len(found)), log=[dict(agent="Reviewer", msg=("approved: " if ok else "changes requested: ") + (f"{len(found)} numbers verified" if ok else "; ".join(notes)))])
def route(s): return END if s["review"]["ok"] or s["revisions"] >= 2 else "writer"
g = StateGraph(State)
for n, f in [("planner", planner), ("researcher", researcher), ("analyst", analyst), ("writer", writer), ("reviewer", reviewer)]: g.add_node(n, f)
g.set_entry_point("planner"); g.add_edge("planner", "researcher"); g.add_edge("researcher", "analyst"); g.add_edge("analyst", "writer"); g.add_edge("writer", "reviewer")
g.add_conditional_edges("reviewer", route, {"writer": "writer", END: END}); APP = g.compile()
if __name__ == "__main__":
    need = " ".join(sys.argv[1:]) or "HTTP client for an async web scraper"
    final = APP.invoke(dict(need=need, log=[]))
    os.makedirs("runs", exist_ok=True); slug = re.sub(r"[^a-z0-9]+", "-", need.lower()).strip("-")[:50]
    open(f"runs/{slug}.md", "w").write(final["draft"] + "\n\n---\n## Agent log\n\n" + "\n".join(f"{i}. **{m['agent']}**: {m['msg']}" for i, m in enumerate(final["log"], 1)) + f"\n\nReview: {final['review']}\n")
    json.dump({k: v for k, v in final.items()}, open(f"runs/{slug}.json", "w"), indent=1, default=str)
    print(open(f"runs/{slug}.md").read())
    try: open("graph.mmd", "w").write(APP.get_graph().draw_mermaid())
    except Exception: pass
