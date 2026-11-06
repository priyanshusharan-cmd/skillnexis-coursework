"""Task 4: a DCGAN that generates handwritten digits (MNIST), PyTorch.
Generator: z(64) -> 7x7x128 -> transposed convs -> 28x28 tanh. Discriminator: strided convs + LeakyReLU + dropout.
Non-saturating loss, Adam (2e-4, beta1 0.5), one-sided label smoothing (0.9). Quality is measured, not eyeballed:
a separate MNIST classifier (trained here, ~99 % test accuracy) labels 10,000 generated digits; we report its mean
confidence and the class spread (entropy of the label histogram: log2(10) = 3.32 bits means all digits appear evenly).
    python src/gan_mnist.py -> results/gan.json, results/gan_samples.png, results/gan_progress.png"""
import json, math, os, sys, time
import numpy as np, torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(__file__)); from mnist_data import load
torch.manual_seed(0); torch.set_num_threads(int(os.environ.get("THREADS", 1)))
xtr, ytr, xte, yte = load("mnist"); X = torch.tensor(xtr[:, None] / 127.5 - 1, dtype=torch.float32)
G = nn.Sequential(nn.Linear(64, 7 * 7 * 128), nn.BatchNorm1d(7 * 7 * 128), nn.ReLU(), nn.Unflatten(1, (128, 7, 7)),
                  nn.ConvTranspose2d(128, 64, 4, 2, 1), nn.BatchNorm2d(64), nn.ReLU(), nn.ConvTranspose2d(64, 1, 4, 2, 1), nn.Tanh())
D = nn.Sequential(nn.Conv2d(1, 64, 4, 2, 1), nn.LeakyReLU(.2), nn.Dropout(.3), nn.Conv2d(64, 128, 4, 2, 1), nn.LeakyReLU(.2), nn.Dropout(.3), nn.Flatten(), nn.Linear(128 * 49, 1))
oG, oD = torch.optim.Adam(G.parameters(), 2e-4, betas=(.5, .999)), torch.optim.Adam(D.parameters(), 2e-4, betas=(.5, .999)); bce = nn.BCEWithLogitsLoss()
EP = int(os.environ.get("EPOCHS", 12)); fixed = torch.randn(64, 64); snaps, hist, t = [], [], time.time()
for ep in range(EP):
    perm = torch.randperm(len(X)); lg = ld = 0; n = 0
    for b in range(0, len(X), 128):
        real = X[perm[b:b + 128]]; k = len(real); z = torch.randn(k, 64); fake = G(z)
        lossD = bce(D(real), torch.full((k, 1), .9)) + bce(D(fake.detach()), torch.zeros(k, 1)); oD.zero_grad(); lossD.backward(); oD.step()
        lossG = bce(D(fake), torch.ones(k, 1)); oG.zero_grad(); lossG.backward(); oG.step(); lg += lossG.item(); ld += lossD.item(); n += 1
    G.eval()
    with torch.no_grad(): snaps.append(G(fixed[:16]).clone())
    G.train(); hist.append(dict(epoch=ep + 1, loss_G=round(lg / n, 3), loss_D=round(ld / n, 3))); print(hist[-1], f"{time.time() - t:.0f}s", flush=True)
# judge: an MNIST classifier
C = nn.Sequential(nn.Conv2d(1, 32, 3, 1, 1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, 1, 1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Dropout(.3), nn.Linear(64 * 49, 10))
oC = torch.optim.Adam(C.parameters(), 1e-3); Y = torch.tensor(ytr, dtype=torch.long)
for ep in range(2):
    perm = torch.randperm(len(X))
    for b in range(0, len(X), 128): i = perm[b:b + 128]; l = nn.functional.cross_entropy(C(X[i]), Y[i]); oC.zero_grad(); l.backward(); oC.step()
C.eval(); G.eval()
with torch.no_grad():
    Xt = torch.tensor(xte[:, None] / 127.5 - 1, dtype=torch.float32); acc = (C(Xt).argmax(1).numpy() == yte).mean()
    gen = torch.cat([G(torch.randn(1000, 64)) for _ in range(10)]); p = torch.softmax(C(gen), 1); lab = p.argmax(1).numpy(); conf = p.max(1).values.numpy()
    real_conf = torch.softmax(C(Xt), 1).max(1).values.mean().item()
h = np.bincount(lab, minlength=10) / len(lab); ent = float(-(h[h > 0] * np.log2(h[h > 0])).sum())
res = dict(epochs=EP, minutes=round((time.time() - t) / 60, 1), judge_test_accuracy=round(float(acc), 4), generated=len(lab), mean_judge_confidence_generated=round(float(conf.mean()), 3),
           mean_judge_confidence_real=round(real_conf, 3), share_confident_over_0_9=round(float((conf > .9).mean()), 3), class_histogram=[round(float(v), 3) for v in h], class_entropy_bits=round(ent, 3), history=hist)
json.dump(res, open("results/gan.json", "w"), indent=1); torch.save(G.state_dict(), "results/gan_generator.pt")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
with torch.no_grad(): s = G(fixed).numpy()
fig, axs = plt.subplots(8, 8, figsize=(6, 6))
for k, a in enumerate(axs.flat): a.imshow(s[k, 0], cmap="gray"); a.axis("off")
fig.suptitle(f"DCGAN samples after {EP} epochs"); fig.tight_layout(); fig.savefig("results/gan_samples.png", dpi=130)
pick = [0, 1, 3, EP // 2, EP - 1] if EP > 4 else list(range(EP)); fig, axs = plt.subplots(len(pick), 16, figsize=(12, len(pick) * .85))
for r, e in enumerate(pick):
    for j in range(16): axs[r, j].imshow(snaps[e][j, 0].numpy(), cmap="gray"); axs[r, j].axis("off")
    axs[r, 0].set_title(f"epoch {e + 1}", fontsize=8, loc="left")
fig.tight_layout(); fig.savefig("results/gan_progress.png", dpi=110); print({k: v for k, v in res.items() if k != "history"})
