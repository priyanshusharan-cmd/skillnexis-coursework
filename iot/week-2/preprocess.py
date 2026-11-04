"""Cleans one week of raw sensor logs with pandas and reports every change it makes.

Steps: parse timestamps -> drop exact duplicates -> sort (late packets) -> reindex to a 1-minute grid
(gaps become NaN) -> range checks -> Hampel filter for spikes -> stuck-sensor detection -> interpolate
gaps of up to 5 minutes, leave longer ones empty -> 15-minute summary.

    python preprocess.py        -> data/env_clean.csv, data/env_15min.csv, results/cleaning_report.md
"""
import numpy as np
import pandas as pd

RANGES = {"temp_c": (0, 50), "humidity_pct": (20, 90), "light_lux": (0, 2000)}   # DHT11 / LDR datasheet ranges
# smallest believable spread per sensor: DHT11 reads humidity in whole %, so its noise floor is ~2 %
MAD_FLOOR = {"temp_c": 0.4, "humidity_pct": 2.5, "light_lux": 40.0}


def hampel(s, floor, window=15, k=4.0):
    """Flags points more than k robust standard deviations from the rolling median."""
    med = s.rolling(window, center=True, min_periods=5).median()
    mad = (s - med).abs().rolling(window, center=True, min_periods=5).median() * 1.4826
    return (s - med).abs() > k * mad.clip(lower=floor)


def stuck(s, minutes=30):
    """Flags runs where a normally noisy signal does not change at all for `minutes`."""
    filled = s.ffill(limit=5)               # a lost packet inside a frozen run must not split it
    change = filled.diff().ne(0)
    run_id = change.cumsum()
    run_len = filled.groupby(run_id).transform("size")
    return run_len >= minutes


def clean(raw: pd.DataFrame):
    log = []
    df = raw.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    n = len(df)
    df = df.drop_duplicates(subset=["timestamp", "device_id"])
    log.append(("Duplicate packets removed", n - len(df)))
    late = int((df["timestamp"].diff() < pd.Timedelta(0)).sum())
    df = df.sort_values("timestamp").set_index("timestamp")
    log.append(("Out-of-order rows re-sorted", late))
    grid = pd.date_range(df.index.min().floor("1min"), df.index.max().ceil("1min"), freq="1min")
    missing = len(grid.difference(df.index))
    df = df.reindex(grid)
    df.index.name = "timestamp"
    log.append(("Missing minutes (lost packets + outages)", missing))
    flags = pd.DataFrame(index=df.index)
    for col, (lo, hi) in RANGES.items():
        bad = (df[col] < lo) | (df[col] > hi)
        log.append((f"{col}: outside {lo}-{hi}", int(bad.sum())))
        flags[f"{col}_range"] = bad
        df.loc[bad, col] = np.nan
        spike = hampel(df[col], MAD_FLOOR[col]).fillna(False) & ~bad
        log.append((f"{col}: Hampel spikes", int(spike.sum())))
        flags[f"{col}_spike"] = spike
        df.loc[spike, col] = np.nan
    st = stuck(df["humidity_pct"]) & df["humidity_pct"].notna()
    log.append(("humidity_pct: stuck-sensor minutes (no change >= 30 min)", int(st.sum())))
    flags["humidity_pct_stuck"] = st
    df.loc[st, "humidity_pct"] = np.nan
    before = df[list(RANGES)].isna().sum().sum()
    for col in RANGES:
        df[col] = df[col].interpolate(method="time", limit=5, limit_area="inside")
    after = df[list(RANGES)].isna().sum().sum()
    log.append(("Values filled by time interpolation (gaps <= 5 min)", int(before - after)))
    log.append(("Values left empty (gaps > 5 min, not invented)", int(after)))
    df["device_id"] = "esp32-garden-01"
    df["flagged"] = flags.any(axis=1)
    return df, log, flags


def summarise(df):
    out = df[list(RANGES)].resample("15min").agg(["mean", "min", "max"])
    out.columns = ["_".join(c) for c in out.columns]
    out["valid_minutes"] = df["temp_c"].resample("15min").count()
    return out.round(2)


if __name__ == "__main__":
    raw = pd.read_csv("data/env_raw.csv")
    df, log, flags = clean(raw)
    df.drop(columns=["true_anomaly"]).to_csv("data/env_clean.csv")
    summarise(df).to_csv("data/env_15min.csv")
    truth = df["true_anomaly"].fillna(0).astype(bool)
    caught = (df["flagged"] & truth).sum()
    lines = ["# Cleaning report", "", f"Input: {len(raw)} rows from `data/env_raw.csv` (synthetic, see `simulate_sensors.py`).", "",
             "| Step | Rows / values |", "|---|---:|"] + [f"| {a} | {b} |" for a, b in log] + [
        "", f"Injected glitches caught by the range/spike/stuck checks: **{caught} of {int(truth.sum())}** "
        f"({caught / truth.sum():.0%}); false flags on clean minutes: {int((df['flagged'] & ~truth).sum())}.",
        "", f"Output: `data/env_clean.csv` ({len(df)} minutes on a regular grid), `data/env_15min.csv` (15-minute mean/min/max)."]
    open("results/cleaning_report.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
