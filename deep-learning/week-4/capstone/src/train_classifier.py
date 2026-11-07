"""Capstone, model: blood-cell type classifier (RBC / WBC / Platelets) on BCCD cell crops.
MobileNetV2 (ImageNet weights, official Keras file) at 96x96, transfer learning in two stages:
  A: frozen backbone, train a small head on cached features, class-weighted (RBCs outnumber the others 11:1)
  B: unfreeze the last 30 layers and fine-tune with augmentation (flips, 90-degree rotations: cells have no
     orientation, brightness/contrast for stain variation) at a low learning rate
The stage with the better validation macro-F1 is kept, exported to TFLite (dynamic-range int8) for the API.
Official BCCD splits by image: train 205 images, val 87, test 72.
    python src/train_classifier.py -> models/cells.keras, models/cells.tflite, results/classifier.json, results/classifier_confusion.png"""
import json, os, sys, time
import numpy as np
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import tensorflow as tf, keras
from keras import layers
T = int(os.environ.get("THREADS", 0))
if T: tf.config.threading.set_intra_op_parallelism_threads(T); tf.config.threading.set_inter_op_parallelism_threads(1)
from sklearn.metrics import classification_report, confusion_matrix, f1_score
sys.path.insert(0, os.path.dirname(__file__)); import bccd
tf.keras.utils.set_random_seed(0); S = 96; W = os.environ.get("MNV2_WEIGHTS", "/tmp/claude-0/mobilenetv2_notop.h5"); os.makedirs("models", exist_ok=True)
(Xtr, ytr), (Xva, yva), (Xte, yte) = [bccd.crops(bccd.split(s), S) for s in ("train", "val", "test")]
counts = np.bincount(ytr, minlength=3); cw = {i: float(len(ytr) / (3 * c)) for i, c in enumerate(counts)}
print("crops", dict(train=len(ytr), val=len(yva), test=len(yte)), "train per class", dict(zip(bccd.CLASSES, counts.tolist())), flush=True)
base = keras.applications.MobileNetV2(include_top=False, weights=None, input_shape=(S, S, 3)); base.load_weights(W)
fi = keras.Input((S, S, 3)); fe = keras.Model(fi, layers.GlobalAveragePooling2D()(base(layers.Rescaling(1 / 127.5, offset=-1)(fi), training=False)))
res = {"data": dict(train=len(ytr), val=len(yva), test=len(yte), train_per_class=dict(zip(bccd.CLASSES, counts.tolist())))}; t = time.time()
Ftr, Fva, Fte = [fe.predict(X, batch_size=128, verbose=0) for X in (Xtr, Xva, Xte)]
head = keras.Sequential([keras.Input(Ftr.shape[1:]), layers.Dropout(.3), layers.Dense(3, activation="softmax")]); head.compile(keras.optimizers.Adam(1e-3), "sparse_categorical_crossentropy", metrics=["accuracy"])
head.fit(Ftr, ytr, validation_data=(Fva, yva), epochs=60, batch_size=64, verbose=0, class_weight=cw, callbacks=[keras.callbacks.EarlyStopping(patience=8, restore_best_weights=True)])
mf1 = lambda y, p: round(float(f1_score(y, p, average="macro")), 4)
res["A_frozen"] = dict(val_macro_f1=mf1(yva, head.predict(Fva, verbose=0).argmax(1)), test_macro_f1=mf1(yte, head.predict(Fte, verbose=0).argmax(1)), minutes=round((time.time() - t) / 60, 1)); print(res["A_frozen"], flush=True)
aug = keras.Sequential([layers.RandomFlip("horizontal_and_vertical"), layers.RandomRotation(.5, fill_mode="reflect"), layers.RandomBrightness(.15, value_range=(0, 255)), layers.RandomContrast(.15)], name="augment")
i = keras.Input((S, S, 3)); x = layers.Rescaling(1 / 127.5, offset=-1, name="preprocess")(aug(i)); x = base(x, training=False); x = layers.GlobalAveragePooling2D()(x); x = layers.Dropout(.3)(x)
out = layers.Dense(3, activation="softmax")(x); model = keras.Model(i, out); model.layers[-1].set_weights(head.layers[-1].get_weights()); wA = model.get_weights()
base.trainable = True
for l in base.layers[:-30]: l.trainable = False
for l in base.layers:
    if isinstance(l, layers.BatchNormalization): l.trainable = False
model.compile(keras.optimizers.Adam(3e-5), "sparse_categorical_crossentropy", metrics=["accuracy"]); t = time.time()
h = model.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=int(os.environ.get("FT_EPOCHS", 12)), batch_size=32, verbose=2, class_weight=cw, callbacks=[keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True)])
vB = mf1(yva, model.predict(Xva, verbose=0).argmax(1)); tB = mf1(yte, model.predict(Xte, verbose=0).argmax(1))
res["B_finetuned"] = dict(val_macro_f1=vB, test_macro_f1=tB, epochs=len(h.history["loss"]), minutes=round((time.time() - t) / 60, 1)); chosen = "B_finetuned"
if vB < res["A_frozen"]["val_macro_f1"]: model.set_weights(wA); chosen = "A_frozen"
print(res["B_finetuned"], "-> keeping", chosen, flush=True)
p = model.predict(Xte, verbose=0); pred = p.argmax(1)
res["deployed"] = dict(stage=chosen, test_accuracy=round(float((pred == yte).mean()), 4), test_macro_f1=mf1(yte, pred), report=classification_report(yte, pred, target_names=bccd.CLASSES, output_dict=True),
                       confusion=confusion_matrix(yte, pred).tolist())
# deployment model: drop the augmentation layer (identity at inference) and export
inf_i = keras.Input((S, S, 3)); y = model.get_layer("preprocess")(inf_i); y = base(y, training=False)
for l in model.layers[-3:]: y = l(y)
inf = keras.Model(inf_i, y); inf.save("models/cells.keras")
c = tf.lite.TFLiteConverter.from_keras_model(inf); c.optimizations = [tf.lite.Optimize.DEFAULT]; open("models/cells.tflite", "wb").write(c.convert())
from ai_edge_litert.interpreter import Interpreter
it = Interpreter(model_path="models/cells.tflite"); it.allocate_tensors(); ii, oo = it.get_input_details()[0]["index"], it.get_output_details()[0]["index"]; tp = []
for x in Xte: it.set_tensor(ii, x[None].astype("float32")); it.invoke(); tp.append(it.get_tensor(oo)[0].argmax())
res["tflite"] = dict(size_kb=round(os.path.getsize("models/cells.tflite") / 1024), test_accuracy=round(float((np.array(tp) == yte).mean()), 4), agreement_with_keras=round(float((np.array(tp) == pred).mean()), 4))
json.dump(res, open("results/classifier.json", "w"), indent=1); print(json.dumps({k: v for k, v in res.items() if k != "deployed"}, indent=1), res["deployed"]["test_macro_f1"], res["deployed"]["confusion"])
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
cm = np.array(res["deployed"]["confusion"]); fig, ax = plt.subplots(figsize=(4.6, 4)); ax.imshow(cm / cm.sum(1, keepdims=True), cmap="Reds", vmin=0, vmax=1)
for a in range(3):
    for b in range(3): ax.text(b, a, cm[a, b], ha="center", va="center", color="white" if cm[a, b] / cm[a].sum() > .5 else "black")
ax.set_xticks(range(3), bccd.CLASSES); ax.set_yticks(range(3), bccd.CLASSES); ax.set_xlabel("predicted"); ax.set_ylabel("true")
ax.set_title(f"Test crops: macro-F1 {res['deployed']['test_macro_f1']:.3f}"); fig.tight_layout(); fig.savefig("results/classifier_confusion.png", dpi=130)
