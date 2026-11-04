Duty cycle from the 3-day simulation: 138 wake-ups/day, awake 1.45 % (21 min/day), pump 288 s/day (1.3 waterings/day)

| Build | Awake mAh/day | Pump mAh/day | Sleep mAh/day | Total mAh/day | Days on one 18650 (no sun) |
|---|---:|---:|---:|---:|---:|
| Bare ESP32-WROOM module (next PCB rev) | 41.8 | 32.0 | 1.4 | 75.2 | 34 |
| DOIT DevKit, power LED removed | 41.8 | 32.0 | 23.7 | 97.4 | 26 |
| DOIT DevKit as bought (LED on) | 41.8 | 32.0 | 189.2 | 263.0 | 10 |

A 1 W 6 V panel gives about 811 mAh/day at the cell on a 4-sun-hour day, several times the load, so the node runs indefinitely with a TP4056-class charger.
