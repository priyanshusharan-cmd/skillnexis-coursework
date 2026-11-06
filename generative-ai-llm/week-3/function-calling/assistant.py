"""Function-calling assistant. With an LLM configured, the specs are bound as tools (LangChain bind_tools works for
Gemini, OpenAI-compatible APIs and Ollama): the model emits tool calls, we validate and execute them, return the
results, and the model writes the answer. Offline, a rule-based planner emits the same {name, arguments} JSON, so the
validation and execution path is identical.
    python assistant.py ["request"] -> ../results/function_calling.md"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "week-2"))
from functions import SPECS, execute
from common.models import chat_model
def plan(req):
    """Offline planner: request -> list of function calls (the JSON an LLM would produce)."""
    r = req.lower(); calls = []
    m = re.search(r"compare ([\w.,\s-]+?)(?:\?|$| on | by )", r)
    if m: calls.append(dict(name="compare_packages", arguments=dict(names=[x for x in re.split(r",\s*|\s+and\s+|\s+vs\.?\s+|\s+", m.group(1)) if x])))
    m = re.search(r"(?:convert\s+)?([\d.]+)\s*(kb|mb|gb|tb|b|ms|s|min|h|hours?|days?|minutes?|seconds?)\s+(?:to|in|into)\s+(kb|mb|gb|tb|b|ms|s|min|h|hours?|days?|minutes?|seconds?)\b", r)
    if m:
        norm = lambda u: {"hours": "h", "hour": "h", "days": "day", "minutes": "min", "minute": "min", "seconds": "s", "second": "s"}.get(u, u)
        calls.append(dict(name="convert_units", arguments=dict(value=float(m.group(1)), from_unit=norm(m.group(2)), to_unit=norm(m.group(3)))))
    m = re.search(r"(?:version|release|licen[cs]e|about) (?:of |for )?(?:the )?(?:package )?([a-z0-9._-]+)", r)
    if m and not calls: calls.append(dict(name="get_package_info", arguments=dict(name=m.group(1))))
    m = re.search(r"(?:top|most[- ]starred|popular|best)\s+(\d+)?\s*(.+?) (?:repositories|repos|projects|libraries)\b(?: in| written in)? ?(\w+)?", r) or \
        re.search(r"find\s+(\d+)?\s*(?:the )?(.+?) (?:repositories|repos|projects|libraries)\b(?: in| written in)? ?(\w+)?", r)
    if m and not calls:
        a = dict(query=m.group(2).replace("github", "").strip(), sort="updated" if "recent" in r else "stars", limit=int(m.group(1)) if m.group(1) else 5)
        if m.group(3) and m.group(3) not in ("on", "github"): a["language"] = m.group(3)
        calls.append(dict(name="search_github", arguments=a))
    return calls
def summarise(req, results):
    out = []
    for c, r in results:
        if not r["ok"]: out.append(f"⚠️ {c['name']} failed: {r['error']}"); continue
        v = r["result"]
        if c["name"] == "get_package_info": out.append(v.get("error") or f"**{v['name']} {v['version']}** (released {v['released']}, {v['releases']} releases, licence {v['licence'] or 'n/a'}): {v['summary']}. {v['url']}")
        elif c["name"] == "compare_packages": out.append("| Package | Latest | Released | Releases |\n|---|---|---|---|\n" + "\n".join(f"| {p.get('name', '?')} | {p.get('version', '—')} | {p.get('released', '—')} | {p.get('releases', '—')} |" if "error" not in p else f"| ? | {p['error']} | | |" for p in v))
        elif c["name"] == "search_github": out.append("\n".join(f"- [{x['repo']}]({x['url']}): {x['stars']:,} ★, updated {x['updated']}. {x['description']}" for x in v) or "no repositories found")
        elif c["name"] == "convert_units": out.append(v.get("error") or f"{v['value']:g} {v['from_unit']} = **{v['result']:g} {v['to_unit']}**")
    return "\n\n".join(out) or "I couldn't map that request to any of my functions (PyPI info, package comparison, GitHub search, unit conversion)."
def run(req):
    llm = chat_model(); log = []
    if llm is not None:
        from langchain_core.messages import HumanMessage, ToolMessage
        bound = llm.bind_tools([{"type": "function", "function": s} for s in SPECS]); msgs = [HumanMessage(req)]
        for _ in range(4):
            ai = bound.invoke(msgs); msgs.append(ai)
            if not ai.tool_calls: return dict(engine=type(llm).__name__, calls=log, answer=ai.content)
            for tc in ai.tool_calls:
                r = execute(dict(name=tc["name"], arguments=tc["args"])); log.append(dict(call=dict(name=tc["name"], arguments=tc["args"]), ok=r["ok"], error=r.get("error")))
                msgs.append(ToolMessage(json.dumps(r)[:4000], tool_call_id=tc["id"]))
        return dict(engine=type(llm).__name__, calls=log, answer=msgs[-1].content)
    results = []
    for c in plan(req):
        r = execute(c)
        if not r["ok"] and "maximum" in r["error"] and c["name"] == "search_github":            # self-correct: clamp to the schema's maximum and retry
            log.append(dict(call=c, ok=False, error=r["error"])); c = dict(c, arguments=dict(c["arguments"], limit=10)); r = execute(c)
        log.append(dict(call=c, ok=r["ok"], error=r.get("error"))); results.append((c, r))
    return dict(engine="rule planner", calls=log, answer=summarise(req, results))
REQS = ["What's the latest version of fastapi?", "Compare httpx, requests and aiohttp", "Find the top 25 vector database repositories in rust",
        "Convert 3.5 GB to MB", "What's the licence of the package definitely-not-a-real-package-xyz?", "Book me a flight to Goa"]
if __name__ == "__main__":
    reqs = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else REQS; md = ["# Function calling runs", ""]
    for q in reqs:
        r = run(q); md += [f"## {q}", "", f"*engine: {r['engine']}*", "", "Function calls (validated against the JSON schema before running):", ""]
        md += [f"- `{json.dumps(c['call'])}` → {'✅ ok' if c['ok'] else '❌ ' + c['error']}" for c in r["calls"]] or ["- none"]
        md += ["", r["answer"], ""]; print(q, "->", r["answer"][:150].replace("\n", " "))
    if len(sys.argv) == 1: open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "function_calling.md"), "w").write("\n".join(md) + "\n")
