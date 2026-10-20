# Tokenizer comparison (conceptual exercise)

| Method | Core idea | Common surface clue | Typical use |
|---|---|---|---|
| BPE | Repeatedly merges frequent adjacent symbol pairs into a vocabulary | Segmentation depends on learned merges | Many GPT-family tokenizers use BPE variants |
| WordPiece | Greedy subword segmentation selected to improve a language-modeling objective | Continuation pieces may use `##` in BERT displays | BERT-family models |
| SentencePiece | Learns subword units directly from raw text and treats whitespace explicitly | `▁` often marks a word boundary | Multilingual and language-model tokenizers |

Toy demonstration for “unhappiness”: a vocabulary might segment BPE as `un + happ + iness`, WordPiece as `un + ##happi + ##ness`, and SentencePiece as `▁un + happi + ness`. This is illustrative only; actual token IDs depend on the exact model vocabulary. To compare real tokenizers, record package/model name, version, input, token strings, and token count. Never infer production counts from this toy example.

## Definitions

- **Token:** unit a model consumes/emits; it may be a word, subword, punctuation, or byte fragment.
- **Context window:** maximum token budget available to one model request, including instructions and output.
- **Inference:** using a trained model to produce outputs.
- **Hallucination:** unsupported or incorrect generated content stated as though true.
- **Prompting, RAG, fine-tuning:** prompting supplies instructions at inference; retrieval-augmented generation adds retrieved context; fine-tuning updates model parameters using training examples.
