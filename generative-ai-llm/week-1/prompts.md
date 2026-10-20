# Twenty optimized prompt templates

Replace bracketed fields. Each prompt names its task, source/context, output constraints, and how to handle missing evidence.

1. **Summarize:** Summarize [source] for [audience] in [length]. Preserve names, dates, and caveats; flag missing context.
2. **Extract:** Extract [fields] from [source]. Return JSON matching [schema], with null when a value is absent.
3. **Classify:** Assign [item] one label from [allowed labels]. Return label and one quoted evidence span.
4. **Question answering:** Answer [question] using only [source]. Cite the supporting section; say “not found” if absent.
5. **Rewrite:** Rewrite [text] for [audience] in [tone] at [reading level]. Preserve claims; list any unavoidable changes.
6. **Translate:** Translate [text] to [language], preserving names, numbers, units, and formatting. Mark ambiguous phrases.
7. **Compare:** Compare [A] and [B] using [criteria]. Return a table, evidence, and assumptions.
8. **Outline:** Create an outline for [goal] aimed at [audience]. Include a clear sequence and exclude unsupported claims.
9. **Lesson plan:** Make a [duration] lesson for [learner level] with objective, example, activity, and check for understanding.
10. **Code explanation:** Explain [code] for [audience], walk through one input, and identify one limitation.
11. **Code review:** Review [code] for [risk categories]. Cite lines; distinguish confirmed defects from suggestions.
12. **Test generation:** Create positive, negative, and boundary tests from [requirements]. Do not invent behavior not specified.
13. **Email draft:** Draft a [tone] email to [recipient role] for [purpose]. Use only facts below and flag missing details.
14. **Product description:** Write a [word count] description for [product/audience]. Use only listed features; avoid unsupported superlatives.
15. **Meeting notes:** Convert [transcript] to decisions, owners, and due dates. Mark unclear owners/dates as unknown.
16. **Research synthesis:** Synthesize [sources]. Cite each claim and separate agreement, disagreement, and gaps.
17. **Data explanation:** Explain [table] trends using the provided values; calculate only from supplied data and state units.
18. **Creative ideation:** Generate [N] concepts for [brief], respecting [constraints]. Label unusual assumptions.
19. **Safety review:** Inspect [content] for [specified risks]. Quote evidence and suggest a minimal correction.
20. **Factuality check:** Check each claim in [draft] against [sources]. Return claim, support, contradiction, or not verifiable.

## Ten basic-vs-improved comparisons to run

For each template above, create a basic one-line prompt and the structured version, run both against the same input/model/settings, save exact outputs, score correctness and instruction following from 0–2, and explain differences. Do not fill scores until actual outputs are reviewed. The included `evaluation.csv` is the record sheet.
