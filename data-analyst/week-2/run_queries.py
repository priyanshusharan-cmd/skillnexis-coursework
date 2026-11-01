"""Load orders.xlsx into an in-memory SQLite database, run queries.sql and print each result."""
import re
import sqlite3
from pathlib import Path

import pandas as pd

here = Path(__file__).parent
orders = pd.read_excel(here / "orders.xlsx")
orders["order_date"] = pd.to_datetime(orders["order_date"]).dt.strftime("%Y-%m-%d")

# Data checks before querying: the totals should equal quantity x unit price.
mismatch = (orders["quantity"] * orders["unit_price"] != orders["total_price"]).sum()
print(f"{len(orders)} orders, {orders['customer_name'].nunique()} customers, "
      f"{orders['order_date'].min()} to {orders['order_date'].max()}, rows where total != qty*price: {mismatch}")

con = sqlite3.connect(":memory:")
orders.to_sql("orders", con, index=False)

statements = [s.strip() for s in (here / "queries.sql").read_text().split(";") if s.strip()]
for stmt in statements:
    title = [l for l in stmt.splitlines() if l.startswith("--")][-1].lstrip("- ").strip()
    print(f"\n## {title}")
    print(pd.read_sql_query(re.sub(r"^--.*$", "", stmt, flags=re.M), con).to_string(index=False))
