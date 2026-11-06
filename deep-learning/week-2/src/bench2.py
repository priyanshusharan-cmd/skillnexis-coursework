import time, sys, os, numpy as np
os.environ["TF_CPP_MIN_LOG_LEVEL"]="3"
import tensorflow as tf, keras
if sys.argv[2] == "bf16": keras.mixed_precision.set_global_policy("mixed_bfloat16")
sys.path.insert(0, "src"); from cifar_data import load
from cifar_cnn import build
x, y, xt, yt = load(); m = build(int(sys.argv[1])); m.compile("adam", keras.losses.SparseCategoricalCrossentropy(from_logits=True), jit_compile=(sys.argv[2]=="xla"))
m.fit(x[:1024], y[:1024], batch_size=128, epochs=1, verbose=0)
t = time.time(); m.fit(x[:5120], y[:5120], batch_size=128, epochs=1, verbose=0); print(sys.argv[1:], "s per 5120:", round(time.time() - t, 1))
