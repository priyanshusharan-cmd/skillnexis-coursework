"""Week 2: data modelling and relationships. Builds the star schema, creates the calendar table the way the
brief's DAX does, and checks every relationship. Run it, then follow README.md to rebuild it in Power BI."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import load_orders, load_people

out = Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
orders = load_orders()
people = load_people()
print(f"Orders: {len(orders):,} rows, {orders['Order Date'].min():%Y-%m-%d} to {orders['Order Date'].max():%Y-%m-%d}")

# ---- Dimension tables (the "one" side of each relationship) ----
customers = orders[["Customer ID", "Customer Name", "Segment"]].drop_duplicates("Customer ID").reset_index(drop=True)
products = orders[["Product ID", "Product Name", "Category", "Sub-Category"]].drop_duplicates("Product ID").reset_index(drop=True)
# Regions come from the regions that actually appear in Orders. The People sheet splits Canada into
# "Western Canada" and "Eastern Canada" while Orders only has "Canada", so Canada gets both managers.
managers = people.groupby("Region")["Person"].apply(lambda s: " / ".join(s)).to_dict()
managers["Canada"] = " / ".join(managers.pop(r) for r in ["Western Canada", "Eastern Canada"])
regions = pd.DataFrame({"Region": sorted(orders["Region"].unique())})
regions["Regional manager"] = regions["Region"].map(managers)
regions.insert(0, "Region ID", range(1, len(regions) + 1))
orders = orders.merge(regions[["Region", "Region ID"]], on="Region", how="left")  # Orders has the Region name, so add the ID
# Equivalent of: Calendar = CALENDAR(MIN(Orders[Order Date]), MAX(Orders[Order Date]))
cal = pd.DataFrame({"Date": pd.date_range(orders["Order Date"].min(), orders["Order Date"].max(), freq="D")})
cal["Year"], cal["MonthNo"], cal["Month"], cal["Day"] = cal["Date"].dt.year, cal["Date"].dt.month, cal["Date"].dt.strftime("%b"), cal["Date"].dt.day

# ---- Check each relationship: the key must be unique on the "one" side and present on the "many" side ----
checks = [
    ("Orders[Customer ID] -> Customers[Customer ID]", orders["Customer ID"], customers["Customer ID"]),
    ("Orders[Product ID] -> Products[Product ID]", orders["Product ID"], products["Product ID"]),
    ("Orders[Region ID] -> Regions[Region ID]", orders["Region ID"], regions["Region ID"]),
    ("Orders[Order Date] -> Calendar[Date]", orders["Order Date"].dt.normalize(), cal["Date"]),
]
rows = []
for name, many, one in checks:
    unique = one.is_unique
    orphans = int((~many.isin(one)).sum())
    rows.append({"relationship (many -> one)": name, "one-side unique": unique, "orphan rows": orphans, "dimension rows": len(one), "ok": unique and orphans == 0})
report = pd.DataFrame(rows)
print("\nRELATIONSHIP CHECKS (many-to-one, single direction from dimension to Orders)")
print(report.to_string(index=False))
assert report["ok"].all(), "a relationship would fail in Power BI"

print(f"\nCalendar: {len(cal):,} days; years {cal['Year'].min()}-{cal['Year'].max()}; hierarchy Year > Month > Day.")
print(f"Days with no orders: {int((~cal['Date'].isin(orders['Order Date'].dt.normalize())).sum())} (normal: a calendar table covers every day, including days with no sales).")
print("\nDATA QUALITY NOTES")
print(f"  Customer IDs: {customers['Customer ID'].nunique():,}, but distinct customer names: {customers['Customer Name'].nunique():,}.")
print("  So one person can hold many Customer IDs. The relationship is valid, but count customers by name, not by ID.")
print(f"  Regions in Orders: {orders['Region'].nunique()}. The People sheet lists 24 (it splits Canada into Western and Eastern Canada), so the Regions table is built from Orders and Canada carries both managers.")
print(f"  Regions with no manager listed: {int(regions['Regional manager'].isna().sum())}.")
print(f"  Postal Code is blank on {orders['Postal Code'].isna().mean():.0%} of rows (only US orders have one).")

# ---- Star schema diagram ----
fig, ax = plt.subplots(figsize=(10, 6.2))
ax.axis("off")
def box(x, y, title, fields, color):
    ax.text(x, y, title + "\n" + "\n".join(fields), ha="center", va="center", fontsize=9, family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", fc=color, ec="#333"))
box(0.5, 0.5, "Orders (fact)", ["Order Date  *", "Customer ID *", "Product ID  *", "Region ID   *", "Sales, Profit,", "Quantity, Discount"], "#fde9c7")
box(0.14, 0.82, "Customers", ["Customer ID (key)", "Customer Name", "Segment"], "#d6e8fb")
box(0.86, 0.82, "Products", ["Product ID (key)", "Product Name", "Category", "Sub-Category"], "#d6e8fb")
box(0.14, 0.18, "Regions", ["Region ID (key)", "Region", "Regional manager"], "#d6e8fb")
box(0.86, 0.18, "Calendar", ["Date (key)", "Year > Month > Day"], "#d6e8fb")
for x, y in [(0.14, 0.82), (0.86, 0.82), (0.14, 0.18), (0.86, 0.18)]:
    ax.annotate("", xy=(0.5 + (x - 0.5) * 0.45, 0.5 + (y - 0.5) * 0.45), xytext=(x - (x - 0.5) * 0.35, y - (y - 0.5) * 0.35), arrowprops=dict(arrowstyle="->", color="#444"))
    ax.text((x + 0.5) / 2, (y + 0.5) / 2 + 0.03, "1 : *", ha="center", fontsize=9, color="#444")
ax.set_title("Star schema: each dimension filters Orders (1 to many)")
fig.savefig(out / "star_schema.png", dpi=130, bbox_inches="tight")
report.to_csv(out / "relationship_checks.csv", index=False)
print("\nWrote output/star_schema.png and output/relationship_checks.csv")
