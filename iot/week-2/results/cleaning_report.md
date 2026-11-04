# Cleaning report

Input: 9867 rows from `data/env_raw.csv` (synthetic, see `simulate_sensors.py`).

| Step | Rows / values |
|---|---:|
| Duplicate packets removed | 150 |
| Out-of-order rows re-sorted | 1 |
| Missing minutes (lost packets + outages) | 363 |
| temp_c: outside 0-50 | 23 |
| temp_c: Hampel spikes | 16 |
| humidity_pct: outside 20-90 | 0 |
| humidity_pct: Hampel spikes | 0 |
| light_lux: outside 0-2000 | 0 |
| light_lux: Hampel spikes | 0 |
| humidity_pct: stuck-sensor minutes (no change >= 30 min) | 176 |
| Values filled by time interpolation (gaps <= 5 min) | 1013 |
| Values left empty (gaps > 5 min, not invented) | 352 |

Injected glitches caught by the range/spike/stuck checks: **214 of 214** (100%); false flags on clean minutes: 1.

Output: `data/env_clean.csv` (10080 minutes on a regular grid), `data/env_15min.csv` (15-minute mean/min/max).
