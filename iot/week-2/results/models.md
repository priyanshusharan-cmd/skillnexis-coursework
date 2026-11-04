## 1. Anomaly detection (raw readings, scored against the injected faults)

Faults in the data: 214 readings (DHT11 spikes and a 3-hour frozen humidity sensor). Models are fitted on days 1-2 and the alert threshold is the 99.5th percentile of training scores, so no test labels are used to tune anything.

| Method | Precision | Recall | F1 | Alerts |
|---|---:|---:|---:|---:|
| Rolling z-score (temperature) | 0.49 | 0.17 | 0.26 | 76 |
| Isolation Forest (4 features) | 0.38 | 0.19 | 0.25 | 109 |
| Local Outlier Factor, novelty mode (4 features) | 0.86 | 0.94 | 0.90 | 235 |

**Why the Isolation Forest misses the frozen sensor:** a frozen sensor has a spread of exactly 0, lower than anything in the training days. An Isolation Forest only splits *within* the range it was trained on, so a value beyond that range lands in the same leaf as the lowest normal readings and gets an ordinary score. LOF measures distance to the nearest training neighbours, so the further outside the range a point is, the higher it scores, and it catches both the spikes and the frozen sensor.

## 2. Temperature 30 minutes ahead (linear regression)

Train: days 1-5 (1379 samples), test: days 6-7 (547 samples), 5-minute averages.

| Model | MAE (°C) |
|---|---:|
| Persistence ("same as now") | 0.519 |
| Linear regression | **0.115** |

The regression is 78% better than assuming nothing changes. The 30-minute slope and time-of-day features carry most of the signal:

| Feature | Coefficient |
|---|---:|
| cos_h | -0.497 |
| sin_h | +0.336 |
| temp_lag0 | +0.300 |
| temp_lag1 | +0.277 |
| temp_lag12 | -0.251 |
| temp_lag2 | +0.249 |
