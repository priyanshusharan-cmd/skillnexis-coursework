"""Week 2 models on the cleaned sensor data.

1. Anomaly detection on the raw environmental readings: a rolling z-score baseline vs an Isolation Forest,
   both scored against the injected ground truth.
2. Linear regression that predicts temperature 30 minutes ahead, compared with the "no change" baseline,
   on a chronological train/test split (no shuffling: the future must not leak into training).

    python models.py   -> results/anomaly.png, results/forecast.png, results/models.md
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, precision_recall_fscore_support
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler

out = []

# ------------------------------------------------------------------ 1. anomaly detection on raw readings
raw = pd.read_csv("data/env_raw.csv", parse_dates=["timestamp"]).drop_duplicates(["timestamp"]).sort_values("timestamp").set_index("timestamp")
raw = raw.dropna(subset=["temp_c", "humidity_pct"])
feat = pd.DataFrame(index=raw.index)
for col in ["temp_c", "humidity_pct"]:
    feat[f"{col}_dev"] = (raw[col] - raw[col].rolling("30min").median()).abs()            # distance from recent behaviour
    feat[f"{col}_flat"] = np.log(raw[col].rolling("15min").std().fillna(1) + 0.05)        # a frozen sensor has zero spread
y = raw["true_anomaly"].astype(int)
train = feat[feat.index < feat.index[0] + pd.Timedelta(days=2)]           # every model is fitted on days 1-2 only
Q = 0.995   # alert above the 99.5th percentile of training scores, i.e. assume ~0.5 % glitches in training data

z = feat["temp_c_dev"] / feat["temp_c_dev"].rolling("6h").std().clip(lower=0.2)
pred_z = (z > 4).astype(int)

iso = IsolationForest(n_estimators=300, random_state=0).fit(train)
s_if, s_if_tr = -iso.score_samples(feat), -iso.score_samples(train)
pred_if = (s_if > np.quantile(s_if_tr, Q)).astype(int)

scaler = RobustScaler().fit(train)
lof = LocalOutlierFactor(n_neighbors=50, novelty=True).fit(scaler.transform(train))
s_lof, s_lof_tr = -lof.score_samples(scaler.transform(feat)), -lof.score_samples(scaler.transform(train))
pred_lof = (s_lof > np.quantile(s_lof_tr, Q)).astype(int)

rows = []
for name, p in [("Rolling z-score (temperature)", pred_z), ("Isolation Forest (4 features)", pred_if), ("Local Outlier Factor, novelty mode (4 features)", pred_lof)]:
    pr, rc, f1, _ = precision_recall_fscore_support(y, p, average="binary", zero_division=0)
    rows.append((name, pr, rc, f1, int(p.sum())))
out += ["## 1. Anomaly detection (raw readings, scored against the injected faults)", "",
        f"Faults in the data: {int(y.sum())} readings (DHT11 spikes and a 3-hour frozen humidity sensor). Models are fitted on days 1-2 "
        "and the alert threshold is the 99.5th percentile of training scores, so no test labels are used to tune anything.", "",
        "| Method | Precision | Recall | F1 | Alerts |", "|---|---:|---:|---:|---:|"] + [f"| {n} | {p:.2f} | {r:.2f} | {f:.2f} | {a} |" for n, p, r, f, a in rows]
out += ["", "**Why the Isolation Forest misses the frozen sensor:** a frozen sensor has a spread of exactly 0, lower than anything in "
        "the training days. An Isolation Forest only splits *within* the range it was trained on, so a value beyond that range lands in the "
        "same leaf as the lowest normal readings and gets an ordinary score. LOF measures distance to the nearest training neighbours, so the "
        "further outside the range a point is, the higher it scores, and it catches both the spikes and the frozen sensor.", ""]
pred_if = pred_lof   # the chart shows the best model

fig, ax = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
ax[0].plot(raw.index, raw["temp_c"], lw=0.5, color="#495057", label="raw temperature")
ax[0].scatter(raw.index[pred_if == 1], raw["temp_c"][pred_if == 1], s=12, color="#e03131", label="LOF anomaly", zorder=3)
ax[0].set_ylim(-45, 90)
ax[0].legend(loc="upper right", fontsize=8)
ax[0].set_ylabel("°C")
ax[1].plot(raw.index, raw["humidity_pct"], lw=0.5, color="#1c7ed6", label="raw humidity")
m = (pred_if == 1) & (feat["humidity_pct_flat"] < np.log(0.3))
ax[1].scatter(raw.index[m], raw["humidity_pct"][m], s=8, color="#e03131", label="flagged: frozen sensor", zorder=3)
ax[1].legend(loc="upper right", fontsize=8)
ax[1].set_ylabel("%RH")
fig.suptitle("Anomaly detection on one week of (synthetic) ESP32 + DHT11 readings")
fig.tight_layout()
fig.savefig("results/anomaly.png", dpi=100)

# ------------------------------------------------------------------ 2. 30-minute-ahead temperature forecast
df = pd.read_csv("data/env_clean.csv", parse_dates=["timestamp"], index_col="timestamp")[["temp_c", "humidity_pct", "light_lux"]]
d = df.resample("5min").mean()
H = 6                                                                      # 6 x 5 min = 30 minutes ahead
X = pd.DataFrame(index=d.index)
for lag in [0, 1, 2, 3, 6, 12]:
    X[f"temp_lag{lag}"] = d["temp_c"].shift(lag)
X["temp_slope_30m"] = d["temp_c"] - d["temp_c"].shift(6)
X["light"] = d["light_lux"]
X["hum"] = d["humidity_pct"]
hour = d.index.hour + d.index.minute / 60
X["sin_h"], X["cos_h"] = np.sin(2 * np.pi * hour / 24), np.cos(2 * np.pi * hour / 24)
target = d["temp_c"].shift(-H)
ok = X.notna().all(axis=1) & target.notna()
X, target = X[ok], target[ok]
split = X.index[0] + pd.Timedelta(days=5)                                  # days 1-5 train, days 6-7 test
Xtr, Xte, ytr, yte = X[X.index < split], X[X.index >= split], target[X.index < split], target[X.index >= split]
lr = LinearRegression().fit(Xtr, ytr)
pred = lr.predict(Xte)
mae_lr = mean_absolute_error(yte, pred)
mae_naive = mean_absolute_error(yte, Xte["temp_lag0"])
out += ["## 2. Temperature 30 minutes ahead (linear regression)", "",
        f"Train: days 1-5 ({len(Xtr)} samples), test: days 6-7 ({len(Xte)} samples), 5-minute averages.", "",
        "| Model | MAE (°C) |", "|---|---:|", f"| Persistence (\"same as now\") | {mae_naive:.3f} |", f"| Linear regression | **{mae_lr:.3f}** |", "",
        f"The regression is {100 * (1 - mae_lr / mae_naive):.0f}% better than assuming nothing changes. The 30-minute slope and time-of-day features carry most of the signal:", "",
        "| Feature | Coefficient |", "|---|---:|"] + [f"| {n} | {c:+.3f} |" for n, c in sorted(zip(X.columns, lr.coef_), key=lambda x: -abs(x[1]))[:6]]
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(yte.index, yte, label="actual (30 min later)", color="#212529", lw=1.2)
ax.plot(yte.index, pred, label=f"linear regression (MAE {mae_lr:.2f} °C)", color="#e8590c", lw=1.2, ls="--")
ax.set_ylabel("°C")
ax.legend()
ax.set_title("Predicted vs actual temperature, test days 6-7")
fig.tight_layout()
fig.savefig("results/forecast.png", dpi=100)

open("results/models.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
