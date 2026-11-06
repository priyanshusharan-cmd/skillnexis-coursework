# Pipeline report

Source: `data/raw/chipotle.tsv`

| Step | Rows | Note |
|---|---|---|
| extract | 4,622 | 5 columns |
| drop unparseable prices | 4,622 | 0 removed |
| merge identical lines | 4,562 | 60 repeated lines (same order, item and options) merged into their first occurrence (quantity and price summed, so no revenue is lost) |
| normalise item names | 4,562 | 8 variants mapped |
| derive columns | 4,562 | options list, unit_price, outlier flag, category, protein |

## Output checks (all passed)

* order totals reconcile with line totals
* total revenue after cleaning equals the raw file's total (nothing lost by merging)
* item revenue reconciles with line totals
* every unit price is positive

## Results

```json
{
 "rows_in": 4622,
 "rows_out": 4562,
 "orders": 1834,
 "revenue": 34500.16,
 "avg_order": 18.81,
 "median_order": 16.2,
 "price_outliers": 0,
 "lines_without_options": 1227
}
```

## Top 8 items by revenue

| category   | item_name           |   lines |   quantity |   revenue |   avg_unit_price |
|:-----------|:--------------------|--------:|-----------:|----------:|-----------------:|
| Bowl       | Chicken Bowl        |     717 |        761 |   7342.73 |             9.66 |
| Burrito    | Chicken Burrito     |     546 |        591 |   5575.82 |             9.48 |
| Burrito    | Steak Burrito       |     365 |        386 |   3851.43 |             9.99 |
| Bowl       | Steak Bowl          |     210 |        221 |   2260.19 |            10.24 |
| Chips      | Chips and Guacamole |     474 |        506 |   2201.04 |             4.34 |
| Bowl       | Chicken Salad Bowl  |     119 |        132 |   1309.84 |             9.84 |
| Tacos      | Chicken Soft Tacos  |     111 |        120 |   1108.09 |             9.24 |
| Burrito    | Veggie Burrito      |      95 |         97 |    934.77 |             9.6  |

## Top 8 options

| option             |   times_chosen |   orders |
|:-------------------|---------------:|---------:|
| Rice               |           2371 |     1640 |
| Cheese             |           2260 |     1563 |
| Lettuce            |           1724 |     1220 |
| Sour Cream         |           1697 |     1248 |
| Black Beans        |           1331 |     1013 |
| Fresh Tomato Salsa |           1033 |      761 |
| Guacamole          |           1030 |      790 |
| Fajita Vegetables  |            716 |      524 |
