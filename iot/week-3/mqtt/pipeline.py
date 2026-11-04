"""Real-time MQTT data pipeline with alerting.

  publisher  replays week 2's cleaned sensor data (fast-forwarded) to sensors/<device>/telemetry, sends a
             heartbeat, and registers a last-will so the broker announces it if the device drops off.
  alerter    subscribes to sensors/#, applies rules and publishes to alerts/<device>; every alert is also
             stored in SQLite (alerts.db) for the dashboard.

Rules: threshold with hysteresis (no alert storms around the limit), rate of change (temperature jumping
> 2 °C in 5 readings), and a stale-data watchdog (no telemetry for N seconds, or the broker's last-will).

    python mqtt/pipeline.py alerter &      python mqtt/pipeline.py publish --speed 600
"""
import argparse
import json
import sqlite3
import time
from collections import defaultdict, deque

import paho.mqtt.client as mqtt

RULES = {"temp_c": {"high": 31.0, "clear": 30.0}, "humidity_pct": {"low": 52.0, "clear": 55.0}}
RATE_LIMIT, RATE_WINDOW, STALE_S = 2.0, 5, 10


class Alerter:
    def __init__(self, host, port, db="alerts.db", stale_s=STALE_S):
        self.db = sqlite3.connect(db, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS alerts (ts REAL, device TEXT, kind TEXT, state TEXT, value REAL, message TEXT)")
        self.active = defaultdict(set)
        self.recent = defaultdict(lambda: deque(maxlen=RATE_WINDOW))
        self.last_seen = {}
        self.stale_s = stale_s
        self.c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="alerter")
        self.c.on_message = self.on_message
        self.c.connect(host, port)
        self.c.subscribe([("sensors/+/telemetry", 1), ("sensors/+/status", 1)])

    def emit(self, device, kind, state, value, message):
        self.db.execute("INSERT INTO alerts VALUES (?,?,?,?,?,?)", (time.time(), device, kind, state, value, message))
        self.db.commit()
        self.c.publish(f"alerts/{device}", json.dumps({"kind": kind, "state": state, "value": value, "message": message}), qos=1)
        print(f"[alert] {device} {kind} {state}: {message}", flush=True)

    def on_message(self, client, userdata, msg):
        device, kind = msg.topic.split("/")[1:3]
        if kind == "status":
            if msg.payload == b"offline" and "offline" not in self.active[device]:
                self.active[device].add("offline")
                self.emit(device, "offline", "raised", 0, "device offline (status topic or broker last-will)")
            elif msg.payload == b"online" and "offline" in self.active[device]:
                self.active[device].discard("offline")
                self.emit(device, "offline", "cleared", 0, "device back online")
            return
        d = json.loads(msg.payload)
        self.last_seen[device] = time.time()
        if "stale" in self.active[device]:
            self.active[device].discard("stale")
            self.emit(device, "stale", "cleared", 0, "telemetry resumed")
        for field, r in RULES.items():
            v = d.get(field)
            if v is None:
                continue
            key = f"{field}_{'high' if 'high' in r else 'low'}"
            breach = v > r["high"] if "high" in r else v < r["low"]
            clear = v < r["clear"] if "high" in r else v > r["clear"]
            if breach and key not in self.active[device]:
                self.active[device].add(key)
                self.emit(device, key, "raised", v, f"{field} = {v} (limit {r.get('high', r.get('low'))}) at {d['ts']}")
            elif clear and key in self.active[device]:
                self.active[device].discard(key)
                self.emit(device, key, "cleared", v, f"{field} back to {v} at {d['ts']}")
        t = d.get("temp_c")
        if t is not None:
            q = self.recent[device]
            q.append(t)
            if len(q) == RATE_WINDOW and abs(q[-1] - q[0]) > RATE_LIMIT:
                self.emit(device, "temp_rate", "event", t, f"temperature changed {q[-1] - q[0]:+.1f} °C in {RATE_WINDOW} readings at {d['ts']}")
                q.clear()

    def check_stale(self):
        for device, seen in list(self.last_seen.items()):
            if time.time() - seen > self.stale_s and not self.active[device] & {"stale", "offline"}:
                self.active[device].add("stale")
                self.emit(device, "stale", "raised", 0, f"no telemetry for {self.stale_s} s")

    def run(self, seconds=None):
        self.c.loop_start()
        end = time.time() + seconds if seconds else None
        while end is None or time.time() < end:
            self.check_stale()
            time.sleep(0.5)
        self.c.loop_stop()


def publish(host, port, csv="../week-2/data/env_15min.csv", device="esp32-garden-01", speed=600.0, limit=None, glitch_at=None, drop_for=0):
    import pandas as pd
    rows = pd.read_csv(csv, parse_dates=["timestamp"])
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=device)
    c.will_set(f"sensors/{device}/status", "offline", qos=1, retain=True)
    c.connect(host, port, keepalive=5)
    c.loop_start()
    c.publish(f"sensors/{device}/status", "online", qos=1, retain=True)
    for i, r in enumerate(rows.itertuples()):
        if limit and i >= limit:
            break
        if drop_for and i == limit // 2:            # simulate a WiFi drop: go quiet
            time.sleep(drop_for)
        temp = r.temp_c_mean + (6.0 if glitch_at is not None and i == glitch_at else 0)
        if temp != temp:                             # NaN: no reading in that window
            continue
        c.publish(f"sensors/{device}/telemetry", json.dumps({"ts": str(r.timestamp), "temp_c": round(temp, 2),
                                                            "humidity_pct": round(r.humidity_pct_mean, 1)}), qos=1)
        time.sleep(15 * 60 / speed)                  # 15-minute windows, fast-forwarded
    c.publish(f"sensors/{device}/status", "offline", qos=1, retain=True)
    c.loop_stop()
    c.disconnect()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["alerter", "publish"])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--speed", type=float, default=600)
    a = ap.parse_args()
    Alerter(a.host, a.port).run() if a.mode == "alerter" else publish(a.host, a.port, speed=a.speed)
