"""Evaluation of the PDF knowledge base: 10 questions with the PDF that answers them, 2 unanswerable ones.
Measures retrieval hit@5 / MRR (by file), whether the answer cites the right file, and abstention.
    python evaluate.py -> results.json, examples.md"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb
Q = [("What does ParamSpec allow you to annotate?", "pep-0612.pdf"), ("How can I write a union type using the | operator?", "pep-0604.pdf"),
     ("How do I annotate a method that returns an instance of its own class?", "pep-0673.pdf"), ("What is LiteralString used for?", "pep-0675.pdf"),
     ("What does the dataclass_transform decorator do?", "pep-0681.pdf"), ("What is the new syntax for declaring type parameters in a generic class?", "pep-0695.pdf"),
     ("How do I attach extra metadata to a type with Annotated?", "pep-0593.pdf"), ("Can I use list[int] instead of typing.List[int]?", "pep-0585.pdf"),
     ("What is the syntax for annotating a variable with a type?", "pep-0526.pdf"), ("What is a type hint stub file?", "pep-0484.pdf")]
OOS = ["What is the capital of Australia?", "How do I reset my router?"]
R = kb.retriever(); rows, md = [], ["# PDF knowledge base: example answers", ""]
for q, f in Q:
    r = kb.ask(q, R=R); docs = R.search(q); files = [d.metadata["source"] for d in docs]; rank = files.index(f) + 1 if f in files else None
    rows.append(dict(q=q, expected=f, rank=rank, cited=any(s["source"] == f for s in r["sources"])))
    md += [f"**Q: {q}** (expected {f}, rank {rank or '—'})", "", r["answer"], "", "Sources: " + "; ".join(f"[{s['n']}] {s['source']} p.{s['page']}" for s in r["sources"]), ""]
oos = [kb.ask(q, R=R)["answer"] for q in OOS]; md += ["## Unanswerable", ""] + [f"**Q: {q}** → {a}" for q, a in zip(OOS, oos)]
res = dict(hit_at_5=sum(r["rank"] is not None for r in rows) / len(rows), mrr=round(sum(1 / r["rank"] for r in rows if r["rank"]) / len(rows), 3), cites_right_file=sum(r["cited"] for r in rows) / len(rows),
           abstained=sum(a.startswith("I don't know") for a in oos), of_unanswerable=len(oos), rows=rows)
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json"), "w"), indent=1)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples.md"), "w").write("\n".join(md) + "\n"); print({k: v for k, v in res.items() if k != "rows"})
