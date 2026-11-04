"""Predictive maintenance engine for the motor data (data/machine_raw.csv, synthetic).

- Learns what "healthy" looks like from the first 7 days only.
- Health index (HI) = robust Mahalanobis distance of 30-minute feature windows from healthy behaviour,
  with the load effect regressed out (vibration and temperature rise with load, which is not a fault).
- Alerts need persistence: WARNING when the HI stays above its threshold for 2 hours, CRITICAL above a
  higher one (halfway between warning and failure on a log scale). A 3-minute transient (a dropped tool, a voltage dip) is logged as an event, not an alert.
- Remaining useful life: fits a quadratic to the HI over the last 48 hours and extrapolates to the failure
  level (the HI at which vibration reaches the ISO 10816 class II 7.1 mm/s "damage" zone).
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.covariance import MinCovDet
from sklearn.linear_model import LinearRegression

FEATURES = ["vib_mean", "vib_std", "vib_p95", "temp_mean", "temp_rate"]


def windows(raw: pd.DataFrame) -> pd.DataFrame:
    r = raw.set_index("timestamp").resample("30min")
    w = pd.DataFrame({
        "vib_mean": r["vibration_rms_mm_s"].median(),        # median: robust to a 3-minute transient
        "vib_std": r["vibration_rms_mm_s"].std(),
        "vib_p95": r["vibration_rms_mm_s"].quantile(0.95),
        "vib_max": r["vibration_rms_mm_s"].max(),
        "temp_mean": r["bearing_temp_c"].median(),
        "current_mean": r["current_a"].median(),
        "current_max": r["current_a"].max(),
    })
    w["temp_rate"] = w["temp_mean"].diff().fillna(0)
    return w.dropna()


@dataclass
class Engine:
    healthy_days: int = 7
    warn_q: float = 0.995
    hold_windows: int = 4          # 4 x 30 min = 2 hours above threshold before an alert

    def fit(self, w: pd.DataFrame):
        healthy = w[w.index < w.index[0] + pd.Timedelta(days=self.healthy_days)]
        self.load_models = {f: LinearRegression().fit(healthy[["current_mean"]], healthy[f]) for f in FEATURES}
        res = self._residuals(healthy)
        self.mcd = MinCovDet(random_state=0).fit(res)
        hi = self._hi(res)
        self.warn = float(np.quantile(hi, self.warn_q))
        # failure level: HI of a window whose vibration median sits at 7.1 mm/s at normal load
        probe = healthy.median(numeric_only=True).to_frame().T
        base_vib = probe["vib_mean"].iloc[0]
        probe = probe.assign(vib_mean=7.1, vib_p95=7.1 + (probe["vib_p95"].iloc[0] - base_vib),
                             temp_mean=probe["temp_mean"].iloc[0] + 14 * (7.1 - base_vib) / 2.9)
        self.failure = float(self._hi(self._residuals(probe))[0])
        self.critical = float(np.sqrt(self.warn * self.failure))   # halfway to failure on a log scale
        return self

    def _residuals(self, w):
        return np.column_stack([w[f] - self.load_models[f].predict(w[["current_mean"]]) for f in FEATURES])

    def _hi(self, res):
        return np.sqrt(self.mcd.mahalanobis(res))

    def score(self, w: pd.DataFrame) -> pd.DataFrame:
        out = w.copy()
        out["hi"] = self._hi(self._residuals(w))
        above_w = (out["hi"] > self.warn).astype(int)
        above_c = (out["hi"] > self.critical).astype(int)
        held_w = above_w.rolling(self.hold_windows).sum() == self.hold_windows
        held_c = above_c.rolling(self.hold_windows).sum() == self.hold_windows
        out["status"] = np.select([held_c, held_w], ["CRITICAL", "WARNING"], "OK")
        # a transient: a few minutes of very high vibration/current inside an otherwise normal window
        out["transient"] = (out["vib_max"] > out["vib_mean"] + 1.5) & (out["current_max"] > out["current_mean"] + 2)
        return out

    def rul_hours(self, scored: pd.DataFrame, at: pd.Timestamp, lookback_h: int = 48):
        """Hours until the fitted HI trend reaches the failure level, or None if there is no upward trend."""
        hist = scored.loc[at - pd.Timedelta(hours=lookback_h):at, "hi"]
        if len(hist) < 24 or hist.iloc[-8:].median() < self.warn:
            return None
        t = (hist.index - hist.index[0]).total_seconds() / 3600
        a, b, c = np.polyfit(t, hist.values, 2)
        now = t[-1]
        for h in np.arange(0, 24 * 21, 0.5):         # search up to 3 weeks ahead
            x = now + h
            if a * x * x + b * x + c >= self.failure:
                return float(h) if (2 * a * now + b) > 0 else None
        return None
