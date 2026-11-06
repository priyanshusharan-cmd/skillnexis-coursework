"""Extra check of the saved LoRA adapter, because the 16 test PEPs happen to be all 'Final' / 'Standards Track', so
answering the most common value would score 100 % on those two fields. Here: 200 NEW synthetic cards whose status and
type are drawn uniformly (Active, Final, Draft, ... / Process, Informational, Standards Track), with dates and PEP
numbers never seen in training, scored against the majority-answer baseline.
    python eval_adapter.py -> ../results/lora_synthetic_eval.json"""
import collections, json, os, random, sys
import torch
from peft import PeftModel
from transformers import GPT2LMHeadModel
sys.argv = [sys.argv[0]]; os.environ.setdefault("N_SYNTHETIC", "0")
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "lora_finetune.py")).read().split("res = dict(")[0]          # reuse data + evaluate()
exec(src)
rng = random.Random(123); sts = ["Active", "Final", "Draft", "Accepted", "Rejected", "Withdrawn"]; tys = ["Standards Track", "Informational", "Process"]
words = sorted({w for m in train_peps for w in m["title"].split()}); cards = []
for _ in range(200):
    cards.append(dict(pep=rng.randint(800, 999), title=" ".join(rng.sample(words, rng.randint(2, 5))), status=rng.choice(sts), type=rng.choice(tys),
                      created=f"{rng.randint(1, 28):02d}-{rng.choice(['Jan', 'Mar', 'May', 'Jul', 'Sep', 'Nov'])}-{rng.randint(2026, 2030)}"))   # future years: never in training
data = [r for r in rows(cards, Q, 1, 7)]
model = PeftModel.from_pretrained(GPT2LMHeadModel.from_pretrained(BASE), os.path.join(HERE, "adapter"))
score, ex = evaluate(model, data, show=8)
maj = {k: collections.Counter(m[k] for m in train_peps).most_common(1)[0][0] for k in ("status", "type")}
baseline = {k: round(sum(c[k] == maj[k] for c in cards) / len(cards), 3) for k in maj} | dict(title=0.0, created=0.0)
res = dict(cards=len(cards), lora=score, majority_baseline=baseline, majority_answers=maj, examples=ex)
json.dump(res, open(os.path.join(HERE, "..", "results", "lora_synthetic_eval.json"), "w"), indent=1); print(json.dumps({k: v for k, v in res.items() if k != "examples"}, indent=1))
