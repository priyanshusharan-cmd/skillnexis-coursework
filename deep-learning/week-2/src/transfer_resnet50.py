"""Task 2: transfer learning with ResNet50 (ImageNet weights) on a 5-class custom dataset: PlantVillage tomato
leaves (healthy, early blight, late blight, leaf mold, bacterial spot), with 280 training images per class.
CPU-friendly two-stage recipe:
  A. frozen ResNet50 -> global-average-pooled features -> softmax head            (feature extraction)
  B. unfreeze the last stage (conv5, ~15 M parameters) and fine-tune it with the head at a low learning rate,
     running it on cached conv4 outputs so the frozen 80 % of the network is computed only once
  Baseline: the same images through a small CNN trained from scratch, to show what pretraining buys.
Weights: the official Keras ResNet50 'notop' file (github.com/fchollet/deep-learning-models releases), MD5 checked.
    python src/transfer_resnet50.py -> results/transfer.json, results/transfer_confusion.png"""
import json, os, sys, time
import numpy as np
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import tensorflow as tf, keras
from keras import layers
sys.path.insert(0, os.path.dirname(__file__))
import plant_data as P
W = os.environ.get("RESNET_WEIGHTS", "/tmp/claude-0/resnet50_notop.h5"); C = os.path.join(os.path.dirname(__file__), "..", "data", "cache"); os.makedirs(C, exist_ok=True)
tf.keras.utils.set_random_seed(0)
s = P.split(P.FIVE); cls = P.FIVE
base = keras.applications.ResNet50(include_top=False, weights=None, input_shape=(224, 224, 3)); import resnet_weights; print("loaded", resnet_weights.load(base, W), "layers")
cut = base.get_layer("conv4_block6_out").output
front = keras.Model(base.input, cut)
def conv5_stage():
    """ResNet50's conv5 stage rebuilt as its own model (same layer names, weights copied from the pretrained base), so it
    can be trained on cached conv4 outputs."""
    i = keras.Input((14, 14, 1024)); x = i
    for b in (1, 2, 3):
        n = f"conv5_block{b}"; st = 2 if b == 1 else 1
        sc = layers.BatchNormalization(epsilon=1.001e-5, name=n + "_0_bn")(layers.Conv2D(2048, 1, strides=st, name=n + "_0_conv")(x)) if b == 1 else x
        y = layers.Activation("relu")(layers.BatchNormalization(epsilon=1.001e-5, name=n + "_1_bn")(layers.Conv2D(512, 1, strides=st, name=n + "_1_conv")(x)))
        y = layers.Activation("relu")(layers.BatchNormalization(epsilon=1.001e-5, name=n + "_2_bn")(layers.Conv2D(512, 3, padding="same", name=n + "_2_conv")(y)))
        y = layers.BatchNormalization(epsilon=1.001e-5, name=n + "_3_bn")(layers.Conv2D(2048, 1, name=n + "_3_conv")(y))
        x = layers.Activation("relu")(layers.Add()([sc, y]))
    m = keras.Model(i, x, name="conv5")
    for l in m.layers:
        if l.get_weights(): l.set_weights(base.get_layer(l.name).get_weights())
    return m
back = conv5_stage()
chk = np.random.default_rng(0).normal(size=(1, 224, 224, 3)).astype("float32")
assert np.allclose(back(front(chk)).numpy(), base(chk).numpy(), atol=1e-3), "rebuilt conv5 differs from the original"
def conv4(part):
    f = os.path.join(C, f"r50_conv4_{part}.npz")
    if os.path.exists(f): d = np.load(f); return d["x"], d["y"]
    rows = s[part]; t = time.time(); Fs, ys = [], []
    for k in range(0, len(rows), 96):                                   # in chunks: keeps memory under ~1 GB
        X, y = P.arrays(rows[k:k + 96], cls, 224); Fs.append(front.predict(keras.applications.resnet50.preprocess_input(X), batch_size=32, verbose=0).astype("float16")); ys.append(y)
    F, y = np.concatenate(Fs), np.concatenate(ys); print(part, F.shape, f"{time.time() - t:.0f}s", flush=True); np.savez(f, x=F, y=y); return F, y
(Xtr, ytr), (Xva, yva), (Xte, yte) = conv4("train"), conv4("val"), conv4("test")

def head_model(trainable):
    back.trainable = trainable; i = keras.Input(Xtr.shape[1:]); x = back(i, training=False)       # BN stays in inference mode
    x = layers.GlobalAveragePooling2D()(x); x = layers.Dropout(.3)(x); return keras.Model(i, layers.Dense(len(cls), activation="softmax")(x))
def ds(X, y, shuffle=False):
    d = tf.data.Dataset.from_tensor_slices((X, y))
    if shuffle: d = d.shuffle(len(y), seed=0)
    return d.batch(32).map(lambda a, b: (tf.cast(a, tf.float32), b)).prefetch(2)
TR, VA, TE = ds(Xtr, ytr, True), ds(Xva, yva), ds(Xte, yte)
res = {}
# A: frozen
m = head_model(False); m.compile(keras.optimizers.Adam(1e-3), "sparse_categorical_crossentropy", metrics=["accuracy"])
t = time.time(); hA = m.fit(TR, validation_data=VA, epochs=15, verbose=0, callbacks=[keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True)])
res["A_frozen"] = dict(test_accuracy=round(float(m.evaluate(TE, verbose=0)[1]), 4), best_val=round(max(hA.history["val_accuracy"]), 4), epochs=len(hA.history["loss"]), seconds=round(time.time() - t))
# B: fine-tune conv5 (starting from A's head)
back.trainable = True; m.compile(keras.optimizers.Adam(1e-5), "sparse_categorical_crossentropy", metrics=["accuracy"])
t = time.time(); hB = m.fit(TR, validation_data=VA, epochs=8, verbose=0, callbacks=[keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True)])
pb = m.predict(TE, verbose=0); res["B_finetuned_conv5"] = dict(test_accuracy=round(float((pb.argmax(1) == yte).mean()), 4), best_val=round(max(hB.history["val_accuracy"]), 4), epochs=len(hB.history["loss"]), seconds=round(time.time() - t),
                                                                trainable_params=int(sum(np.prod(v.shape) for v in m.trainable_weights)))
# baseline: from scratch at 128 px
Xs, ys_ = P.arrays(s["train"], cls, 128); Xsv, ysv = P.arrays(s["val"], cls, 128); Xst, yst = P.arrays(s["test"], cls, 128)
aug = keras.Sequential([layers.RandomFlip("horizontal_and_vertical"), layers.RandomRotation(.1)])
i = keras.Input((128, 128, 3)); x = aug(i); x = layers.Rescaling(1 / 255.)(x)
for f in (32, 64, 128, 128): x = layers.Conv2D(f, 3, padding="same", activation="relu")(x); x = layers.BatchNormalization()(x); x = layers.MaxPooling2D()(x)
x = layers.GlobalAveragePooling2D()(x); x = layers.Dropout(.3)(x); sc = keras.Model(i, layers.Dense(len(cls), activation="softmax")(x))
sc.compile(keras.optimizers.Adam(1e-3), "sparse_categorical_crossentropy", metrics=["accuracy"]); t = time.time()
hS = sc.fit(Xs, ys_, validation_data=(Xsv, ysv), epochs=30, batch_size=32, verbose=0, callbacks=[keras.callbacks.EarlyStopping(patience=6, restore_best_weights=True)])
res["baseline_scratch_cnn"] = dict(test_accuracy=round(float(sc.evaluate(Xst, yst, verbose=0)[1]), 4), best_val=round(max(hS.history["val_accuracy"]), 4), epochs=len(hS.history["loss"]), seconds=round(time.time() - t), params=sc.count_params())
res["data"] = dict(classes=[P.pretty(c) for c in cls], train=len(ytr), val=len(yva), test=len(yte))
from sklearn.metrics import confusion_matrix, classification_report
cm = confusion_matrix(yte, pb.argmax(1)); res["B_report"] = classification_report(yte, pb.argmax(1), target_names=res["data"]["classes"], output_dict=True)
json.dump(res, open("results/transfer.json", "w"), indent=1); m.save("results/resnet50_tomato5.keras")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6.2, 5.2)); ax.imshow(cm, cmap="Greens"); n = len(cls)
for a in range(n):
    for b in range(n): ax.text(b, a, cm[a, b], ha="center", va="center", color="white" if cm[a, b] > cm.max() / 2 else "black")
ax.set_xticks(range(n), res["data"]["classes"], rotation=30, ha="right"); ax.set_yticks(range(n), res["data"]["classes"]); ax.set_title(f"ResNet50 fine-tuned · test {res['B_finetuned_conv5']['test_accuracy']:.1%}")
fig.tight_layout(); fig.savefig("results/transfer_confusion.png", dpi=130)
print(json.dumps({k: v for k, v in res.items() if k != "B_report"}, indent=1))
