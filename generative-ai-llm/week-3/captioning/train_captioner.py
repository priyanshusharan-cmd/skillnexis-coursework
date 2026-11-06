"""Image captioning, step 2: a Transformer decoder that writes captions while attending to the 25 visual tokens
(encoder-decoder captioning, the architecture family of 'Show, Attend and Tell' and today's VLMs, at small scale).
  decoder: 3 layers, d=256, 4 heads, causal self-attention + cross-attention to the image regions; vocabulary =
  words seen >= 3 times in the training captions; label smoothing 0.1; AdamW; 6 epochs on 6,000 images x 5 captions.
Evaluation on the 1,000 official test images: BLEU-1..4 against all 5 human references (greedy decoding on all 1,000; beam width 3 on the first 200), plus
example captions. A vision-language model (e.g. a hosted Gemini) would do far better; this shows the full pipeline
trained end to end on a CPU.
    python train_captioner.py -> model.pt, vocab.json, ../results/captioning.json, ../results/captioning_examples.md"""
import collections, json, math, os, random, re, time
import numpy as np, torch, torch.nn as nn
from nltk.translate.bleu_score import corpus_bleu, SmoothingFunction
torch.manual_seed(0); random.seed(0); torch.set_num_threads(int(os.environ.get("THREADS", 1)))
TXT = os.environ.get("FLICKR_TXT", "/tmp/claude-0/flickr/text"); D = np.load("cache/features.npz"); idx = {n: i for i, n in enumerate(D["names"])}; FE = torch.tensor(D["feats"].astype("float32"))
caps = collections.defaultdict(list)
for line in open(os.path.join(TXT, "Flickr8k.token.txt")):
    k, c = line.rstrip("\n").split("\t"); n = k.split("#")[0]
    if n in idx: caps[n].append(re.findall(r"[a-z]+", c.lower()))
split = {s: [l.strip() for l in open(os.path.join(TXT, f"Flickr_8k.{s}Images.txt")) if l.strip() in idx] for s in ("train", "dev", "test")}
cnt = collections.Counter(w for n in split["train"] for c in caps[n] for w in c); itos = ["<pad>", "<s>", "</s>", "<unk>"] + sorted(w for w, k in cnt.items() if k >= 3); stoi = {w: i for i, w in enumerate(itos)}
L = 22
def enc(c): ids = [1] + [stoi.get(w, 3) for w in c][:L - 2] + [2]; return ids + [0] * (L - len(ids))
pairs = [(idx[n], enc(c)) for n in split["train"] for c in caps[n]]
class Captioner(nn.Module):
    def __init__(s, V, d=256):
        super().__init__(); s.img = nn.Sequential(nn.Linear(1280, d), nn.LayerNorm(d)); s.pos_img = nn.Parameter(torch.randn(25, d) * .02)
        s.emb = nn.Embedding(V, d); s.pos = nn.Parameter(torch.randn(L, d) * .02)
        s.dec = nn.TransformerDecoder(nn.TransformerDecoderLayer(d, 4, 4 * d, .2, batch_first=True, norm_first=True), 3); s.out = nn.Linear(d, V)
    def forward(s, f, y):
        m = s.img(f) + s.pos_img; T = y.shape[1]; mask = torch.triu(torch.full((T, T), float("-inf")), 1)
        return s.out(s.dec(s.emb(y) + s.pos[:T], m, tgt_mask=mask, tgt_key_padding_mask=(y == 0)))
model = Captioner(len(itos)); opt = torch.optim.AdamW(model.parameters(), 5e-4, weight_decay=.01); EPOCHS, BS = int(os.environ.get("CAP_EPOCHS", 6)), 64
steps = EPOCHS * math.ceil(len(pairs) / BS); sched = torch.optim.lr_scheduler.OneCycleLR(opt, 5e-4, total_steps=steps, pct_start=.1); lossf = nn.CrossEntropyLoss(ignore_index=0, label_smoothing=.1)
@torch.no_grad()
def beam(f, k=3):
    model.eval(); m = model.img(f[None]) + model.pos_img; beams = [([1], 0.0)]
    for _ in range(L - 1):
        cand = []
        for seq, sc in beams:
            if seq[-1] == 2: cand.append((seq, sc)); continue
            y = torch.tensor([seq]); T = y.shape[1]; o = model.out(model.dec(model.emb(y) + model.pos[:T], m, tgt_mask=torch.triu(torch.full((T, T), float("-inf")), 1)))[0, -1]
            lp = torch.log_softmax(o, -1); lp[3] -= 5                                  # discourage <unk>
            for v, i in zip(*lp.topk(k)): cand.append((seq + [int(i)], sc + float(v)))
        beams = sorted(cand, key=lambda x: -x[1] / len(x[0]) ** .7)[:k]
        if all(s[-1] == 2 for s, _ in beams): break
    model.train(); return [itos[i] for i in beams[0][0][1:] if i not in (0, 1, 2)]
@torch.no_grad()
def greedy(names, bs=250):
    """Batched greedy decoding (fast); beam search is used for the showcased examples."""
    model.eval(); out = []
    for k in range(0, len(names), bs):
        f = FE[[idx[n] for n in names[k:k + bs]]]; m = model.img(f) + model.pos_img; y = torch.ones(len(f), 1, dtype=torch.long)
        for _ in range(L - 1):
            T = y.shape[1]; o = model.out(model.dec(model.emb(y) + model.pos[:T], m, tgt_mask=torch.triu(torch.full((T, T), float("-inf")), 1)))[:, -1]; o[:, 3] -= 5
            y = torch.cat([y, o.argmax(-1, keepdim=True)], 1)
        for row in y.tolist():
            words = []
            for i in row[1:]:
                if i == 2: break
                if i > 3: words.append(itos[i])
            out.append(words)
    model.train(); return out
def bleu(names, n=None, use_beam=False):
    names = names[:n] if n else names; hyp = [beam(FE[idx[x]]) for x in names] if use_beam else greedy(names); refs = [caps[x] for x in names]; sm = SmoothingFunction().method1
    return {f"BLEU-{k}": round(corpus_bleu(refs, hyp, weights=tuple([1 / k] * k), smoothing_function=sm), 4) for k in (1, 2, 3, 4)}, hyp
t0 = time.time(); hist = []
for ep in range(EPOCHS):
    random.shuffle(pairs); tot = 0
    for b in range(0, len(pairs), BS):
        chunk = pairs[b:b + BS]; f = FE[[i for i, _ in chunk]]; y = torch.tensor([c for _, c in chunk])
        loss = lossf(model(f, y[:, :-1]).reshape(-1, len(itos)), y[:, 1:].reshape(-1)); opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); tot += loss.item() * len(chunk)
    dv = bleu(split["dev"], 200)[0]; hist.append(dict(epoch=ep + 1, loss=round(tot / len(pairs), 3), dev_bleu4_200=dv["BLEU-4"])); print(hist[-1], f"{time.time() - t0:.0f}s", flush=True)
scores, hyp = bleu(split["test"]); beam_scores, beam_hyp = bleu(split["test"], 200, use_beam=True)
torch.save(model.state_dict(), "model.pt"); json.dump(itos, open("vocab.json", "w"))
ex = [dict(image=n, generated=" ".join(h), references=[" ".join(r) for r in caps[n][:2]]) for n, h in list(zip(split["test"], beam_hyp))[:12]]
json.dump(dict(vocab=len(itos), train_pairs=len(pairs), epochs=EPOCHS, params=sum(p.numel() for p in model.parameters()), minutes=round((time.time() - t0) / 60, 1), test_images=len(split["test"]), test_greedy=scores, test_beam3_first200=beam_scores, history=hist,
               distinct_captions=len({" ".join(h) for h in hyp})), open("../results/captioning.json", "w"), indent=1)
md = ["# Captioning examples (Flickr8k test images, beam 3)", "", "Images are not reproduced here (Flickr photos); look them up by file name in the dataset.", "", "| Image | Generated | Two of the five human captions |", "|---|---|---|"]
md += [f"| {e['image']} | **{e['generated']}** | {' / '.join(e['references'])} |" for e in ex]
open("../results/captioning_examples.md", "w").write("\n".join(md) + "\n"); print(scores)
