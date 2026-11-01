"""Week 4: the Global Sales dashboard. Four visuals, filters for Year, Segment and Region, a logo and theme colours.
Power BI Desktop is not available on this Mac and nothing can be published to the Power BI Service from here, so the
dashboard is built as a self-contained HTML page with Plotly. theme.json is a real Power BI theme file for the same colours."""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from common import load_orders

here = Path(__file__).parent
out = here / "output"
out.mkdir(exist_ok=True)
theme = json.loads((here / "theme.json").read_text())
C = theme["dataColors"]

ap = argparse.ArgumentParser()
ap.add_argument("--year", type=int)
ap.add_argument("--segment")
ap.add_argument("--region")
args = ap.parse_args()

df = load_orders()
for col, val in (("Year", args.year), ("Segment", args.segment), ("Region", args.region)):
    if val is not None:
        df = df[df[col] == val]
if df.empty:
    raise SystemExit("No rows match those filters.")
filters = {k: v for k, v in (("Year", args.year), ("Segment", args.segment), ("Region", args.region)) if v is not None}
label = ", ".join(f"{k}: {v}" for k, v in filters.items()) or "All data"

# Company logo: a placeholder monogram drawn here, since no logo file was supplied.
fig, ax = plt.subplots(figsize=(1.2, 1.2))
ax.add_patch(plt.Circle((0.5, 0.5), 0.48, color=C[0])); ax.text(0.5, 0.5, "SN", ha="center", va="center", color="white", fontsize=26, weight="bold")
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
fig.savefig(out / "logo.png", dpi=150, transparent=True, bbox_inches="tight")
plt.close(fig)
import base64
logo_b64 = base64.b64encode((out / "logo.png").read_bytes()).decode()

# ---- KPIs ----
sales, profit, avg_disc = df["Sales"].sum(), df["Profit"].sum(), df["Discount"].mean()
print(f"FILTERS: {label} ({len(df):,} rows)")
print(f"  Sales {sales:,.0f} | Profit {profit:,.0f} | Margin {profit / sales:.1%} | Average discount {avg_disc:.1%}")

# ---- The four visuals ----
by_country = df.groupby("Country")["Sales"].sum().reset_index()
by_cat = df.groupby("Category")["Profit"].sum().sort_values()
monthly = df.groupby(df["Order Date"].dt.to_period("M").dt.to_timestamp())["Sales"].sum()
top_cust = df.groupby("Customer Name").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum")).sort_values("Sales", ascending=False).head(5).reset_index()
top_prod = df.groupby("Product Name")["Sales"].sum().sort_values(ascending=False).head(5)
top_reg = df.groupby("Region")["Sales"].sum().sort_values(ascending=False).head(5)
print("\nTop 5 customers by sales (by name):")
print(top_cust.round(0).to_string(index=False))
print("\nTop 5 products:", "; ".join(f"{n} ({v:,.0f})" for n, v in top_prod.items()))
print("Top 5 regions: ", "; ".join(f"{n} ({v:,.0f})" for n, v in top_reg.items()))

fig = make_subplots(rows=2, cols=2, specs=[[{"type": "choropleth"}, {"type": "bar"}], [{"type": "scatter"}, {"type": "table"}]],
                    subplot_titles=("Sales by country", "Profit by category", "Monthly revenue trend", "Top 5 customers"),
                    horizontal_spacing=0.13, vertical_spacing=0.14)
fig.add_trace(go.Choropleth(locations=by_country["Country"], locationmode="country names", z=by_country["Sales"], colorscale=[[0, "#dce9f5"], [1, C[0]]],
                            colorbar=dict(title="Sales", len=0.4, y=0.8), marker_line_width=0.3), row=1, col=1)
fig.add_trace(go.Bar(x=by_cat.values, y=by_cat.index, orientation="h", marker_color=[theme["bad"] if v < 0 else C[1] for v in by_cat.values]), row=1, col=2)
fig.add_trace(go.Scatter(x=monthly.index, y=monthly.values, mode="lines+markers", line=dict(color=C[0])), row=2, col=1)
fig.add_trace(go.Table(header=dict(values=["Customer", "Sales", "Profit"], fill_color=C[0], font=dict(color="white")),
                       cells=dict(values=[top_cust["Customer Name"], top_cust["Sales"].map("{:,.0f}".format), top_cust["Profit"].map("{:,.0f}".format)],
                                  font=dict(color=[theme["foreground"], theme["foreground"], [theme["bad"] if v < 0 else theme["good"] for v in top_cust["Profit"]]]),
                                  align=["left", "right", "right"])), row=2, col=2)
fig.update_layout(height=820, showlegend=False, template="simple_white", margin=dict(t=130, l=30, r=30, b=30),
                  width=1250,
                  title=dict(text=f"<b>Global Sales Dashboard</b><br><sup>Filters: {label}  |  Sales {sales:,.0f}  |  Profit {profit:,.0f} ({profit / sales:.1%} margin)  |  Average discount {avg_disc:.1%}</sup>",
                             x=0.1, y=0.97, xanchor="left", font=dict(color=C[0], size=22)),
                  images=[dict(source="data:image/png;base64," + logo_b64, xref="paper", yref="paper", x=0.0, y=1.19, sizex=0.07, sizey=0.12, xanchor="left", yanchor="top")])
fig.update_geos(showcountries=True, countrycolor="#bbbbbb", showcoastlines=False, showland=True, landcolor="#f2f2f2", projection_type="natural earth", showframe=False)
name = "dashboard" + ("_" + "_".join(str(v).replace(" ", "") for v in filters.values()) if filters else "")
fig.write_html(out / f"{name}.html", include_plotlyjs="cdn")
print(f"\nWrote output/{name}.html (opens in any browser; loads plotly.js from a CDN, so it needs internet access)")
