# Power BI — Week 1

Import `sales.csv`, set Date to Date and numeric columns to Decimal/Whole Number in Power Query, then create measures:

```DAX
Total Revenue = SUMX(Sales, Sales[Quantity] * Sales[UnitPrice])
Total Profit = SUM(Sales[Profit])
Sales by Region = [Total Revenue]
```

Use a card for Total Revenue, a region bar chart for revenue, and a product bar chart filtered to Top N = 5 by Total Profit. The included CSV is synthetic because the course’s sample-data link was only a placeholder. Save the finished report as a `.pbix` after building it in Power BI Desktop; no `.pbix` is included because that application/data link was unavailable.
