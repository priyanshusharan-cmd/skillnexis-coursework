"""Summarize a CSV without third-party libraries: python3 csv_summary.py sales.csv"""
import csv, sys
from collections import Counter
from decimal import Decimal, InvalidOperation
path = sys.argv[1] if len(sys.argv) > 1 else "sales.csv"
with open(path, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
if not rows:
    raise SystemExit("CSV has no data rows")
print(f"Rows: {len(rows)}")
print("Columns:", ", ".join(rows[0]))
for name in rows[0]:
    values = [r[name].strip() for r in rows if (r.get(name) or "").strip()]
    missing = len(rows) - len(values)
    print(f"\n{name}: {len(values)} non-empty, {missing} missing")
    try:
        nums = [Decimal(v) for v in values]
        print(f"  sum={sum(nums)} min={min(nums)} max={max(nums)}")
    except (InvalidOperation, ValueError):
        print("  common values:", Counter(values).most_common(5))
