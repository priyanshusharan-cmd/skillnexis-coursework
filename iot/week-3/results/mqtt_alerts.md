Replay of 200 cleaned 15-minute readings (~2 days) from week 2 at 45,000x speed through a local Mosquitto broker,
with two injected faults: a +6 °C spike at reading 60 and a 4-second WiFi drop halfway. Stale timeout set to 2 s for the demo.

| # | Alert | State | Message |
|---:|---|---|---|
| 1 | offline | raised | device offline (status topic or broker last-will) |
| 2 | offline | cleared | device back online |
| 3 | temp_c_high | raised | temp_c = 31.1 (limit 31.0) at 2026-10-19 12:45:00 |
| 4 | temp_rate | event | temperature changed +6.4 °C in 5 readings at 2026-10-19 15:00:00 |
| 5 | temp_c_high | cleared | temp_c back to 29.95 at 2026-10-19 18:15:00 |
| 6 | stale | raised | no telemetry for 2 s |
| 7 | stale | cleared | telemetry resumed |
| 8 | temp_c_high | raised | temp_c = 31.01 (limit 31.0) at 2026-10-20 12:15:00 |
| 9 | temp_c_high | cleared | temp_c back to 29.71 at 2026-10-20 18:45:00 |
| 10 | offline | raised | device offline (status topic or broker last-will) |

Every rule fired exactly when expected: the spike gave one rate-of-change event; the daily afternoon heat crossed 31 °C on both days and cleared below 30 °C (hysteresis, so no flapping at 30.9/31.1); the drop raised and cleared a stale alert; the device's offline status (retained, also used as its MQTT last-will) raised one offline alert. Natural temperature ramps never triggered the rate rule. Rows 1-2 are the retained `offline` status left on the broker by the previous run, delivered as soon as the alerter subscribed, then cleared when the device announced itself `online`: a restarted alerter learns device state immediately instead of waiting.
