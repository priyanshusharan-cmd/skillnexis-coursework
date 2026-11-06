"""Task 3: conversational memory. The same 6-turn conversation (with follow-ups that only make sense with memory) runs
through the RAG chain four times: no memory, buffer, window (k=2) and summary (k=1). It records the memory size each
turn and whether retrieval found the right PEP for each follow-up.
    python memory_demo.py -> results/memory.json, results/memory.md"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.memory import BufferMemory, SummaryMemory, WindowMemory
from common.rag import HybridRetriever, answer
HERE = os.path.dirname(os.path.abspath(__file__))
TURNS = [("What are assignment expressions in Python?", 572), ("Why is it called the walrus operator?", 572), ("Can it be used inside a comprehension?", 572),
         ("Now tell me about dataclasses.", 557), ("Which methods does it generate automatically?", 557), ("Going back to the first topic, what was the operator's symbol?", 572)]
R = HybridRetriever(os.path.join(HERE, "chroma")); out = {}; md = ["# Memory comparison", ""]
for mem in (None, BufferMemory(), WindowMemory(2), SummaryMemory(1)):
    name = mem.name if mem else "none"; rows = []
    for q, pep in TURNS:
        query = mem.standalone(q) if mem else q
        r = answer(R, query, history=(mem.context() + "\n\n") if mem else "")
        if mem: mem.add(q, r["answer"])
        rows.append(dict(q=q, query=query, expected=f"PEP {pep}", top=r["retrieved"][0], found_in_top3=f"PEP {pep}" in r["retrieved"][:3], memory_tokens=mem.size() if mem else 0))
    out[name] = dict(correct_top3=sum(x["found_in_top3"] for x in rows), turns=len(rows), final_memory_tokens=rows[-1]["memory_tokens"], rows=rows,
                     final_memory=mem.context() if mem else "")
    md += [f"## {name}: right PEP in the top 3 for {out[name]['correct_top3']}/6 turns, memory at the end ≈ {out[name]['final_memory_tokens']} tokens", "", "| Turn | Search query used | Top result | ✓ |", "|---|---|---|---|"]
    md += [f"| {x['q']} | {x['query'][:90]} | {x['top']} | {'✓' if x['found_in_top3'] else '✗'} |" for x in rows] + [""]
    if mem: md += ["<details><summary>final memory contents</summary>", "", "```", mem.context()[:1500], "```", "</details>", ""]
json.dump(out, open(os.path.join(HERE, "results", "memory.json"), "w"), indent=1); open(os.path.join(HERE, "results", "memory.md"), "w").write("\n".join(md) + "\n")
print({k: (v["correct_top3"], v["final_memory_tokens"]) for k, v in out.items()})
