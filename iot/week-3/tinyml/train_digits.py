"""TinyML image classification: a small CNN for handwritten digits (scikit-learn's bundled 8x8 digits),
quantised to an int8 TFLite model and run with the TFLite interpreter, exactly as on a Raspberry Pi.

    python tinyml/train_digits.py     -> tinyml/digits_int8.tflite, results/tinyml_digits.md
    python tinyml/classify_pi.py img.png   (on the Pi: classifies a photo of a handwritten digit)
"""
import os
import sys

import numpy as np
import tensorflow as tf
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(__file__))
from tflite_utils import TFLiteModel, to_int8_tflite

tf.keras.utils.set_random_seed(0)
d = load_digits()
X = (d.images / 16.0).astype(np.float32)[..., None]          # 1797 x 8 x 8 x 1, scaled 0..1
Xtr, Xte, ytr, yte = train_test_split(X, d.target, test_size=0.25, stratify=d.target, random_state=0)

model = tf.keras.Sequential([
    tf.keras.layers.Input((8, 8, 1)),
    tf.keras.layers.Conv2D(16, 3, padding="same", activation="relu"),
    tf.keras.layers.Conv2D(32, 3, padding="same", activation="relu"),
    tf.keras.layers.MaxPool2D(),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(10, activation="softmax"),
])
model.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])
model.fit(Xtr, ytr, epochs=40, batch_size=32, validation_split=0.1, verbose=0,
          callbacks=[tf.keras.callbacks.EarlyStopping(patience=6, restore_best_weights=True)])
float_acc = model.evaluate(Xte, yte, verbose=0)[1]

path = os.path.join(os.path.dirname(__file__), "digits_int8.tflite")
size = to_int8_tflite(model, Xtr, path)
lite = TFLiteModel(path)
pred = np.array([lite.predict_proba(x).argmax() for x in Xte])
int8_acc = (pred == yte).mean()
cm = tf.math.confusion_matrix(yte, pred).numpy()
worst = max(((i, j, cm[i, j]) for i in range(10) for j in range(10) if i != j), key=lambda t: t[2])

lines = ["| Model | Test accuracy | Size |", "|---|---:|---:|",
         f"| Keras float32 | {float_acc:.3f} | {model.count_params() * 4 / 1024:.1f} KB of weights |",
         f"| **TFLite int8** | **{int8_acc:.3f}** | **{size / 1024:.1f} KB** file |", "",
         f"Parameters: {model.count_params():,}. int8 inference: {lite.latency_ms(Xte[0]) * 1000:.0f} µs per image on this PC (single thread). "
         f"Most common confusion: {worst[0]} read as {worst[1]} ({worst[2]} times). Test set: {len(yte)} images, never seen in training."]
os.makedirs("results", exist_ok=True)
open("results/tinyml_digits.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
