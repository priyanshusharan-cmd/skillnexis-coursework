"""Security checks against the real broker configuration: TLS + client certificates + ACL + payload crypto."""
import json
import os
import socket
import ssl
import threading
import time

import paho.mqtt.client as mqtt
import pytest
from secure_payload import Opener, Sealer, SecurityError


def client(broker, who, cert=True, verify=True):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{who}-{time.time_ns()}")
    d = broker["certs"]
    c.tls_set(ca_certs=str(d / "ca.crt") if verify else None,
              certfile=str(d / f"{who}.crt") if cert else None, keyfile=str(d / f"{who}.key") if cert else None,
              cert_reqs=ssl.CERT_REQUIRED if verify else ssl.CERT_NONE)
    if not verify:
        c.tls_insecure_set(True)
    return c


def connects(c, port):
    ok = threading.Event()
    c.on_connect = lambda cl, u, f, rc, p: ok.set() if rc == 0 else None
    try:
        c.connect("127.0.0.1", port, keepalive=5)
    except (ssl.SSLError, OSError):
        return False
    c.loop_start()
    r = ok.wait(2)
    c.loop_stop()
    c.disconnect()
    return r


def test_device_with_certificate_connects(tls_broker):
    assert connects(client(tls_broker, "esp32-living"), tls_broker["port"])


def test_client_without_certificate_is_refused(tls_broker):
    assert not connects(client(tls_broker, "phone", cert=False), tls_broker["port"])


def test_plaintext_mqtt_is_refused(tls_broker):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    assert not connects(c, tls_broker["port"])


def test_certificate_from_another_ca_is_refused(tls_broker, tmp_path):
    import subprocess
    other = tmp_path / "rogue"
    subprocess.run([os.path.join(os.path.dirname(__file__), "..", "security", "gen_certs.sh"), str(other)], check=True, capture_output=True)
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.tls_set(ca_certs=str(tls_broker["certs"] / "ca.crt"), certfile=str(other / "esp32-living.crt"), keyfile=str(other / "esp32-living.key"))
    assert not connects(c, tls_broker["port"])


def test_acl_stops_a_device_from_writing_another_rooms_topics(tls_broker):
    got = []
    hub = client(tls_broker, "hub")
    hub.on_message = lambda c, u, m: got.append(m.topic)
    hub.connect("127.0.0.1", tls_broker["port"])
    hub.subscribe("home/#", qos=1)
    hub.loop_start()
    dev = client(tls_broker, "esp32-living")
    dev.connect("127.0.0.1", tls_broker["port"])
    dev.loop_start()
    time.sleep(0.4)
    dev.publish("home/living/telemetry", "own room", qos=1).wait_for_publish(2)
    dev.publish("home/bedroom/telemetry", "spoofed", qos=1).wait_for_publish(2)    # not allowed
    dev.publish("home/bedroom/cmd", "fan on", qos=1).wait_for_publish(2)            # not allowed
    time.sleep(0.6)
    for c in (dev, hub):
        c.loop_stop()
        c.disconnect()
    assert got == ["home/living/telemetry"]


def test_tls_traffic_is_not_readable_on_the_wire(tls_broker):
    """Raw TLS handshake check: the broker only speaks TLS 1.2+ and presents our CA-signed certificate."""
    ctx = ssl.create_default_context(cafile=str(tls_broker["certs"] / "ca.crt"))
    ctx.load_cert_chain(str(tls_broker["certs"] / "phone.crt"), str(tls_broker["certs"] / "phone.key"))
    with socket.create_connection(("127.0.0.1", tls_broker["port"])) as s, ctx.wrap_socket(s, server_hostname="localhost") as t:
        assert t.version() in ("TLSv1.2", "TLSv1.3")
        assert dict(x[0] for x in t.getpeercert()["subject"])["commonName"] == "localhost"


KEY = bytes(range(32))


def test_payload_round_trip_and_ciphertext_hides_values():
    s, o = Sealer("esp32-living", KEY), Opener({"esp32-living": KEY})
    msg = s.seal("home/living/telemetry", {"temp_c": 29.5, "occupancy": 0.93})
    assert "29.5" not in msg and "occupancy" not in msg
    assert o.open("home/living/telemetry", msg) == ("esp32-living", {"temp_c": 29.5, "occupancy": 0.93})


def test_tampered_payload_is_rejected():
    s, o = Sealer("esp32-living", KEY), Opener({"esp32-living": KEY})
    m = json.loads(s.seal("home/living/telemetry", {"fan": "off"}))
    ct = bytearray(__import__("base64").b64decode(m["ct"]))
    ct[0] ^= 1
    m["ct"] = __import__("base64").b64encode(bytes(ct)).decode()
    with pytest.raises(SecurityError, match="authentication"):
        o.open("home/living/telemetry", json.dumps(m))


def test_replayed_message_is_rejected():
    s, o = Sealer("esp32-living", KEY), Opener({"esp32-living": KEY})
    m = s.seal("home/living/cmd", {"fan": "on"})
    o.open("home/living/cmd", m)
    with pytest.raises(SecurityError, match="replay"):
        o.open("home/living/cmd", m)


def test_message_moved_to_another_topic_is_rejected():
    s, o = Sealer("esp32-living", KEY), Opener({"esp32-living": KEY})
    with pytest.raises(SecurityError):
        o.open("home/bedroom/cmd", s.seal("home/living/cmd", {"fan": "on"}))


def test_wrong_key_and_unknown_device_are_rejected():
    m = Sealer("esp32-living", os.urandom(32)).seal("t", {"x": 1})
    with pytest.raises(SecurityError):
        Opener({"esp32-living": KEY}).open("t", m)
    with pytest.raises(SecurityError, match="unknown"):
        Opener({"esp32-bedroom": KEY}).open("t", m)
