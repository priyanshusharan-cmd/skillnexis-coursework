# IoT & C Embedded Programming — Week 1

This week covers digital output, debounced inputs, bitwise port patterns, a timed traffic light, and a button-triggered digital dice. The sketch in `embedded_lab.ino` uses one menu selected at compile time so each exercise can be tried on an Arduino-compatible board.

## Wiring

- LED outputs: pins 2 through 8, each with a 220–330 Ω series resistor to GND.
- Button: pin 10 to GND; internal pull-up is enabled.
- Buzzer: optional active buzzer on pin 11 and GND.
- Use the board's documented logic voltage and disconnect power before rewiring.

No physical board was connected, so this is source code and a wiring plan, not a verified circuit. Select `LAB_MODE` in the sketch, upload with Arduino IDE or PlatformIO, and record board, port, and observed results for evidence.
