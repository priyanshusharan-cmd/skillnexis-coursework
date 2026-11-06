"""Multi-agent research assistant (LangGraph). Three agents pass a shared state:
  Searcher   plans 3-5 search queries for the topic, runs them across GitHub, PyPI, Wikipedia and DuckDuckGo
             (whatever is reachable), and de-duplicates the sources
  Summarizer writes a short summary of each source and pulls out its key facts (stars, versions, dates)
  Writer     turns the summaries into a structured report: overview, key findings, comparison table, open
             questions, numbered sources
With an LLM configured (GEMINI_API_KEY / OLLAMA_MODEL / OPENAI_API_KEY) the Searcher's query planning, the summaries
and the report prose come from the LLM; otherwise rules and templates do it, and every number still comes from the
tools. The Writer's report is checked: every [n] citation must point to a real source.
    python agents.py "vector databases in Python"  -> reports/<topic>.md"""
import datetime, json, operator, os, re, sys
from typing import Annotated, TypedDict
from langgraph.graph import END, StateGraph
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "..", "week-2"))
import search_tools as T
from common.models import chat_model
class S(TypedDict, total=False):
    topic: str; queries: list; sources: list; summaries: list; report: str; checks: dict
    log: Annotated[list, operator.add]
def llm_json(prompt):
    m = chat_model()
    if m is None: return None
    txt = m.invoke(prompt).content; g = re.search(r"\{.*\}|\[.*\]", txt, re.S); return json.loads(g.group(0)) if g else None
def searcher(s):
    t = s["topic"]; plan = llm_json(f"Plan 4 web search queries to research: {t}. Return a JSON list of objects {{\"tool\": one of github_search|pypi_package|wikipedia|web_search, \"q\": query}}.")
    if not plan:
        core = re.sub(r"\b(in|for|with|python|the|a|an|of)\b", " ", t.lower()); core = " ".join(core.split())
        plan = [dict(tool="github_search", q=f"{core} language:python" if "python" in t.lower() else core), dict(tool="wikipedia", q=t), dict(tool="web_search", q=f"{t} comparison"), dict(tool="github_search", q=f"{core} topic:{core.split()[0]}")]
    srcs, seen, notes = [], set(), []
    for p in plan:
        r = T.run(p["tool"], p["q"]); notes.append(f"{p['tool']}({p['q']!r}) -> " + (f"{len(r['results'])} results" if r["ok"] else "unavailable: " + r["error"][:60]))
        for x in (r["results"] if r["ok"] else []):
            if x["url"] in seen: continue
            seen.add(x["url"]); srcs.append(dict(x, tool=p["tool"]))
    for x in [x for x in srcs if x["tool"] == "github_search"][:4]:                 # enrich: PyPI facts for the top repos when the package links back
        name = x["title"].split("/")[1].lower(); r = T.run("pypi_package", name)
        if r["ok"] and x["title"].lower() in r["results"][0]["facts"].get("repos", []): x["facts"]["pypi_latest"], x["facts"]["pypi_released"] = r["results"][0]["facts"]["latest"], r["results"][0]["facts"]["released"]
    return dict(queries=plan, sources=srcs[:12], log=[dict(agent="Searcher", msg="; ".join(notes) + f" | {len(srcs[:12])} unique sources")])
def summarizer(s):
    out = []
    for i, x in enumerate(s["sources"], 1):
        f = x.get("facts", {}); llm = llm_json(f"Summarise this source in one sentence and list up to 3 key facts as JSON {{\"summary\": str, \"facts\": [str]}}.\n{x['title']}\n{x['snippet']}\n{json.dumps(f)}")
        if llm: out.append(dict(n=i, title=x["title"], url=x["url"], summary=llm["summary"], facts=llm["facts"])); continue
        facts = []
        if "stars" in f: facts.append(f"{f['stars']:,} GitHub stars")
        if f.get("last_push"): facts.append(f"last commit {f['last_push']}")
        if f.get("pypi_latest"): facts.append(f"PyPI {f['pypi_latest']} ({f['pypi_released']})")
        if f.get("licence"): facts.append(f"licence {f['licence']}")
        if f.get("latest") and not f.get("pypi_latest"): facts.append(f"latest {f['latest']} ({f.get('released')})")
        sent = re.split(r"(?<=[.!?])\s", (x["snippet"] or "").strip())[0][:220]
        out.append(dict(n=i, title=x["title"], url=x["url"], summary=sent or "(no description)", facts=facts, stars=f.get("stars", 0), last_push=f.get("last_push")))
    return dict(summaries=out, log=[dict(agent="Summarizer", msg=f"summarised {len(out)} sources")])
def writer(s):
    sm, t, today = s["summaries"], s["topic"], datetime.date.today()
    llm = chat_model()
    if llm is not None:
        rep = llm.invoke(f"Write a structured research report on '{t}' in markdown with sections Overview, Key findings, Comparison table, Open questions, Sources. Use ONLY these source summaries and cite them as [n]:\n{json.dumps(sm)}").content
    else:
        repos = sorted([x for x in sm if x.get("stars")], key=lambda x: -x["stars"]); active = [x for x in repos if x.get("last_push") and (today - datetime.date.fromisoformat(x["last_push"])).days <= 60]
        L = [f"# Research report: {t}", f"*{today} · generated by a 3-agent pipeline (Searcher → Summarizer → Writer)*", "", "## Overview", ""]
        L.append(f"I found {len(sm)} sources on **{t}**" + (f", including {len(repos)} open-source projects. The most widely adopted by GitHub stars is **{repos[0]['title']}** [{repos[0]['n']}]" if repos else "") + ".")
        if repos: L.append(f"{len(active)} of the {len(repos)} projects had commits in the last 60 days, a sign of active maintenance.")
        L += ["", "## Key findings", ""] + [f"- **{x['title']}**: {x['summary']}" + (f" ({'; '.join(x['facts'])})" if x["facts"] else "") + f" [{x['n']}]" for x in sm[:8]]
        if repos:
            L += ["", "## Comparison", "", "| Project | Stars | Last commit | Latest release | Licence |", "|---|---|---|---|---|"]
            for x in repos[:6]:
                fx = next(f for f in s["sources"] if f["url"] == x["url"])["facts"]
                L.append(f"| [{x['title']}]({x['url']}) [{x['n']}] | {x['stars']:,} | {x['last_push']} | {fx.get('pypi_latest', '—')} | {fx.get('licence') or '—'} |")
        L += ["", "## Open questions", "", "- Stars measure popularity, not fitness: benchmark the top candidates on your own data and workload.", "- Check the licences against your use (several projects use copyleft or source-available licences).",
              "- General web and encyclopedia sources were unavailable here; a run with web access adds articles and docs." if not any(x["url"].startswith(("https://en.wikipedia", "http")) and "github.com" not in x["url"] and "pypi.org" not in x["url"] for x in sm) else "- Cross-check claims in the articles against the projects' own documentation."]
        L += ["", "## Sources", ""] + [f"{x['n']}. [{x['title']}]({x['url']})" for x in sm]
        rep = "\n".join(L)
    cites = {int(c) for c in re.findall(r"\[(\d+)\]", rep)}; bad = sorted(c for c in cites if c < 1 or c > len(sm))
    return dict(report=rep, checks=dict(citations=len(cites), invalid_citations=bad, sources=len(sm)), log=[dict(agent="Writer", msg=f"report {len(rep)} chars, {len(cites)} distinct citations, invalid: {bad or 'none'}")])
g = StateGraph(S); [g.add_node(n, f) for n, f in (("searcher", searcher), ("summarizer", summarizer), ("writer", writer))]
g.set_entry_point("searcher"); g.add_edge("searcher", "summarizer"); g.add_edge("summarizer", "writer"); g.add_edge("writer", END); APP = g.compile()
def research(topic, on_step=None):
    state = dict(topic=topic, log=[])
    for ev in APP.stream(state, stream_mode="updates"):
        for node, upd in ev.items():
            state.update({k: v for k, v in upd.items() if k != "log"}); state["log"] = state.get("log", []) + upd.get("log", [])
            if on_step: on_step(node, upd)
    return state
if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) or "vector databases in Python"; st = research(topic, lambda n, u: print(f"[{n}] {u['log'][0]['msg'][:200]}", flush=True))
    os.makedirs(os.path.join(HERE, "reports"), exist_ok=True); slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:50]
    open(os.path.join(HERE, "reports", slug + ".md"), "w").write(st["report"] + "\n\n---\n### Agent log\n\n" + "\n".join(f"- **{m['agent']}**: {m['msg']}" for m in st["log"]) + "\n")
    print(st["checks"])
