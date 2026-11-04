"""Tests for the week 2 pipeline and dashboard.   python -m pytest tests"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "maintenance"))
import preprocess  # noqa: E402
from engine import Engine, windows  # noqa: E402


def test_cleaning_catches_every_injected_fault_with_almost_no_false_flags():
    raw = pd.read_csv(ROOT / "data/env_raw.csv")
    df, log, _ = preprocess.clean(raw)
    truth = df["true_anomaly"].fillna(0).astype(bool)
    assert (df["flagged"] & truth).sum() == truth.sum()
    assert (df["flagged"] & ~truth).sum() <= 5
    assert df.index.is_monotonic_increasing and df.index.is_unique
    assert len(df) == 7 * 24 * 60                         # a regular 1-minute grid for the whole week
    assert df["temp_c"].dropna().between(0, 50).all()     # gaps stay empty, everything present is plausible


def test_interpolation_never_bridges_long_gaps():
    s = pd.Series([20.0, np.nan, np.nan, 22.0] + [np.nan] * 10 + [25.0], index=pd.date_range("2026-01-01", periods=15, freq="1min"))
    out = s.interpolate(method="time", limit=5, limit_area="inside")
    assert out.iloc[1] == pytest.approx(20 + 2 / 3) and out.iloc[3:14].isna().sum() >= 5


def test_hampel_flags_a_single_spike_only():
    s = pd.Series(25 + np.random.default_rng(0).normal(0, 0.2, 200))
    s.iloc[100] = 85
    flags = preprocess.hampel(s, floor=0.4)
    assert flags.iloc[100] and flags.sum() == 1


@pytest.fixture(scope="module")
def scored():
    raw = pd.read_csv(ROOT / "data/machine_raw.csv", parse_dates=["timestamp"])
    w = windows(raw)
    eng = Engine().fit(w)
    return eng, eng.score(w)


def test_no_alerts_while_healthy_and_warning_before_failure(scored):
    eng, s = scored
    healthy = s[s.index < pd.Timestamp("2026-09-19")]
    assert (healthy["status"] == "OK").all()
    first_warn = s.index[s["status"] == "WARNING"][0]
    assert first_warn < pd.Timestamp("2026-09-28")        # days before the 30 Sep damage-zone crossing
    assert eng.warn < eng.critical < eng.failure


def test_rul_is_none_when_healthy_and_shrinks_as_wear_grows(scored):
    eng, s = scored
    assert eng.rul_hours(s, pd.Timestamp("2026-09-10 12:00")) is None
    early, late = eng.rul_hours(s, pd.Timestamp("2026-09-27 06:00")), eng.rul_hours(s, pd.Timestamp("2026-09-29 06:00"))
    assert early is not None and late is not None and late < early


def test_dashboard_renders_and_shows_the_right_status():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "maintenance/app.py"), default_timeout=120).run()
    assert not at.exception
    assert "CRITICAL" in at.markdown[0].value or any("CRITICAL" in m.value for m in at.markdown)
    at.slider[0].set_value(200).run()                     # day 5: healthy
    assert any("Normal operation" in s.value for s in at.success)
