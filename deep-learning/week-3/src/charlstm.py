"""Character-level LSTM language model (PyTorch), shared by task 2 (Shakespeare) and the mini project (Python code).
2-layer LSTM, embedding 64, hidden 384, dropout 0.2, 128-character sequences, AdamW + cosine schedule. Sampling
supports temperature, top-k and a seed prompt. 5 % of the corpus (the end) is held out to report bits per character.
    python src/charlstm.py <corpus.txt> <out.pt> [steps]"""
import json, math, os, sys, time
import torch, torch.nn as nn
torch.manual_seed(0); torch.set_num_threads(int(os.environ.get("THREADS", 1)))
class CharLSTM(nn.Module):
    def __init__(s, V, E=64, H=384, L=2, p=.2):
        super().__init__(); s.emb = nn.Embedding(V, E); s.lstm = nn.LSTM(E, H, L, batch_first=True, dropout=p); s.drop = nn.Dropout(p); s.out = nn.Linear(H, V)
    def forward(s, x, h=None): y, h = s.lstm(s.emb(x), h); return s.out(s.drop(y)), h
def load(path):
    ck = torch.load(path, map_location="cpu", weights_only=False); m = CharLSTM(len(ck["chars"]), **ck["cfg"]); m.load_state_dict(ck["state"]); m.eval(); return m, ck
@torch.no_grad()
def sample(m, ck, prompt="", n=400, temperature=.8, top_k=0, seed=None):
    if seed is not None: torch.manual_seed(seed)
    stoi = {c: i for i, c in enumerate(ck["chars"])}; prompt = "".join(c for c in prompt if c in stoi) or ck["chars"][0]
    x = torch.tensor([[stoi[c] for c in prompt]]); logits, h = m(x); out = []
    for _ in range(n):
        l = logits[0, -1] / max(temperature, 1e-3)
        if top_k: v, _ = l.topk(top_k); l[l < v[-1]] = -float("inf")
        c = torch.multinomial(torch.softmax(l, -1), 1); out.append(ck["chars"][c.item()]); logits, h = m(c.view(1, 1), h)
    return prompt + "".join(out)
if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]; STEPS = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
    text = open(src, encoding="utf-8").read(); chars = sorted(set(text)); stoi = {c: i for i, c in enumerate(chars)}
    data = torch.tensor([stoi[c] for c in text]); n = int(len(data) * .95); tr, va = data[:n], data[n:]; T, B = 128, 64
    cfg = dict(E=64, H=384, L=2, p=.2); m = CharLSTM(len(chars), **cfg); opt = torch.optim.AdamW(m.parameters(), 3e-3, weight_decay=.01)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, 3e-3, total_steps=STEPS, pct_start=.05); lossf = nn.CrossEntropyLoss()
    def batch(d): ix = torch.randint(0, len(d) - T - 1, (B,)); return torch.stack([d[i:i + T] for i in ix]), torch.stack([d[i + 1:i + T + 1] for i in ix])
    @torch.no_grad()
    def val():
        m.eval(); L = []
        for k in range(0, min(len(va) - T - 1, 64 * T * 8), T * 64):
            xs = torch.stack([va[k + j * T:k + j * T + T] for j in range(64) if k + j * T + T + 1 <= len(va)]); ys = torch.stack([va[k + j * T + 1:k + j * T + T + 1] for j in range(len(xs))])
            L.append(lossf(m(xs)[0].reshape(-1, len(chars)), ys.reshape(-1)).item())
        m.train(); return sum(L) / len(L)
    hist, t0 = [], time.time()
    for s in range(1, STEPS + 1):
        x, y = batch(tr); loss = lossf(m(x)[0].reshape(-1, len(chars)), y.reshape(-1)); opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step(); sched.step()
        if s % 250 == 0 or s == STEPS:
            v = val(); hist.append(dict(step=s, train_loss=round(loss.item(), 3), val_loss=round(v, 3), val_bpc=round(v / math.log(2), 3))); print(hist[-1], f"{time.time() - t0:.0f}s", flush=True)
    torch.save(dict(state=m.state_dict(), chars=chars, cfg=cfg, history=hist, corpus=os.path.basename(src), corpus_chars=len(text), minutes=round((time.time() - t0) / 60, 1)), dst)
    m.eval(); ck = dict(chars=chars)
    print(json.dumps({t: sample(m, ck, "\n", 300, t, seed=1) for t in (.5, .8, 1.2)}, indent=1))
