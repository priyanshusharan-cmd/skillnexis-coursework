"""The firmware's portable C++ (feature extraction, AES-GCM sealing) compiled for the PC and checked against
the Python reference: same features to float precision, and messages that each side can open."""
import json
import os
import shutil
import subprocess

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KEY = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"


@pytest.fixture(scope="module")
def host_bin(tmp_path_factory):
    if shutil.which("g++") is None or not os.path.exists("/usr/include/mbedtls/gcm.h"):
        pytest.skip("needs g++ and libmbedtls-dev")
    out = tmp_path_factory.mktemp("fw") / "host_main"
    subprocess.run(["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-o", str(out),
                    os.path.join(ROOT, "firmware", "host_test", "host_main.cc"),
                    os.path.join(ROOT, "firmware", "main", "secure_payload.cc"), "-lmbedcrypto"], check=True)
    return str(out)


@pytest.mark.parametrize("room", ["living", "bedroom"])
def test_cpp_features_match_python(host_bin, room):
    from occupancy import FEATURES, make_features
    df = pd.read_csv(os.path.join(ROOT, "data", "home_1min.csv"), parse_dates=["timestamp"])
    df = df[(df.room == room) & (df.timestamp < df.timestamp.min() + pd.Timedelta(days=2))]
    ref = make_features(df)[FEATURES].to_numpy()
    minute = df.timestamp.dt.hour * 60 + df.timestamp.dt.minute
    rows = "\n".join(f"{m} {s} {t} {mi} {int(w)} {int(room == 'bedroom')}" for m, s, t, mi, w in
                     zip(df.motion, df.sound_db, df.temp_c, minute, df.timestamp.dt.dayofweek >= 5))
    out = subprocess.run([host_bin, "features"], input=rows, capture_output=True, text=True, check=True).stdout
    got = np.loadtxt(out.splitlines())
    assert got.shape == ref.shape
    np.testing.assert_allclose(got, ref, atol=2e-3)


def test_c_sealed_message_opens_in_python(host_bin):
    from secure_payload import Opener
    msg = subprocess.run([host_bin, "seal", KEY, "esp32-living", "home/living/telemetry", '{"occ":0.91,"temp_c":29.4}'],
                         capture_output=True, text=True, check=True).stdout.strip()
    dev, obj = Opener({"esp32-living": bytes.fromhex(KEY)}).open("home/living/telemetry", msg)
    assert dev == "esp32-living" and obj == {"occ": 0.91, "temp_c": 29.4} and json.loads(msg)["ctr"] == 42


def test_python_command_opens_on_device_and_replay_is_refused(host_bin):
    from secure_payload import Sealer
    s = Sealer("hub", bytes.fromhex(KEY), counter=99)
    msg = s.seal("home/living/cmd", {"light": 1, "fan": 0})
    ok = subprocess.run([host_bin, "open", KEY, "esp32-living", "home/living/cmd", msg, "0"], capture_output=True, text=True)
    assert ok.returncode == 0 and json.loads(ok.stdout) == {"light": 1, "fan": 0}
    replay = subprocess.run([host_bin, "open", KEY, "esp32-living", "home/living/cmd", msg, "100"], capture_output=True, text=True)
    assert replay.returncode == 1 and "REJECTED" in replay.stdout
    moved = subprocess.run([host_bin, "open", KEY, "esp32-living", "home/bedroom/cmd", msg, "0"], capture_output=True, text=True)
    assert moved.returncode == 1
