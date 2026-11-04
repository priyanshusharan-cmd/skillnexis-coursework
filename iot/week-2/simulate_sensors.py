"""Generates the two SYNTHETIC datasets used this week (no real sensors were available).

1. data/env_raw.csv      one week of ESP32 + DHT11 + LDR readings, every minute, written the way a real
                         node's log looks: missing packets, duplicated rows, out-of-order rows, DHT11
                         glitch spikes, a stuck sensor, and an unplugged-sensor period.
2. data/machine_raw.csv  30 days of a motor's vibration (RMS, mm/s), bearing temperature and current,
                         every minute, with a bearing that starts wearing on day 18 and would fail on day
                         ~27, plus short transient faults. data/machine_labels.csv holds the ground truth.

Everything is seeded, so the files are reproducible:  python simulate_sensors.py
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)


def env_week():
    t = pd.date_range("2026-10-19 00:00", periods=7 * 24 * 60, freq="1min")
    hours = np.asarray(t.hour + t.minute / 60, dtype=float)
    day = np.asarray((t - t[0]).days)
    temp = 26 + 6 * np.sin((hours - 9) / 24 * 2 * np.pi) + 0.6 * np.sin(day / 7 * 2 * np.pi) + rng.normal(0, 0.25, len(t))
    temp[day == 3] -= 3 * np.clip(np.sin((hours[day == 3] - 6) / 12 * np.pi), 0, None)  # a rainy day
    hum = 68 - 1.8 * (temp - 26) + rng.normal(0, 1.0, len(t))
    light = np.clip(np.sin((hours - 6) / 12 * np.pi), 0, None) * 900 * np.where(day == 3, 0.35, 1) + rng.normal(0, 8, len(t))
    df = pd.DataFrame({"timestamp": t, "temp_c": temp.round(1), "humidity_pct": hum.round(0), "light_lux": np.clip(light, 0, None).round(0)})
    df["device_id"] = "esp32-garden-01"
    truth = np.zeros(len(df), dtype=int)

    spikes = rng.choice(len(df), 40, replace=False)               # DHT11 glitches: single wild readings
    df.loc[spikes, "temp_c"] = rng.choice([-40.0, 85.0, 0.0], 40)
    truth[spikes] = 1
    stuck = slice(4 * 1440 + 600, 4 * 1440 + 780)                 # 3 hours of a frozen humidity value
    df.loc[stuck, "humidity_pct"] = df.loc[4 * 1440 + 600, "humidity_pct"]
    truth[stuck] = 1
    unplug = slice(5 * 1440 + 200, 5 * 1440 + 260)                # LDR unplugged: reads 0 in daylight... at night
    df.loc[unplug, "light_lux"] = np.nan
    df["true_anomaly"] = truth

    drop = rng.random(len(df)) < 0.03                             # 3 % lost packets
    gap = (df.index >= 2 * 1440 + 900) & (df.index < 2 * 1440 + 945)  # 45-minute WiFi outage
    df = df[~drop & ~gap]
    dup = df.sample(150, random_state=1)                          # retransmitted packets
    df = pd.concat([df, dup])
    df = df.sample(frac=1, random_state=2).sort_values("timestamp", kind="stable")  # mostly ordered...
    swap = df.index[:: 997]
    df = pd.concat([df.drop(swap), df.loc[swap]])                 # ...with a few late arrivals at the end
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return df


def machine_month():
    t = pd.date_range("2026-09-01 00:00", periods=30 * 24 * 60, freq="1min")
    days = np.asarray((t - t[0]).total_seconds() / 86400)
    load = 0.75 + 0.2 * (np.sin(days * 2 * np.pi) > 0) + rng.normal(0, 0.02, len(t))      # two shifts
    wear = np.clip((days - 18) / 9, 0, None) ** 2.2                                       # bearing wear from day 18
    vib = 1.8 + 0.6 * load + 2.9 * wear + rng.normal(0, 0.12, len(t))                     # ISO 10816: >4.5 mm/s alarm
    temp = 48 + 9 * load + 14 * wear + rng.normal(0, 0.4, len(t))
    current = 11.0 * load + 0.9 * wear + rng.normal(0, 0.15, len(t))
    label = np.where(wear > 0.08, 1, 0)                                                   # "degrading"
    transients = rng.choice(len(t), 25, replace=False)                                    # e.g. a dropped tool, a voltage dip
    for i in transients:
        vib[i:i + 3] += rng.uniform(2.5, 4)
        current[i:i + 3] += rng.uniform(3, 6)
    df = pd.DataFrame({"timestamp": t, "vibration_rms_mm_s": vib.round(3), "bearing_temp_c": temp.round(2), "current_a": current.round(2)})
    labels = pd.DataFrame({"timestamp": t, "degrading": label, "transient": 0})
    for i in transients:
        labels.loc[i:i + 2, "transient"] = 1
    return df, labels


if __name__ == "__main__":
    env = env_week()
    env.to_csv("data/env_raw.csv", index=False)
    m, lab = machine_month()
    m.to_csv("data/machine_raw.csv", index=False)
    lab.to_csv("data/machine_labels.csv", index=False)
    print(f"env_raw.csv: {len(env)} rows  machine_raw.csv: {len(m)} rows  (synthetic, seed 7)")
