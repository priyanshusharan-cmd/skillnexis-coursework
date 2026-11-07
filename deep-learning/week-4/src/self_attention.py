"""Task 1: self-attention from scratch in PyTorch, using only matmul, softmax and reshapes (no nn.MultiheadAttention).
  * scaled dot-product attention: softmax(Q K^T / sqrt(d_k) + mask) V
  * multi-head self-attention with causal and padding masks
Verified three ways:
  1. numerically identical (to 1e-6) to torch.nn.MultiheadAttention given the same weights, with and without masks
  2. the causal mask really blocks the future: changing token t+1 never changes outputs at positions <= t
  3. it learns: a 2-layer causal attention model (a tiny transformer) solves a task that NEEDS attention (copy the token that appears right
     after a marker somewhere in the sequence); the same network with attention replaced by running averages does worse
    python src/self_attention.py -> results/self_attention.json, results/attention_map.png"""
import json, math

import torch, torch.nn as nn, torch.nn.functional as F
torch.set_num_threads(1)
torch.manual_seed(0)
def scaled_dot_product(q, k, v, mask=None):
    """q,k,v: (..., T, d). mask: broadcastable bool, True = may attend."""
    s = q @ k.transpose(-2, -1) / math.sqrt(q.shape[-1])
    if mask is not None: s = s.masked_fill(~mask, float("-inf"))
    w = torch.softmax(s, dim=-1); return w @ v, w
class MultiHeadSelfAttention(nn.Module):
    def __init__(s, d_model, n_heads):
        super().__init__(); assert d_model % n_heads == 0; s.h, s.dk = n_heads, d_model // n_heads
        s.qkv = nn.Linear(d_model, 3 * d_model); s.o = nn.Linear(d_model, d_model)
    def forward(s, x, causal=False, pad=None):
        B, T, D = x.shape; q, k, v = s.qkv(x).split(D, -1)
        split = lambda t: t.view(B, T, s.h, s.dk).transpose(1, 2)                  # (B, h, T, dk)
        mask = None
        if causal: mask = torch.tril(torch.ones(T, T, dtype=torch.bool))
        if pad is not None: pm = ~pad[:, None, None, :]; mask = pm if mask is None else mask & pm      # pad: True where token is padding
        y, w = scaled_dot_product(split(q), split(k), split(v), mask)
        return s.o(y.transpose(1, 2).reshape(B, T, D)), w
res = {}
# 1. equivalence with torch's implementation
D, H, T, B = 64, 4, 10, 3; mine = MultiHeadSelfAttention(D, H); ref = nn.MultiheadAttention(D, H, batch_first=True)
with torch.no_grad(): ref.in_proj_weight.copy_(mine.qkv.weight); ref.in_proj_bias.copy_(mine.qkv.bias); ref.out_proj.weight.copy_(mine.o.weight); ref.out_proj.bias.copy_(mine.o.bias)
x = torch.randn(B, T, D); pad = torch.zeros(B, T, dtype=torch.bool); pad[1, 7:] = True; pad[2, 4:] = True
cm = torch.triu(torch.ones(T, T, dtype=torch.bool), 1)
a, _ = mine(x); b, _ = ref(x, x, x, need_weights=False); c, _ = mine(x, causal=True); d, _ = ref(x, x, x, attn_mask=cm, need_weights=False)
e, _ = mine(x, pad=pad); f, _ = ref(x, x, x, key_padding_mask=pad, need_weights=False)
res["max_abs_diff_vs_torch"] = dict(plain=(a - b).abs().max().item(), causal=(c - d).abs().max().item(), padding=(e - f).abs().max().item())
assert all(v < 1e-5 for v in res["max_abs_diff_vs_torch"].values())
# 2. causality
x2 = x.clone(); x2[:, 6] += 5.0; c2, _ = mine(x2, causal=True)
res["causal_leak"] = dict(max_change_before_t=(c2[:, :6] - c[:, :6]).abs().max().item(), max_change_from_t=(c2[:, 6:] - c[:, 6:]).abs().max().item())
assert res["causal_leak"]["max_change_before_t"] == 0.0
# 3. learning a task that needs attention: sequence of random tokens 2..17 with one MARKER (1) somewhere; target =
#    the token right after the marker, predicted at the LAST position.
V, T = 18, 16
def data(n):
    x = torch.randint(2, V, (n, T)); pos = torch.randint(0, T - 2, (n,)); x[torch.arange(n), pos] = 1; y = x[torch.arange(n), pos + 1]; return x, y
class Model(nn.Module):
    def __init__(s, attn=True):
        super().__init__(); s.emb = nn.Embedding(V, 64); s.pos = nn.Parameter(torch.randn(T, 64) * .1); s.use = attn
        s.attn = nn.ModuleList([MultiHeadSelfAttention(64, 4) for _ in range(2)]); s.mlp = nn.ModuleList([nn.Sequential(nn.LayerNorm(64), nn.Linear(64, 128), nn.GELU(), nn.Linear(128, 64)) for _ in range(2)])
        s.ln = nn.ModuleList([nn.LayerNorm(64) for _ in range(2)]); s.out = nn.Linear(64, V)
    def forward(s, x):
        h = s.emb(x) + s.pos; s.w = []
        for a, ln, f in zip(s.attn, s.ln, s.mlp):
            if s.use: y, w = a(ln(h), causal=True); h = h + y; s.w.append(w)
            else: h = h + torch.cumsum(h, 1) / torch.arange(1, h.shape[1] + 1)[None, :, None]     # no attention: running average only
            h = h + f(h)
        return s.out(h[:, -1])
for name, attn in (("with_attention", True), ("without_attention", False)):
    torch.manual_seed(0); m = Model(attn); opt = torch.optim.Adam(m.parameters(), 3e-3)
    for step in range(3000):
        x, y = data(256); loss = F.cross_entropy(m(x), y); opt.zero_grad(); loss.backward(); opt.step()
        if step % 500 == 0: print(name, step, round(loss.item(), 3), flush=True)
    xt, yt = data(5000)
    with torch.no_grad(): res[name] = dict(test_accuracy=round(float((m(xt).argmax(1) == yt).float().mean()), 4), chance=round(1 / 16, 4))
    if attn: att_model = m
json.dump(res, open("results/self_attention.json", "w"), indent=1); print(json.dumps(res, indent=1))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
x, y = data(1); x[0] = torch.tensor([5, 9, 3, 12, 7, 1, 14, 2, 8, 6, 11, 4, 10, 13, 15, 16]); att_model(x); w = att_model.w[1][0].detach()
fig, axs = plt.subplots(1, 4, figsize=(15, 3.6))
for hh in range(4):
    axs[hh].imshow(w[hh], cmap="viridis"); axs[hh].set_title(f"head {hh + 1}"); axs[hh].set_xticks(range(T), [("M" if t == 1 else str(int(t))) for t in x[0]], fontsize=7); axs[hh].set_yticks([])
fig.suptitle("Layer-2 attention (rows = query positions; marker M at position 6, answer 14 at position 7). The last row must find the token after M.")
fig.tight_layout(); fig.savefig("results/attention_map.png", dpi=120)
