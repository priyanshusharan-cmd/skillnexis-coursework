"""Chart the 3-day simulation: soil moisture with thresholds, pump runs, temperature/light, events."""
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

tele = list(csv.DictReader(open("results/sim-telemetry.csv")))
events = list(csv.reader(open("results/sim-events.csv")))[1:]
h = [int(r["t_s"]) / 3600 for r in tele]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 6.5), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
a1.plot(h, [float(r["soil_true_pct"]) for r in tele], color="#8a5a2b", lw=1.6, label="soil moisture (%)")
a1.axhline(35, color="#d9480f", ls="--", lw=1, label="start watering < 35 %")
a1.axhline(60, color="#2b8a3e", ls="--", lw=1, label="stop > 60 %")
on = None
for t, ev, *_ in events:
    if ev == "pump_on":
        on = int(t) / 3600
    elif ev == "pump_off" and on is not None:
        a1.axvspan(on, int(t) / 3600, color="#1c7ed6", alpha=0.35, lw=0)
        on = None
a1.axvspan(38, 41, color="#e03131", alpha=0.10, lw=0, label="tank empty")
a1.axvspan(50, 50.5, color="#7048e8", alpha=0.25, lw=0, label="probe unplugged")
a1.annotate("manual 'water'\nvia MQTT", xy=(55.1, 55), xytext=(57, 82), arrowprops={"arrowstyle": "->"}, fontsize=9)
a1.set_ylabel("soil moisture %")
a1.set_ylim(0, 100)
a1.legend(loc="upper left", fontsize=8, ncol=3)
a1.set_title("Smart irrigation node - 3 simulated days (blue bands = pump running)")
a2.plot(h, [float(r["temp_c"]) for r in tele], color="#e8590c", lw=1.2, label="air temp (C)")
a2b = a2.twinx()
a2b.fill_between(h, [float(r["light_pct"]) for r in tele], color="#fab005", alpha=0.25, label="light (%)")
a2.set_ylabel("temp C")
a2b.set_ylabel("light %")
a2.set_xlabel("hours since start")
a2.set_xticks(range(0, 73, 6))
for d in (24, 48):
    a1.axvline(d, color="#868e96", lw=0.6)
    a2.axvline(d, color="#868e96", lw=0.6)
fig.tight_layout()
fig.savefig(sys.argv[1] if len(sys.argv) > 1 else "results/sim-3days.png", dpi=110)
print("saved")
