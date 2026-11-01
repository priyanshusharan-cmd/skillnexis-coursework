"""Week 4 capstone: end-to-end analysis case study on the financial sample dataset."""
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

here = Path(__file__).parent
out = here / "output"
out.mkdir(exist_ok=True)

# ---------- 1. Load and clean ----------
raw = pd.read_excel(here / "financial_sample.xlsx")
df = raw.copy()
df.columns = [c.strip() for c in df.columns]
checks = {
    "rows": len(df),
    "duplicate rows": int(df.duplicated().sum()),
    "missing Discount Band": int(df["Discount Band"].isna().sum()),
    "missing Units Sold": int(df["Units Sold"].isna().sum()),
}
df["Discount Band"] = df["Discount Band"].fillna("None")  # blank means no discount band applies
df = df.dropna(subset=["Units Sold"])
df["Date"] = pd.to_datetime(df["Date"])
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.to_period("M").astype(str)
# Consistency checks on the arithmetic in the data.
profit_ok = ((df["Sales"] - df["COGS"] - df["Profit"]).abs() < 1).mean()
sales_ok = ((df["Gross Sales"] - df["Discounts"] - df["Sales"]).abs() < 1).mean()
df["Margin"] = df["Profit"] / df["Sales"]

# ---------- 2. Analyse with SQL ----------
con = sqlite3.connect(":memory:")
df.assign(Date=df["Date"].dt.strftime("%Y-%m-%d")).to_sql("sales", con, index=False)
q = lambda sql: pd.read_sql_query(sql, con)
by_segment = q("SELECT Segment, SUM(Sales) AS sales, SUM(Profit) AS profit, ROUND(100.0*SUM(Profit)/SUM(Sales),1) AS margin_pct FROM sales GROUP BY Segment ORDER BY profit DESC")
by_country = q("SELECT Country, SUM(Sales) AS sales, SUM(Profit) AS profit FROM sales GROUP BY Country ORDER BY profit DESC")
by_product = q("SELECT Product, SUM([Units Sold]) AS units, SUM(Sales) AS sales, SUM(Profit) AS profit, ROUND(100.0*SUM(Profit)/SUM(Sales),1) AS margin_pct FROM sales GROUP BY Product ORDER BY profit DESC")
by_band = q("SELECT [Discount Band] AS band, COUNT(*) AS orders, SUM(Sales) AS sales, SUM(Profit) AS profit, ROUND(100.0*SUM(Profit)/SUM(Sales),1) AS margin_pct, ROUND(AVG([Units Sold]),0) AS avg_units FROM sales GROUP BY band ORDER BY margin_pct DESC")
by_year = q("SELECT Year, SUM(Sales) AS sales, SUM(Profit) AS profit FROM sales GROUP BY Year ORDER BY Year")
# The same question in pandas as a cross-check on the SQL result.
assert abs(by_segment["profit"].sum() - df["Profit"].sum()) < 1e-6
monthly = df.groupby("Month")[["Sales", "Profit"]].sum()

# ---------- 3. Visualise ----------
sns.set_theme(style="whitegrid")
fig, ax = plt.subplots(2, 3, figsize=(17, 9))
sns.barplot(data=by_segment, x="Segment", y="profit", ax=ax[0, 0], color="#3b78c4"); ax[0, 0].set_title("Profit by segment")
sns.barplot(data=by_country, y="Country", x="profit", ax=ax[0, 1], color="#2a9d8f"); ax[0, 1].set_title("Profit by country")
sns.barplot(data=by_product, y="Product", x="profit", ax=ax[0, 2], color="#e9a23b"); ax[0, 2].set_title("Profit by product")
ax[1, 0].plot(monthly.index, monthly["Sales"], marker="o", label="Sales"); ax[1, 0].plot(monthly.index, monthly["Profit"], marker="o", label="Profit")
ax[1, 0].set_title("Monthly sales and profit"); ax[1, 0].legend(); ax[1, 0].tick_params(axis="x", rotation=90, labelsize=7)
sns.barplot(data=by_band, x="band", y="margin_pct", ax=ax[1, 1], color="#c4513b"); ax[1, 1].set_title("Profit margin % by discount band")
avg_month = by_year.assign(avg=by_year["sales"] / df.groupby("Year")["Month"].nunique().values)
sns.barplot(data=avg_month, x="Year", y="avg", ax=ax[1, 2], color="#6a5acd"); ax[1, 2].set_title("Average monthly sales (2013 has 4 months)")
from matplotlib.ticker import FuncFormatter
millions = FuncFormatter(lambda v, _: f"{v/1e6:.1f}M")
for a in ax.ravel():
    a.set_xlabel(""); a.set_ylabel("")
    (a.xaxis if a in (ax[0, 1], ax[0, 2]) else a.yaxis).set_major_formatter(millions) if a is not ax[1, 1] else None
ax[0, 0].tick_params(axis="x", rotation=25)
fig.suptitle("Financial sample: business metrics", fontsize=15)
fig.tight_layout()
fig.savefig(out / "dashboard.png", dpi=120)

# Excel workbook with native Excel charts.
with pd.ExcelWriter(out / "report.xlsx", engine="xlsxwriter") as xl:
    tables = {"Segment": by_segment, "Country": by_country, "Product": by_product, "Discount band": by_band, "Year": by_year}
    for name, t in tables.items():
        t.to_excel(xl, sheet_name=name, index=False)
    wb = xl.book
    for name, t in tables.items():
        ws = xl.sheets[name]
        chart = wb.add_chart({"type": "column"})
        col = list(t.columns).index("profit") if "profit" in t.columns else list(t.columns).index("margin_pct")
        chart.add_series({"name": f"{name}: {t.columns[col]}", "categories": [name, 1, 0, len(t), 0], "values": [name, 1, col, len(t), col]})
        chart.set_title({"name": f"{name}: {t.columns[col]}"})
        ws.insert_chart(1, len(t.columns) + 1, chart)
        ws.set_column(0, len(t.columns) - 1, 16)

# ---------- 4. Report with figures computed from the data ----------
best_seg, worst_seg = by_segment.iloc[0], by_segment.iloc[-1]
top_c = by_country.iloc[0]
best_p, worst_p = by_product.iloc[0], by_product.iloc[-1]
hi_margin_band, lo_margin_band = by_band.iloc[0], by_band.iloc[-1]
months_per_year = df.groupby('Year')['Month'].nunique()
monthly_avg = by_year.set_index('Year')['sales'] / months_per_year
growth = (monthly_avg.iloc[-1] / monthly_avg.iloc[0] - 1) * 100
loss_makers = by_segment[by_segment['profit'] < 0]
loss_note = (' **' + ', '.join(loss_makers['Segment']) + ' loses money overall**, so its sales are not adding profit.') if len(loss_makers) else ''
units_lo, units_hi = by_band['avg_units'].min(), by_band['avg_units'].max()
inr = lambda v: f"{v:,.0f}"
report = f"""# End-to-end analysis: financial sample

## Data and cleaning
- {checks['rows']} rows, {len(raw.columns)} columns, {df['Date'].min():%b %Y} to {df['Date'].max():%b %Y}.
- Duplicate rows: {checks['duplicate rows']}. Blank `Discount Band`: {checks['missing Discount Band']} (read as "None", meaning no discount band applies). Rows with missing `Units Sold`: {checks['missing Units Sold']} (dropped).
- Consistency checks: `Sales - COGS = Profit` holds on {profit_ok:.1%} of rows, and `Gross Sales - Discounts = Sales` on {sales_ok:.1%}.
- Totals: sales {inr(df['Sales'].sum())}, profit {inr(df['Profit'].sum())}, overall margin {df['Profit'].sum()/df['Sales'].sum():.1%}.

## Findings
1. **Segments.** {best_seg['Segment']} earns the most profit ({inr(best_seg['profit'])}) and {worst_seg['Segment']} the least ({inr(worst_seg['profit'])}). Margins run from {by_segment['margin_pct'].min()}% to {by_segment['margin_pct'].max()}%.{loss_note} The highest margin ({by_segment.sort_values('margin_pct').iloc[-1]['Segment']}, {by_segment['margin_pct'].max()}%) sits on a small sales base ({inr(by_segment.sort_values('margin_pct').iloc[-1]['sales'])}), so it adds little total profit.
2. **Countries.** {top_c['Country']} leads on profit ({inr(top_c['profit'])}); {by_country.iloc[-1]['Country']} is last ({inr(by_country.iloc[-1]['profit'])}).
3. **Products.** {best_p['Product']} is the most profitable product ({inr(best_p['profit'])}, margin {best_p['margin_pct']}%); {worst_p['Product']} is the least ({inr(worst_p['profit'])}, margin {worst_p['margin_pct']}%).
4. **Discounts.** Orders in the "{hi_margin_band['band']}" band have the highest margin ({hi_margin_band['margin_pct']}%), and "{lo_margin_band['band']}" the lowest ({lo_margin_band['margin_pct']}%). Average units per order are similar across bands ({units_lo:.0f} to {units_hi:.0f}), so deeper discounts are not visibly bringing bigger orders in this data.
5. **Trend.** The data has {months_per_year.iloc[0]} months of {int(months_per_year.index[0])} and {months_per_year.iloc[-1]} months of {int(months_per_year.index[-1])}, so yearly totals are not comparable. Per month, average sales changed by {growth:+.0f}% between the two years (see the monthly chart).

## Recommendations
- Review pricing and discounting for the loss-making or lowest-margin segment and for the high-discount band, since those are where profit per sale is lowest.
- Check why the weakest country and product trail the leaders (volume, price or cost) before deciding whether to push or drop them.
- These numbers describe this sample only. They show association, not cause, so test any change before relying on it.

## Files
`output/dashboard.png` (six charts), `output/report.xlsx` (one sheet and native chart per table), and this report.
"""
(out / "REPORT.md").write_text(report)
print(report)
print("Tables:")
print(by_segment.to_string(index=False)); print(by_band.to_string(index=False)); print(by_year.to_string(index=False))
