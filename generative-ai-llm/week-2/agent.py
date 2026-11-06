"""Task 4: an agent with 3 tools: web search, calculator, document retrieval (LangChain tools).
* With a chat model configured: LangGraph's prebuilt ReAct agent (create_react_agent) picks and chains tools itself.
* Without one: a transparent router plans the tool calls from the question (an arithmetic expression goes to the
  calculator; "PEP" or Python language features go to retrieval; versions, stars and "latest" go to web search), and
  can chain them (look up two PEP dates, then compute the gap). Each step is logged.
Web search uses DuckDuckGo where reachable and falls back to the GitHub and PyPI APIs (all this sandbox can reach).
    python agent.py ["question"] -> results/agent_runs.md"""
import ast, datetime, json, operator as op, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import requests
from langchain_core.tools import tool
from common.models import chat_model
from common.rag import HybridRetriever
HERE = os.path.dirname(os.path.abspath(__file__)); R = HybridRetriever(os.path.join(HERE, "chroma"))
OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod, ast.FloorDiv: op.floordiv, ast.USub: op.neg, ast.UAdd: op.pos}
def _eval(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)): return n.value
    if isinstance(n, ast.BinOp) and type(n.op) in OPS:
        if isinstance(n.op, ast.Pow) and abs(_eval(n.right)) > 100: raise ValueError("exponent too large")
        return OPS[type(n.op)](_eval(n.left), _eval(n.right))
    if isinstance(n, ast.UnaryOp) and type(n.op) in OPS: return OPS[type(n.op)](_eval(n.operand))
    if isinstance(n, ast.Call) and getattr(n.func, "id", "") in ("sqrt", "round", "abs") and len(n.args) == 1: return {"sqrt": lambda x: x ** .5, "round": round, "abs": abs}[n.func.id](_eval(n.args[0]))
    raise ValueError(f"unsupported expression: {ast.dump(n)[:60]}")
@tool
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression (+ - * / // % ** sqrt round abs). No variables, no code execution."""
    try: v = _eval(ast.parse(expression.replace("^", "**"), mode="eval").body); return str(round(v, 6) if isinstance(v, float) else v)
    except Exception as e: return f"error: {e}"
@tool
def document_search(query: str) -> str:
    """Search the Python Enhancement Proposals (PEPs) knowledge base. Returns the top passages with PEP number, title and created date."""
    return "\n\n".join(f"[{d.metadata['source']}: {d.metadata['title']} (created {d.metadata.get('created')})] {d.page_content[:500]}" for d in R.search(query, k=3))
@tool
def web_search(query: str) -> str:
    """Search the web. Falls back to GitHub repositories and PyPI package data when general search is unavailable."""
    out = []
    try:
        from bs4 import BeautifulSoup
        h = requests.get("https://html.duckduckgo.com/html/", params={"q": query}, timeout=8, headers={"User-Agent": "Mozilla/5.0"}); h.raise_for_status()
        out = [f"{a.get_text(' ', strip=True)} - {a.get('href')}" for a in BeautifulSoup(h.text, "lxml").select(".result__a")[:5]]
    except Exception as e: out.append(f"(general web search unavailable: {type(e).__name__})")
    words = [w for w in re.findall(r"[a-z0-9_.-]+", query.lower()) if w not in {"latest", "version", "of", "the", "what", "is", "how", "many", "stars", "does", "have", "on", "github", "pypi", "python", "package", "which", "projects", "most", "are", "top", "popular"}]
    for w in (words[:2] if re.search(r"version|package|pypi|release", query.lower()) else []):
        try:
            d = requests.get(f"https://pypi.org/pypi/{w}/json", timeout=8).json()["info"]; out.append(f"PyPI {d['name']}: latest version {d['version']}, summary: {d['summary']} (https://pypi.org/project/{d['name']}/)")
        except Exception: pass
    try:
        g = requests.get("https://api.github.com/search/repositories", params={"q": " ".join(words) or query, "sort": "stars", "per_page": 3}, timeout=8).json().get("items", [])
        out += [f"GitHub {r['full_name']}: {r['stargazers_count']:,} stars, last push {r['pushed_at'][:10]} ({r['html_url']})" for r in g]
    except Exception as e: out.append(f"(GitHub search failed: {type(e).__name__})")
    return "\n".join(out) or "no results"
TOOLS = [web_search, calculator, document_search]
def run(q):
    llm = chat_model()
    if llm is not None:
        from langgraph.prebuilt import create_react_agent
        res = create_react_agent(llm, TOOLS).invoke({"messages": [("user", q)]}); steps = [dict(tool=m.name, output=m.content[:300]) for m in res["messages"] if m.type == "tool"]
        return dict(engine=type(llm).__name__, steps=steps, answer=res["messages"][-1].content)
    steps = []
    def call(t, arg): out = t.invoke(arg); steps.append(dict(tool=t.name, input=arg, output=out[:400])); return out
    ql = q.lower(); peps = re.findall(r"pep\s*(\d+)", ql)
    if len(peps) >= 2 and re.search(r"years?|between|apart|gap", ql):                                    # chain: 2 lookups + arithmetic
        years = []
        for p in peps[:2]:
            meta = next((m for m in R.metas if m["pep"] == int(p)), None)          # exact lookup in the knowledge base's metadata
            steps.append(dict(tool="document_search", input=f"PEP {p} (metadata lookup)", output=f"PEP {p}: {meta['title']}, created {meta['created']}" if meta else "not in the knowledge base"))
            years.append(int(meta["created"][-4:]) if meta else None)
        if None in years: return dict(engine="router", steps=steps, answer="I couldn't find both PEPs in the knowledge base.")
        gap = call(calculator, f"{max(years)} - {min(years)}")
        return dict(engine="router", steps=steps, answer=f"PEP {peps[0]} was created in {years[0]} and PEP {peps[1]} in {years[1]}: {gap} years apart.")
    expr = re.sub(r"^(what is|what's|calculate|compute|evaluate)\s+", "", q.strip().rstrip("?"), flags=re.I)
    if re.fullmatch(r"[-+*/().\d\s^%a-z]*", expr.lower()) and re.search(r"\d\s*[-+*/^%]\s*\(?\d|sqrt\(", expr):
        v = call(calculator, expr); return dict(engine="router", steps=steps, answer=f"{expr} = {v}")
    if re.search(r"\b(latest|version|stars|github|pypi|released|download)\b", ql):
        out = call(web_search, q); lines = [l for l in out.split("\n") if l.startswith(("PyPI", "GitHub"))]
        best = [l for l in lines if l.startswith("GitHub")] if re.search(r"stars|github|projects", ql) else lines[:1]
        return dict(engine="router", steps=steps, answer="From the web search: " + ("; ".join(best[:3]) or out.split("\n")[0]))
    out = call(document_search, q); top = R.search(q, k=1)[0]
    from common.rag import extractive
    text, _ = extractive(q, R.search(q), R.emb)
    return dict(engine="router", steps=steps, answer=f"{text} (source: {top.metadata['source']}, {top.metadata['title']})")
QS = ["What is the latest version of the httpx package?", "What is (1250 * 18) / 7 + sqrt(144)?", "How many years apart were PEP 8 and PEP 572 created?",
      "What does the walrus operator do?", "Which Python web scraping projects have the most GitHub stars?", "What is 2^10 - 24?"]
if __name__ == "__main__":
    qs = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else QS; md = ["# Agent runs", ""]
    for q in qs:
        r = run(q); md += [f"## {q}", "", f"*engine: {r['engine']}*", ""] + [f"{i}. **{s['tool']}**(`{s.get('input', '')}`) → {s['output'][:200].replace(chr(10), ' | ')}" for i, s in enumerate(r["steps"], 1)] + ["", f"**Answer:** {r['answer']}", ""]
        print(q, "->", r["answer"][:160])
    if len(sys.argv) == 1: open(os.path.join(HERE, "results", "agent_runs.md"), "w").write("\n".join(md) + "\n")
