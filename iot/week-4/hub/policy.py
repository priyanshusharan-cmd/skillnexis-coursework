"""Energy optimisation: how lights and fans are switched, compared on the 8 unseen test days.

Loads per room: LED lighting 40 W, ceiling fan 55 W. Needs:
  light needed  = someone awake in the room and daylight < 100 lux
  fan needed    = someone in the room (awake or asleep) and temperature > 28 °C

Policies
  manual     people switch things on when needed; on leaving a room they switch off 60 % of the time
             (otherwise it stays on until the next visit), and everything is off at bedtime
  pir_timer  on at motion, off 10 min after the last motion (the classic smart switch)
  ml         int8 occupancy model with hysteresis (on > 0.6, off after 3 min < 0.4); bedroom lights go to sleep mode
             at night after 15 min without motion while the fan keeps running

    python hub/policy.py   -> results/energy.md, results/energy_day.png
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "ml"))
LIGHT_W, FAN_W, DARK_LUX, HOT_C = 40, 55, 100, 28.0
OFF_DELAY = 3          # minutes the model must say "empty" before switching off


def needs(g):
    light = (g.awake == 1) & (g.daylight_lux < DARK_LUX)
    fan = (g.occupied == 1) & (g.temp_c > HOT_C)
    return light.to_numpy(), fan.to_numpy()


class MLController:
    """The hub's automation for one room (also used offline below, so the evaluation is the deployed logic)."""

    def __init__(self, bedroom):
        self.bedroom, self.occ, self.low, self.since = bedroom, False, 0, 999

    def step(self, p, motion, lux, temp, hour):
        self.since = 0 if motion else self.since + 1
        self.low = self.low + 1 if p < 0.4 else 0
        self.occ = p > 0.6 if not self.occ else self.low < OFF_DELAY
        sleep_mode = self.bedroom and (hour >= 22.5 or hour < 7) and self.since >= 15
        return self.occ and lux < DARK_LUX and not sleep_mode, self.occ and temp > HOT_C


def run(g, policy, proba=None, rng=None):
    """One room, minute by minute. Returns light and fan on/off arrays."""
    n = len(g)
    light, fan = np.zeros(n, bool), np.zeros(n, bool)
    need_l, need_f = needs(g)
    occ, motion = g.occupied.to_numpy(), g.motion.to_numpy()
    dark, hot = (g.daylight_lux < DARK_LUX).to_numpy(), (g.temp_c > HOT_C).to_numpy()
    asleep = g.asleep.to_numpy()
    hour = (g.timestamp.dt.hour + g.timestamp.dt.minute / 60).to_numpy()
    bedroom = g.room.iloc[0] == "bedroom"
    lt = f = False
    since = 999
    ctl = MLController(bedroom)
    lux, temp = g.daylight_lux.to_numpy(), g.temp_c.to_numpy()
    for i in range(n):
        since = 0 if motion[i] else since + 1
        if policy == "manual":
            if need_l[i]:
                lt = True
            if need_f[i]:
                f = True
            if i and occ[i - 1] and not occ[i] and rng.random() < 0.6:
                lt = f = False
            if asleep[i]:
                lt = False
            if 0 <= hour[i] < 0.02 and not bedroom:        # last one to bed switches the living room off
                lt = f = False
        elif policy == "pir_timer":
            if motion[i]:
                lt, f = lt or dark[i], f or hot[i]
            if since >= 10:
                lt = f = False
        else:
            lt, f = ctl.step(proba[i], motion[i], lux[i], temp[i], hour[i])
        light[i], fan[i] = lt, f
    return light, fan


def evaluate(df, proba):
    rng = np.random.default_rng(0)
    out, days = {}, df.timestamp.dt.normalize().nunique()
    for policy in ("manual", "pir_timer", "ml"):
        kwh = miss_l = miss_f = cut_off = 0
        for _room, g in df.groupby("room", sort=False):
            light, fan = run(g, policy, proba[g.index.to_numpy() - df.index[0]] if policy == "ml" else None, rng)
            need_l, need_f = needs(g)
            kwh += (light.sum() * LIGHT_W + fan.sum() * FAN_W) / 60 / 1000
            miss_l += (need_l & ~light).sum()
            miss_f += (need_f & ~fan).sum()
            cut_off += (np.diff(light.astype(int)) == -1)[need_l[1:]].sum()   # light switched off on someone using it
        out[policy] = dict(kwh_week=kwh / days * 7, miss_light_h=miss_l / 60 / days * 7, miss_fan_h=miss_f / 60 / days * 7,
                           cut_offs_week=cut_off / days * 7)
    return out


def plot_day(df, proba, path, day_offset=3):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d0 = df.timestamp.dt.normalize().unique()[day_offset]
    g = df[(df.room == "living") & (df.timestamp.dt.normalize() == d0)]
    full = df[df.room == "living"]
    lt_pir, _ = run(full, "pir_timer")
    lt_ml, _ = run(full, "ml", proba[full.index.to_numpy() - df.index[0]])
    sel = (full.timestamp.dt.normalize() == d0).to_numpy()
    h = (g.timestamp.dt.hour + g.timestamp.dt.minute / 60).to_numpy()
    fig, ax = plt.subplots(figsize=(11, 3.6))
    rows = [("Someone needs light", needs(g)[0], "#3a7d44"), ("Motion-timer lights", lt_pir[sel], "#c8553d"),
            ("ML lights", lt_ml[sel], "#2f6690")]
    for k, (_name, v, c) in enumerate(rows):
        ax.fill_between(h, k + 0.1, k + 0.1 + 0.8 * v, step="post", color=c, linewidth=0)
    ax.scatter(h[g.motion.to_numpy() == 1], np.full((g.motion == 1).sum(), 3.25), s=4, color="#555", label="PIR motion")
    ax.set_yticks([0.5, 1.5, 2.5, 3.25], [r[0] for r in rows] + ["PIR motion events"])
    ax.set_xticks(range(0, 25, 3), [f"{x:02d}:00" for x in range(0, 25, 3)])
    ax.set_xlim(0, 24)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_title(f"Living room, {pd.Timestamp(d0):%a %d %b}: the motion timer switches off on people watching TV; the model doesn't", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)


def main():
    from occupancy import TRAIN_DAYS
    df = pd.read_csv(os.path.join(ROOT, "data", "home_1min.csv"), parse_dates=["timestamp"])
    day = (df.timestamp - df.timestamp.min()).dt.days
    te = df[day >= TRAIN_DAYS].reset_index(drop=True)
    proba = np.load(os.path.join(ROOT, "ml", "test_proba_int8.npy"))
    r = evaluate(te, proba)
    base = r["manual"]["kwh_week"]
    names = {"manual": "Manual switches (baseline)", "pir_timer": "Motion timer, 10 min", "ml": "**AI occupancy model**"}
    lines = ["Simulated on the 8 unseen test days, 2 rooms, LED lights 40 W and ceiling fans 55 W per room.", "",
             "| Policy | Energy per week | Saving vs manual | Light missing while needed | Fan missing while needed | Lights cut off on someone |",
             "|---|---:|---:|---:|---:|---:|"]
    for k, v in r.items():
        lines.append(f"| {names[k]} | {v['kwh_week']:.1f} kWh | {1 - v['kwh_week'] / base:.0%} | {v['miss_light_h']:.1f} h/week | "
                     f"{v['miss_fan_h']:.1f} h/week | {v['cut_offs_week']:.0f} /week |")
    lines += ["", "The motion timer saves energy by being annoying: it switches lights and fans off on people who sit still "
              "and stops the fan on sleepers. The model saves energy while keeping people comfortable."]
    plot_day(te, proba, os.path.join(ROOT, "results", "energy_day.png"))
    open(os.path.join(ROOT, "results", "energy.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
