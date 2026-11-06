"""Task 4: data pipeline that extracts, validates, cleans, transforms and exports CSV data.
Input: data/raw/chipotle.tsv, 4,622 real order lines (public dataset from the DAT8 data-science course,
github.com/justmarkham/DAT8). It's messy in realistic ways: prices are text ("$2.39 " with trailing spaces), the
options are a bracketed string list, there are inconsistent item names ("Chips and Mild Fresh Tomato Salsa", bare
"Burrito"), exact duplicate lines and multi-quantity lines.
Steps: extract -> validate schema -> clean -> transform -> validate output -> export (+ a data-quality report).
    python src/pipeline.py [input] -> outputs/pipeline/*.csv, outputs/pipeline/report.md"""
import json, os, re, sys
import pandas as pd
SRC = sys.argv[1] if len(sys.argv) > 1 else "data/raw/chipotle.tsv"; OUT = "outputs/pipeline"; os.makedirs(OUT, exist_ok=True)
SCHEMA = {"order_id": "int64", "quantity": "int64", "item_name": "object", "choice_description": "object", "item_price": "object"}
# only mappings that are safe: "<protein> Salad" and "<protein> Salad Bowl" are the same menu item under two names; the bare names
# ("Burrito", "Bowl"...) have no protein recorded, so they're labelled as such rather than guessed
RENAME = {"Veggie Salad": "Veggie Salad Bowl", "Chicken Salad": "Chicken Salad Bowl", "Steak Salad": "Steak Salad Bowl", "Carnitas Salad": "Carnitas Salad Bowl",
          "Burrito": "Burrito (protein not recorded)", "Bowl": "Bowl (protein not recorded)", "Crispy Tacos": "Crispy Tacos (protein not recorded)", "Salad": "Salad Bowl (protein not recorded)"}
log = []
def step(name, df, note=""): log.append((name, len(df), note)); return df
# 1 extract
raw = pd.read_csv(SRC, sep="\t", dtype=str, keep_default_na=False); step("extract", raw, f"{raw.shape[1]} columns")
# 2 validate schema
missing = set(SCHEMA) - set(raw.columns); assert not missing, f"missing columns {missing}"
df = raw.copy()
# 3 clean
df["item_price"] = df["item_price"].str.strip().str.replace(r"^\$", "", regex=True)
bad_price = ~df["item_price"].str.fullmatch(r"\d+(\.\d{1,2})?"); df = step("drop unparseable prices", df[~bad_price], f"{int(bad_price.sum())} removed")
df["order_id"] = df["order_id"].astype(int); df["quantity"] = df["quantity"].astype(int); df["item_price"] = df["item_price"].astype(float)
df["choice_description"] = df["choice_description"].replace({"NULL": "", "nan": ""})
n0 = len(df)                                          # identical lines in one order = the same item bought again: merge, keep the revenue
df = df.groupby(["order_id", "item_name", "choice_description"], sort=False, as_index=False).agg(quantity=("quantity", "sum"), item_price=("item_price", "sum"))
df = step("merge identical lines", df, f"{n0 - len(df)} repeated lines (same order, item and options) merged into their first occurrence (quantity and price summed, so no revenue is lost)")
df["item_name"] = df["item_name"].str.strip().replace(RENAME); step("normalise item names", df, f"{len(RENAME)} variants mapped")
def options(s):
    """'[Fresh Tomato Salsa, [Rice, Cheese]]' -> ['Fresh Tomato Salsa', 'Rice', 'Cheese'] (nested brackets flattened)."""
    return [o.strip() for o in re.sub(r"[\[\]]", "", s).split(",") if o.strip()]
df["options"] = df["choice_description"].map(options); df["n_options"] = df["options"].map(len)
df["unit_price"] = (df["item_price"] / df["quantity"]).round(2)       # item_price is the LINE total
q1, q3 = df["unit_price"].quantile([.25, .75]); iqr = q3 - q1; df["price_outlier"] = (df["unit_price"] > q3 + 3 * iqr) | (df["unit_price"] < max(0, q1 - 3 * iqr))
df["category"] = df["item_name"].str.extract(r"(Burrito|Bowl|Tacos|Salad|Chips|Soda|Soft Drink|Water|Nectar|Izze|Drink)", expand=False).fillna("Other").replace(
    {"Soda": "Drink", "Soft Drink": "Drink", "Water": "Drink", "Nectar": "Drink", "Izze": "Drink", "Salad": "Bowl"})
df["protein"] = df["item_name"].str.extract(r"^(Chicken|Steak|Carnitas|Barbacoa|Veggie)", expand=False).fillna("—")
step("derive columns", df, "options list, unit_price, outlier flag, category, protein")
# 4 transform
lines = df.drop(columns=["choice_description"]).assign(options=lambda d: d["options"].map("; ".join))
orders = df.groupby("order_id").agg(lines=("item_name", "size"), items=("quantity", "sum"), total=("item_price", "sum"), categories=("category", lambda s: ", ".join(sorted(set(s))))).round(2).reset_index()
items = df.groupby(["category", "item_name"]).agg(lines=("order_id", "size"), quantity=("quantity", "sum"), revenue=("item_price", "sum"), avg_unit_price=("unit_price", "mean")).round(2).reset_index().sort_values("revenue", ascending=False)
opt = df.explode("options").dropna(subset=["options"]); opt = opt[opt["options"] != ""]
toppings = opt.groupby("options").agg(times_chosen=("order_id", "size"), orders=("order_id", "nunique")).sort_values("times_chosen", ascending=False).reset_index().rename(columns={"options": "option"})
# 5 validate output
assert orders["total"].sum().round(2) == round(df["item_price"].sum(), 2), "order totals don't reconcile with line totals"
assert (df["unit_price"] > 0).all() and df["order_id"].is_monotonic_increasing
assert items["revenue"].sum().round(2) == round(df["item_price"].sum(), 2)
assert round(df["item_price"].sum(), 2) == round(raw["item_price"].str.strip().str.lstrip("$").astype(float).sum(), 2), "revenue lost in cleaning"
# 6 export
lines.to_csv(f"{OUT}/order_lines_clean.csv", index=False); orders.to_csv(f"{OUT}/orders.csv", index=False); items.to_csv(f"{OUT}/items.csv", index=False); toppings.to_csv(f"{OUT}/options.csv", index=False)
q = dict(rows_in=len(raw), rows_out=len(df), orders=len(orders), revenue=round(df["item_price"].sum(), 2), avg_order=round(orders["total"].mean(), 2),
         median_order=round(orders["total"].median(), 2), price_outliers=int(df["price_outlier"].sum()), lines_without_options=int((df["n_options"] == 0).sum()))
L = ["# Pipeline report", "", f"Source: `{SRC}`", "", "| Step | Rows | Note |", "|---|---|---|"] + [f"| {a} | {b:,} | {c} |" for a, b, c in log]
L += ["", "## Output checks (all passed)", "", "* order totals reconcile with line totals", "* total revenue after cleaning equals the raw file's total (nothing lost by merging)", "* item revenue reconciles with line totals", "* every unit price is positive", "",
      "## Results", "", "```json", json.dumps(q, indent=1), "```", "", "## Top 8 items by revenue", "", items.head(8).to_markdown(index=False), "", "## Top 8 options", "", toppings.head(8).to_markdown(index=False)]
open(f"{OUT}/report.md", "w").write("\n".join(L) + "\n"); print("\n".join(L[:22]))
