"""Attempt 1 (kept for the record; see README): closed-book version. Fine-tune the GPT-2-architecture model with LoRA (PEFT) on a custom Q&A dataset.
Dataset (built from the PEP metadata): 3 question types x 66 PEPs: the title of PEP n, its status, the PEP number for a
title. Training uses one phrasing per question type; the test uses DIFFERENT phrasings of the same facts, so it
measures whether the model learned the facts and the answer format rather than memorising strings.
Compared: the base model (no fine-tuning, few-shot prompted), LoRA (r=8 on attention + MLP projections, about 2 % of
the weights trainable) and full fine-tuning (100 % trainable), with the same steps and data.
    python lora_closed_book.py -> ../results/lora_closed_book.json"""
import json, os, random, re, sys, time
import torch
from peft import LoraConfig, get_peft_model
from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "week-2"))
from common.loaders import load_peps
torch.manual_seed(0); random.seed(0); torch.set_num_threads(int(os.environ.get("THREADS", 1)))
tok = PreTrainedTokenizerFast.from_pretrained(os.path.join(HERE, "base")); BASE = os.path.join(HERE, "base")
peps = [d.metadata for d in load_peps(os.path.join(HERE, "..", "..", "week-2", "data", "peps"))]
TRAIN_T = {"title": "Question: What is the title of PEP {n}?\nAnswer:", "status": "Question: What is the status of PEP {n}?\nAnswer:", "number": "Question: Which PEP is titled \"{t}\"?\nAnswer:"}
TEST_T = {"title": "Question: PEP {n} is called what?\nAnswer:", "status": "Question: Is PEP {n} accepted, final or something else? Give its status.\nAnswer:", "number": "Question: What number is the PEP named \"{t}\"?\nAnswer:"}
def answer(kind, m): return {"title": m["title"], "status": m["status"], "number": f"PEP {m['pep']}"}[kind]
def rows(T): return [(T[k].format(n=m["pep"], t=m["title"]), " " + answer(k, m), k) for m in peps for k in T]
train, test = rows(TRAIN_T), rows(TEST_T); random.shuffle(train)
def encode(q, a):
    qi, ai = tok(q)["input_ids"], tok(a)["input_ids"] + [tok.eos_token_id]; ids = (qi + ai)[:128]
    return ids, ([-100] * len(qi) + ai)[:128]                                    # loss only on the answer tokens
def collate(batch):
    L = max(len(i) for i, _ in batch); x = torch.full((len(batch), L), tok.pad_token_id); y = torch.full((len(batch), L), -100); att = torch.zeros((len(batch), L), dtype=torch.long)
    for k, (i, l) in enumerate(batch): x[k, :len(i)] = torch.tensor(i); y[k, :len(l)] = torch.tensor(l); att[k, :len(i)] = 1
    return x, y, att
SHOT = "Question: What is the title of PEP 1?\nAnswer: PEP Purpose and Guidelines\n\n"           # for the base model only
@torch.no_grad()
def evaluate(model, data, few_shot=False, show=0):
    model.eval(); ok = {}; examples = []
    for q, a, k in data:
        p = (SHOT if few_shot else "") + q; g = tok(p, return_tensors="pt")
        out = model.generate(**g, max_new_tokens=24, do_sample=False, pad_token_id=tok.pad_token_id, eos_token_id=tok.eos_token_id)
        pred = tok.decode(out[0, g["input_ids"].shape[1]:], skip_special_tokens=True).split("\n")[0].strip()
        hit = pred.lower() == a.strip().lower(); ok.setdefault(k, []).append(hit)
        if len(examples) < show: examples.append(dict(q=q.replace("\nAnswer:", ""), expected=a.strip(), got=pred))
    model.train(); return {k: round(sum(v) / len(v), 3) for k, v in ok.items()} | dict(overall=round(sum(sum(v) for v in ok.values()) / len(data), 3)), examples
def train_model(model, steps=900, lr=2e-3, bs=16):
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr); enc = [encode(q, a) for q, a, _ in train]; t = time.time(); losses = []
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, lr, total_steps=steps, pct_start=.1)
    for s in range(steps):
        x, y, att = collate(random.sample(enc, bs)); loss = model(input_ids=x, attention_mask=att, labels=y).loss
        opt.zero_grad(); loss.backward(); opt.step(); sched.step(); losses.append(loss.item())
        if (s + 1) % 150 == 0: print(f"step {s + 1} loss {sum(losses[-150:]) / 150:.3f}", flush=True)
    return round((time.time() - t) / 60, 1), round(sum(losses[-50:]) / 50, 3)
res = dict(train_examples=len(train), test_examples=len(test))
base = GPT2LMHeadModel.from_pretrained(BASE); total = sum(p.numel() for p in base.parameters())
res["base_few_shot"], ex_base = evaluate(base, test, few_shot=True, show=6)
lora = get_peft_model(GPT2LMHeadModel.from_pretrained(BASE), LoraConfig(r=8, lora_alpha=16, lora_dropout=.05, target_modules=["c_attn", "c_proj", "c_fc"], fan_in_fan_out=True, task_type="CAUSAL_LM"))
trainable = sum(p.numel() for p in lora.parameters() if p.requires_grad); mins, last = train_model(lora)
res["lora"] = dict(trainable_params=trainable, trainable_share=round(trainable / total, 4), minutes=mins, final_loss=last, train_set=evaluate(lora, train[:120])[0], test=None)
res["lora"]["test"], ex_lora = evaluate(lora, test, show=6); lora.save_pretrained(os.path.join(HERE, "adapter_closed_book"))
full = GPT2LMHeadModel.from_pretrained(BASE); mins, last = train_model(full, lr=5e-4)
res["full_finetune"] = dict(trainable_params=total, minutes=mins, final_loss=last, test=evaluate(full, test)[0])
res["adapter_size_kb"] = round(sum(os.path.getsize(os.path.join(HERE, "adapter_closed_book", f)) for f in os.listdir(os.path.join(HERE, "adapter_closed_book"))) / 1024)
res["examples_base"], res["examples_lora"] = ex_base, ex_lora
json.dump(res, open(os.path.join(HERE, "..", "results", "lora_closed_book.json"), "w"), indent=1); print(json.dumps({k: v for k, v in res.items() if not k.startswith("examples")}, indent=1))
