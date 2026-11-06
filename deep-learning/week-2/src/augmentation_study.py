"""Task 3: does data augmentation help, and which kind? A controlled experiment on a 10,000-image CIFAR-10 training
subset (augmentation matters most when data is limited): the same network (width 32), seed, schedule and 8 epochs (AUG_EPOCHS);
only the augmentation changes. Validation and test sets are untouched (no augmentation at evaluation time).
  none | flip | crop (pad 4 + random 32x32 crop) | rotation (±15°) | zoom (0.9-1.1) | all four together
    python src/augmentation_study.py -> results/augmentation.json, results/augmentation.png, results/augmentation_examples.png"""
import json, math, os, sys, time
import numpy as np
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import tensorflow as tf, keras
T = int(os.environ.get("THREADS", 0))
if T: tf.config.threading.set_intra_op_parallelism_threads(T); tf.config.threading.set_inter_op_parallelism_threads(1)
from keras import layers
sys.path.insert(0, os.path.dirname(__file__))
from cifar_data import load
from cifar_cnn import build, OneCycle
E, N = int(os.environ.get("AUG_EPOCHS", 8)), 10000
POL = {"none": [], "flip": [layers.RandomFlip("horizontal")], "crop": ["crop"], "rotation": [layers.RandomRotation(15 / 360, fill_mode="reflect")],
       "zoom": [layers.RandomZoom((-.1, .1), fill_mode="reflect")], "all": [layers.RandomFlip("horizontal"), "crop", layers.RandomRotation(15 / 360, fill_mode="reflect"), layers.RandomZoom((-.1, .1), fill_mode="reflect")]}
def pipeline(ops):
    def f(x, y):
        x = tf.cast(x, tf.float32)
        for op in ops:
            if op == "crop": x = tf.image.random_crop(tf.image.resize_with_crop_or_pad(x, 40, 40), (32, 32, 3))
            else: x = op(x[None], training=True)[0]
        return x, y
    return f
X, Y, XT, YT = load(); rng = np.random.default_rng(0); idx = rng.permutation(len(X)); tr, va = idx[:N], idx[45000:]
res = json.load(open("results/augmentation.json")) if os.path.exists("results/augmentation.json") else {}
for name, ops in POL.items():
    if name in res: continue
    tf.keras.utils.set_random_seed(0); m = build(32)
    m.compile(keras.optimizers.SGD(.1, momentum=.9, nesterov=True), keras.losses.SparseCategoricalCrossentropy(from_logits=True), metrics=["accuracy"])
    ds = tf.data.Dataset.from_tensor_slices((X[tr], Y[tr])).shuffle(N, seed=0)
    if ops: ds = ds.map(pipeline(ops), num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(128).prefetch(tf.data.AUTOTUNE); vd = tf.data.Dataset.from_tensor_slices((X[va], Y[va])).batch(512)
    t = time.time(); h = m.fit(ds, validation_data=vd, epochs=E, callbacks=[OneCycle(E * math.ceil(N / 128))], verbose=0)
    test = m.evaluate(XT, YT, batch_size=512, verbose=0)[1]
    res[name] = dict(test_accuracy=round(float(test), 4), final_train_accuracy=round(h.history["accuracy"][-1], 4), best_val=round(max(h.history["val_accuracy"]), 4),
                     train_minus_val=round(h.history["accuracy"][-1] - h.history["val_accuracy"][-1], 4), minutes=round((time.time() - t) / 60, 1), val_curve=[round(v, 4) for v in h.history["val_accuracy"]])
    json.dump(res, open("results/augmentation.json", "w"), indent=1); print(name, res[name]["test_accuracy"], flush=True)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2)); names = list(res); base = res["none"]["test_accuracy"]
b = ax[0].bar(names, [res[n]["test_accuracy"] * 100 for n in names], color=["#9aa1ad"] + ["#3b5bdb"] * (len(names) - 2) + ["#e8590c"])
for r, n in zip(b, names): ax[0].text(r.get_x() + r.get_width() / 2, r.get_height() + .4, f"{res[n]['test_accuracy']:.1%}\n({(res[n]['test_accuracy'] - base) * 100:+.1f})", ha="center", fontsize=9)
ax[0].set_ylim(min(res[n]["test_accuracy"] for n in names) * 100 - 8, max(res[n]["test_accuracy"] for n in names) * 100 + 5); ax[0].set_ylabel("test accuracy %"); ax[0].set_title(f"10k training images, {E} epochs")
ax[1].bar(names, [res[n]["train_minus_val"] * 100 for n in names], color="#868e96"); ax[1].set_ylabel("train - validation accuracy (points)"); ax[1].set_title("overfitting gap (lower is better)")
fig.tight_layout(); fig.savefig("results/augmentation.png", dpi=130)
ex = X[tr[:6]]; fig, axs = plt.subplots(6, 6, figsize=(8, 8))
for i in range(6):
    for j, n in enumerate(["none", "flip", "crop", "rotation", "zoom", "all"]):
        tf.keras.utils.set_random_seed(i * 10 + j); im = pipeline(POL[n])(ex[i], 0)[0].numpy().clip(0, 255).astype("uint8")
        axs[i, j].imshow(im); axs[i, j].axis("off")
        if i == 0: axs[i, j].set_title(n)
fig.tight_layout(); fig.savefig("results/augmentation_examples.png", dpi=110)
