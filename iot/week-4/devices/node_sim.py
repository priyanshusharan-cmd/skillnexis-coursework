"""Software twin of the ESP32 room node, for running the whole home without hardware.

It replays the simulated sensor data minute by minute, runs the same int8 model with the TFLite interpreter
(the firmware runs it with TFLite Micro; outputs were checked identical in QEMU), seals telemetry with the
device's AES key, sends it over TLS with the device's own certificate, and applies the hub's sealed commands
to its "relays". Time is simulated: each minute waits for the hub's command, so a day runs in seconds and the
energy bookkeeping is exact.
"""
import json
import os
import socket
import ssl
import sys
import threading
import time

import numpy as np
import paho.mqtt.client as mqtt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
for p in ("ml", "security", os.path.join("..", "week-3", "tinyml")):
    sys.path.insert(0, os.path.join(ROOT, p))
from secure_payload import Opener, Sealer, load_key  # noqa: E402


class NodeSim:
    def __init__(self, room, certs, port, host="127.0.0.1"):
        from tflite_utils import TFLiteModel
        self.room, self.dev = room, f"esp32-{room}"
        key = load_key(os.path.join(certs, f"{self.dev}.aeskey"))
        self.sealer, self.opener = Sealer(self.dev, key), Opener({"hub": key})
        self.model = TFLiteModel(os.path.join(ROOT, "ml", "occupancy_int8.tflite"))
        self.mean, self.std = np.load(os.path.join(ROOT, "ml", "norm.npy"))
        self.light = self.fan = 0
        self.cmd_event, self.last_cmd_minute, self.rejected = threading.Event(), None, 0
        self.c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.dev)
        self.c.tls_set(ca_certs=os.path.join(certs, "ca.crt"), certfile=os.path.join(certs, f"{self.dev}.crt"),
                       keyfile=os.path.join(certs, f"{self.dev}.key"), cert_reqs=ssl.CERT_REQUIRED)
        self.c.will_set(f"home/{room}/status", "offline", qos=1, retain=True)
        self.c.on_message = self.on_cmd
        self.c.connect(host, port, keepalive=5)
        self.c.socket().setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.c.subscribe(f"home/{room}/cmd", qos=1)
        self.c.loop_start()
        self.c.publish(f"home/{room}/status", "online", qos=1, retain=True)

    def on_cmd(self, client, userdata, msg):
        try:
            _, cmd = self.opener.open(msg.topic, msg.payload)
        except Exception:
            self.rejected += 1
            return
        self.light, self.fan, self.last_cmd_minute = cmd["light"], cmd["fan"], cmd["minute"]
        self.cmd_event.set()

    def run(self, rows, feats, minute0=0, hook=None):
        """rows: this room's sensor rows (DataFrame); feats: their raw features. Returns per-minute records."""
        out, rtt = [], []
        for i, (r, f) in enumerate(zip(rows.itertuples(), feats)):
            p = float(self.model.predict_proba((f - self.mean) / self.std)[0])
            minute = minute0 + i
            if hook:
                hook(minute)
            msg = {"occ": round(p, 4), "motion": int(r.motion), "sound_db": float(r.sound_db), "temp_c": float(r.temp_c),
                   "lux": float(r.daylight_lux), "light": self.light, "fan": self.fan, "minute": minute,
                   "ts": r.timestamp.timestamp()}
            self.cmd_event.clear()
            t0 = time.perf_counter()
            self.c.publish(f"home/{self.room}/telemetry", self.sealer.seal(f"home/{self.room}/telemetry", msg), qos=1)
            if self.cmd_event.wait(2) and self.last_cmd_minute == minute:
                rtt.append((time.perf_counter() - t0) * 1000)
            out.append((p, self.light, self.fan))      # relay state after the hub's decision for this minute
        return np.array(out), np.array(rtt)

    def die(self):
        """Simulate a power cut: drop the TCP connection without DISCONNECT, so the broker sends the last-will."""
        self.c.loop_stop()
        self.c.socket().close()


if __name__ == "__main__":
    print(json.dumps({"usage": "used by tests/test_e2e.py and hub/demo.py"}))
