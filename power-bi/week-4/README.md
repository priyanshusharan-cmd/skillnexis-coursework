# Power BI — Week 4: Dashboard Design & Publishing

**Power BI Desktop was not used, and nothing was published or shared.** Power BI Desktop is Windows-only and publishing to the Power BI Service needs your own account, so assignment item 4 (publish and share a link) is **not done**. The dashboard is built as a self-contained HTML page with Plotly from the brief's Global Superstore data, with the same visuals.

- **Four visuals:** sales by country (map), profit by category (bar), monthly revenue trend (line) and the top 5 customers (table, profit coloured green or red).
- **Filters:** `--year`, `--segment` and `--region`, for example `python3 dashboard.py --year 2014 --segment Consumer --region "Western Europe"`.
- **Logo and theme:** a placeholder "SN" monogram (no logo file was supplied) and the colours in `theme.json`. `theme.json` is a real Power BI theme file, so it can be imported with View → Themes → Browse for themes.
- **Project task:** KPIs for sales, profit and average discount are in the subtitle, and the console output also lists the top 5 products and regions.

Overall figures: sales 12,642,502, profit 1,467,457 (11.6% margin), average discount 14.3%. Top customers are counted by name. Open `output/dashboard.html` in a browser; it loads plotly.js from a CDN, so it needs internet access.

```
pip install pandas openpyxl plotly matplotlib
python3 dashboard.py
```
