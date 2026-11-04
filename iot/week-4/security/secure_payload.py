"""End-to-end payload protection on top of TLS: AES-256-GCM with a per-device key and a message counter.

Why both? TLS protects each hop (device <-> broker, broker <-> hub). The payload layer protects the data
*through* the broker: a compromised or cloud-hosted broker sees only ciphertext, can't alter a command
without detection, and can't replay an old "unlock"/"fan on" message.

Wire format (JSON):  {"dev": "esp32-living", "ctr": 1842, "iv": <12 B b64>, "ct": <ciphertext+16 B tag, b64>}
Associated data (authenticated, not encrypted): topic | dev | ctr, so a valid message can't be moved to
another topic or device. The receiver keeps the highest counter per device and rejects anything older.
The ESP32 does the same with mbedTLS (firmware/main/secure_payload.cc), so the formats are interoperable.
"""
import base64
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SecurityError(Exception):
    pass


def load_key(path):
    return bytes.fromhex(open(path).read().strip())


class Sealer:
    """Sender side. The counter must survive reboots (the ESP32 stores it in NVS every 100 messages and
    skips ahead 100 on boot, so a reboot never reuses a counter)."""

    def __init__(self, device, key, counter=0):
        self.dev, self.aes, self.ctr = device, AESGCM(key), counter

    def seal(self, topic, obj):
        self.ctr += 1
        iv = os.urandom(12)
        aad = f"{topic}|{self.dev}|{self.ctr}".encode()
        ct = self.aes.encrypt(iv, json.dumps(obj, separators=(",", ":")).encode(), aad)
        return json.dumps({"dev": self.dev, "ctr": self.ctr, "iv": base64.b64encode(iv).decode(),
                           "ct": base64.b64encode(ct).decode()})


class Opener:
    """Receiver side (the hub, or a device for commands): authenticates, decrypts, rejects replays."""

    def __init__(self, keys):
        self.keys = {d: AESGCM(k) for d, k in keys.items()}
        self.last = {}

    def open(self, topic, payload):
        try:
            m = json.loads(payload)
            dev, ctr = m["dev"], int(m["ctr"])
            iv, ct = base64.b64decode(m["iv"]), base64.b64decode(m["ct"])
        except (ValueError, KeyError, TypeError) as e:
            raise SecurityError(f"malformed message: {e}") from None
        if dev not in self.keys:
            raise SecurityError(f"unknown device {dev!r}")
        if ctr <= self.last.get(dev, 0):
            raise SecurityError(f"replay: counter {ctr} <= {self.last.get(dev, 0)}")
        try:
            pt = self.keys[dev].decrypt(iv, ct, f"{topic}|{dev}|{ctr}".encode())
        except Exception:
            raise SecurityError("authentication failed (tampered, wrong key, or wrong topic)") from None
        self.last[dev] = ctr
        return dev, json.loads(pt)
