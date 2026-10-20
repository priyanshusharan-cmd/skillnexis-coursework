# Ten reusable prompt templates

Every template states task, context, constraints, output format, and an uncertainty rule. Replace bracketed values and inspect the result.

1. **Summarize:** Summarize [text] for [audience] in [N] bullets. Preserve key facts; flag missing context.
2. **Extract:** Extract [fields] from [document]. Return JSON matching [schema]; use null when absent.
3. **Classify:** Assign [item] one label from [allowed labels]. Return label and one sentence of evidence.
4. **Rewrite:** Rewrite [text] for [audience] in [tone], preserving meaning and names; list material changes.
5. **Explain:** Explain [concept] to [learner level] using one example and one limitation.
6. **Compare:** Compare [A] and [B] against [criteria]. Return a table and state assumptions.
7. **Plan:** Create a [duration] plan for [goal], considering [constraints]. Include sequence and checkpoints.
8. **Review code:** Review [code] for [risk categories]. Cite exact lines; separate confirmed issues from suggestions.
9. **Generate tests:** Create boundary and negative tests for [feature] from [requirements]; do not invent requirements.
10. **Grounded Q&A:** Answer [question] using only [sources]. Cite source passages; say “not found” if unsupported.

Optimization: define a single task, supply relevant context, specify allowed outputs and format, add examples only when useful, and evaluate correctness against source material. A longer prompt is not automatically better.
