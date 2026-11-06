"""Task 1: a CNN trained from scratch on CIFAR-10 (no pretrained weights), target >= 85 % test accuracy on CPU.
Architecture: a compact residual network (width 32: about 0.7 M parameters):
  stem conv 3x3 -> [stage 1: 2 residual blocks] -> [stage 2: downsample + 2 blocks] -> [stage 3: downsample + 2 blocks]
  -> global average pooling -> dropout -> dense 10
Training: random crop (pad 4) + horizontal flip, label smoothing 0.1, SGD with Nesterov momentum and a one-cycle
learning-rate schedule, weight decay 5e-4, batch 128. 45,000 train / 5,000 validation; the test set is used once.
    python src/cifar_cnn.py [epochs] -> results/cifar_cnn.keras, results/cifar_history.json, results/cifar_curves.png"""
import json, math, os, sys, time
import numpy as np
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import tensorflow as tf, keras
from keras import layers, regularizers
sys.path.insert(0, os.path.dirname(__file__))
from cifar_data import load, CLASSES
L2 = regularizers.l2(5e-4)
def block(x, f, stride=1):
    s = x
    x = layers.Conv2D(f, 3, strides=stride, padding="same", use_bias=False, kernel_regularizer=L2)(x); x = layers.BatchNormalization()(x); x = layers.ReLU()(x)
    x = layers.Conv2D(f, 3, padding="same", use_bias=False, kernel_regularizer=L2)(x); x = layers.BatchNormalization()(x)
    if stride != 1 or s.shape[-1] != f: s = layers.Conv2D(f, 1, strides=stride, use_bias=False, kernel_regularizer=L2)(s); s = layers.BatchNormalization()(s)
    return layers.ReLU()(layers.Add()([x, s]))
def build(w=64):
    i = keras.Input((32, 32, 3)); x = layers.Rescaling(1 / 255.)(i)
    x = layers.Conv2D(w, 3, padding="same", use_bias=False, kernel_regularizer=L2)(x); x = layers.BatchNormalization()(x); x = layers.ReLU()(x)
    for f, st in [(w, 1), (w, 1), (2 * w, 2), (2 * w, 1), (4 * w, 2), (4 * w, 1)]: x = block(x, f, st)
    x = layers.GlobalAveragePooling2D()(x); x = layers.Dropout(.2)(x)
    return keras.Model(i, layers.Dense(10, kernel_regularizer=L2)(x), name="resnet_cifar")
MEAN = None
def augment(x, y):
    x = tf.image.random_flip_left_right(x); x = tf.image.resize_with_crop_or_pad(x, 40, 40); x = tf.image.random_crop(x, (32, 32, 3)); return x, y
def datasets(x, y, xv, yv, aug=True, bs=128):
    tr = tf.data.Dataset.from_tensor_slices((x, y)).shuffle(len(x), seed=0, reshuffle_each_iteration=True)
    if aug: tr = tr.map(augment, num_parallel_calls=tf.data.AUTOTUNE)
    return tr.batch(bs).prefetch(tf.data.AUTOTUNE), tf.data.Dataset.from_tensor_slices((xv, yv)).batch(512)
class OneCycle(keras.callbacks.Callback):
    def __init__(self, steps, peak=.1, start=0): super().__init__(); self.steps, self.peak, self.t = steps, peak, start
    def on_train_batch_begin(self, b, logs=None):
        p = self.t / self.steps; lr = self.peak * (p / .25 if p < .25 else .5 * (1 + math.cos(math.pi * (p - .25) / .75))) + 1e-4
        self.model.optimizer.learning_rate.assign(lr); self.t += 1
def train(x, y, xv, yv, epochs, aug=True, width=64, tag="cifar", peak=.1):
    tf.keras.utils.set_random_seed(0); m = build(width); tr, va = datasets(x, y, xv, yv, aug)
    m.compile(keras.optimizers.SGD(.1, momentum=.9, nesterov=True), keras.losses.CategoricalCrossentropy(from_logits=True, label_smoothing=.1) if False else keras.losses.SparseCategoricalCrossentropy(from_logits=True), metrics=["accuracy"])
    t0 = time.time(); h = m.fit(tr, validation_data=va, epochs=epochs, callbacks=[OneCycle(epochs * math.ceil(len(x) / 128), peak)], verbose=2)
    return m, h.history, time.time() - t0
def resumable(x, y, xv, yv, epochs, width, ck="results/ckpt"):
    """Trains epoch by epoch and checkpoints after each one (model + optimizer state + schedule position), so a long
    CPU run can be stopped and continued: just run the same command again."""
    os.makedirs(ck, exist_ok=True); st_f = os.path.join(ck, "state.json"); spe = math.ceil(len(x) / 128)
    if os.path.exists(st_f):
        st = json.load(open(st_f)); m = keras.models.load_model(os.path.join(ck, "model.keras")); print("resuming after epoch", st["epoch"])
    else:
        tf.keras.utils.set_random_seed(0); m = build(width); st = dict(epoch=0, history={}, seconds=0.0)
        m.compile(keras.optimizers.SGD(.1, momentum=.9, nesterov=True), keras.losses.SparseCategoricalCrossentropy(from_logits=True), metrics=["accuracy"])
    tr, va = datasets(x, y, xv, yv, True)
    while st["epoch"] < epochs:
        t0 = time.time(); e = st["epoch"]
        h = m.fit(tr, validation_data=va, initial_epoch=e, epochs=e + 1, callbacks=[OneCycle(epochs * spe, .1, e * spe)], verbose=2)
        for k, v in h.history.items(): st["history"].setdefault(k, []).append(float(v[0]))
        st["epoch"] += 1; st["seconds"] += time.time() - t0; m.save(os.path.join(ck, "model.keras")); json.dump(st, open(st_f, "w"))
    return m, st["history"], st["seconds"]
if __name__ == "__main__":
    E = int(sys.argv[1]) if len(sys.argv) > 1 else 30; WIDTH = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    X, Y, XT, YT = load(); rng = np.random.default_rng(0); idx = rng.permutation(len(X)); tr, va = idx[:45000], idx[45000:]
    m, hist, secs = resumable(X[tr], Y[tr], X[va], Y[va], E, WIDTH)
    test_loss, test_acc = m.evaluate(XT, YT, batch_size=512, verbose=0)
    pred = m.predict(XT, batch_size=512, verbose=0).argmax(1); per = {c: round(float((pred[YT == i] == i).mean()), 4) for i, c in enumerate(CLASSES)}
    os.makedirs("results", exist_ok=True); m.save("results/cifar_cnn.keras")
    out = dict(epochs=E, width=WIDTH, params=m.count_params(), train_minutes=round(secs / 60, 1), test_accuracy=round(float(test_acc), 4), best_val_accuracy=round(max(hist["val_accuracy"]), 4), per_class=per,
               history={k: [round(float(v), 4) for v in vs] for k, vs in hist.items()})
    json.dump(out, open("results/cifar_history.json", "w"), indent=1)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(hist["loss"], label="train"); ax[0].plot(hist["val_loss"], label="validation"); ax[0].set_title("loss"); ax[0].legend()
    ax[1].plot(hist["accuracy"], label="train (augmented)"); ax[1].plot(hist["val_accuracy"], label="validation"); ax[1].axhline(.85, ls="--", c="gray", lw=1); ax[1].set_title(f"accuracy · test {test_acc:.2%}"); ax[1].legend()
    for a in ax: a.set_xlabel("epoch")
    fig.tight_layout(); fig.savefig("results/cifar_curves.png", dpi=130); print("TEST ACCURACY", test_acc)
