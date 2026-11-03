# IoT & C Embedded Programming — Week 2: Sensors & Communication

Bare-metal C for the **ATmega328P** (Arduino Uno, 16 MHz) with direct register access to the ADC, timers, UART and TWI (I2C), and no Arduino library. Everything is compiled with `avr-gcc -Wall -Wextra -Werror` and the logger **runs on a simulated ATmega328P in simavr**, with scripted sensor inputs, an echo pulse and a simulated second microcontroller on I2C.

| Brief item | Where | Evidence |
| --- | --- | --- |
| **Read an analog temperature sensor with the ADC, print on serial** | `firmware/hal.c` `adc_read()` (AVCC reference, /128 prescaler, discards the first sample after a mux change, averages 4); `sensors.c` `lm35_tenths_c()` | Unit tests; `results/sim-serial.log` column 2 |
| **Ultrasonic sensor distance in cm** | `ultrasonic_echo_us()`: 10 µs trigger on D7, echo on D8 timed with Timer1 at 0.5 µs resolution, 65 ms timeout for "nothing in range"; `echo_us_to_mm()` uses 343 m/s | Unit tests (10 cm, 20 cm, 4 m limit, timeout); simulated 80 cm and 6 cm targets |
| **I2C between two microcontrollers** | Master: `twi_read_regs()` at 100 kHz. Slave: `node/humidity_node.c`, an interrupt-driven TWI slave at `0x42` that serves humidity plus a **CRC-8** so a corrupted reading is rejected, not logged | In simulation the logger reads 55.2 %RH from the node, and logs `NA` when the node stops answering |
| **UART serial logger with timestamps** | 57600 8N1, interrupt-driven 128-byte transmit ring buffer, so the main loop never blocks on serial; Timer0 gives a 1 ms `millis()` | Every log line starts with the millisecond timestamp |
| **Mini project: temperature + distance + light logger with buzzer alerts** | `firmware/main.c` samples every 500 ms and prints `ms,temp_c,dist_cm,light_pct,humidity_pct,alerts`. Buzzer on D3 sounds while any alert is active. | 7 of 7 simulated scenarios pass (below) |

## Alerts, with hysteresis

| Flag | Turns on | Turns off | Why the gap |
| --- | --- | --- | --- |
| `H` hot | > 35.0 °C | < 34.0 °C | A temperature hovering at 35 °C would otherwise toggle the buzzer every sample |
| `N` near | < 10 cm | > 12 cm, or nothing in range | Same, for an object at the edge |
| `D` dark | < 20 % light | > 25 % | Same |
| `S` sensor fault | LM35 below 2 °C or above 150 °C | next good reading | Catches an unplugged sensor (A0 reads 0) |

## Simulation results (`make sim`)

`sim/harness.c` loads `build/logger.elf` into simavr, sets the analog voltages, answers each trigger pulse with an echo of the right width, plays the I2C humidity node, records the buzzer pin, and checks every log line. Full output: `results/sim-run.txt`, raw serial: `results/sim-serial.log`.

| Scenario (simulated time) | Inputs | Expected | Result |
| --- | --- | --- | --- |
| 0–2 s normal | 25 °C, 60 % light, 80 cm, 55.2 %RH | `-`, buzzer off | PASS (4/4 lines) |
| 2–4 s hot | 36.5 °C | `H`, buzzer on | PASS |
| 4–5 s cooling | 34.5 °C (reads 34.2, inside the band) | still `H` | PASS |
| 5–7 s object | 25 °C, object at 6 cm | `N` | PASS |
| 7–9 s dark | 10 % light | `D` | PASS |
| 9–11 s node offline | no I2C ACK, nothing in range | humidity `NA`, `-` | PASS |
| 11–12 s LM35 unplugged | A0 = 0 V | `S` | PASS |

The buzzer pin matched the alert column on all 24 lines, and the humidity column matched the node's value on every line.

```
# ms,temp_c,dist_cm,light_pct,humidity_pct,alerts
2006,36.2,80.0,60,56.0,H
5502,24.9,6.0,60,54.8,N
9007,24.9,NA,60,NA,-
11006,0.0,80.0,60,55.2,S
```

The 36.5 °C input reads 36.2 °C because the 10-bit ADC on a 5 V reference has 4.9 mV (0.49 °C) steps. Switching the LM35 to the internal 1.1 V reference would give 0.11 °C steps at the cost of a 110 °C ceiling.

**Two simulator quirks are handled in `twi_read_regs()`, with comments.** simavr 1.6 reports status `0x28` instead of `0x18` after SLA+W, and can repeat the START status before the SLA+R result arrives. The workarounds are no-ops on real hardware. The read is also split into two transactions (set the register, STOP, then read) instead of a repeated START, which the node firmware supports.

## Unit tests (`make test`)

`tests/test_sensors.c` runs the pure logic on the host with AddressSanitizer and UBSan: **34 checks, 0 failures**. They cover ADC→°C rounding, LDR clamping, echo→distance including the 4 m limit, every hysteresis edge, log formatting (including truncation without overflow) and the CRC-8/SMBUS check value `0xF4`. They found one real bug: a double rounding read 1.500 V as 150.1 °C. It is now fixed.

## Build size

| Firmware | Flash | RAM |
| --- | --- | --- |
| Logger | 2,930 B (8.9%) | 224 B (10.9%) |
| Humidity node | 626 B (1.9%) | 8 B (0.4%) |

## Wiring

| Logger Uno pin | Connects to |
| --- | --- |
| A0 | LM35 Vout (LM35 +Vs to 5 V, GND to GND) |
| A1 | LDR / 10 kΩ divider midpoint (LDR to 5 V, 10 kΩ to GND) |
| D7 / D8 | HC-SR04 TRIG / ECHO (VCC 5 V) |
| D3 | Active buzzer + (− to GND), with a transistor if it draws over 20 mA |
| A4 / A5 | Node Uno A4 / A5, **4.7 kΩ pull-ups to 5 V on both**, common GND |
| TX (D1) | USB serial → terminal at 57600 baud |

Node Uno: A0 to an analog humidity sensor (0–5 V = 0–100 %RH). For a DHT11 instead, replace the ADC read with the DHT single-wire protocol; the I2C side stays the same.

## Build and run

```sh
sudo apt install gcc-avr avr-libc simavr libsimavr-dev libelf-dev
make            # build/logger.hex and build/node.hex
make test       # host unit tests
make sim        # run the logger in simavr
avrdude -p m328p -c arduino -P /dev/ttyUSB0 -b 115200 -U flash:w:build/logger.hex   # flash a real Uno
```

CI (`.github/workflows/embedded.yml`) runs build, tests and simulation on every push.

**Not done here:** no physical board or sensors were used. To show it on hardware, flash both Unos, wire them as above, and capture the serial monitor and a photo.
