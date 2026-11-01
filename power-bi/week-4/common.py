"""Shared loading code for the Power BI weeks: downloads the Superstore workbook named in the briefs."""
import urllib.request
from pathlib import Path

import pandas as pd

URL = "https://github.com/hshariq/Global-Superstore-2016-Power-BI/raw/main/global_superstore_2016.xlsx"
CACHE = Path.home() / ".cache" / "skillnexis" / "global_superstore_2016.xlsx"


def workbook() -> Path:
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading the Superstore workbook (about 8 MB) to {CACHE} ...")
        urllib.request.urlretrieve(URL, CACHE)
    return CACHE


def load_orders() -> pd.DataFrame:
    df = pd.read_excel(workbook(), sheet_name="Orders", parse_dates=["Order Date", "Ship Date"])
    df["Year"] = df["Order Date"].dt.year
    return df


def load_people() -> pd.DataFrame:
    return pd.read_excel(workbook(), sheet_name="People")
