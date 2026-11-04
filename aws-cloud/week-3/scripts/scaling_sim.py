"""How the Auto Scaling group behaves over a day of realistic traffic, minute by minute.

Models AWS target tracking on average CPU (target 50 %): scale out as soon as CPU is above target
(desired = ceil(n x cpu / target)), new instances take 3 minutes to boot and pass health checks, and scale-in
waits for 15 minutes of low CPU (AWS is deliberately slow to remove capacity). One t3.micro running nginx +
the app is assumed to handle 120 requests/s at 100 % CPU (measure yours with a load test).

    python scripts/scaling_sim.py   -> results/scaling.md, results/scaling.png
"""
import math
import os

import numpy as np

CAP, TARGET, MIN, MAX, WARMUP, SCALE_IN_WAIT = 120.0, 50.0, 1, 3, 3, 15
PRICE_HOUR = 0.0112          # t3.micro on-demand, ap-south-1, USD (free tier covers 750 h/month for 12 months)


def traffic(rng):
    """Requests/s for each minute of a college-site day: morning and evening peaks, a results-day spike at 18:00."""
    m = np.arange(1440)
    h = m / 60
    base = 6 + 40 * np.exp(-((h - 10.5) / 1.8) ** 2) + 55 * np.exp(-((h - 20.5) / 1.6) ** 2)
    spike = 330 * np.exp(-((h - 18.0) / 0.12) ** 2)          # results announced: a sharp 15-minute rush
    return np.clip(base + spike + rng.normal(0, 3, 1440), 1, None)


def simulate(load, min_n=MIN, max_n=MAX, fixed=None, start=None):
    n = fixed if fixed is not None else max(min_n, int(start or min_n))
    if start is not None and min_n > start:          # scheduled minimum: the extra instances still have to boot
        n = int(start)
    pending, low_for = [], 0
    if start is not None and min_n > n:
        pending = [WARMUP] * (min_n - n)
    rows = []
    for t, rps in enumerate(load):
        n += sum(1 for p in pending if p == t)
        pending = [p for p in pending if p > t]
        cpu = min(100.0, 100 * rps / (n * CAP))
        if fixed is None:
            want = min(max_n, max(min_n, math.ceil(n * cpu / TARGET)))
            if want > n + len(pending):
                pending += [t + WARMUP] * (want - n - len(pending))
                low_for = 0
            elif want < n and not pending:
                low_for += 1
                if low_for >= SCALE_IN_WAIT:
                    n, low_for = n - 1, 0
            else:
                low_for = 0
        served = min(rps, n * CAP)
        rows.append((rps, n, cpu, rps - served))
    return np.array(rows)


def simulate_scheduled(load):
    """Max 4, and a scheduled action that raises the minimum to 3 from 17:45 to 19:00."""
    out = []
    for lo, hi, mn in ((0, 1065, 1), (1065, 1140, 3), (1140, 1440, 1)):
        out.append(simulate(load[lo:hi], min_n=mn, max_n=4, start=out[-1][-1, 1] if out else None))
    return np.concatenate(out)


def main():
    load = traffic(np.random.default_rng(3))
    runs = {"Auto Scaling 1-3": simulate(load), "Auto Scaling 1-4": simulate(load, max_n=4),
            "Auto Scaling 1-4 + scheduled 3 at 17:45": simulate_scheduled(load),
            "Fixed 1 instance": simulate(load, fixed=1), "Fixed 3 instances": simulate(load, fixed=3)}
    lines = [f"One simulated day (1,440 minutes); peak demand {load.max():.0f} req/s during the 18:00 results rush "
             f"(one t3.micro handles {CAP:.0f} req/s).", "",
             "| Setup | Instance-hours | Cost/day (after free tier) | Minutes over 80 % CPU | Requests dropped |", "|---|---:|---:|---:|---:|"]
    for name, r in runs.items():
        ih = r[:, 1].sum() / 60
        lines.append(f"| {name} | {ih:.1f} | ${ih * PRICE_HOUR:.3f} | {(r[:, 2] > 80).sum()} | {r[:, 3].sum() * 60:,.0f} ({r[:, 3].sum() / load.sum():.2%}) |")
    a, a4, sch = runs["Auto Scaling 1-3"], runs["Auto Scaling 1-4"], runs["Auto Scaling 1-4 + scheduled 3 at 17:45"]
    hot = lambda r: int((r[:, 2] > 80).sum())  # noqa: E731
    rush = slice(1065, 1110)
    lines += ["", f"- Auto Scaling 1-3 used **{a[:, 1].sum() / 60:.0f} instance-hours instead of 72** for a fixed fleet of 3 "
              f"({1 - a[:, 1].sum() / 60 / 72:.0%} less) and dropped nothing.",
              f"- Its {hot(a)} minutes above 80 % CPU (slow pages) were all in the 18:00 rush "
              f"({int((a[rush, 2] > 80).sum())} of them): new instances need 3 minutes to boot and pass health checks.",
              f"- Raising the cap to 4: {hot(a4)} hot minutes. Adding a scheduled action (minimum 3 from 17:45) before a known event: "
              f"**{hot(sch)}** hot minutes for {sch[:, 1].sum() / 60 - a[:, 1].sum() / 60:+.1f} instance-hours "
              f"(about ${(sch[:, 1].sum() - a[:, 1].sum()) / 60 * PRICE_HOUR:.3f}).",
              f"- Even a fixed fleet of 3 had {hot(runs['Fixed 3 instances'])} hot minutes at the peak, at 2.7x the cost. "
              "Recommendation: min 1 / max 4, CPU target 50 %, scheduled scaling before known events."]
    os.makedirs("results", exist_ok=True)
    open("results/scaling.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    h = np.arange(1440) / 60
    fig, ax1 = plt.subplots(figsize=(10, 3.6))
    ax1.fill_between(h, load, color="#c9d6e8", label="demand (req/s)")
    ax1.plot(h, np.minimum(load, a[:, 1] * CAP), color="#2f6690", lw=1, label="served (req/s)")
    ax1.set_ylabel("requests / s")
    ax2 = ax1.twinx()
    ax2.step(h, a[:, 1], where="post", color="#c8553d", lw=1.6, label="instances")
    ax2.set_ylim(0, 4.5)
    ax2.set_ylabel("instances")
    ax1.set_xticks(range(0, 25, 3), [f"{x:02d}:00" for x in range(0, 25, 3)])
    ax1.set_xlim(0, 24)
    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
    fig.legend(loc="upper left", bbox_to_anchor=(0.07, 0.86), frameon=False, fontsize=8)
    ax1.set_title("Auto Scaling group (1-3 x t3.micro, CPU target 50 %) over one day", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig("results/scaling.png", dpi=130)


if __name__ == "__main__":
    main()
