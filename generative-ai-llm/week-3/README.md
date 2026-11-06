# Week 3: Fine-tuning, multimodal models & agents

| Task | Folder | Result |
|---|---|---|
| Fine-tune a model with LoRA (PEFT) on a custom dataset | [`lora/`](lora/) | A GPT-2-architecture model, pretrained here, then fine-tuned with **LoRA (6 % of weights, a 1 MB adapter)** against full fine-tuning and the few-shot base model. LoRA **learned the task format and reads closed-set fields** (PEP type on unseen cards **100 %** vs a 33 % majority baseline), but **didn't learn to copy new free text** (titles). The limits are measured and explained, not hidden |
| Multimodal: image captioning | [`captioning/`](captioning/) | A pretrained CNN encoder plus a Transformer decoder trained here on **Flickr8k** (6,000 photos × 5 captions). On the 1,000 official test images: **BLEU-4 0.162** (greedy), **0.197** (beam 3, first 200 images) |
| Function calling with external APIs | [`function-calling/`](function-calling/) | 4 functions with JSON-schema declarations: PyPI info, package comparison, GitHub search, unit conversion. Every call is **validated against its schema before it runs**, with a self-correcting retry. 6 runs, including an invalid argument, an unknown package and an out-of-scope request |
| **Mini project:** multi-agent research assistant | [`research-assistant/`](research-assistant/) | **LangGraph** Searcher → Summarizer → Writer with a citation check, a Gradio UI, and the same roles written for **CrewAI** ([`crew.py`](research-assistant/crew.py)). A live report on "vector databases in Python" from GitHub and PyPI data |

## What runs where (please read)
This sandbox can't reach Hugging Face or any LLM API. So:
* **No pretrained GPT-2 download:** the LoRA task first **pretrains a small GPT-2-architecture model here**
  (`transformers.GPT2LMHeadModel`, 4.3 M parameters) on 66 public-domain PEPs, then fine-tunes it. With internet
  access, swap in `GPT2LMHeadModel.from_pretrained("gpt2")` and the LoRA code is unchanged.
* **No LLM for the agents and function calling:** with a free `GEMINI_API_KEY`, an Ollama model or any
  OpenAI-compatible key, the LLM plans the calls and writes the prose. Without one, a transparent rule planner emits
  the **same JSON tool calls** through the same validation and execution path. Every committed run says which
  engine produced it.
* **CrewAI:** `crewai` would not install in this sandbox (the dependency install timed out), and it needs an LLM for
  every step anyway, so **`crew.py` is written but untested**. The LangGraph version is the tested one.

## 1 · LoRA fine-tuning (`lora/`)
**Step 0, a base model** ([`base_model.py`](lora/base_model.py)). No pretrained weights are reachable from this
sandbox, so this step builds one:
* a byte-level BPE tokenizer (vocabulary 4,096);
* `GPT2LMHeadModel` with 4 layers, 4 heads and 256 dims (4.3 M parameters);
* pretrained for 1,000 steps (28 minutes) on 60 PEPs, about 0.4 M tokens;
* held-out perplexity went from **4,314 to 135**: it writes PEP-flavoured English, but it's a *tiny* language model.

**The custom dataset** ([`lora_finetune.py`](lora/lora_finetune.py)): a PEP "header card" (Title, Status, Type,
Created, PEP number, in random order) followed by a question about one field, with a short exact answer.
* **Train:** 50 real PEPs × 3 shuffled cards × 4 questions, plus 2,000 synthetic cards with random values (without
  them, the model just memorised the 50 answers; see `results/lora_no_synthetic.json`).
* **Test:** 16 PEPs the model never saw, plus the same 16 with reworded questions.

**Methods, all with the same data and 2,500 steps:**

| | Trainable | Saved size | Unseen PEPs: status / type / created / title | Reworded questions |
|---|---|---|---|---|
| Base model, 1-shot prompt | 0 | – | 0 / 0 / 0 / 0 % | 0 % |
| **LoRA** r=16 on `c_attn`, `c_proj`, `c_fc` | 262 k (**6.1 %**) | **1.0 MB** adapter | 100 / 100 / **50** / 0 % | 2 % |
| Full fine-tuning | 4.27 M (100 %) | 17 MB | 100 / 100 / **75** / 0 % | 11 % |

**Read those numbers carefully:**
* **All 16 test PEPs happen to be "Final" and "Standards Track"**, so the most common answer also scores 100 % on
  status and type there. To check that the model really reads the card, [`eval_adapter.py`](lora/eval_adapter.py)
  scores the LoRA adapter on 200 new synthetic cards with uniformly random values
  ([`results/lora_synthetic_eval.json`](results/lora_synthetic_eval.json)):

  | Field | LoRA | Majority-answer baseline |
  |---|---|---|
  | type | **100 %** | 33 % |
  | status | **40 %** | 19 % (Draft/Accepted/Rejected/Withdrawn never occur in training, so it can't produce them) |
  | created (years 2026–2030, never seen) | 0 % | 0 % |
  | title | 3.5 % | 0 % |

* **What LoRA learned:** the answer format (the base model outputs nothing useful) and **finding the right field
  and reading its value**, as long as that value is one it has seen as an answer. Type is perfect on random cards,
  and the real creation dates of unseen PEPs are right 50 % of the time.
* **What it didn't learn:** copying *new* strings. Titles and unseen years need "induction heads" (look up the token
  after `Title:` and copy what follows), and a 4.3 M-parameter model pretrained for 28 minutes doesn't have them.
  Full fine-tuning gets a little further (dates 75 %) at 16× the stored size. **This is exactly what a real
  pretrained GPT-2 provides:** run the same script on `gpt2` (124 M) and LoRA is the cheap way to adapt it.
* **Attempt 1 (closed book)**, kept in [`lora_closed_book.py`](lora/lora_closed_book.py): recall facts ("What is
  the title of PEP 572?") with reworded test questions. LoRA scored 1.5 %, full fine-tuning 28 %. Paraphrase
  generalisation of memorised facts is beyond a model this small, which is why the open-book task replaced it.

**LoRA's practical advantages, measured:** 6 % of the parameters trained, a 1 MB adapter instead of a 17 MB model,
and the base model is untouched, so one base can serve many adapters. Training time was the same here (17 minutes),
because at this size the forward and backward passes through the frozen weights dominate.

## 2 · Image captioning (`captioning/`)
**Data:** Flickr8k (Hodosh, Young & Hockenmaier 2013): 8,091 photos with 5 human captions each and the official
6,000/1,000/1,000 split. It's fetched from the `jbrownlee/Datasets` GitHub release. Photos are not committed or
reproduced here.

**Encoder** ([`features.py`](captioning/features.py)): MobileNetV2 with ImageNet weights at 160×160. The last
5×5×1280 feature map is kept as **25 visual tokens**, so the decoder can attend to image regions. Each image is
encoded once and cached.

**Decoder** ([`train_captioner.py`](captioning/train_captioner.py)):
* a 3-layer Transformer decoder (d=256, 4 heads) with causal self-attention and cross-attention to the visual
  tokens;
* 5.3 M parameters and a 3,469-word vocabulary;
* label smoothing 0.1, AdamW with a one-cycle schedule, 6 epochs in 25 minutes on one CPU core.

| Test set (1,000 images, 5 references each) | BLEU-1 | BLEU-2 | BLEU-3 | BLEU-4 |
|---|---|---|---|---|
| Greedy decoding, all 1,000 | 0.569 | 0.383 | 0.248 | **0.162** |
| Beam search (width 3), first 200 | 0.602 | 0.416 | 0.285 | **0.197** |

For scale, the original *Show, Attend and Tell* paper reports BLEU-4 ≈ 0.21 on Flickr8k with a far bigger model.
937 of the 1,000 generated captions are distinct, so the model doesn't output one generic sentence.

**Examples** ([`results/captioning_examples.md`](results/captioning_examples.md)):
* good: "two brown dogs are playing in the snow" and "a brown and white dog is jumping into a pool";
* plausible but wrong: festive dancers became "a woman in a green shirt is sitting on a street".

Dogs and outdoor sports dominate Flickr8k, and it shows.

> A hosted vision-language model (Gemini's free tier, for example) would caption far better. This task shows the
> encoder-decoder pipeline built and trained end to end.

## 3 · Function calling (`function-calling/`)
**Functions** ([`functions.py`](function-calling/functions.py)), each declared with an OpenAI/Gemini-style JSON
schema that includes types, patterns, enums, ranges and `additionalProperties: false`:

| Function | API |
|---|---|
| `get_package_info(name)` | PyPI JSON API |
| `compare_packages(names[2..4])` | PyPI JSON API |
| `search_github(query, language?, sort?, limit 1-10)` | GitHub search API |
| `convert_units(value, from_unit, to_unit)` | local (data sizes use 1 GB = 1024 MB) |

**Loop** ([`assistant.py`](function-calling/assistant.py)):
1. The model (or offline planner) emits `{name, arguments}`.
2. **`jsonschema` validates the call before anything runs.**
3. The call is executed against the real API.
4. The result goes back for the final answer.

**Runs** ([`results/function_calling.md`](results/function_calling.md)), live data from 6 Nov 2026:
* "latest fastapi" → **0.162.0**;
* httpx vs requests vs aiohttp → a comparison table;
* "top **25** vector database repos in rust" → **rejected by the schema** (limit maximum is 10) → the assistant
  clamps to 10 and retries → Qdrant leads with 35 k stars;
* unknown package → a clear "no such package";
* "Book me a flight" → no function fits, so it says so instead of inventing a call.

## 4 · Mini project: research assistant (`research-assistant/`)
**Agents** ([`agents.py`](research-assistant/agents.py), a LangGraph `StateGraph`):

| Agent | Job |
|---|---|
| **Searcher** | plans 3–5 queries and runs them on GitHub, PyPI, Wikipedia and DuckDuckGo (whatever is reachable; failures are logged and routed around), then de-duplicates |
| **Summarizer** | a short summary of each source and its key facts (stars, versions, dates, licence) |
| **Writer** | a structured report: overview, key findings, comparison table, open questions, numbered sources. **A check rejects any `[n]` citation that doesn't point to a real source** |

**Interfaces:**
* [`app.py`](research-assistant/app.py) (Gradio, port 7862): enter a topic, watch each agent's step live, then
  download the Markdown report.
* [`crew.py`](research-assistant/crew.py): the same three roles as a CrewAI `Crew` with the same tools (untested,
  see above).

**Sample report** ([`reports/vector-databases-in-python.md`](research-assistant/reports/vector-databases-in-python.md)):
10 live GitHub sources, each with stars, last commit, PyPI release and licence, plus a comparison table.

**Honest limitation:** without an LLM to judge relevance, GitHub's keyword search lets in loosely related projects:
general databases with vector features (Doris, OceanBase) and a prompt-testing tool. An LLM Searcher filters these.
Wikipedia and DuckDuckGo were unreachable, so the report has no articles or docs.

## Run
```bash
pip install torch transformers tokenizers peft tensorflow-cpu keras nltk langgraph langchain-core gradio jsonschema requests beautifulsoup4
cd generative-ai-llm/week-3
(cd lora && python base_model.py 1000 && python lora_finetune.py && python eval_adapter.py)
(cd captioning && python features.py && python train_captioner.py)     # needs Flickr8k: FLICKR_IMG / FLICKR_TXT
(cd function-calling && python assistant.py)
(cd research-assistant && python agents.py "vector databases in Python" && python app.py)
# optional: GEMINI_API_KEY=... (free) or OLLAMA_MODEL=qwen2.5:1.5b switches the agents and function calling to an LLM
```
**Flickr8k:** `https://github.com/jbrownlee/Datasets/releases/download/Flickr8k/Flickr8k_Dataset.zip` and
`Flickr8k_text.zip`.
