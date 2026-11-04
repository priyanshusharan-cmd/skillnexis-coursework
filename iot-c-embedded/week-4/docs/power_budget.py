"""Battery-life estimate from the simulated duty cycle (results/sim-run.txt) and datasheet currents.
Currents are typical datasheet values, not measurements; measure your own build with a USB power meter or
a uCurrent and replace them."""
import re

run = open("results/sim-run.txt").read()
m = re.search(r"(\d+) wake-ups, (\d+) waterings, pump ran (\d+) s, awake ([\d.]+)%", run)
wakes, waterings, pump_s, awake_pct = int(m[1]), int(m[2]), int(m[3]), float(m[4])
days = 3
awake_h = awake_pct / 100 * 24
pump_h = pump_s / days / 3600
sleep_h = 24 - awake_h

I_AWAKE = 120.0     # mA: ESP32 with WiFi on, averaged over connect + MQTT + sampling (bursts reach 400 mA)
I_PUMP = 400.0      # mA: 3-6 V submersible mini pump at 3.7 V
SLEEP = {
    "Bare ESP32-WROOM module (next PCB rev)": 0.010 + 0.040 + 0.010,   # chip deep sleep + LDO Iq + divider (3.7 V / 200 k)
    "DOIT DevKit, power LED removed": 1.0,                              # USB-UART + DevKit regulator leakage, varies by clone
    "DOIT DevKit as bought (LED on)": 8.0,
}
CELL_MAH = 3000 * 0.85   # 18650, 85 % usable

print(f"Duty cycle from the 3-day simulation: {wakes / days:.0f} wake-ups/day, awake {awake_pct:.2f} % "
      f"({awake_h * 60:.0f} min/day), pump {pump_s / days:.0f} s/day ({waterings / days:.1f} waterings/day)\n")
print("| Build | Awake mAh/day | Pump mAh/day | Sleep mAh/day | Total mAh/day | Days on one 18650 (no sun) |")
print("|---|---:|---:|---:|---:|---:|")
for name, i_sleep in SLEEP.items():
    a, p, s = I_AWAKE * awake_h, I_PUMP * pump_h, i_sleep * sleep_h
    total = a + p + s
    print(f"| {name} | {a:.1f} | {p:.1f} | {s:.1f} | {total:.1f} | {CELL_MAH / total:.0f} |")
solar = 1.0 * 4 * 0.75 / 3.7 * 1000   # 1 W panel, 4 peak-sun hours, 75 % charger + wiring efficiency
print(f"\nA 1 W 6 V panel gives about {solar:.0f} mAh/day at the cell on a 4-sun-hour day, several times the load, "
      "so the node runs indefinitely with a TP4056-class charger.")
