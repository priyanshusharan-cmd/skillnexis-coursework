"""Replays the 30-day motor log through the engine as if it were live and measures what matters:
when the first WARNING / CRITICAL fired relative to the real fault, how many false alerts there were,
whether transients stayed out of the alerts, and how accurate the remaining-life estimate was.

    python maintenance/evaluate.py   -> results/maintenance.png, results/maintenance.md
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from engine import Engine, windows

raw = pd.read_csv("data/machine_raw.csv", parse_dates=["timestamp"])
labels = pd.read_csv("data/machine_labels.csv", parse_dates=["timestamp"]).set_index("timestamp")
w = windows(raw)
eng = Engine().fit(w)
s = eng.score(w)

wear_start = labels.index[labels["degrading"] == 1][0]
fail_time = raw.loc[raw["vibration_rms_mm_s"].rolling(60).median() >= 7.1, "timestamp"].iloc[0]   # vibration enters ISO "damage" zone
first = {lvl: s.index[s["status"] == lvl][0] if (s["status"] == lvl).any() else None for lvl in ["WARNING", "CRITICAL"]}
false_alerts = int(((s["status"] != "OK") & (s.index < wear_start)).sum())
trans_windows = labels["transient"].resample("30min").max().reindex(s.index).fillna(0).astype(bool)
trans_in_alert = int((trans_windows & (s["status"] != "OK") & (s.index < wear_start)).sum())
trans_detected = int((trans_windows & s["transient"]).sum())

rul_rows = []
for hrs_before in [96, 72, 48, 24, 12]:
    at = fail_time - pd.Timedelta(hours=hrs_before)
    at = s.index[s.index <= at][-1]
    est = eng.rul_hours(s, at)
    rul_rows.append((hrs_before, est))

lines = ["## 3. Predictive maintenance (30 days of a motor, synthetic)", "",
         f"Healthy model: days 1-7. Bearing wear starts **{wear_start:%d %b %H:%M}**; vibration reaches the ISO 10816 damage zone "
         f"(7.1 mm/s) at **{fail_time:%d %b %H:%M}**.", "",
         "| Check | Result |", "|---|---|",
         f"| First WARNING | {first['WARNING']:%d %b %H:%M} = **{(fail_time - first['WARNING']).total_seconds() / 3600:.0f} h before failure** "
         f"({(first['WARNING'] - wear_start).total_seconds() / 3600:.0f} h after wear began) |",
         f"| First CRITICAL | {first['CRITICAL']:%d %b %H:%M} = {(fail_time - first['CRITICAL']).total_seconds() / 3600:.0f} h before failure |",
         f"| False alerts during 18 healthy days (36 shift changes) | **{false_alerts}** |",
         f"| Transient spikes (25 injected) shown as events, not alerts | {trans_detected} of {int(trans_windows.sum())} flagged as transients, {trans_in_alert} raised an alert |",
         "", "Remaining useful life (RUL) estimate vs truth:", "", "| Asked at | True RUL | Estimated RUL | Error |", "|---|---:|---:|---:|"]
for true_h, est in rul_rows:
    lines.append(f"| {true_h} h before failure | {true_h} h | {'no trend yet' if est is None else f'{est:.0f} h'} | "
                 f"{'-' if est is None else f'{est - true_h:+.0f} h'} |")
open("results/maintenance.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

fig, ax = plt.subplots(2, 1, figsize=(12, 6.5), sharex=True)
ax[0].plot(raw["timestamp"], raw["vibration_rms_mm_s"], lw=0.3, color="#868e96", label="vibration RMS (1-min)")
ax[0].plot(s.index, s["vib_mean"], color="#1c7ed6", lw=1.2, label="30-min median")
ax[0].axhline(7.1, color="#e03131", ls="--", lw=1, label="ISO 10816 damage zone 7.1 mm/s")
ax[0].axvline(wear_start, color="#f08c00", lw=1, label="wear begins (ground truth)")
ax[0].set_ylim(0, 12)
ax[0].set_ylabel("mm/s")
ax[0].legend(loc="upper left", fontsize=8)
ax[1].plot(s.index, s["hi"], color="#212529", lw=1, label="health index")
ax[1].axhline(eng.warn, color="#f59f00", ls="--", lw=1, label="warning level")
ax[1].axhline(eng.critical, color="#e03131", ls="--", lw=1, label="critical level")
for lvl, col in [("WARNING", "#ffec99"), ("CRITICAL", "#ffc9c9")]:
    m = s["status"] == lvl
    ax[1].fill_between(s.index, 0, s["hi"].max() * 1.05, where=m, color=col, alpha=0.6, step="mid", label=f"{lvl} (held 2 h)")
ax[1].scatter(s.index[s["transient"]], s["hi"][s["transient"]], s=14, marker="x", color="#7048e8", label="transient event", zorder=3)
ax[1].set_yscale("log")
ax[1].set_ylabel("health index (log)")
ax[1].legend(loc="upper left", fontsize=8, ncol=3)
fig.suptitle("Predictive maintenance: alerts and health index over 30 days")
fig.tight_layout()
fig.savefig("results/maintenance.png", dpi=100)
