# Data Science with Python — Week 2

This course's Week 2 brief is the same as the Data Analyst course's Week 2 brief (the course site serves the same document for both), so this folder contains the same solution. Its details follow.


Assignment: query a sample database to find top customers and average order values.

- `orders.xlsx` is the sample data from the brief's Google Sheet (200 orders, Dec 2024 to Jun 2025).
- `queries.sql` has 7 queries: top customers, average order value overall and by region, revenue by category, a subquery for above-average customers, a `CASE` order-size band, a join against a per-region summary, and monthly revenue.
- `run_queries.py` loads the sheet into an in-memory SQLite database, runs every query and prints the results. Run it with `pip install pandas openpyxl` and then `python3 run_queries.py`.

Something to know about this data: all 200 customer names are different, so every customer has exactly one order. "Top customers" is therefore the largest single orders, and per-customer averages are the same as the order value. The script also checks that `total_price` equals `quantity × unit_price` for every row (it does).
