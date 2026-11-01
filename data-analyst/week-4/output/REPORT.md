# End-to-end analysis: financial sample

## Data and cleaning
- 700 rows, 16 columns, Sep 2013 to Dec 2014.
- Duplicate rows: 0. Blank `Discount Band`: 53 (read as "None", meaning no discount band applies). Rows with missing `Units Sold`: 0 (dropped).
- Consistency checks: `Sales - COGS = Profit` holds on 100.0% of rows, and `Gross Sales - Discounts = Sales` on 100.0%.
- Totals: sales 118,726,350, profit 16,893,702, overall margin 14.2%.

## Findings
1. **Segments.** Government earns the most profit (11,388,173) and Enterprise the least (-614,546). Margins run from -3.1% to 73.1%. **Enterprise loses money overall**, so its sales are not adding profit. The highest margin (Channel Partners, 73.1%) sits on a small sales base (1,800,594), so it adds little total profit.
2. **Countries.** France leads on profit (3,781,021); Mexico is last (2,907,523).
3. **Products.** Paseo is the most profitable product (4,797,438, margin 14.5%); Carretera is the least (1,826,805, margin 13.2%).
4. **Discounts.** Orders in the "None" band have the highest margin (21.9%), and "High" the lowest (9.1%). Average units per order are similar across bands (1569 to 1637), so deeper discounts are not visibly bringing bigger orders in this data.
5. **Trend.** The data has 4 months of 2013 and 12 months of 2014, so yearly totals are not comparable. Per month, average sales changed by +16% between the two years (see the monthly chart).

## Recommendations
- Review pricing and discounting for the loss-making or lowest-margin segment and for the high-discount band, since those are where profit per sale is lowest.
- Check why the weakest country and product trail the leaders (volume, price or cost) before deciding whether to push or drop them.
- These numbers describe this sample only. They show association, not cause, so test any change before relying on it.

## Files
`output/dashboard.png` (six charts), `output/report.xlsx` (one sheet and native chart per table), and this report.
