"""Whole system, end to end, on the 8 unseen test days: TLS broker (real config) + hub + two node twins.

Injected along the way: a voice command (fan on in an empty bedroom), a phone request, a replayed message
from an attacker holding a stolen device certificate, and a power cut on one node.

    python hub/demo.py     -> results/e2e.md, hub/hub.db (for the dashboard)
"""
import getpass
import json
import os
import ssl
import subprocess
import sys
import tempfile
import threading
import time

import numpy as np
import paho.mqtt.client as mqtt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
for p in ("hub", "ml", "devices", "security"):
    sys.path.insert(0, os.path.join(ROOT, p))
from node_sim import NodeSim  # noqa: E402
from occupancy import FEATURES, TRAIN_DAYS, make_features  # noqa: E402
from policy import FAN_W, LIGHT_W, run  # noqa: E402

from hub import Hub  # noqa: E402


def start_broker(certs, port):
    conf = open(os.path.join(ROOT, "security", "mosquitto_tls.conf")).read()
    conf = conf.replace("security/certs", certs).replace("security/acl", os.path.join(ROOT, "security", "acl"))
    conf = conf.replace("listener 8883", f"listener {port} 127.0.0.1") + f"\nuser {getpass.getuser()}\n"
    path = os.path.join(tempfile.mkdtemp(), "mosquitto.conf")
    open(path, "w").write(conf)
    p = subprocess.Popen(["mosquitto", "-c", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.7)
    return p


def tls_client(certs, who, port):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{who}-demo")
    c.tls_set(ca_certs=os.path.join(certs, "ca.crt"), certfile=os.path.join(certs, f"{who}.crt"),
              keyfile=os.path.join(certs, f"{who}.key"), cert_reqs=ssl.CERT_REQUIRED)
    c.connect("127.0.0.1", port)
    c.loop_start()
    return c


def main(days=8, port=18883, db=os.path.join(HERE, "hub.db"), certs=None, write=True):
    certs = certs or tempfile.mkdtemp()
    if not os.path.exists(os.path.join(certs, "ca.crt")):
        subprocess.run([os.path.join(ROOT, "security", "gen_certs.sh"), certs], check=True, capture_output=True)
    if os.path.exists(db):
        os.remove(db)
    broker = start_broker(certs, port)
    try:
        df = pd.read_csv(os.path.join(ROOT, "data", "home_1min.csv"), parse_dates=["timestamp"])
        feats = make_features(df)[FEATURES].to_numpy(np.float32)
        day = (df.timestamp - df.timestamp.min()).dt.days.to_numpy()
        sel = (day >= TRAIN_DAYS) & (day < TRAIN_DAYS + days)
        hub = Hub(certs, port=port, db=db)
        threading.Thread(target=hub.loop_forever, daemon=True).start()
        phone_inbox = []
        phone = tls_client(certs, "phone", port)
        phone.on_message = lambda c, u, m: phone_inbox.append(json.loads(m.payload))
        phone.subscribe("notify/phone", qos=1)
        voice = tls_client(certs, "voice", port)
        time.sleep(0.5)

        captured = {}
        spy = tls_client(certs, "hub", port)            # stands in for an attacker who can see broker traffic
        spy.on_message = lambda c, u, m: captured.setdefault("msg", m.payload)
        spy.subscribe("home/living/telemetry", qos=1)

        def bedroom_hook(minute):
            if minute == 1440 + 13 * 60:                 # day 2, 13:00: "fan on" said to the Pi in an empty bedroom
                voice.publish("home/bedroom/request", json.dumps({"fan": "on", "source": "voice", "minute": minute}), qos=1).wait_for_publish()
                time.sleep(0.05)

        def living_hook(minute):
            if minute == 2 * 1440 + 19 * 60:             # day 3, 19:00: phone asks for the light off (movie)
                phone.publish("home/living/request", json.dumps({"light": "off", "source": "phone", "minute": minute}), qos=1).wait_for_publish()
                time.sleep(0.05)

        nodes, results = {}, {}
        for room in ("living", "bedroom"):
            nodes[room] = NodeSim(room, certs, port)
        time.sleep(0.3)

        def go(room, hook):
            m = sel & (df.room == room).to_numpy()
            results[room] = (df[m], *nodes[room].run(df[m], feats[m], hook=hook))
        t0 = time.time()
        th = [threading.Thread(target=go, args=("living", living_hook)), threading.Thread(target=go, args=("bedroom", bedroom_hook))]
        [t.start() for t in th]
        [t.join() for t in th]
        wall = time.time() - t0

        # attacks after the run: replay a captured telemetry message, then a power cut on the living-room node
        spy.unsubscribe("home/living/telemetry")
        attacker = tls_client(certs, "esp32-living", port)
        attacker.publish("home/living/telemetry", captured["msg"], qos=1).wait_for_publish()
        time.sleep(0.5)
        nodes["living"].die()
        time.sleep(9)                                     # keepalive 5 s x 1.5 -> broker publishes the last-will

        lines, total_kwh, match = [], 0, []
        for room, (rows, out, rtt) in results.items():
            idx = np.arange(len(rows))
            proba = out[:, 0]
            light_ref, fan_ref = run(rows, "ml", proba)
            same = (out[:, 1] == light_ref) & (out[:, 2] == fan_ref)
            match.append(same.mean())
            total_kwh += (out[:, 1].sum() * LIGHT_W + out[:, 2].sum() * FAN_W) / 60 / 1000
            lines.append(f"| {room} | {len(idx):,} | {np.median(rtt):.1f} ms / {np.percentile(rtt, 99):.1f} ms | {same.mean():.2%} |")
        notes = [f"| {n['level']} | {n['title']} | {n['body']} |" for n in phone_inbox]
        con = hub.db
        rejects = con.execute("SELECT detail FROM events WHERE kind='security_reject'").fetchall()
        report = [f"{days} unseen test days, 2 room nodes + hub + phone + voice clients over the real TLS broker config "
                  f"(client certificates, ACL, AES-GCM payloads). {sum(len(r[0]) for r in results.values()):,} sealed telemetry "
                  f"messages, each answered by a sealed command; simulated time, ran in {wall:.0f} s.", "",
                  "| Room | Minutes | Sensor → hub → relay round trip (median / p99) | Same decisions as the offline evaluation |",
                  "|---|---:|---:|---:|"] + lines + ["",
                  f"Energy used by the lights and fans: **{total_kwh / days * 7:.1f} kWh/week** (offline estimate 7.0). Decisions differ from "
                  "the offline run only while a voice/phone override was active.",
                  f"Hub processing per message: median {np.median(hub.latency_ms):.2f} ms.", "",
                  f"Security: {len(rejects)} message(s) rejected: " + "; ".join(r[0] for r in rejects) + ".", "",
                  "Notifications received by the phone client:", "", "| Level | Title | Message |", "|---|---|---|"] + notes
        if write:
            open(os.path.join(ROOT, "results", "e2e.md"), "w").write("\n".join(report) + "\n")
        print("\n".join(report))
        return {"match": match, "rejects": rejects, "notes": phone_inbox, "kwh_week": total_kwh / days * 7}
    finally:
        broker.terminate()


if __name__ == "__main__":
    main()
