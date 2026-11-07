"""Task 2: what do batch normalisation, dropout and a learning-rate schedule each contribute?
A controlled ablation on Fashion-MNIST (Xiao et al. 2017): one small CNN, the same data, optimiser (SGD + Nesterov
momentum), epochs and seeds; exactly one ingredient changes between rows. Each configuration is trained with 2 seeds
and we report mean +/- spread of the test accuracy, plus the train-test gap (a direct read-out of over-fitting).

  plain            no BN, no dropout, constant LR 0.02
  +bn              batch norm after every conv/dense layer, constant LR (BN tolerates a larger LR: 0.05)
  +dropout         dropout 0.3 (dense) / 0.1 (conv), constant LR 0.02
  +bn+dropout      both, constant LR 0.05
  +bn+dropout+cos  both, cosine decay from 0.05 to 0
  +bn+dropout+step both, step decay (x0.1 at 50 % and 75 % of training)

Training uses a 20,000-image subset (over-fitting, the thing dropout fights, only shows up when data is limited);
the full 10,000-image test set is used for evaluation.
    python src/ablation.py -> results/ablation.json, results/ablation.png"""
import json, math, os, sys, time
import numpy as np
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import tensorflow as tf, keras
T = int(os.environ.get("THREADS", 0))
if T: tf.config.threading.set_intra_op_parallelism_threads(T); tf.config.threading.set_inter_op_parallelism_threads(1)
from keras import layers
sys.path.insert(0, os.path.dirname(__file__)); from mnist_data import load
E, N = int(os.environ.get("ABL_EPOCHS", 12)), 20000
SEEDS = tuple(int(x) for x in os.environ.get("SEEDS", "0,1").split(","))   # run seeds in parallel processes with SEEDS=0 / SEEDS=1, then SEEDS=0,1 to summarise
xtr, ytr, xte, yte = load("fashion")
rng = np.random.default_rng(0); idx = rng.permutation(len(xtr))[:N]
Xtr, Ytr = (xtr[idx, :, :, None] / 255.).astype("float32"), ytr[idx]; Xte, Yte = (xte[..., None] / 255.).astype("float32"), yte
CFG = {"plain": dict(bn=False, do=False, lr=.02, sched="const"), "+bn": dict(bn=True, do=False, lr=.05, sched="const"),
       "+dropout": dict(bn=False, do=True, lr=.02, sched="const"), "+bn+dropout": dict(bn=True, do=True, lr=.05, sched="const"),
       "+bn+dropout+cos": dict(bn=True, do=True, lr=.05, sched="cos"), "+bn+dropout+step": dict(bn=True, do=True, lr=.05, sched="step")}
def build(bn, do):
    def block(x, f):
        for _ in range(2):
            x = layers.Conv2D(f, 3, padding="same", use_bias=not bn)(x)
            if bn: x = layers.BatchNormalization()(x)
            x = layers.ReLU()(x)
        x = layers.MaxPool2D()(x)
        return layers.Dropout(.1)(x) if do else x
    i = keras.Input((28, 28, 1)); x = block(i, 32); x = block(x, 64); x = layers.Flatten()(x)
    x = layers.Dense(256, use_bias=not bn)(x)
    if bn: x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    if do: x = layers.Dropout(.3)(x)
    return keras.Model(i, layers.Dense(10)(x))
def schedule(kind, lr0, total):
    if kind == "cos": return keras.optimizers.schedules.CosineDecay(lr0, total)
    if kind == "step": return keras.optimizers.schedules.PiecewiseConstantDecay([int(total * .5), int(total * .75)], [lr0, lr0 * .1, lr0 * .01])
    return lr0
out = "results/ablation.json"; part = out if len(SEEDS) > 1 else f"results/ablation_seed{SEEDS[0]}.json"
res = {}
for f in {out, part, "results/ablation_seed0.json", "results/ablation_seed1.json"}:
    if os.path.exists(f): res.update({k: v for k, v in json.load(open(f)).items() if "|" in k})
for name, c in CFG.items():
    for seed in SEEDS:
        key = f"{name}|{seed}"
        if key in res: continue
        tf.keras.utils.set_random_seed(seed); m = build(c["bn"], c["do"]); steps = E * math.ceil(N / 128)
        m.compile(keras.optimizers.SGD(schedule(c["sched"], c["lr"], steps), momentum=.9, nesterov=True),
                  keras.losses.SparseCategoricalCrossentropy(from_logits=True), metrics=["accuracy"])
        t = time.time(); h = m.fit(Xtr, Ytr, validation_data=(Xte, Yte), epochs=E, batch_size=128, verbose=0)
        tr_acc = m.evaluate(Xtr, Ytr, verbose=0, batch_size=512)[1]; te_acc = m.evaluate(Xte, Yte, verbose=0, batch_size=512)[1]
        res[key] = dict(train_accuracy=round(float(tr_acc), 4), test_accuracy=round(float(te_acc), 4), seconds=round(time.time() - t),
                        test_curve=[round(v, 4) for v in h.history["val_accuracy"]], train_loss=[round(v, 4) for v in h.history["loss"]])
        json.dump({k: v for k, v in res.items() if "|" in k}, open(part, "w"), indent=1); print(key, res[key]["train_accuracy"], res[key]["test_accuracy"], res[key]["seconds"], "s", flush=True)
if len(SEEDS) == 1: sys.exit(0)
summary = {}
for name in CFG:
    te = [res[f"{name}|{s}"]["test_accuracy"] for s in SEEDS]; tr = [res[f"{name}|{s}"]["train_accuracy"] for s in SEEDS]
    summary[name] = dict(test_mean=round(float(np.mean(te)), 4), test_spread=round(float(np.ptp(te)) / 2, 4), gap=round(float(np.mean(tr) - np.mean(te)), 4))
res["summary"] = summary; res["setup"] = dict(epochs=E, train_images=N, test_images=len(Yte), seeds=list(SEEDS)); json.dump(res, open(out, "w"), indent=1)
print(json.dumps(summary, indent=1))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5)); names = list(CFG)
ax[0].barh(names, [summary[n]["test_mean"] * 100 for n in names], xerr=[summary[n]["test_spread"] * 100 for n in names], color="#4c6ef5")
lo = min(summary[n]["test_mean"] for n in names) * 100 - 1.5; hi = max(summary[n]["test_mean"] for n in names) * 100 + 3; ax[0].set_xlim(lo, hi); ax[0].invert_yaxis()
for k, n in enumerate(names): ax[0].text((summary[n]["test_mean"] + summary[n]["test_spread"]) * 100 + .1, k, f'{summary[n]["test_mean"]:.2%}  (gap {summary[n]["gap"]:.1%})', va="center", fontsize=8)
ax[0].set_xlabel("test accuracy %, mean of 2 seeds"); ax[0].set_title("Ablation (Fashion-MNIST, 20k training images)")
for n in names: ax[1].plot(range(1, E + 1), np.mean([res[f"{n}|{s}"]["test_curve"] for s in SEEDS], 0) * 100, label=n)
ax[1].set_xlabel("epoch"); ax[1].set_ylabel("test accuracy %"); ax[1].set_ylim(85, None); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3); ax[1].set_title("Test accuracy per epoch")
fig.tight_layout(); fig.savefig("results/ablation.png", dpi=130)
