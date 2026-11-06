"""Baseline for task 2: the same 5-class tomato images through a small CNN trained from scratch (no pretraining),
128x128, flips + rotation, Adam 3e-4, up to 40 epochs with early stopping on validation accuracy. Updates
results/transfer.json -> baseline_scratch_cnn."""
import json, os, sys, time
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import numpy as np, tensorflow as tf, keras
from keras import layers
sys.path.insert(0, os.path.dirname(__file__)); import plant_data as P
tf.keras.utils.set_random_seed(0); s = P.split(P.FIVE); cls = P.FIVE
(X, y), (Xv, yv), (Xt, yt) = [P.arrays(s[k], cls, 128) for k in ("train", "val", "test")]
i = keras.Input((128, 128, 3)); x = layers.RandomFlip("horizontal_and_vertical")(i); x = layers.RandomRotation(.1)(x); x = layers.Rescaling(1 / 255.)(x)
for f in (32, 64, 128, 128):
    x = layers.Conv2D(f, 3, padding="same", use_bias=False)(x); x = layers.BatchNormalization()(x); x = layers.ReLU()(x); x = layers.MaxPooling2D()(x)
x = layers.GlobalAveragePooling2D()(x); x = layers.Dropout(.3)(x); m = keras.Model(i, layers.Dense(5, activation="softmax")(x))
m.compile(keras.optimizers.Adam(3e-4), "sparse_categorical_crossentropy", metrics=["accuracy"]); t = time.time()
h = m.fit(X, y, validation_data=(Xv, yv), epochs=40, batch_size=32, verbose=2, callbacks=[keras.callbacks.EarlyStopping("val_accuracy", patience=8, restore_best_weights=True)])
r = json.load(open("results/transfer.json"))
r["baseline_scratch_cnn"] = dict(test_accuracy=round(float(m.evaluate(Xt, yt, verbose=0)[1]), 4), best_val=round(max(h.history["val_accuracy"]), 4), epochs=len(h.history["loss"]), seconds=round(time.time() - t), params=m.count_params())
json.dump(r, open("results/transfer.json", "w"), indent=1); print(r["baseline_scratch_cnn"])
