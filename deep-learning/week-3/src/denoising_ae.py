"""Task 3: convolutional denoising autoencoder on Fashion-MNIST (PyTorch).
Noise: Gaussian (sigma 0.5) on [0,1] pixels, clipped, re-sampled every batch. Encoder 28 -> 14 -> 7 (32/64 channels),
decoder mirrors it with transposed convolutions; trained to output the CLEAN image (MSE). Evaluated on the 10,000 test
images: PSNR of noisy vs denoised against the clean image, at the training noise level and at unseen levels.
    python src/denoising_ae.py -> results/denoising.json, results/denoising.png, results/dae.pt"""
import json, math, os, sys, time
import numpy as np, torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(__file__)); from mnist_data import load
torch.manual_seed(0); torch.set_num_threads(int(os.environ.get("THREADS", 1)))
xtr, _, xte, _ = load("fashion"); Xtr = torch.tensor(xtr[:, None] / 255., dtype=torch.float32); Xte = torch.tensor(xte[:, None] / 255., dtype=torch.float32)
class DAE(nn.Module):
    def __init__(s):
        super().__init__()
        s.enc = nn.Sequential(nn.Conv2d(1, 32, 3, 2, 1), nn.BatchNorm2d(32), nn.ReLU(), nn.Conv2d(32, 64, 3, 2, 1), nn.BatchNorm2d(64), nn.ReLU(), nn.Conv2d(64, 64, 3, 1, 1), nn.ReLU())
        s.dec = nn.Sequential(nn.ConvTranspose2d(64, 32, 4, 2, 1), nn.BatchNorm2d(32), nn.ReLU(), nn.ConvTranspose2d(32, 16, 4, 2, 1), nn.ReLU(), nn.Conv2d(16, 1, 3, 1, 1), nn.Sigmoid())
    def forward(s, x): return s.dec(s.enc(x))
noisy = lambda x, s: (x + s * torch.randn_like(x)).clamp(0, 1)
psnr = lambda a, b: (10 * torch.log10(1 / ((a - b) ** 2).mean((1, 2, 3)))).mean().item()
m = DAE(); opt = torch.optim.Adam(m.parameters(), 1e-3); EP = int(os.environ.get("EPOCHS", 8)); t = time.time(); hist = []
for ep in range(EP):
    perm = torch.randperm(len(Xtr)); tot = 0
    for b in range(0, len(Xtr), 128):
        x = Xtr[perm[b:b + 128]]; loss = ((m(noisy(x, .5)) - x) ** 2).mean(); opt.zero_grad(); loss.backward(); opt.step(); tot += loss.item() * len(x)
    hist.append(round(tot / len(Xtr), 5)); print(ep + 1, hist[-1], f"{time.time() - t:.0f}s", flush=True)
m.eval(); torch.manual_seed(1); res = dict(epochs=EP, params=sum(p.numel() for p in m.parameters()), minutes=round((time.time() - t) / 60, 1), train_mse=hist, test={})
with torch.no_grad():
    for s in (.3, .5, .7):
        n = noisy(Xte, s); d = torch.cat([m(n[k:k + 1000]) for k in range(0, len(n), 1000)])
        res["test"][f"sigma_{s}"] = dict(psnr_noisy=round(psnr(n, Xte), 2), psnr_denoised=round(psnr(d, Xte), 2), gain_db=round(psnr(d, Xte) - psnr(n, Xte), 2))
torch.save(m.state_dict(), "results/dae.pt"); json.dump(res, open("results/denoising.json", "w"), indent=1)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
torch.manual_seed(2); idx = [0, 1, 2, 3, 5, 8, 13, 21]; x = Xte[idx]
with torch.no_grad(): rows = [("clean", x), ("noisy σ=0.5", noisy(x, .5))]; rows.append(("denoised", m(rows[1][1])))
fig, axs = plt.subplots(3, len(idx), figsize=(len(idx) * 1.2, 4))
for r, (name, im) in enumerate(rows):
    for j in range(len(idx)): axs[r, j].imshow(im[j, 0], cmap="gray", vmin=0, vmax=1); axs[r, j].axis("off")
    axs[r, 0].set_title(name, fontsize=9, loc="left")
fig.suptitle(f"Denoising autoencoder · test PSNR {res['test']['sigma_0.5']['psnr_noisy']} → {res['test']['sigma_0.5']['psnr_denoised']} dB"); fig.tight_layout(); fig.savefig("results/denoising.png", dpi=130); print(res["test"])
