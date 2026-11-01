"""Python Week 4 capstone, Option 1: Employee data analysis with pandas."""
import sys

import pandas as pd

THRESHOLD = 80000


def main(path="employees.csv", threshold=THRESHOLD):
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} employees from {path}")

    print(f"Average salary: {df['salary'].mean():,.2f}")
    print("Employees per department:")
    print(df["department"].value_counts().to_string())
    print("Average salary per department:")
    print(df.groupby("department")["salary"].mean().round(2).sort_values(ascending=False).to_string())

    high = df[df["salary"] > threshold].sort_values("salary", ascending=False)
    print(f"Employees above {threshold:,}: {len(high)}")
    print(high.head(5).to_string(index=False))

    high.to_csv("high_earners.csv", index=False)
    print("Wrote high_earners.csv")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0] if args else "employees.csv", int(args[1]) if len(args) > 1 else THRESHOLD)
