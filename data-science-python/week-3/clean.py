"""Week 3: clean a messy dataset in pandas: handle missing values, filter rows, create new columns."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

here = Path(__file__).parent
raw = pd.read_csv(here / "messy_workouts.csv", dtype={"Date": "string"})
log = []
df = raw.copy()
df["row"] = df.index + 2  # line number in the CSV file, to refer back to the original

print("RAW DATA CHECK")
print(f"  rows: {len(df)}, missing per column: {df.isna().sum().to_dict()}")
print(f"  exact duplicate rows: {df.duplicated(subset=['Duration', 'Date', 'Pulse', 'Maxpulse', 'Calories']).sum()}")

# 1. Dates come in three shapes: '2020/12/01' (with quotes), 20201226, and missing.
d = df["Date"].str.strip("'").str.strip()
parsed = pd.to_datetime(d, format="%Y/%m/%d", errors="coerce")
parsed = parsed.fillna(pd.to_datetime(d, format="%Y%m%d", errors="coerce"))
df["Date"] = parsed
df["date_imputed"] = False
# The file is one row per day in order, so a missing date is the day between its neighbours.
for i in df.index[df["Date"].isna()]:
    prev, nxt = df["Date"].loc[:i].dropna().iloc[-1], df["Date"].loc[i:].dropna().iloc[0]
    if (nxt - prev).days == 2:
        df.loc[i, "Date"] = prev + pd.Timedelta(days=1)
        df.loc[i, "date_imputed"] = True
        log.append(f"row {df.loc[i, 'row']}: missing Date set to {df.loc[i, 'Date']:%Y-%m-%d} (the neighbours are two days apart)")
    else:
        log.append(f"row {df.loc[i, 'row']}: missing Date could not be inferred, row dropped")
df = df.dropna(subset=["Date"])

# 2. Exact duplicate rows.
dups = df.duplicated(subset=["Duration", "Date", "Pulse", "Maxpulse", "Calories"], keep="first")
for r in df.loc[dups, "row"]:
    log.append(f"row {r}: exact duplicate of the row before it, dropped")
df = df[~dups]

# 3. Duration outlier. Every other session is 30, 45 or 60 minutes, and the 450-minute row burns 253 kcal,
#    which matches a 45-minute session, so the value is treated as a typo with an extra zero.
q1, q3 = df["Duration"].quantile([0.25, 0.75])
fence = q3 + 1.5 * (q3 - q1)
for i in df.index[df["Duration"] > fence]:
    old = df.loc[i, "Duration"]
    if old % 10 == 0 and old / 10 in (30, 45, 60):
        df.loc[i, "Duration"] = old // 10
        log.append(f"row {df.loc[i, 'row']}: Duration {old} is above the outlier fence ({fence:.0f}); corrected to {old // 10}")
    else:
        log.append(f"row {df.loc[i, 'row']}: Duration {old} above the fence but no clear correction; kept")

# 4. Maxpulse can never be below the average Pulse, so a row where it is has the two values swapped.
bad = df["Maxpulse"] < df["Pulse"]
for i in df.index[bad]:
    df.loc[i, ["Pulse", "Maxpulse"]] = df.loc[i, ["Maxpulse", "Pulse"]].values
    log.append(f"row {df.loc[i, 'row']}: Pulse and Maxpulse were in the wrong order, swapped")

# 5. Missing Calories: estimate from the median calories per minute of the complete rows.
rate = (df["Calories"] / df["Duration"]).median()
for i in df.index[df["Calories"].isna()]:
    df.loc[i, "Calories"] = round(rate * df.loc[i, "Duration"], 1)
    log.append(f"row {df.loc[i, 'row']}: missing Calories estimated as {df.loc[i, 'Calories']} ({rate:.2f} kcal/min median x {df.loc[i, 'Duration']} min)")
df["calories_estimated"] = df["row"].isin(raw.index[raw["Calories"].isna()] + 2)

# New columns.
df["calories_per_min"] = (df["Calories"] / df["Duration"]).round(2)
df["pulse_reserve"] = df["Maxpulse"] - df["Pulse"]
df["weekday"] = df["Date"].dt.day_name()
df["intensity"] = pd.qcut(df["calories_per_min"], 3, labels=["Low", "Medium", "High"])

df = df.rename(columns=str.lower).drop(columns="row")
df["date"] = df["date"].dt.strftime("%Y-%m-%d")

print("\nCLEANING LOG")
print("\n".join("  " + l for l in log))

# Filter rows: the sessions of 45 minutes or more.
long_sessions = df[df["duration"] >= 45]
print(f"\nFILTER: {len(long_sessions)} of {len(df)} sessions last 45 minutes or more")
print("\nSUMMARY AFTER CLEANING")
print(df[["duration", "pulse", "maxpulse", "calories", "calories_per_min"]].describe().round(2).to_string())
print("\nAverage calories per minute by intensity:")
print(df.groupby("intensity", observed=True)["calories_per_min"].agg(["count", "mean"]).round(2).to_string())

df.to_csv(here / "clean_workouts.csv", index=False)
(here / "cleaning_log.txt").write_text("\n".join(log) + "\n")

sns.set_theme(style="whitegrid")
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
sns.lineplot(data=df.assign(date=pd.to_datetime(df["date"])), x="date", y="calories", marker="o", ax=ax[0])
ax[0].set(title="Calories per session, December 2020", xlabel="", ylabel="kcal")
ax[0].tick_params(axis="x", rotation=45)
sns.scatterplot(data=df, x="pulse", y="calories_per_min", hue="intensity", ax=ax[1])
ax[1].set(title="Average pulse vs calories per minute", xlabel="Average pulse", ylabel="kcal per minute")
fig.tight_layout()
fig.savefig(here / "workouts.png", dpi=130)
print("\nWrote clean_workouts.csv, cleaning_log.txt, workouts.png")
