"""Task 2: RAG pipeline with LangChain over the PEP collection, plus an evaluation: 16 questions with a known source
PEP (does the right PEP come back in the top 5? at what rank?) and 2 out-of-scope questions (does it abstain?).
    python rag.py ["your question"] -> results/rag_eval.json, results/rag_examples.md"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.rag import HybridRetriever, rag_chain
from common.models import engine_name
HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = [("How should constants be named in Python code?", 8), ("What does the walrus operator := do?", 572), ("What is the syntax of structural pattern matching with match and case?", 634),
        ("How do f-strings evaluate expressions inside braces?", 498), ("Why was the @ operator added for matrix multiplication?", 465), ("How do I write type hints for function arguments?", 484),
        ("What methods does the dataclass decorator generate?", 557), ("How do async and await define coroutines?", 492), ("What problem does the with statement solve?", 343),
        ("What does yield from do in a generator?", 380), ("What are positional-only parameters and the / marker?", 570), ("How do the | and |= operators merge dictionaries?", 584),
        ("What does zip strict=True do when iterables have different lengths?", 618), ("What are the conventions for one-line docstrings?", 257), ("What is the annual release cycle for Python versions?", 602),
        ("How do you annotate a method that returns an instance of its own class with Self?", 673)]
OOS = ["How do I bake sourdough bread?", "Who won the football world cup in 2018?"]
if __name__ == "__main__":
    R = HybridRetriever(os.path.join(HERE, "chroma")); chain = rag_chain(R)
    if len(sys.argv) > 1: print(json.dumps(chain.invoke({"question": " ".join(sys.argv[1:])}), indent=1)); sys.exit()
    rows, md = [], [f"# RAG examples (engine: {engine_name()})", ""]
    for q, pep in EVAL:
        r = chain.invoke({"question": q}); ranks = [i for i, s in enumerate(r["retrieved"], 1) if s == f"PEP {pep}"]
        rows.append(dict(question=q, expected=f"PEP {pep}", rank=ranks[0] if ranks else None, cited_expected=any(s["source"] == f"PEP {pep}" for s in r["sources"]), answer=r["answer"]))
        md += [f"**Q: {q}** (expected PEP {pep}, retrieved at rank {ranks[0] if ranks else '—'})", "", r["answer"], "", "Sources: " + ", ".join(f"[{s['n']}] {s['source']} ({s['title']})" for s in r["sources"]), ""]
    oos = [chain.invoke({"question": q}) for q in OOS]
    md += ["## Out of scope", ""] + [f"**Q: {q}**\n\n{r['answer']}\n" for q, r in zip(OOS, oos)]
    hit = sum(r["rank"] is not None for r in rows); mrr = sum(1 / r["rank"] for r in rows if r["rank"]) / len(rows)
    res = dict(engine=engine_name(), questions=len(rows), hit_at_5=round(hit / len(rows), 3), hit_at_1=round(sum(r["rank"] == 1 for r in rows) / len(rows), 3), mrr=round(mrr, 3),
               answers_citing_expected_pep=round(sum(r["cited_expected"] for r in rows) / len(rows), 3), out_of_scope_abstained=sum(r["answer"].startswith("I don't know") for r in oos), rows=rows)
    json.dump(res, open(os.path.join(HERE, "results", "rag_eval.json"), "w"), indent=1); open(os.path.join(HERE, "results", "rag_examples.md"), "w").write("\n".join(md) + "\n")
    print({k: v for k, v in res.items() if k != "rows"}); [print(r["rank"], r["expected"], r["question"][:50]) for r in rows]
