"""Create a SYNTHETIC employee dataset (the Kaggle file was not downloaded).

The data is random with a fixed seed. It is not real employee data.
"""
import csv
import random

random.seed(2026)
departments = {"Engineering": (60000, 140000), "Sales": (35000, 90000), "HR": (32000, 70000), "Finance": (45000, 110000)}
first = ["Asha", "Ravi", "Meera", "Kabir", "Isha", "Arjun", "Neha", "Vikram", "Pooja", "Rohan"]
last = ["Rao", "Kumar", "Shah", "Iyer", "Singh", "Das", "Nair", "Mehta"]

with open("employees.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "name", "department", "salary", "years_experience"])
    for i in range(1, 101):
        dept = random.choice(list(departments))
        lo, hi = departments[dept]
        w.writerow([i, f"{random.choice(first)} {random.choice(last)}", dept, random.randrange(lo, hi, 500), random.randint(0, 20)])
