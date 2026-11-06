"""Mini project, model: tomato leaf disease classifier, 10 classes (9 diseases + healthy), PlantVillage.
MobileNetV2 (ImageNet weights, the official Keras release file) at 224x224, chosen because it is small (2.3 M
parameters, 9 MB) and fast enough for a CPU web app.
  stage A: frozen backbone, train the head on cached features (fast)
  stage B: unfreeze the top 40 layers and fine-tune with augmentation (flip, rotation, zoom, brightness) at a low LR;
  the stage with the better VALIDATION accuracy is deployed (the test set is only used for the final report)
Evaluation: held-out test split, confusion matrix, per-class precision/recall, and calibration of the confidence
score (the app shows it, so it should mean something).
    python src/train_plant.py -> plant-app/model/plant_mnv2.keras, results/plant.json, results/plant_confusion.png"""
import json, os, sys, time
import numpy as np
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import tensorflow as tf, keras
from keras import layers
sys.path.insert(0, os.path.dirname(__file__))
import plant_data as P
S = int(os.environ.get("PLANT_SIZE", 224)); W = os.environ.get("MNV2_WEIGHTS", "/tmp/claude-0/mobilenetv2_notop.h5"); tf.keras.utils.set_random_seed(0)
sp = P.split(); cls = sp["classes"]; names = [P.pretty(c) for c in cls]
(Xtr, ytr), (Xva, yva), (Xte, yte) = [P.arrays(sp[k], cls, S) for k in ("train", "val", "test")]
print({k: len(sp[k]) for k in ("train", "val", "test")}, flush=True)
base = keras.applications.MobileNetV2(include_top=False, weights=None, input_shape=(S, S, 3)); base.load_weights(W, skip_mismatch=False)
pre = keras.applications.mobilenet_v2.preprocess_input
aug = keras.Sequential([layers.RandomFlip("horizontal_and_vertical"), layers.RandomRotation(.08), layers.RandomZoom(.12), layers.RandomBrightness(.15, value_range=(0, 255))], name="augment")
i = keras.Input((S, S, 3)); x = aug(i); x = layers.Lambda(pre, name="preprocess")(x) if False else layers.Rescaling(1 / 127.5, offset=-1, name="preprocess")(x)
x = base(x, training=False); x = layers.GlobalAveragePooling2D()(x); x = layers.Dropout(.25)(x); out = layers.Dense(len(cls), activation="softmax")(x); model = keras.Model(i, out)
res = {}
# stage A on cached features (augmentation off for the cache)
fi = keras.Input((S, S, 3)); fe = keras.Model(fi, layers.GlobalAveragePooling2D()(base(layers.Rescaling(1 / 127.5, offset=-1)(fi), training=False))); t = time.time()
Ftr, Fva, Fte = [fe.predict(X, batch_size=64, verbose=0) for X in (Xtr, Xva, Xte)]
head = keras.Sequential([keras.Input(Ftr.shape[1:]), layers.Dropout(.25), layers.Dense(len(cls), activation="softmax")]); head.compile(keras.optimizers.Adam(1e-3), "sparse_categorical_crossentropy", metrics=["accuracy"])
head.fit(Ftr, ytr, validation_data=(Fva, yva), epochs=40, batch_size=64, verbose=0, callbacks=[keras.callbacks.EarlyStopping(patience=6, restore_best_weights=True)])
res["A_frozen"] = dict(test_accuracy=round(float(head.evaluate(Fte, yte, verbose=0)[1]), 4), minutes=round((time.time() - t) / 60, 1)); print(res, flush=True)
model.layers[-1].set_weights(head.layers[-1].get_weights()); wA = model.get_weights()
res["A_frozen"]["val_accuracy"] = round(float(head.evaluate(Fva, yva, verbose=0)[1]), 4)
# stage B: fine-tune the top of the backbone
base.trainable = True
for l in base.layers[:-40]: l.trainable = False
for l in base.layers:
    if isinstance(l, layers.BatchNormalization): l.trainable = False
model.compile(keras.optimizers.Adam(float(os.environ.get("FT_LR", 3e-5))), "sparse_categorical_crossentropy", metrics=["accuracy"]); t = time.time()
h = model.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=int(os.environ.get("FT_EPOCHS", 10)), batch_size=32, verbose=2, callbacks=[keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True)])
valB = float(model.evaluate(Xva, yva, verbose=0)[1]); testB = float(model.evaluate(Xte, yte, verbose=0)[1]); chosen = "B_finetuned"
if valB < res["A_frozen"]["val_accuracy"]:  # keep whichever stage validates better (decided on val, never on test)
    model.set_weights(wA); chosen = "A_frozen"
print("val A", res["A_frozen"]["val_accuracy"], "val B", round(valB, 4), "-> deploying", chosen, flush=True)
p = model.predict(Xte, batch_size=64, verbose=0); pred = p.argmax(1); conf = p.max(1)
from sklearn.metrics import classification_report, confusion_matrix
bins = np.linspace(0, 1, 11); ece = sum(abs((pred[(conf > a) & (conf <= b)] == yte[(conf > a) & (conf <= b)]).mean() - conf[(conf > a) & (conf <= b)].mean()) * ((conf > a) & (conf <= b)).mean()
          for a, b in zip(bins[:-1], bins[1:]) if ((conf > a) & (conf <= b)).any())
TH = .6
res["B_finetuned"] = dict(val_accuracy=round(valB, 4), test_accuracy=round(testB, 4), minutes=round((time.time() - t) / 60, 1), epochs=len(h.history["loss"]), history={k: [round(v, 4) for v in vs] for k, vs in h.history.items()})
res["deployed"] = dict(stage=chosen, test_accuracy=round(float((pred == yte).mean()), 4), expected_calibration_error=round(float(ece), 4),
                          threshold=TH, share_above_threshold=round(float((conf >= TH).mean()), 4), accuracy_above_threshold=round(float((pred == yte)[conf >= TH].mean()), 4))
res["classes"] = names; res["report"] = classification_report(yte, pred, target_names=names, output_dict=True); res["data"] = {k: len(sp[k]) for k in ("train", "val", "test")}
model.save("plant-app/model/plant_mnv2.keras"); json.dump(dict(classes=names, raw_classes=cls, image_size=S, threshold=TH), open("plant-app/model/labels.json", "w"), indent=1)
json.dump(res, open("results/plant.json", "w"), indent=1)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
cm = confusion_matrix(yte, pred); fig, ax = plt.subplots(figsize=(8, 7)); ax.imshow(cm, cmap="Greens")
for a in range(len(cls)):
    for b in range(len(cls)):
        if cm[a, b]: ax.text(b, a, cm[a, b], ha="center", va="center", fontsize=8, color="white" if cm[a, b] > cm.max() / 2 else "black")
ax.set_xticks(range(len(cls)), names, rotation=40, ha="right", fontsize=8); ax.set_yticks(range(len(cls)), names, fontsize=8); ax.set_title(f"MobileNetV2 tomato diseases ({chosen}) · test {res['deployed']['test_accuracy']:.1%}")
fig.tight_layout(); fig.savefig("results/plant_confusion.png", dpi=130); print(json.dumps({k: v for k, v in res.items() if k not in ("report",)}, indent=1)[:1500])
