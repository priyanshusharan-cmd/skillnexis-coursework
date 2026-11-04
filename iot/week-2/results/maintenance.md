## 3. Predictive maintenance (30 days of a motor, synthetic)

Healthy model: days 1-7. Bearing wear starts **21 Sep 20:32**; vibration reaches the ISO 10816 damage zone (7.1 mm/s) at **30 Sep 06:14**.

| Check | Result |
|---|---|
| First WARNING | 25 Sep 02:30 = **124 h before failure** (78 h after wear began) |
| First CRITICAL | 27 Sep 09:30 = 69 h before failure |
| False alerts during 18 healthy days (36 shift changes) | **0** |
| Transient spikes (25 injected) shown as events, not alerts | 27 of 27 flagged as transients, 0 raised an alert |

Remaining useful life (RUL) estimate vs truth:

| Asked at | True RUL | Estimated RUL | Error |
|---|---:|---:|---:|
| 96 h before failure | 96 h | 114 h | +18 h |
| 72 h before failure | 72 h | 76 h | +4 h |
| 48 h before failure | 48 h | 50 h | +2 h |
| 24 h before failure | 24 h | 34 h | +10 h |
| 12 h before failure | 12 h | 16 h | +4 h |
