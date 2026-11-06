"""Step 1 (because no pretrained GPT-2 weights are reachable from this sandbox): build a GPT-2 *architecture* model and
pretrain it here.
  * tokenizer: byte-level BPE (the GPT-2 tokenizer algorithm), vocabulary 4,096, trained on the corpus
  * model: transformers.GPT2LMHeadModel, 4 layers x 4 heads x 256 dims, 256-token context (~4.4 M parameters)
  * data: the 66 public-domain PEPs from week 2 (~0.5 M tokens); 6 PEPs are held out to measure perplexity
With internet access, replace this with GPT2LMHeadModel.from_pretrained("gpt2") and skip straight to lora_finetune.py.
    python base_model.py [steps] -> base/ (model + tokenizer), ../results/pretrain.json"""
import json, math, os, random, sys, time
import torch
from tokenizers import ByteLevelBPETokenizer
from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "week-2"))
from common.loaders import load_peps
torch.manual_seed(0); random.seed(0); torch.set_num_threads(int(os.environ.get("THREADS", 1)))
OUT = os.path.join(HERE, "base"); os.makedirs(OUT, exist_ok=True)
docs = load_peps(os.path.join(HERE, "..", "..", "week-2", "data", "peps")); held = {8, 257, 484, 572, 634, 695}
train_txt = [f"PEP {d.metadata['pep']}: {d.metadata['title']}\n\n{d.page_content}" for d in docs if d.metadata["pep"] not in held]
val_txt = [f"PEP {d.metadata['pep']}: {d.metadata['title']}\n\n{d.page_content}" for d in docs if d.metadata["pep"] in held]
meta_txt = [f"PEP {d.metadata['pep']} is titled {d.metadata['title']}. Its status is {d.metadata['status']}." for d in docs]
bpe = ByteLevelBPETokenizer(); bpe.train_from_iterator(train_txt + meta_txt, vocab_size=4096, min_frequency=2, special_tokens=["<|endoftext|>", "<pad>"])
tok = PreTrainedTokenizerFast(tokenizer_object=bpe._tokenizer, bos_token="<|endoftext|>", eos_token="<|endoftext|>", pad_token="<pad>"); tok.save_pretrained(OUT)
def ids(texts): return torch.tensor([i for t in texts for i in tok(t)["input_ids"] + [tok.eos_token_id]])
tr, va = ids(train_txt), ids(val_txt); T = 256
cfg = GPT2Config(vocab_size=len(tok), n_positions=T, n_embd=256, n_layer=4, n_head=4, bos_token_id=tok.eos_token_id, eos_token_id=tok.eos_token_id, pad_token_id=tok.pad_token_id)
model = GPT2LMHeadModel(cfg); n_params = sum(p.numel() for p in model.parameters())
opt = torch.optim.AdamW(model.parameters(), lr=6e-4, weight_decay=.1, betas=(.9, .95)); STEPS = int(sys.argv[1]) if len(sys.argv) > 1 else 1500; B = 16
sched = torch.optim.lr_scheduler.OneCycleLR(opt, 6e-4, total_steps=STEPS, pct_start=.06)
def batch(data):
    ix = torch.randint(0, len(data) - T - 1, (B,)); return torch.stack([data[i:i + T] for i in ix])
@torch.no_grad()
def val_loss():
    model.eval(); L = [model(x, labels=x).loss.item() for x in [va[i:i + T].unsqueeze(0) for i in range(0, len(va) - T, T)][:60]]; model.train(); return sum(L) / len(L)
hist = []; t0 = time.time(); v0 = val_loss()
for s in range(1, STEPS + 1):
    x = batch(tr); loss = model(x, labels=x).loss; opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step()
    if s % 100 == 0 or s == STEPS:
        v = val_loss(); hist.append(dict(step=s, train_loss=round(loss.item(), 3), val_loss=round(v, 3), val_ppl=round(math.exp(v), 1))); print(hist[-1], f"{time.time() - t0:.0f}s", flush=True)
model.save_pretrained(OUT)
g = tok("PEP 572: Assignment Expressions\n\nAbstract\n\nThis is a proposal", return_tensors="pt")
sample = tok.decode(model.generate(**g, max_new_tokens=60, do_sample=True, top_k=40, temperature=.8, pad_token_id=tok.pad_token_id)[0])
json.dump(dict(params=n_params, train_tokens=len(tr), val_tokens=len(va), steps=STEPS, batch=B, context=T, minutes=round((time.time() - t0) / 60, 1), val_ppl_before=round(math.exp(v0), 1), history=hist, sample=sample),
          open(os.path.join(HERE, "..", "results", "pretrain.json"), "w"), indent=1)
print(sample)
