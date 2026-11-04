"""A 2-person, 2-room home simulated minute by minute for 4 weeks: who is where, and what the sensors see.

Each room has a PIR motion sensor, a sound level sensor (dB), an ambient light sensor and a temperature
sensor, matching the ESP32 node in firmware/. Behaviour is what makes occupancy hard to sense:
  * weekdays: work 9-18 (one resident works from home on ~30 % of days), evenings at home, bed ~23:00
  * weekends: late wake-up, outings, sometimes an evening out
  * "still" time (TV, reading, at the desk, asleep) produces almost no PIR motion. A plain motion timer
    switches the lights off on people sitting still, which is the case the ML model has to get right.

    python sim/home.py        -> data/home_1min.csv (80,640 rows: 28 days x 1440 min x 2 rooms)
"""
import os

import numpy as np
import pandas as pd

ROOMS = ["living", "bedroom"]
DAYS = 28
START = pd.Timestamp("2026-10-05")          # a Monday


def person_day(rng, weekday, wfh):
    """1440 minutes of (location, activity). location: away/living/bedroom; activity: active/still/asleep."""
    loc = np.array(["bedroom"] * 1440, dtype=object)
    act = np.array(["asleep"] * 1440, dtype=object)

    def put(a, b, where, what):
        a, b = max(0, int(a)), min(1440, int(b))
        loc[a:b], act[a:b] = where, what

    wake = rng.normal(410 if weekday else 520, 15 if weekday else 30)
    bed = rng.normal(1385 if weekday else 1420, 20)
    put(wake, wake + rng.uniform(5, 15), "bedroom", "active")                  # getting up
    t = wake + 12
    if weekday and not wfh:
        leave, back = rng.normal(500, 12), rng.normal(1100, 35)
        put(t, leave, "living", "active")                                       # breakfast
        put(leave, back, "away", "away")
        t = back
    elif weekday:                                                               # work from home: long still desk spells
        while t < 1080:
            n = rng.uniform(40, 110)
            put(t, t + n, "living", "still")
            put(t + n, t + n + rng.uniform(5, 15), "living", "active")
            t += n + 10
    else:
        put(t, t + rng.uniform(60, 120), "living", "active")
        t = 600
        if rng.random() < 0.65:                                                 # weekend outing
            out = rng.uniform(660, 960)
            put(t, out, "living", rng.choice(["active", "still"]))
            t = out + rng.uniform(120, 300)
            put(out, t, "away", "away")
    while t < bed:                                                              # evening: cook, TV, short bedroom trips
        what = rng.choice(["active", "still", "still", "bedroom"])
        n = rng.uniform(10, 25) if what == "bedroom" else rng.uniform(15, 45) if what == "active" else rng.uniform(30, 120)
        put(t, min(t + n, bed), "bedroom" if what == "bedroom" else "living", "active" if what == "bedroom" else what)
        t += n
    if not weekday and rng.random() < 0.3:                                      # evening out
        s = rng.uniform(1140, 1230)
        put(s, min(bed, s + rng.uniform(150, 240)), "away", "away")
    put(bed - 20, bed, "bedroom", "active")
    put(bed, 1440, "bedroom", "asleep")
    return loc, act


def simulate(seed=7, days=DAYS):
    rng = np.random.default_rng(seed)
    rows = []
    indoor = {r: 28.0 for r in ROOMS}
    for d in range(days):
        day = START + pd.Timedelta(days=d)
        weekday = day.dayofweek < 5
        people = [person_day(rng, weekday, wfh=(i == 0 and weekday and rng.random() < 0.3)) for i in range(2)]
        cloud = rng.uniform(0.35, 1.0)
        t_mean, t_amp = rng.normal(29, 1.5), rng.uniform(3, 6)
        for m in range(1440):
            hour = m / 60
            t_out = t_mean + t_amp * np.sin((hour - 9) / 24 * 2 * np.pi)
            daylight = max(0.0, np.sin((hour - 6.2) / 12.3 * np.pi)) * 420 * cloud * rng.uniform(0.9, 1.1)
            for r in ROOMS:
                here = [act[m] for loc, act in people if loc[m] == r]
                n = len(here)
                awake = [a for a in here if a != "asleep"]
                # body heat and the room's lag behind the outdoor temperature
                indoor[r] += 0.02 * (t_out + 1.0 - indoor[r]) + 0.004 * n + rng.normal(0, 0.01)
                p_motion = 0.004 + (0.65 if "active" in awake else 0.12 if awake else 0.03 if n else 0)
                motion = int(rng.random() < p_motion)
                sound = 31 + 4 * (7 <= hour <= 21) + rng.normal(0, 2.5)                    # street noise
                if "active" in awake:
                    sound += rng.normal(13, 5)
                elif awake:
                    sound += rng.normal(17, 4) if r == "living" and hour > 18 else rng.normal(4, 3)   # TV vs reading
                if rng.random() < 0.01:
                    sound += rng.uniform(10, 25)                                           # dog bark, horn, delivery
                rows.append((day + pd.Timedelta(minutes=m), r, n, int(bool(awake)), "asleep" in here, motion,
                             round(sound, 1), round(daylight, 0), round(indoor[r] + rng.normal(0, 0.05), 2)))
    df = pd.DataFrame(rows, columns=["timestamp", "room", "occupants", "awake", "asleep", "motion", "sound_db", "daylight_lux", "temp_c"])
    df["occupied"] = (df.occupants > 0).astype(int)
    df["asleep"] = df.asleep.astype(int)
    return df


if __name__ == "__main__":
    df = simulate()
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/home_1min.csv", index=False)
    occ = df.groupby("room").occupied.mean()
    print(f"{len(df):,} rows. Occupied share: {occ.to_dict()}; minutes occupied with no motion in the last 10 min: "
          f"{((df.occupied == 1) & (df.groupby('room').motion.transform(lambda s: s.rolling(10, 1).sum()) == 0)).mean():.1%}")
