"""Whole system on 2 unseen days over the real TLS broker: hub decisions equal the offline evaluation,
overrides behave, attacks are rejected and a dead node is reported."""
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "hub"))


def test_whole_home_end_to_end(certs, tmp_path):
    import shutil
    if shutil.which("mosquitto") is None:
        pytest.skip("mosquitto not installed")
    import demo
    from conftest import free_port
    r = demo.main(days=2, port=free_port(), db=str(tmp_path / "hub.db"), certs=str(certs), write=False)
    living, bedroom = r["match"]
    assert bedroom > 0.97 and living > 0.97          # differences only inside override windows
    assert any("replay" in x[0] for x in r["rejects"])
    titles = [n["title"] for n in r["notes"]]
    assert "bedroom fan switched off" in titles      # voice override in an empty room was reverted
    assert "living node offline" in titles           # last-will after the power cut
    assert 4 < r["kwh_week"] < 10
