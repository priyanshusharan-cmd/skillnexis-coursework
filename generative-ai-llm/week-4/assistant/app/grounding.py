"""Hallucination detection: is every sentence of the answer supported by the retrieved sources?
For each answer sentence (citation markers stripped):
  support = max over source sentences (and adjacent sentence pairs) of
            0.5 * key-word coverage (share of the claim's content words found there) + 0.5 * LSA cosine similarity
  numbers: every number in the claim must appear in the sources ("released in 2019" vs a source saying 2018)
  negation: a 'not'/'never'/'no' mismatch with the best-matching source sentence is flagged
  citations: a sentence citing [n] should be supported by source n itself (else the citation is wrong)
A sentence is 'unsupported' if support < THRESHOLD or a number/negation check fails. The answer's groundedness is the
share of supported sentences; answers below 0.75 get a visible warning. Abstentions ("I don't know") are grounded.
THRESHOLD: on the synthetic dev set F1 only moves between 0.932 and 0.937 for thresholds 0.50-0.88 (eval/run_eval.py), so
the lowest is used: it's the most forgiving to genuine paraphrases, which the synthetic set under-represents (a correct
answer merging two source sentences scored 0.57).
With an LLM configured, `llm_judge()` adds an LLM-as-judge verdict per sentence; the rule-based check runs always."""
import re
import numpy as np
from .text import content_words, numbers, sentences
THRESHOLD = .5
NEG = re.compile(r"\b(not|never|no|cannot|can't|isn't|aren't|doesn't|don't|won't|without)\b", re.I)
ABSTAIN = re.compile(r"i don't know|i do not know|not (?:covered|in the (?:sources|documents))", re.I)
def check(answer, hits, kb, threshold=THRESHOLD):
    if not answer.strip() or ABSTAIN.search(answer): return dict(grounded=1.0, abstained=bool(ABSTAIN.search(answer)), sentences=[], flagged=False)
    src_sents = []
    for i, h in enumerate(hits, 1):                                                   # single sentences AND adjacent pairs: answers often merge two
        ss = [s for s in sentences(h["text"]) if len(s.split()) >= 3]
        src_sents += [(s, i) for s in ss] + [(a + " " + b, i) for a, b in zip(ss, ss[1:])]
    if not src_sents: return dict(grounded=0.0, abstained=False, sentences=[], flagged=True)
    S = kb.embed([s for s, _ in src_sents]); src_words = [set(content_words(s)) for s, _ in src_sents]; all_nums = set().union(*(numbers(h["text"]) for h in hits))
    rows = []
    for raw in sentences(answer):
        cited = [int(x) for x in re.findall(r"\[(\d+)\]", raw)]; claim = re.sub(r"\s*\[\d+\]", "", raw).strip()
        cw = set(content_words(claim))
        if len(cw) < 2: continue
        cov = np.array([len(cw & w) / len(cw) for w in src_words]); sim = S @ kb.embed([claim])[0]; score = .5 * cov + .5 * np.clip(sim, 0, 1)
        j = int(score.argmax()); best, best_src = src_sents[j]
        bad_nums = sorted(numbers(claim) - all_nums - {str(c) for c in cited})
        neg_mismatch = bool(NEG.search(claim)) != bool(NEG.search(best)) and score[j] > .5
        cite_ok = None
        if cited:
            own = [k for k, (_, i) in enumerate(src_sents) if i in cited]; cite_ok = bool(own) and float(score[own].max()) >= threshold
        ok = score[j] >= threshold and not bad_nums and not neg_mismatch
        reason = None if ok else ("number not in sources: " + ", ".join(bad_nums) if bad_nums else "negation differs from the closest source sentence" if neg_mismatch else "no source sentence supports this")
        rows.append(dict(sentence=claim, support=round(float(score[j]), 3), supported=bool(ok), best_source=best_src, evidence=best[:300], cited=cited, citation_ok=cite_ok, reason=reason))
    g = sum(r["supported"] for r in rows) / len(rows) if rows else 1.0
    return dict(grounded=round(g, 3), abstained=False, sentences=rows, flagged=g < .75)
def llm_judge(answer, hits):
    """Optional second opinion from the configured LLM (JSON verdict per sentence). Returns None without an LLM."""
    from .llm import provider, _chat_model, format_sources
    kind, model = provider()
    if kind == "extractive": return None
    import json
    p = ("For each sentence of the ANSWER, say if it is fully supported by the SOURCES. Reply with JSON only: "
         '[{"sentence": "...", "supported": true|false}].\n\nSOURCES:\n' + format_sources(hits) + "\n\nANSWER:\n" + answer)
    raw = _chat_model(kind, model).invoke(p).content
    try: return json.loads(re.search(r"\[.*\]", raw, re.S).group(0))
    except Exception: return None
