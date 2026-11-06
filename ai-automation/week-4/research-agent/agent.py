"""Research agent: answers a question by deciding which tools to call, reading the results and writing a cited answer.
* With an LLM (Gemini / OpenAI-compatible / Ollama, see llm.py): a ReAct loop. The model gets the tool list, replies
  with JSON {"thought", "action", "input"} or {"final_answer"}, sees each observation, and can take up to 6 steps.
* Without an LLM: a deterministic planner (question patterns -> tool plan) and a templated, cited synthesis. This
  is the mode the committed transcripts were made in.
Every run is saved as a transcript (steps, tool calls, observations, answer, sources).
    python agent.py "Which Python libraries are most popular for web scraping, and are they maintained?" """
import datetime, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import llm, tools
SYSTEM = """You are a careful research agent. Tools:
{tools}
Reply ONLY with JSON. To use a tool: {{"thought": "...", "action": "<tool>", "input": "<arg>"}}.
When you can answer: {{"final_answer": "<answer in markdown with [n] citations>", "sources": ["<url>", ...]}}.
Use facts from observations only; if a tool fails, try another; at most 6 tool calls."""
def react(q, max_steps=6):
    tl = "\n".join(f"- {k}: {v[1]}" for k, v in tools.TOOLS.items()); convo = f"QUESTION: {q}\n"; steps = []
    for _ in range(max_steps):
        out, engine = llm.chat(convo, system=SYSTEM.format(tools=tl), temperature=.2, json_mode=True); d = llm.parse_json(out)
        if "final_answer" in d: return dict(engine=engine, steps=steps, answer=d["final_answer"], sources=d.get("sources", []))
        obs = tools.run(d["action"], d["input"]); steps.append(dict(thought=d.get("thought", ""), action=d["action"], input=d["input"], observation=obs))
        convo += f"\nACTION: {json.dumps(d)}\nOBSERVATION: {json.dumps(obs)[:3500]}\n"
    out, engine = llm.chat(convo + "\nYou must now give the final_answer.", system=SYSTEM.format(tools=tl), json_mode=True); d = llm.parse_json(out)
    return dict(engine=engine, steps=steps, answer=d.get("final_answer", out), sources=d.get("sources", []))
# ---------------- offline planner ----------------
PKG = re.compile(r"\b(?:compare|vs\.?|versus|between)\b", re.I)
def plan(q):
    """Question -> list of (tool, arg). Package names are words that exist on PyPI (checked via the tool itself)."""
    ql = q.lower(); steps = []
    names = re.findall(r"\b([a-z][a-z0-9_-]{1,30})\b", ql)
    named = [n for n in names if n not in llm.STOP and n not in {"python", "library", "libraries", "package", "packages", "compare", "which", "best", "popular", "most", "maintained", "latest", "version", "versions", "and", "the", "for", "how", "what", "vs", "versus", "between", "is", "are"}]
    if re.search(r"\b(librar|package|framework|tool|module)", ql) or PKG.search(ql):
        topic = re.sub(r".*?\b(?:for|to do|doing)\b\s+", "", ql) if re.search(r"\bfor\b", ql) else " ".join(named[:3])
        topic = re.sub(r"[,?].*", "", topic).strip()
        if PKG.search(ql): steps += [("pypi_package", n) for n in named[:3]]
        else: steps.append(("github_search", f"{topic} language:python"))
    else:
        steps += [("wikipedia", q), ("web_search", q)]
    return steps
def offline(q):
    steps = []
    for t, a in plan(q):
        obs = tools.run(t, a); steps.append(dict(thought=f"planner: {t} looks right for this question", action=t, input=a, observation=obs))
        if t == "web_search" and not obs["ok"] and not any(x["observation"]["ok"] for x in steps):       # both general tools failed: fall back to GitHub
            t, a = "github_search", re.sub(r"^(what|who|how|why) (is|are|does|do) ", "", q.lower()).strip(" ?"); obs = tools.run(t, a)
            steps.append(dict(thought="planner: general search unavailable, so look for projects on the topic instead", action=t, input=a, observation=obs))
        if t == "github_search" and obs["ok"]:                                       # follow-up: PyPI facts for the top repos
            for r in obs["results"][:4]:
                name = r["title"].split("/")[1].lower(); o2 = tools.run("pypi_package", name)
                steps.append(dict(thought=f"planner: check {name} on PyPI for its latest release", action="pypi_package", input=name, observation=o2))
    return dict(engine="offline:planner + template", steps=steps, **synthesise(q, steps))
def synthesise(q, steps):
    today = datetime.date.today(); src, lines, failed = [], [], []
    def cite(url):
        if url not in src: src.append(url)
        return f"[{src.index(url) + 1}]"
    pypi = {s["input"]: s["observation"]["results"][0] for s in steps if s["action"] == "pypi_package" and s["observation"]["ok"]}
    for s in steps:
        o = s["observation"]
        if not o["ok"]: failed.append(f"{s['action']}({s['input']}): {o['error']}"); continue
        if s["action"] == "github_search":
            lines.append(f"**Most-starred matching repositories on GitHub** (searched {today}):")
            for r in o["results"]:
                f = r["facts"]; age = (today - datetime.date.fromisoformat(f["last_push"])).days; name = r["title"].split("/")[1].lower(); p = pypi.get(name)
                # only attach PyPI facts when the PyPI project links back to THIS repository (names can belong to someone else)
                same = p and r["title"].lower() in p["facts"].get("repos", [])
                rel = f"; PyPI {p['facts']['latest']} released {p['facts']['released']} {cite(p['url'])}" if same else ("; its PyPI namesake doesn't link back to this repo, so no version is claimed" if p else "")
                lines.append(f"- **{r['title']}**: {f['stars']:,} stars, last push {f['last_push']} ({'active' if age <= 90 else f'{age} days ago'}){rel}. {r['snippet'][:110]} {cite(r['url'])}")
        elif s["action"] == "pypi_package" and not any(x["action"] == "github_search" for x in steps):
            r = o["results"][0]; f = r["facts"]
            lines.append(f"- **{r['title'].replace(' on PyPI', '')}** {f['latest']} (released {f['released']}, first release {f['first_release']}, {f['releases']} releases, Python {f['requires_python']}): {r['snippet']} {cite(r['url'])}")
        elif s["action"] in ("wikipedia", "web_search"):
            for r in o["results"][:3]: lines.append(f"- {r['snippet'][:300]} {cite(r['url'])}")
    if not lines: return dict(answer="I couldn't find information with the tools available. Failed calls:\n" + "\n".join(failed), sources=src, failed=failed)
    ans = f"**Question:** {q}\n\n" + "\n".join(lines)
    if any(x["action"] == "github_search" for x in steps):
        ok = [s for s in steps if s["action"] == "github_search" and s["observation"]["ok"]]
        if ok:
            act = [r["title"] for r in ok[0]["observation"]["results"] if (today - datetime.date.fromisoformat(r["facts"]["last_push"])).days <= 90]
            ans += f"\n\n**Answer:** by GitHub stars the leaders are {', '.join(r['title'] for r in ok[0]['observation']['results'][:3])}. {len(act)} of {len(ok[0]['observation']['results'])} were pushed to in the last 90 days, a reasonable sign of active maintenance. Stars measure popularity, not quality, so check the docs and issue tracker before choosing."
    if failed: ans += "\n\n*Tools that failed (unreachable from this environment):* " + "; ".join(failed)
    return dict(answer=ans, sources=src, failed=failed)
def research(q):
    try: return react(q)
    except RuntimeError: return offline(q)
if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Which Python libraries are most popular for web scraping, and are they maintained?"
    r = research(q); r["question"] = q; r["date"] = datetime.date.today().isoformat()
    os.makedirs("transcripts", exist_ok=True); slug = re.sub(r"[^a-z0-9]+", "-", q.lower())[:50].strip("-")
    json.dump(r, open(f"transcripts/{slug}.json", "w"), indent=1, ensure_ascii=False)
    md = [f"# {q}", "", f"*{r['date']} · engine: {r['engine']} · {len(r['steps'])} tool calls*", "", "## Steps", ""]
    md += [f"{i}. `{s['action']}({s['input']!r})` → {'ok, ' + str(len(s['observation']['results'])) + ' results' if s['observation']['ok'] else 'FAILED: ' + s['observation']['error']}" for i, s in enumerate(r["steps"], 1)]
    md += ["", "## Answer", "", r["answer"], "", "## Sources", ""] + [f"{i}. {u}" for i, u in enumerate(r["sources"], 1)]
    open(f"transcripts/{slug}.md", "w").write("\n".join(md) + "\n"); print("\n".join(md))
