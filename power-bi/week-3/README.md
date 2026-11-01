# Power BI — Week 3: DAX Functions & KPI Visuals

**Power BI Desktop was not used** (Windows only). `measures.dax` has the DAX measures from the brief (`Total Sales`, `Total Profit`, `Profit Margin` with `DIVIDE`) plus a `CALCULATE` example and a conditional-formatting colour measure, ready to paste into Power BI. `kpis.py` then computes each measure in pandas with the same logic, including `DIVIDE` returning blank when the denominator is zero, so the numbers can be checked against what Power BI shows.

- **KPI cards:** Total Sales, Total Profit and Profit Margin.
- **Slicers:** `--region`, `--year` and `--category`, which filter the same way slicers would.
- **Conditional formatting:** negative profit is red, including negative-profit sub-categories in the bar chart.
- **Retail dashboard:** cards, a monthly line chart, a category bar chart and a sub-category profit chart in `output/kpi_dashboard*.png`.

Numbers for the full dataset: sales 12,642,502, profit 1,467,457, margin 11.61%. The script checks that region-level totals add up to the overall total. For Central US in 2014 it gives sales 147,429, profit 19,899 and margin 13.50%.

The brief names a separate retail Excel file; its link points to the same Superstore workbook used in Week 4, which is what this uses.

```
pip install pandas matplotlib openpyxl
python3 kpis.py
python3 kpis.py --region "Central US" --year 2014
```
