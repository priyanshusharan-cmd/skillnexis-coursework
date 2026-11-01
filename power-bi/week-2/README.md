# Power BI — Week 2: Data Modeling & Relationships

**Power BI Desktop was not used.** It only runs on Windows, and this work was done on a Mac. Instead, `build_model.py` builds the same star schema from the brief's Superstore workbook and *checks* every relationship the way Power BI would enforce it, and `calendar.dax` has the DAX to rebuild it in Power BI Desktop. There is no `.pbix` file, so the "verify in Model View" step has to be done by opening Power BI and following the steps below.

## What the script builds and checks
| Brief item | Result |
| --- | --- |
| Orders → Customers (Customer ID) | many-to-one, key unique, 0 orphan rows |
| Orders → Products (Product ID) | many-to-one, key unique, 0 orphan rows |
| Orders → Regions (Region ID) | many-to-one, key unique, 0 orphan rows |
| Calendar table `CALENDAR(MIN(Orders[Order Date]), MAX(Orders[Order Date]))` | 1,461 days, 2012 to 2015, no gaps |
| Date hierarchy Year → Month → Day | columns in `calendar.dax` |

`output/star_schema.png` is the diagram and `output/relationship_checks.csv` the check results.

## Data problems the checks found
- **Region ID does not exist in the data.** The brief's Orders → Regions (Region ID) needs a key, so one is created. The first attempt failed 384 orders: Orders has a single region "Canada", but the People sheet has "Western Canada" and "Eastern Canada". The Regions table is built from the regions in Orders, and Canada carries both managers.
- **Customer ID is not one per person.** There are 17,415 customer IDs but only 796 customer names, so count customers by name.

## To rebuild in Power BI Desktop
1. Get Data → Excel → the Superstore workbook, and load Orders and People.
2. Create the dimension tables with Power Query (Remove duplicates on Customer ID, Product ID and Region), and add the Calendar table with the DAX in `calendar.dax`.
3. Model view: drag each key to Orders (one-to-many, single direction), then mark Calendar as a date table and create the Year → Month → Day hierarchy.

Run with `pip install pandas matplotlib openpyxl` and then `python3 build_model.py` (it downloads the ~8 MB workbook from the brief's GitHub link on first run).
