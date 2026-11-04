"""Week 3 checks. MQTT tests start a private mosquitto broker if one is installed (skipped otherwise)."""
import os
import shutil
import socket
import subprocess
import sys
import threading
import time

import cv2
import numpy as np
import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
for d in ("face", "tinyml", "voice", "mqtt", "doorbell"):
    sys.path.insert(0, os.path.join(ROOT, d))

from detect import detect, sample_images
from tflite_utils import TFLiteModel


def test_faces_found_in_both_portraits():
    for name, img in sample_images().items():
        assert len(detect(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))) == 1, name


def test_digit_model_is_small_and_accurate():
    from sklearn.datasets import load_digits
    path = os.path.join(ROOT, "tinyml", "digits_int8.tflite")
    assert os.path.getsize(path) < 32 * 1024
    m = TFLiteModel(path)
    d = load_digits()
    X = (d.images[-200:] / 16.0).astype(np.float32)[..., None]
    acc = np.mean([m.predict_proba(x).argmax() == y for x, y in zip(X, d.target[-200:])])
    assert acc > 0.95


def test_pi_digit_preprocessing_reads_a_drawn_digit():
    from classify_pi import preprocess
    img = np.full((200, 200, 3), 255, np.uint8)
    cv2.line(img, (100, 30), (100, 170), (0, 0, 0), 14)       # a "1"
    p = TFLiteModel(os.path.join(ROOT, "tinyml", "digits_int8.tflite")).predict_proba(preprocess(img))
    assert p.argmax() == 1


@pytest.mark.skipif(shutil.which("espeak-ng") is None, reason="espeak-ng not installed")
def test_keyword_spotter_hears_an_unseen_voice():
    import kws
    m = TFLiteModel(os.path.join(ROOT, "voice", "kws_int8.tflite"))
    rng = np.random.default_rng(1)
    clip = kws.fit_clip(kws.say("fan off", "en-029", 160, 50), rng, shift=False)
    assert kws.LABELS[m.predict_proba(kws.features(clip)).argmax()] == "fan off"


def test_doorbell_decision_rule_prefers_unknown_when_unsure():
    from recognise import decide
    labels = ["alice", "bob", "unknown"]
    assert decide(np.array([0.9, 0.05, 0.05]), labels) == ("alice", pytest.approx(0.9))
    assert decide(np.array([0.6, 0.3, 0.1]), labels)[0] == "unknown"


def test_doorbell_recognises_resident_and_respects_cooldown(tmp_path):
    from doorbell import Doorbell, paste, scene_background, visitor_views
    bell = Doorbell(db=str(tmp_path / "v.db"))
    rng = np.random.default_rng(3)
    img = sample_images()["astronaut"]
    box = max(detect(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)), key=lambda b: b[2])
    frames = lambda: [paste(scene_background(rng), v, rng) for v in visitor_views(img, box, rng)]
    first, second = bell.visit(frames(), now=1000), bell.visit(frames(), now=1010)
    assert first["who"] == second["who"] == "astronaut"
    assert first["notified"] and not second["notified"]
    assert bell.visit([scene_background(rng)] * 3, now=2000)["who"] is None


@pytest.fixture
def broker():
    if shutil.which("mosquitto") is None:
        pytest.skip("mosquitto not installed")
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    p = subprocess.Popen(["mosquitto", "-p", str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)
    yield port
    p.terminate()


def test_mqtt_alert_pipeline_end_to_end(broker, tmp_path):
    import sqlite3

    import pipeline
    db = str(tmp_path / "alerts.db")
    a = pipeline.Alerter("127.0.0.1", broker, db=db, stale_s=2)
    t = threading.Thread(target=a.run, args=(10,))
    t.start()
    time.sleep(0.5)
    csv = os.path.join(ROOT, "..", "week-2", "data", "env_15min.csv")
    pipeline.publish("127.0.0.1", broker, csv=csv, speed=45000, limit=200, glitch_at=60, drop_for=4)
    t.join()
    kinds = {(k, s) for k, s in sqlite3.connect(db).execute("SELECT kind, state FROM alerts")}
    assert {("temp_c_high", "raised"), ("temp_c_high", "cleared"), ("temp_rate", "event"),
            ("stale", "raised"), ("stale", "cleared"), ("offline", "raised")} <= kinds
