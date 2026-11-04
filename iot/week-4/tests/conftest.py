import getpass
import os
import shutil
import socket
import subprocess
import sys
import time

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for d in ("security", "hub", "ml", "sim", "devices"):
    sys.path.insert(0, os.path.join(ROOT, d))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


@pytest.fixture(scope="session")
def certs(tmp_path_factory):
    out = tmp_path_factory.mktemp("certs")
    subprocess.run([os.path.join(ROOT, "security", "gen_certs.sh"), str(out)], check=True, capture_output=True)
    return out


@pytest.fixture(scope="session")
def tls_broker(certs, tmp_path_factory):
    """The real broker config, with absolute paths and a free port; runs as the current user so it can read the 0600 keys."""
    if shutil.which("mosquitto") is None:
        pytest.skip("mosquitto not installed")
    port = free_port()
    conf = open(os.path.join(ROOT, "security", "mosquitto_tls.conf")).read()
    conf = conf.replace("security/certs", str(certs)).replace("security/acl", os.path.join(ROOT, "security", "acl"))
    conf = conf.replace("listener 8883", f"listener {port} 127.0.0.1") + f"\nuser {getpass.getuser()}\n"
    path = tmp_path_factory.mktemp("broker") / "mosquitto.conf"
    path.write_text(conf)
    p = subprocess.Popen(["mosquitto", "-c", str(path)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(0.7)
    assert p.poll() is None, p.stdout.read().decode()
    yield {"port": port, "certs": certs}
    p.terminate()
