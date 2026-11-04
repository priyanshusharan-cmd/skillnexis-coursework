"""Smart doorbell: camera frame -> face detection -> who is it (int8 TinyML) -> MQTT notification + log.

On a visit (bell button or motion) the Pi grabs a short burst of frames. Each face is classified, and
the burst's average decides, so one bad frame (blink, motion blur) doesn't decide alone. Then:
  * MQTT  doorbell/<door>/visit   {"who", "confidence", "faces", "ts", "snapshot"(JPEG, base64)}
  * SQLite doorbell.db  visits(ts, who, confidence, latency_ms, snapshot)   -> dashboard.py
  * repeat visits by the same person within COOLDOWN_S are logged but not re-notified (no phone spam)
The doorbell never unlocks anything: it tells you who is there.

    python doorbell/doorbell.py --camera        (Pi Camera / USB webcam; bell = GPIO17 or Enter key)
    python doorbell/doorbell.py --evaluate      end-to-end test on 90 composed visitor scenes
"""
import argparse
import base64
import json
import os
import sqlite3
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from recognise import (
    UNKNOWN,
    crop,
    decide,
    detect,
    sample_images,
    stranger_split,
)
from tflite_utils import TFLiteModel

COOLDOWN_S = 60


class Doorbell:
    def __init__(self, db=os.path.join(HERE, "doorbell.db"), mqtt_host=None, mqtt_port=1883, door="front"):
        self.model = TFLiteModel(os.path.join(HERE, "faces_int8.tflite"))
        self.labels = open(os.path.join(HERE, "labels.txt")).read().split()
        self.db = sqlite3.connect(db, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS visits (ts REAL, who TEXT, confidence REAL, faces INT, latency_ms REAL, notified INT, snapshot BLOB)")
        self.topic, self.last_notified, self.mqtt = f"doorbell/{door}/visit", {}, None
        if mqtt_host:
            import paho.mqtt.client as mqtt
            self.mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"doorbell-{door}")
            self.mqtt.connect(mqtt_host, mqtt_port)
            self.mqtt.loop_start()

    def identify(self, frames):
        """Burst of BGR frames -> (who, confidence, n_faces, snapshot frame)."""
        probs, best, n = [], frames[0], 0
        for f in frames:
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            boxes = detect(g, min_size=48)
            if not boxes:
                continue
            n = max(n, len(boxes))
            box = max(boxes, key=lambda b: b[2])           # the person closest to the camera
            probs.append(self.model.predict_proba(crop(g, box)[..., None]))
            best = f.copy()
            x, y, w, h = box
            cv2.rectangle(best, (x, y), (x + w, y + h), (0, 200, 0), 2)
        if not probs:
            return None, 0.0, 0, best
        who, conf = decide(np.mean(probs, axis=0), self.labels)
        return who, conf, n, best

    def visit(self, frames, now=None):
        now = time.time() if now is None else now
        t = time.perf_counter()
        who, conf, n, snap = self.identify(frames)
        ms = (time.perf_counter() - t) * 1000
        if who is None:
            return {"who": None, "notified": False, "latency_ms": ms}   # bell pressed, nobody in view
        notify = now - self.last_notified.get(who, -1e9) > COOLDOWN_S
        jpg = cv2.imencode(".jpg", cv2.resize(snap, (320, int(320 * snap.shape[0] / snap.shape[1]))), [cv2.IMWRITE_JPEG_QUALITY, 70])[1].tobytes()
        self.db.execute("INSERT INTO visits VALUES (?,?,?,?,?,?,?)", (now, who, conf, n, ms, int(notify), jpg))
        self.db.commit()
        if notify:
            self.last_notified[who] = now
            if self.mqtt:
                msg = {"who": who, "confidence": round(conf, 3), "faces": n, "ts": now, "snapshot": base64.b64encode(jpg).decode()}
                self.mqtt.publish(self.topic, json.dumps(msg), qos=1).wait_for_publish(2)
        return {"who": who, "confidence": conf, "faces": n, "notified": notify, "latency_ms": ms}


# ---------- end-to-end evaluation on composed scenes ----------

def scene_background(rng, w=480, h=360):
    from skimage import data
    wall = cv2.resize(data.brick(), (w, h)).astype(np.float32)
    shade = np.linspace(rng.uniform(0.5, 0.9), rng.uniform(0.9, 1.2), w)[None, :]       # porch light from one side
    bg = np.clip(wall * shade * rng.uniform(0.7, 1.1), 0, 255).astype(np.uint8)
    return cv2.cvtColor(bg, cv2.COLOR_GRAY2BGR)


def paste(bg, face_bgr, rng):
    h, w = bg.shape[:2]
    s = int(rng.uniform(140, 200))
    face = cv2.resize(face_bgr, (s, int(s * face_bgr.shape[0] / face_bgr.shape[1])))
    fh, fw = face.shape[:2]
    y, x = int(rng.uniform(0, h - fh)), int(rng.uniform(0, w - fw))
    out = bg.copy()
    out[y:y + fh, x:x + fw] = face
    return out


def visitor_views(img, box, rng, n=3):
    """n slightly different frames of a resident: head tilt, lighting and sensor noise change between frames."""
    x, y, w, h = box
    m = int(0.6 * w)
    region = img[max(0, y - m):y + h + m, max(0, x - m):x + w + m]
    tilt, gamma = rng.uniform(-12, 12), rng.uniform(0.65, 1.5)
    views = []
    for _ in range(n):
        M = cv2.getRotationMatrix2D((region.shape[1] / 2, region.shape[0] / 2), tilt + rng.uniform(-3, 3), 1)
        r = cv2.warpAffine(region, M, region.shape[1::-1], borderMode=cv2.BORDER_REFLECT)
        r = np.clip(255 * (r / 255.0) ** gamma + rng.normal(0, 6, r.shape), 0, 255).astype(np.uint8)
        views.append(r)
    return views


def stranger_views(patch, rng, n=3):
    big = cv2.resize((patch * 255).astype(np.uint8), (150, 150), interpolation=cv2.INTER_CUBIC)
    big = cv2.copyMakeBorder(big, 40, 40, 40, 40, cv2.BORDER_REPLICATE)
    out = []
    for _ in range(n):
        v = np.clip(big.astype(np.float32) + rng.normal(0, 6, big.shape), 0, 255).astype(np.uint8)
        out.append(cv2.cvtColor(v, cv2.COLOR_GRAY2BGR))
    return out


def evaluate(mqtt_host=None, mqtt_port=1883):
    from skimage import data
    rng = np.random.default_rng(42)
    db = os.path.join(HERE, "eval.db")
    if os.path.exists(db):
        os.remove(db)
    bell = Doorbell(db=db, mqtt_host=mqtt_host, mqtt_port=mqtt_port)
    received = []
    if mqtt_host:                                      # a phone-app stand-in that subscribes to notifications
        import paho.mqtt.client as mqtt
        phone = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="phone")
        phone.on_message = lambda c, u, m: received.append(json.loads(m.payload))
        phone.connect(mqtt_host, mqtt_port)
        phone.subscribe("doorbell/+/visit", qos=1)
        phone.loop_start()
        time.sleep(0.5)
    people = {}
    for name, img in sample_images().items():
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        people[name] = (img, max(detect(g), key=lambda b: b[2]))
    lfw = data.lfw_subset()[:100]
    _, test_ids = stranger_split()
    cases = [(name, "resident") for name in people for _ in range(20)]
    cases += [(int(i), "stranger") for i in test_ids] + [(None, "empty") for _ in range(20)]
    results, now = [], 0.0
    for who, kind in cases:
        now += COOLDOWN_S + 1                          # visits far enough apart that each one notifies
        bg = scene_background(rng)
        if kind == "resident":
            frames = [paste(bg, v, rng) for v in visitor_views(*people[who], rng)]
        elif kind == "stranger":
            frames = [paste(bg, v, rng) for v in stranger_views(lfw[who], rng)]
        else:
            frames = [np.clip(bg + rng.normal(0, 4, bg.shape), 0, 255).astype(np.uint8) for _ in range(3)]
        r = bell.visit(frames, now=now)
        truth = who if kind == "resident" else (UNKNOWN if kind == "stranger" else None)
        results.append((kind, truth, r["who"], r["latency_ms"]))
    # cooldown check: the same resident rings twice within a minute -> logged twice, notified once
    name = next(iter(people))
    a = bell.visit([paste(scene_background(rng), v, rng) for v in visitor_views(*people[name], rng)], now=now + 500)
    b = bell.visit([paste(scene_background(rng), v, rng) for v in visitor_views(*people[name], rng)], now=now + 520)
    time.sleep(1.5)

    def rate(kind, ok):
        sel = [r for r in results if r[0] == kind]
        return sum(ok(r) for r in sel), len(sel)
    res = rate("resident", lambda r: r[2] == r[1])
    res_wrong = rate("resident", lambda r: r[2] not in (r[1], UNKNOWN, None))
    res_missed_face = rate("resident", lambda r: r[2] is None)
    st_ok = rate("stranger", lambda r: r[2] == UNKNOWN)
    st_in = rate("stranger", lambda r: r[2] not in (UNKNOWN, None))
    st_noface = rate("stranger", lambda r: r[2] is None)
    empty_ok = rate("empty", lambda r: r[2] is None)
    lat = np.array([r[3] for r in results])
    sent = sum(1 for r in results if r[2] is not None) + int(a["notified"]) + int(b["notified"])
    lines = [f"End-to-end: {len(results)} composed doorbell visits (3-frame bursts on a brick-wall porch with uneven light), "
             "run through detection -> int8 classifier -> SQLite -> MQTT.", "",
             "| Visit type | Visits | Correct outcome | Notes |", "|---|---:|---:|---|",
             f"| Resident (2 people × 20) | {res[1]} | {res[0]} named correctly | {res_wrong[0]} named as the other resident, "
             f"{res[1] - res[0] - res_wrong[0] - res_missed_face[0]} called unknown, {res_missed_face[0]} face not found |",
             f"| Stranger (30 unseen LFW faces) | {st_ok[1]} | {st_ok[0]} flagged \"unknown visitor\" | **{st_in[0]} taken for a resident**, "
             f"{st_noface[0]} face not found |",
             f"| Bell pressed, nobody there | {empty_ok[1]} | {empty_ok[0]} no false face | |", "",
             f"Processing per visit (3 frames, detection + classification): median **{np.median(lat):.0f} ms**, "
             f"max {lat.max():.0f} ms on this PC (expect roughly 4-6x on a Raspberry Pi 4).",
             f"Cooldown: same resident rang twice 20 s apart -> notified {int(a['notified'])} + {int(b['notified'])} times, logged twice."]
    if mqtt_host:
        lines.append(f"MQTT: the subscribing \"phone\" received **{len(received)} of {sent}** expected notifications, each with a JPEG snapshot "
                     f"(~{np.mean([len(m['snapshot']) for m in received]) * 3 / 4 / 1024:.0f} KB)." if received else "MQTT: no messages received!")
        if received:
            open(os.path.join("results", "doorbell_snapshot.jpg"), "wb").write(base64.b64decode(received[0]["snapshot"]))
    os.makedirs("results", exist_ok=True)
    open("results/doorbell_e2e.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return results, received


def camera_loop(mqtt_host):
    try:
        from picamera2 import Picamera2
        cam = Picamera2()
        cam.configure(cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
        cam.start()
        grab = lambda: cv2.cvtColor(cam.capture_array(), cv2.COLOR_RGB2BGR)
    except ImportError:
        cap = cv2.VideoCapture(0)
        grab = lambda: cap.read()[1]
    try:
        from gpiozero import Button
        bell_button = Button(17)
        wait = bell_button.wait_for_press
    except Exception:
        wait = lambda: input("press Enter to ring the bell ")
    bell = Doorbell(mqtt_host=mqtt_host)
    while True:
        wait()
        frames = []
        for _ in range(3):
            frames.append(grab())
            time.sleep(0.15)
        print(bell.visit(frames))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", action="store_true")
    ap.add_argument("--evaluate", action="store_true")
    ap.add_argument("--mqtt", default=os.environ.get("MQTT_HOST"))
    ap.add_argument("--port", type=int, default=1883)
    a = ap.parse_args()
    evaluate(a.mqtt, a.port) if a.evaluate or not a.camera else camera_loop(a.mqtt)
