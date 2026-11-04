"""Offline voice control: a tiny keyword-spotting model (TinyML) for five commands, no cloud.

Training data is synthesised with espeak-ng in many voices, speeds and pitches, mixed with noise.
Test data uses *voices the model never heard* (held out by voice), so the score shows how it handles new
speakers, not memorisation. Recognised commands are published to MQTT to switch devices.

    python voice/kws.py train          -> voice/kws_int8.tflite, results/voice.md
    python voice/kws.py listen         (on the Pi: USB microphone -> MQTT home/<device>/set)
"""
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tinyml"))
from tflite_utils import TFLiteModel, to_int8_tflite

COMMANDS = ["light on", "light off", "fan on", "fan off", "status"]
LABELS = COMMANDS + ["_unknown"]
SR = 16000
CLIP = SR  # 1 s
# 8 distinct espeak-ng accents ("en" and "en-gb" are the same voice, and unknown names silently fall back to it,
# so every voice here was checked to produce different audio)
VOICES = ["en-gb", "en-us", "en-gb-scotland", "en-gb-x-rp", "en-029", "en-us-nyc", "en-gb-x-gbclan", "en-gb-x-gbcwmd"]
TEST_VOICES = {"en-gb-scotland", "en-029"}          # Scottish and Caribbean English: held out completely
DISTRACTORS = ["hello there", "open the door", "what time is it", "play music", "lights", "fan", "turn it up", "good morning"]
HERE = os.path.dirname(__file__)


def say(text, voice, speed, pitch):
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(["espeak-ng", "-v", voice, "-s", str(speed), "-p", str(pitch), "-w", f.name, text], check=True, capture_output=True)
        with wave.open(f.name) as w:
            sr, raw = w.getframerate(), w.readframes(w.getnframes())
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    if sr != SR:                                     # espeak-ng writes 22.05 kHz
        x = np.interp(np.arange(0, len(x) * SR / sr) * sr / SR, np.arange(len(x)), x)
    return x


def fit_clip(x, rng, shift=True):
    x = x[np.argmax(np.abs(x) > 0.02):] if np.any(np.abs(x) > 0.02) else x   # trim leading silence
    x = x[:CLIP]
    out = np.zeros(CLIP, np.float32)
    start = rng.integers(0, CLIP - len(x) + 1) if shift and len(x) < CLIP else 0
    out[start:start + len(x)] = x
    return out


def features(x):
    """40 log-mel bands x 49 frames (25 ms windows, 20 ms hop), like TensorFlow's micro_speech example."""
    from python_speech_features import logfbank
    f = logfbank(x, SR, winlen=0.025, winstep=0.02, nfilt=40, nfft=512)[:49]
    return ((f - f.mean()) / (f.std() + 1e-6)).astype(np.float32)[..., None]


def dataset(rng):
    X, y, groups = [], [], []
    for v in VOICES:
        for speed in (130, 160, 190):
            for pitch in (30, 50, 70):
                for i, text in enumerate(LABELS[:-1] + DISTRACTORS):
                    clip = fit_clip(say(text, v, speed, pitch), rng)
                    for noise in (0.0, 0.01, 0.03):  # quiet room, fan hum, busy kitchen
                        X.append(features(clip + rng.normal(0, noise, CLIP).astype(np.float32)))
                        y.append(min(i, len(LABELS) - 1))
                        groups.append(v)
    for _ in range(300):                             # pure background noise -> unknown
        X.append(features(rng.normal(0, rng.uniform(0.005, 0.05), CLIP).astype(np.float32)))
        y.append(len(LABELS) - 1)
        groups.append("noise")
    return np.array(X), np.array(y), np.array(groups)


def train():
    import tensorflow as tf
    tf.keras.utils.set_random_seed(0)
    rng = np.random.default_rng(0)
    X, y, g = dataset(rng)
    test = np.isin(g, list(TEST_VOICES))
    Xtr, ytr, Xte, yte = X[~test], y[~test], X[test], y[test]
    model = tf.keras.Sequential([
        tf.keras.layers.Input(X.shape[1:]),
        tf.keras.layers.Conv2D(8, (5, 3), strides=(2, 1), padding="same", activation="relu"),
        tf.keras.layers.MaxPool2D((2, 2)),
        tf.keras.layers.Conv2D(16, 3, padding="same", activation="relu"),
        tf.keras.layers.MaxPool2D((2, 2)),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dropout(0.4),
        tf.keras.layers.Dense(len(LABELS), activation="softmax"),
    ])
    model.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])
    model.fit(Xtr, ytr, epochs=40, batch_size=32, validation_split=0.15, verbose=0,
              callbacks=[tf.keras.callbacks.EarlyStopping(patience=6, restore_best_weights=True)])
    path = os.path.join(HERE, "kws_int8.tflite")
    size = to_int8_tflite(model, Xtr, path)
    lite = TFLiteModel(path)
    pred = np.array([lite.predict_proba(x).argmax() for x in Xte])
    acc = (pred == yte).mean()
    cmd = yte < len(COMMANDS)
    false_trigger = ((pred < len(COMMANDS)) & ~cmd).sum() / max(1, (~cmd).sum())
    per = [f"| {LABELS[k]} | {(pred[yte == k] == k).mean():.2f} |" for k in range(len(LABELS))]
    lines = [f"Train: {len(ytr)} clips from {len(VOICES) - len(TEST_VOICES)} voices. Test: {len(yte)} clips from **unseen voices** "
             f"({', '.join(sorted(TEST_VOICES))}).", "", f"Overall test accuracy **{acc:.3f}**; distractor phrases or noise wrongly taken as a "
             f"command: **{false_trigger:.1%}**. Model: {model.count_params():,} parameters, **{size / 1024:.1f} KB** int8, "
             f"{lite.latency_ms(Xte[0]) * 1000:.0f} µs per inference on this PC.", "", "| Command | Recall on unseen voices |", "|---|---:|"] + per
    os.makedirs("results", exist_ok=True)
    open("results/voice.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def listen():
    """Pi: 1-second sliding window from the microphone; act when the same command wins twice in a row."""
    import paho.mqtt.client as mqtt
    import sounddevice as sd
    lite = TFLiteModel(os.path.join(HERE, "kws_int8.tflite"))
    cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    cli.connect(os.environ.get("MQTT_HOST", "localhost"))
    cli.loop_start()
    buf, last = np.zeros(CLIP, np.float32), None
    with sd.InputStream(samplerate=SR, channels=1, blocksize=SR // 4) as stream:
        while True:
            block, _ = stream.read(SR // 4)
            buf = np.concatenate([buf[SR // 4:], block[:, 0]])
            p = lite.predict_proba(features(buf))
            k = int(p.argmax())
            if k < len(COMMANDS) and p[k] > 0.8:
                if k == last:
                    device, _, state = COMMANDS[k].partition(" ")
                    cli.publish(f"home/{device}/set" if state else "home/status/get", state or "?")
                    print("->", COMMANDS[k])
                    buf[:], last = 0, None
                    continue
                last = k
            else:
                last = None


if __name__ == "__main__":
    {"train": train, "listen": listen}[sys.argv[1] if len(sys.argv) > 1 else "train"]()
