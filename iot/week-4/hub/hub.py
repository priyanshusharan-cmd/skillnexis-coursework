"""Smart-home hub (Raspberry Pi): the brain between the ESP32 room nodes, the phone and the voice assistant.

  home/<room>/telemetry  sealed (AES-GCM) from the node: on-device occupancy probability + sensor values
  home/<room>/cmd        sealed command back to the node: {"light": 0/1, "fan": 0/1}
  home/<room>/request    from the phone app or the week-3 voice keyword spotter: {"light"|"fan": "on"/"off"/"auto"}
  home/<room>/state      what the room is doing now, for the phone and dashboard (plain JSON, TLS + ACL)
  home/<room>/status     node online/offline (MQTT last-will)
  notify/phone           notifications; also pushed to a phone via ntfy (free, no account) if NTFY_TOPIC is set

Overrides from voice/phone last 60 min; an override that keeps a device on in an empty room is reverted after
30 min with a notification. Every message and decision is logged to SQLite (hub.db) for the dashboard.

    python hub/hub.py --certs security/certs --port 8883
"""
import argparse
import json
import os
import sqlite3
import socket
import ssl
import sys
import threading
import time
import urllib.request

import paho.mqtt.client as mqtt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "security"))
from policy import FAN_W, LIGHT_W, MLController  # noqa: E402
from secure_payload import Opener, Sealer, SecurityError, load_key  # noqa: E402

ROOMS = {"living": "esp32-living", "bedroom": "esp32-bedroom"}
OVERRIDE_MIN, EMPTY_REVERT_MIN, HEAT_C = 60, 30, 32.5


class Hub:
    def __init__(self, certs, host="127.0.0.1", port=8883, db=os.path.join(HERE, "hub.db"), ntfy_topic=None):
        keys = {dev: load_key(os.path.join(certs, f"{dev}.aeskey")) for dev in ROOMS.values()}
        self.opener = Opener(keys)
        self.sealers = {room: Sealer("hub", keys[dev]) for room, dev in ROOMS.items()}
        self.ctl = {room: MLController(room == "bedroom") for room in ROOMS}
        self.override = {room: {} for room in ROOMS}          # device -> (state, until_minute)
        self.empty_for = {room: 0 for room in ROOMS}
        self.house_empty_since, self.heat_alerted = None, set()
        self.ntfy_topic = ntfy_topic
        self.lock = threading.Lock()
        self.db = sqlite3.connect(db, check_same_thread=False)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS telemetry (ts REAL, room TEXT, occ REAL, motion INT, sound_db REAL, temp_c REAL, lux REAL, light INT, fan INT, watts REAL);
            CREATE TABLE IF NOT EXISTS events (ts REAL, room TEXT, kind TEXT, detail TEXT);
            CREATE TABLE IF NOT EXISTS notifications (ts REAL, level TEXT, title TEXT, body TEXT);""")
        self.c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="hub")
        self.c.tls_set(ca_certs=os.path.join(certs, "ca.crt"), certfile=os.path.join(certs, "hub.crt"),
                       keyfile=os.path.join(certs, "hub.key"), cert_reqs=ssl.CERT_REQUIRED)
        self.c.on_connect = lambda c, u, f, rc, p: c.subscribe([("home/+/telemetry", 1), ("home/+/request", 1), ("home/+/status", 1)])
        self.c.on_message = self.on_message
        self.c.connect(host, port)
        self.c.socket().setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.latency_ms = []

    # ---------- outputs ----------
    def notify(self, level, title, body, ts):
        self.db.execute("INSERT INTO notifications VALUES (?,?,?,?)", (ts, level, title, body))
        self.c.publish("notify/phone", json.dumps({"level": level, "title": title, "body": body, "ts": ts}), qos=1)
        if self.ntfy_topic:                                    # e.g. https://ntfy.sh/<secret-topic>, free
            try:
                req = urllib.request.Request(f"https://ntfy.sh/{self.ntfy_topic}", data=body.encode(),
                                             headers={"Title": title, "Priority": "high" if level == "alert" else "default"})
                urllib.request.urlopen(req, timeout=3)
            except OSError:
                pass

    def event(self, ts, room, kind, detail=""):
        self.db.execute("INSERT INTO events VALUES (?,?,?,?)", (ts, room, kind, detail))

    # ---------- inputs ----------
    def on_message(self, client, userdata, msg):
        room, kind = msg.topic.split("/")[1:3]
        if room not in ROOMS:
            return
        with self.lock:
            if kind == "status":
                if msg.payload == b"offline":
                    self.notify("alert", f"{room} node offline", f"The {room} sensor node stopped responding. Lights and fan "
                                "there now run on the node's own model (edge fallback).", time.time())
                self.event(time.time(), room, f"node_{msg.payload.decode()}")
            elif kind == "request":
                self.on_request(room, msg.payload)
            elif kind == "telemetry":
                try:
                    dev, d = self.opener.open(msg.topic, msg.payload)
                except SecurityError as e:
                    self.event(time.time(), room, "security_reject", str(e))
                    self.notify("alert", "Security: message rejected", f"A message on {msg.topic} failed verification ({e}).", time.time())
                    return
                if dev != ROOMS[room]:
                    self.event(time.time(), room, "security_reject", f"{dev} wrote to {room}")
                    return
                self.on_telemetry(room, d, msg.topic)
            self.db.commit()

    def on_request(self, room, payload):
        try:
            r = json.loads(payload)
        except ValueError:
            return
        minute = r.get("minute", 0)
        for dev in ("light", "fan"):
            if r.get(dev) in ("on", "off"):
                self.override[room][dev] = (r[dev] == "on", minute + OVERRIDE_MIN)
            elif r.get(dev) == "auto":
                self.override[room].pop(dev, None)
        self.event(r.get("ts", time.time()), room, "request", json.dumps(r))

    def on_telemetry(self, room, d, topic):
        t0 = time.perf_counter()
        ts, minute = d.get("ts", time.time()), d.get("minute", 0)
        hour = (minute % 1440) / 60
        light, fan = self.ctl[room].step(d["occ"], d["motion"], d["lux"], d["temp_c"], hour)
        auto = {"light": light, "fan": fan}
        occupied = self.ctl[room].occ
        self.empty_for[room] = 0 if occupied else self.empty_for[room] + 1
        for dev, (state, until) in list(self.override[room].items()):
            if minute >= until:
                del self.override[room][dev]
            elif state and self.empty_for[room] >= EMPTY_REVERT_MIN:
                del self.override[room][dev]
                self.notify("info", f"{room} {dev} switched off", f"The {dev} in the {room} was left on by request but the room "
                            f"has been empty for {EMPTY_REVERT_MIN} min, so it is back on automatic.", ts)
            else:
                auto[dev] = state
        cmd = {"light": int(auto["light"]), "fan": int(auto["fan"]), "minute": minute}
        self.c.publish(f"home/{room}/cmd", self.sealers[room].seal(f"home/{room}/cmd", cmd), qos=1)
        watts = d.get("light", 0) * LIGHT_W + d.get("fan", 0) * FAN_W
        self.db.execute("INSERT INTO telemetry VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (ts, room, d["occ"], d["motion"], d.get("sound_db"), d["temp_c"], d["lux"], d.get("light", 0), d.get("fan", 0), watts))
        self.c.publish(f"home/{room}/state", json.dumps({"occupied": occupied, **cmd, "temp_c": d["temp_c"], "ts": ts}), qos=0, retain=True)
        if d["temp_c"] > HEAT_C and occupied and room not in self.heat_alerted:      # someone is in a hot room
            self.heat_alerted.add(room)
            self.notify("alert", f"Heat in the {room}", f"Indoor temperature {d['temp_c']:.1f} °C with someone in the room; "
                        "the fan is on. Consider closing the curtains or switching on the AC.", ts)
        elif d["temp_c"] < HEAT_C - 2:
            self.heat_alerted.discard(room)
        house_empty = all(not c.occ for c in self.ctl.values())
        if house_empty and self.house_empty_since is None:
            self.house_empty_since = ts
        elif not house_empty and self.house_empty_since is not None:
            if ts - self.house_empty_since > 2 * 3600:
                self.notify("info", "Welcome home", f"Arrival detected in the {room}; the house was empty for "
                            f"{(ts - self.house_empty_since) / 3600:.1f} h with everything off.", ts)
            self.house_empty_since = None
        self.latency_ms.append((time.perf_counter() - t0) * 1000)

    def loop_forever(self):
        self.c.loop_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--certs", default=os.path.join(HERE, "..", "security", "certs"))
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8883)
    a = ap.parse_args()
    Hub(a.certs, a.host, a.port, ntfy_topic=os.environ.get("NTFY_TOPIC")).loop_forever()
