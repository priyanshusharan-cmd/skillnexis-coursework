"""Who is at the door? A tiny int8 face classifier: each enrolled resident, or "unknown".

Every face, whether training, test or live, goes through the same path: Haar box -> grey crop -> 25x25.
Using LFW's 25x25 size for everyone means the model can't tell residents from strangers by image
sharpness; it has to use the face.

Enrolment: put a few photos per person in doorbell/known/<name>/*.jpg. Without that folder the demo
enrols the two portraits bundled with matplotlib/scikit-image (Grace Hopper and the astronaut Eileen Collins).
Strangers are 100 faces from Labeled Faces in the Wild (scikit-image `lfw_subset`), split by image.

    python doorbell/recognise.py   -> doorbell/faces_int8.tflite, doorbell/labels.txt, results/doorbell_model.md
"""
import glob
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "face"))
sys.path.insert(0, os.path.join(HERE, "..", "tinyml"))
from detect import detect, sample_images
from tflite_utils import TFLiteModel, to_int8_tflite

SIZE = 25
UNKNOWN = "unknown"
THRESHOLD = 0.75          # below this a "known" prediction is treated as unknown: better to ask than to open up


def crop(gray, box, size=SIZE):
    """LFW-style tight crop of a Haar box, resized to size x size, scaled 0..1."""
    x, y, w, h = box
    m = int(0.1 * w)
    c = gray[y + m:y + h - m // 2, x + m:x + w - m]
    return cv2.resize(c, (size, size), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0


def jitter(gray, box, rng, strong=False):
    """A plausible new doorbell view of an enrolled face: shift, scale, tilt, lighting, blur, noise."""
    x, y, w, h = box
    s = rng.uniform(0.88, 1.12)
    dx, dy = rng.uniform(-0.08, 0.08, 2) * w
    ang = rng.uniform(-15, 15) if strong else rng.uniform(-10, 10)
    cx, cy = x + w / 2 + dx, y + h / 2 + dy
    M = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)
    rot = cv2.warpAffine(gray, M, gray.shape[::-1], borderMode=cv2.BORDER_REFLECT)
    pad = w // 2                                   # so a shifted/scaled box never leaves the image
    rot = cv2.copyMakeBorder(rot, pad, pad, pad, pad, cv2.BORDER_REFLECT)
    nw = int(w * s)
    f = crop(rot, (int(cx - nw / 2) + pad, int(cy - nw / 2) + pad, nw, nw))
    if rng.random() < 0.5:
        f = f[:, ::-1]
    gamma = rng.uniform(0.6, 1.6) if strong else rng.uniform(0.75, 1.35)
    f = np.clip(f, 0, 1) ** gamma * rng.uniform(0.8, 1.15)
    if strong and rng.random() < 0.5:
        f = cv2.GaussianBlur(f, (3, 3), 0)
    return np.clip(f + rng.normal(0, 0.02 if not strong else 0.04, f.shape), 0, 1).astype(np.float32)


def stranger_frame(p):
    """An LFW 25x25 face as the doorbell camera would see it: enlarged and in a frame, then detected like any
    live face. Returns (gray image, Haar box) so strangers go through exactly the same crop path as residents."""
    big = cv2.resize((p * 255).astype(np.uint8), (150, 150), interpolation=cv2.INTER_CUBIC)
    big = cv2.copyMakeBorder(big, 40, 40, 40, 40, cv2.BORDER_REPLICATE)
    boxes = detect(big, min_size=48)
    return big, (max(boxes, key=lambda b: b[2]) if boxes else (40 - 19, 40 - 19, 188, 188))


def jitter_patch(p, rng, strong=False):
    return jitter(*stranger_frame(p), rng, strong=strong)


def enrolled_people():
    """name -> list of (gray image, face box)."""
    people = {}
    for d in sorted(glob.glob(os.path.join(HERE, "known", "*"))):
        shots = []
        for f in glob.glob(os.path.join(d, "*")):
            g = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
            boxes = detect(g) if g is not None else []
            if boxes:
                shots.append((g, max(boxes, key=lambda b: b[2])))
        if shots:
            people[os.path.basename(d)] = shots
    if not people:
        for name, img in sample_images().items():
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            people[name] = [(g, max(detect(g), key=lambda b: b[2]))]
    return people


def stranger_split(rng=None):
    """LFW faces 0..99 -> (train ids, test ids). Same split everywhere (training, doorbell scenes, tests)."""
    order = (rng or np.random.default_rng(0)).permutation(100)
    return order[:70], order[70:]


def build(seed=0, per_person=500):
    from skimage import data
    rng = np.random.default_rng(seed)
    people = enrolled_people()
    labels = sorted(people) + [UNKNOWN]
    lfw = data.lfw_subset()[:100]
    tr_idx, te_idx = stranger_split(rng)
    Xtr, ytr, Xte, yte = [], [], [], []
    for k, name in enumerate(labels[:-1]):
        for i in range(per_person):
            g, b = people[name][i % len(people[name])]
            Xtr.append(jitter(g, b, rng, strong=i % 3 == 0)); ytr.append(k)
        for i in range(60):                         # test views: different seed, harsher lighting and blur
            g, b = people[name][i % len(people[name])]
            Xte.append(jitter(g, b, rng, strong=True)); yte.append(k)
    u = len(labels) - 1
    for i in range(per_person * len(people)):     # balance strangers against residents
        Xtr.append(jitter_patch(lfw[tr_idx[i % 70]], rng, strong=i % 3 == 0)); ytr.append(u)
    for i in te_idx:                               # 30 strangers the model never saw, plus 1 jittered view each
        g, b = stranger_frame(lfw[i])
        Xte.append(crop(g, b)); yte.append(u)
        Xte.append(jitter_patch(lfw[i], rng, strong=True)); yte.append(u)
    f = lambda X: np.array(X, np.float32)[..., None]
    return f(Xtr), np.array(ytr), f(Xte), np.array(yte), labels


def decide(proba, labels):
    k = int(np.argmax(proba))
    if labels[k] != UNKNOWN and proba[k] < THRESHOLD:
        return UNKNOWN, float(proba[k])
    return labels[k], float(proba[k])


def train():
    import tensorflow as tf
    tf.keras.utils.set_random_seed(0)
    Xtr, ytr, Xte, yte, labels = build()
    model = tf.keras.Sequential([
        tf.keras.layers.Input((SIZE, SIZE, 1)),
        tf.keras.layers.Conv2D(12, 3, activation="relu"),
        tf.keras.layers.MaxPool2D(),
        tf.keras.layers.Conv2D(24, 3, activation="relu"),
        tf.keras.layers.MaxPool2D(),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dropout(0.4),
        tf.keras.layers.Dense(len(labels), activation="softmax"),
    ])
    model.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])
    model.fit(Xtr, ytr, epochs=50, batch_size=32, validation_split=0.15, verbose=0,
              callbacks=[tf.keras.callbacks.EarlyStopping(patience=8, restore_best_weights=True)])
    path = os.path.join(HERE, "faces_int8.tflite")
    size = to_int8_tflite(model, Xtr, path)
    open(os.path.join(HERE, "labels.txt"), "w").write("\n".join(labels) + "\n")
    lite = TFLiteModel(path)
    pred = np.array([labels.index(decide(lite.predict_proba(x), labels)[0]) for x in Xte])
    u = len(labels) - 1
    stranger_let_in = ((yte == u) & (pred != u)).sum() / (yte == u).sum()
    resident_missed = ((yte != u) & (pred != yte)).sum() / (yte != u).sum()
    rows = [f"| {labels[k]} | {(yte == k).sum()} | {(pred[yte == k] == k).mean():.2f} |" for k in range(len(labels))]
    lines = [f"Classes: {', '.join(labels)}. Input 25x25 grey, {model.count_params():,} parameters, **{size / 1024:.1f} KB** int8, "
             f"{lite.latency_ms(Xte[0]) * 1000:.0f} µs per face on this PC.", "",
             "| True class | Test faces | Recognised correctly |", "|---|---:|---:|"] + rows + ["",
             f"**Strangers recognised as a resident: {stranger_let_in:.1%}** (the number that matters for a door). "
             f"Residents not recognised: {resident_missed:.1%} (they just get an \"unknown visitor\" notification). "
             f"Decision rule: a resident is only accepted at ≥ {THRESHOLD:.0%} confidence."]
    os.makedirs("results", exist_ok=True)
    open("results/doorbell_model.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    train()
