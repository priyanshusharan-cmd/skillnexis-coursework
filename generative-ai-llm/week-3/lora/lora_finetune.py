"""Task 1: fine-tune the GPT-2-architecture model with LoRA (PEFT) on a custom dataset: answering questions about a
PEP from its header card, in a fixed short-answer format (open-book extraction).
Dataset: for every PEP, a card with its Title, Status, Type, Created date and PEP number, with the fields in a
random order, then a question about one field. 4 question types x 3 shuffled cards per PEP. The split is by PEP:
50 PEPs for training (plus 2,000 synthetic cards with random values, see synthetic()), 16 completely unseen PEPs for testing, so the score measures whether the model learned the SKILL
(find the field, copy the value, stop), not the facts. A second test re-asks the unseen PEPs with reworded questions.
Compared with the same steps and data: the base model (few-shot prompted), LoRA (r=16 on attention + MLP projections,
about 6 % of the weights trainable) and full fine-tuning (100 % trainable).
(Attempt 1, closed-book recall of facts from reworded questions, is in lora_closed_book.py; it failed at this model size.)
    python lora_finetune.py -> adapter/ (LoRA weights only), ../results/lora.json"""
import json, os, random, re, sys, time
import torch
from peft import LoraConfig, get_peft_model
from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "week-2"))
from common.loaders import load_peps
torch.manual_seed(0); random.seed(0); torch.set_num_threads(int(os.environ.get("THREADS", 1)))
tok = PreTrainedTokenizerFast.from_pretrained(os.path.join(HERE, "base")); BASE = os.path.join(HERE, "base")
peps = [d.metadata for d in load_peps(os.path.join(HERE, "..", "..", "week-2", "data", "peps"))]; random.Random(0).shuffle(peps)
train_peps, test_peps = peps[:50], peps[50:]
FIELDS = {"title": "Title", "status": "Status", "type": "Type", "created": "Created"}
Q = {"title": "What is the title?", "status": "What is the status?", "type": "What type of PEP is it?", "created": "When was it created?"}
Q2 = {"title": "Name this PEP.", "status": "Is it accepted, final, active or something else?", "type": "Which category does it belong to?", "created": "On what date was it written?"}
def card(m, rng):
    f = [f"{FIELDS[k]}: {m[k]}" for k in FIELDS] + [f"PEP: {m['pep']}"]; rng.shuffle(f); return "\n".join(f)
def rows(ps, Qs, n_cards, seed):
    rng = random.Random(seed); out = []
    for m in ps:
        for _ in range(n_cards):
            c = card(m, rng)
            for k in FIELDS: out.append((f"{c}\nQuestion: {Qs[k]}\nAnswer:", " " + m[k], k))
    return out
def synthetic(n, seed):
    """Extra training cards with random field values (title words from the TRAINING titles, random dates and numbers):
    with only 50 real PEPs the model can memorise the 50 answers instead of learning to read the card."""
    rng = random.Random(seed); words = sorted({w for m in train_peps for w in m["title"].split()}); out = []
    sts, tys = sorted({m["status"] for m in train_peps}), sorted({m["type"] for m in train_peps})
    for _ in range(n):
        out.append(dict(pep=rng.randint(1, 799), title=" ".join(rng.sample(words, rng.randint(2, 6))), status=rng.choice(sts), type=rng.choice(tys),
                        created=f"{rng.randint(1, 28):02d}-{rng.choice(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])}-{rng.randint(2000, 2025)}"))
    return out
N_SYN = int(os.environ.get("N_SYNTHETIC", 2000))
train = rows(train_peps, Q, 3, 1) + rows(synthetic(N_SYN, 4), Q, 1, 5); test, test_reworded = rows(test_peps, Q, 1, 2), rows(test_peps, Q2, 1, 3); random.shuffle(train)
def encode(q, a):
    qi, ai = tok(q)["input_ids"], tok(a)["input_ids"] + [tok.eos_token_id]; ids = (qi + ai)[:160]
    return ids, ([-100] * len(qi) + ai)[:160]                                    # loss only on the answer tokens
def collate(batch):
    L = max(len(i) for i, _ in batch); x = torch.full((len(batch), L), tok.pad_token_id); y = torch.full((len(batch), L), -100); att = torch.zeros((len(batch), L), dtype=torch.long)
    for k, (i, l) in enumerate(batch): x[k, :len(i)] = torch.tensor(i); y[k, :len(l)] = torch.tensor(l); att[k, :len(i)] = 1
    return x, y, att
SHOT = rows([peps[0]], Q, 1, 9)[0][0] + rows([peps[0]], Q, 1, 9)[0][1] + "\n\n"           # one worked example, for the base model only (a TRAIN pep)
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
STEPS, R = int(os.environ.get("STEPS", 2500)), int(os.environ.get("LORA_R", 16))
def train_model(model, steps=STEPS, lr=2e-3, bs=16):
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr); enc = [encode(q, a) for q, a, _ in train]; t = time.time(); losses = []
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, lr, total_steps=steps, pct_start=.1)
    for s in range(steps):
        x, y, att = collate(random.sample(enc, bs)); loss = model(input_ids=x, attention_mask=att, labels=y).loss
        opt.zero_grad(); loss.backward(); opt.step(); sched.step(); losses.append(loss.item())
        if (s + 1) % 150 == 0: print(f"step {s + 1} loss {sum(losses[-150:]) / 150:.3f}", flush=True)
    return round((time.time() - t) / 60, 1), round(sum(losses[-50:]) / 50, 3)
res = dict(steps=STEPS, lora_r=R, synthetic_cards=N_SYN, train_examples=len(train), test_examples=len(test), train_peps=len(train_peps), test_peps=len(test_peps))
base = GPT2LMHeadModel.from_pretrained(BASE); total = sum(p.numel() for p in base.parameters())
res["base_few_shot"], ex_base = evaluate(base, test, few_shot=True, show=6); res["base_few_shot_reworded"] = evaluate(base, test_reworded, few_shot=True)[0]
lora = get_peft_model(GPT2LMHeadModel.from_pretrained(BASE), LoraConfig(r=R, lora_alpha=2 * R, lora_dropout=.05, target_modules=["c_attn", "c_proj", "c_fc"], fan_in_fan_out=True, task_type="CAUSAL_LM"))
trainable = sum(p.numel() for p in lora.parameters() if p.requires_grad); mins, last = train_model(lora, lr=float(os.environ.get("LORA_LR", 2e-3)))
res["lora"] = dict(trainable_params=trainable, trainable_share=round(trainable / total, 4), minutes=mins, final_loss=last, train_set=evaluate(lora, train[:120])[0], test=None)
res["lora"]["test"], ex_lora = evaluate(lora, test, show=6); res["lora"]["test_reworded"] = evaluate(lora, test_reworded)[0]; lora.save_pretrained(os.path.join(HERE, "adapter"))
full = GPT2LMHeadModel.from_pretrained(BASE); mins, last = train_model(full, lr=5e-4)
res["full_finetune"] = dict(trainable_params=total, minutes=mins, final_loss=last, test=evaluate(full, test)[0], test_reworded=evaluate(full, test_reworded)[0])
res["adapter_size_kb"] = round(sum(os.path.getsize(os.path.join(HERE, "adapter", f)) for f in os.listdir(os.path.join(HERE, "adapter"))) / 1024)
res["examples_base"], res["examples_lora"] = ex_base, ex_lora
json.dump(res, open(os.path.join(HERE, "..", "results", "lora.json"), "w"), indent=1); print(json.dumps({k: v for k, v in res.items() if not k.startswith("examples")}, indent=1))
