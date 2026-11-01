# Python Programming — Week 4: Capstone (Option 1, Employee Data Analysis)

Loads an employee CSV with pandas, reports the average salary and department counts, filters employees above a salary threshold and exports them to a new CSV.

**Data source:** the Kaggle employee dataset named in the brief was not downloaded. `generate_dataset.py` creates a synthetic 100-row `employees.csv` with a fixed random seed. The data is made up, and any figures printed are about that synthetic file only. To use real data, replace `employees.csv` with a file that has the same columns.

```
pip install pandas
python3 generate_dataset.py
python3 main.py            # optional: python3 main.py employees.csv 90000
```
