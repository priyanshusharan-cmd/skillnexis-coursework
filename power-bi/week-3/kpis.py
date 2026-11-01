"""Week 3: DAX measures and KPI visuals. Power BI is not available here, so each DAX measure is computed
in pandas with the same logic (including DIVIDE's blank-on-zero rule), under the same Region and Year slicers."""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import load_orders

out = Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
ap = argparse.ArgumentParser()
ap.add_argument("--region", help="slicer: one Region, e.g. 'Central US'")
ap.add_argument("--year", type=int, help="slicer: one Year, e.g. 2014")
ap.add_argument("--category", help="slicer: one Category")
args = ap.parse_args()

df = load_orders().rename(columns={"Sales": "Sales", "Profit": "Profit"})
filtered = df
for col, val in (("Region", args.region), ("Year", args.year), ("Category", args.category)):
    if val is not None:
        filtered = filtered[filtered[col] == val]
if filtered.empty:
    raise SystemExit("No rows match those slicers.")


def divide(num, den):  # DAX DIVIDE returns BLANK instead of an error when the denominator is 0
    return None if den == 0 else num / den


def measures(d):
    total_sales, total_profit = d["Sales"].sum(), d["Profit"].sum()
    return {"Total Sales": total_sales, "Total Profit": total_profit, "Profit Margin": divide(total_profit, total_sales),
            "Total Quantity": d["Quantity"].sum(), "Loss-making Sales": d.loc[d["Profit"] < 0, "Sales"].sum()}


m = measures(filtered)
label = ", ".join(f"{k}={v}" for k, v in (("Region", args.region), ("Year", args.year), ("Category", args.category)) if v is not None) or "no slicers (all data)"
print(f"SLICERS: {label}  ({len(filtered):,} of {len(df):,} rows)")
for k, v in m.items():
    print(f"  {k:<18}{v:>16,.2f}" if k != "Profit Margin" else f"  {k:<18}{v:>16.2%}")

# Cross-check: the sum of the KPI over every Region equals the unfiltered total (a check that slicing loses nothing).
by_region = df.groupby("Region")[["Sales", "Profit"]].sum()
assert abs(by_region["Sales"].sum() - df["Sales"].sum()) < 1e-6 and abs(by_region["Profit"].sum() - df["Profit"].sum()) < 1e-6

# Conditional formatting rule: negative profit in red.
by_cat = filtered.groupby("Category")[["Sales", "Profit"]].sum().assign(margin=lambda t: t["Profit"] / t["Sales"])
by_sub = filtered.groupby("Sub-Category")["Profit"].sum().sort_values()
trend = filtered.groupby(filtered["Order Date"].dt.to_period("M").dt.to_timestamp())[["Sales", "Profit"]].sum()

fig = plt.figure(figsize=(14, 8))
gs = fig.add_gridspec(3, 3, height_ratios=[0.6, 1.5, 1.5], hspace=0.55)
cards = [("Total Sales", f"{m['Total Sales']:,.0f}", "#1f4e79"), ("Total Profit", f"{m['Total Profit']:,.0f}", "#1E8449" if m["Total Profit"] >= 0 else "#C0392B"),
         ("Profit Margin", f"{m['Profit Margin']:.1%}", "#1E8449" if m["Profit Margin"] >= 0 else "#C0392B")]
for i, (name, val, color) in enumerate(cards):
    ax = fig.add_subplot(gs[0, i]); ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, fc="#f4f6f8", ec="#cfd6dd", transform=ax.transAxes))
    ax.text(0.5, 0.68, name, ha="center", fontsize=11, color="#555", transform=ax.transAxes)
    ax.text(0.5, 0.25, val, ha="center", fontsize=24, weight="bold", color=color, transform=ax.transAxes)
ax = fig.add_subplot(gs[1, :2])
ax.plot(trend.index, trend["Sales"], label="Sales"); ax.plot(trend.index, trend["Profit"], label="Profit")
ax.set_title("Monthly sales and profit"); ax.legend(); ax.grid(alpha=0.3)
ax = fig.add_subplot(gs[1, 2])
ax.bar(by_cat.index, by_cat["Sales"], color="#7fa8d1"); ax.set_title("Sales by category"); ax.tick_params(axis="x", rotation=15)
ax = fig.add_subplot(gs[2, :])
ax.bar(by_sub.index, by_sub.values, color=["#C0392B" if v < 0 else "#1E8449" for v in by_sub.values])
ax.set_title("Profit by sub-category (negative profit in red)"); ax.tick_params(axis="x", rotation=30); ax.axhline(0, color="#333", lw=0.8)
fig.suptitle(f"Retail KPI dashboard: {label}", fontsize=14)
name = "kpi_dashboard" + ("_" + "_".join(str(v).replace(" ", "") for v in (args.region, args.year, args.category) if v is not None) if label != "no slicers (all data)" else "")
fig.savefig(out / f"{name}.png", dpi=110, bbox_inches="tight")
print(f"\nWrote output/{name}.png")
print(f"Negative-profit sub-categories shown in red: {', '.join(by_sub[by_sub < 0].index) or 'none'}")
