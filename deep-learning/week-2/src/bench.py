import time, sys, numpy as np, tensorflow as tf, keras
sys.path.insert(0, "src"); from cifar_data import load
from cifar_cnn import build
x, y, xt, yt = load(); m = build(int(sys.argv[1]) if len(sys.argv) > 1 else 64); m.compile("adam", "sparse_categorical_crossentropy"); print(m.count_params())
t = time.time(); m.fit(x[:5120].astype("float32") / 255, y[:5120], batch_size=128, epochs=1, verbose=0); print("s per 5120:", round(time.time() - t, 1))
