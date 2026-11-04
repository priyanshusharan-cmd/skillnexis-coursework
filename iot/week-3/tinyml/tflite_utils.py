"""Shared helpers: full-integer (int8) TFLite conversion, evaluation and latency measurement.
On the Raspberry Pi only `ai-edge-litert` (the TFLite runtime, a few MB) is needed, not TensorFlow."""
import time

import numpy as np

try:
    from ai_edge_litert.interpreter import Interpreter
except ImportError:  # older Pi images
    from tflite_runtime.interpreter import Interpreter


def to_int8_tflite(model, rep_x, path):
    import tensorflow as tf
    conv = tf.lite.TFLiteConverter.from_keras_model(model)
    conv.optimizations = [tf.lite.Optimize.DEFAULT]
    conv.representative_dataset = lambda: ([x[None].astype(np.float32)] for x in rep_x[:300])
    conv.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    conv.inference_input_type = tf.int8
    conv.inference_output_type = tf.int8
    blob = conv.convert()
    open(path, "wb").write(blob)
    return len(blob)


class TFLiteModel:
    def __init__(self, path):
        self.it = Interpreter(model_path=str(path), num_threads=1)
        self.it.allocate_tensors()
        self.inp = self.it.get_input_details()[0]
        self.out = self.it.get_output_details()[0]

    def predict_proba(self, x):
        """x: one float sample. Quantises the input, runs the model, de-quantises the output."""
        s, z = self.inp["quantization"]
        q = np.clip(np.round(x / s + z), -128, 127).astype(np.int8)[None]
        self.it.set_tensor(self.inp["index"], q)
        self.it.invoke()
        o = self.it.get_tensor(self.out["index"])[0].astype(np.float32)
        s, z = self.out["quantization"]
        return (o - z) * s

    def latency_ms(self, x, n=200):
        self.predict_proba(x)
        t = time.perf_counter()
        for _ in range(n):
            self.predict_proba(x)
        return (time.perf_counter() - t) / n * 1000
