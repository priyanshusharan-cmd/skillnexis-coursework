"""Task 3: optimise a trained model for deployment with TensorFlow Lite, and measure what each option costs and buys.
Model: the week-2 CIFAR-10 ResNet-style CNN (Keras, 91.94 % test accuracy), copied to models/cifar_cnn.keras.
Variants: Keras (reference) | TFLite float32 | TFLite float16 weights | dynamic-range int8 (int8 weights, float
activations) | full integer int8 (weights AND activations, calibrated on 500 training images; int8 in/out).
Measured on the same machine, one CPU thread: file size, accuracy on all 10,000 test images, agreement with the Keras
model's predictions, and single-image latency (median and p95 of 300 runs after 30 warm-up runs).
    python src/tflite_benchmark.py -> models/*.tflite, results/tflite.json, results/tflite.png"""
import json, os, sys, time
import numpy as np
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import tensorflow as tf, keras
tf.config.threading.set_intra_op_parallelism_threads(1); tf.config.threading.set_inter_op_parallelism_threads(1)   # fair 1-thread comparison
from ai_edge_litert.interpreter import Interpreter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "week-2", "src")); from cifar_data import load
os.makedirs("models", exist_ok=True); X, Y, XT, YT = load(); XT = XT.astype("float32")
SRC = "models/cifar_cnn.keras"
if not os.path.exists(SRC):
    import shutil; shutil.copy(os.path.join(os.path.dirname(__file__), "..", "..", "week-2", "results", "cifar_cnn.keras"), SRC)
model = keras.models.load_model(SRC, compile=False)
def convert(kind):
    c = tf.lite.TFLiteConverter.from_keras_model(model)
    if kind != "float32": c.optimizations = [tf.lite.Optimize.DEFAULT]
    if kind == "float16": c.target_spec.supported_types = [tf.float16]
    if kind == "int8_full":
        rng = np.random.default_rng(0); cal = X[rng.choice(len(X), 500, replace=False)].astype("float32")
        c.representative_dataset = lambda: ([cal[i:i + 1]] for i in range(len(cal)))
        c.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]; c.inference_input_type = tf.int8; c.inference_output_type = tf.int8
    b = c.convert(); p = f"models/cifar_{kind}.tflite"; open(p, "wb").write(b); return p
def tflite_runner(path):
    it = Interpreter(model_path=path, num_threads=1); it.allocate_tensors(); i, o = it.get_input_details()[0], it.get_output_details()[0]
    si, zi = i["quantization"]; so, zo = o["quantization"]
    def run(x):
        if i["dtype"] == np.int8: x = np.clip(np.round(x / si + zi), -128, 127).astype(np.int8)
        it.set_tensor(i["index"], x); it.invoke(); y = it.get_tensor(o["index"])
        return (y.astype("float32") - zo) * so if o["dtype"] == np.int8 else y
    return run
def keras_runner():
    f = tf.function(lambda x: model(x, training=False)); return lambda x: f(x).numpy()
def latency(run):
    x = XT[:1]
    for _ in range(30): run(x)
    ts = []
    for k in range(300): t = time.perf_counter(); run(XT[k:k + 1]); ts.append((time.perf_counter() - t) * 1000)
    return float(np.median(ts)), float(np.percentile(ts, 95))
ref = model.predict(XT, batch_size=500, verbose=0).argmax(1); res = {}
size_keras = os.path.getsize(SRC)
med, p95 = latency(keras_runner())
res["keras"] = dict(size_kb=round(size_keras / 1024), test_accuracy=round(float((ref == YT).mean()), 4), agreement_with_keras=1.0, latency_ms_median=round(med, 2), latency_ms_p95=round(p95, 2))
print("keras", res["keras"], flush=True)
for kind in ("float32", "float16", "int8_dynamic", "int8_full"):
    p = convert(kind); run = tflite_runner(p)
    pred = np.array([run(XT[k:k + 1])[0].argmax() for k in range(len(XT))])
    med, p95 = latency(run)
    res[kind] = dict(size_kb=round(os.path.getsize(p) / 1024), test_accuracy=round(float((pred == YT).mean()), 4), agreement_with_keras=round(float((pred == ref).mean()), 4),
                     latency_ms_median=round(med, 2), latency_ms_p95=round(p95, 2)); print(kind, res[kind], flush=True)
res["note"] = "The .keras file also stores the model config and the optimizer state saved during training (so it is larger than the weights alone); latency is single-image, 1 thread, this sandbox CPU (x86-64 with AVX-512/AMX)."
json.dump(res, open("results/tflite.json", "w"), indent=1)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
names = list(k for k in res if k != "note"); fig, ax = plt.subplots(1, 3, figsize=(14, 4))
for a, key, lab in zip(ax, ("size_kb", "latency_ms_median", "test_accuracy"), ("size (KB)", "latency per image (ms, median)", "test accuracy")):
    v = [res[n][key] * (100 if key == "test_accuracy" else 1) for n in names]; a.bar(names, v, color=["#868e96"] + ["#4c6ef5"] * 4)
    for k, val in enumerate(v): a.text(k, val, f"{val:.2f}" if key == "test_accuracy" else f"{val:.0f}" if key == "size_kb" else f"{val:.2f}", ha="center", va="bottom", fontsize=8)
    a.set_title(lab); a.tick_params(axis="x", rotation=30)
    if key == "test_accuracy": a.set_ylim(min(v) - 2, max(v) + .8)
fig.tight_layout(); fig.savefig("results/tflite.png", dpi=130)
