"""Draws the agri-node schematic (docs/schematic.png) with schemdraw.
Net names match hardware/make_pcb.py exactly, so the drawing and the PCB describe the same circuit."""
import matplotlib

matplotlib.use("Agg")
import schemdraw
import schemdraw.elements as elm

schemdraw.config(fontsize=11, lw=1.3)
with schemdraw.Drawing(show=False) as d:
    # ---------------- power: 1S Li-ion -> LDO -> +3V3
    d += elm.Label().at((0, 0)).label("POWER", fontsize=13, halign="left")
    d += (bat := elm.BatteryCell().up().at((0, -4)).label("J1\n1S Li-ion\n3.0-4.2 V", loc="bot"))
    d += elm.Line().up(0.5).at(bat.end)
    d += elm.Line().right(2)
    d += elm.Dot().label("BAT+", loc="top")
    batp = d.here
    d += elm.Line().right(1.5)
    d += (ldo := elm.Ic(pins=[elm.IcPin("VIN", side="left"), elm.IcPin("EN", side="left"), elm.IcPin("GND", side="bot"),
                              elm.IcPin("VOUT", side="right")], size=(2.2, 1.8)).anchor("VIN").label("U1 ME6211C33\n500 mA LDO", loc="top", ofst=0.3))
    d += elm.Line().at(ldo.EN).left(0.6)
    d += elm.Line().toy(ldo.VIN)                     # EN tied to VIN: always on
    d += elm.Line().at(ldo.VOUT).right(1.2)
    d += elm.Dot().label("+3V3", loc="top")
    v33 = d.here
    d += elm.Line().right(1.5)
    d += elm.Capacitor(polar=True).down().label("C3 470µ", loc="bot")
    d += elm.Ground()
    d += elm.Capacitor().down().at(v33).label("C2 10µ")
    d += elm.Ground()
    d += elm.Capacitor().down().at(batp).label("C1 10µ", loc="bot")
    d += elm.Ground()
    d += elm.Line().down(1).at(ldo.GND)
    d += elm.Ground()
    d += elm.Line().down(0.5).at(bat.start)
    d += elm.Ground()

    # ---------------- pump driver
    d += elm.Label().at((0, -7)).label("PUMP DRIVER (low-side N-MOSFET)", fontsize=13, halign="left")
    d += elm.Label().at((0.4, -8.5)).label("BAT+", halign="left")
    d += elm.Line().at((1.6, -8.5)).to((7, -8.5))
    d += elm.Motor().down(2.2).at((4, -8.5)).label("J2 pump\n3-6 V, <1 A", loc="top")
    d += elm.Dot().at((4, -10.7))
    d += elm.Diode().up(2.2).at((7, -10.7)).label("D1 SS14\nflyback", loc="bot")
    d += elm.Line().at((4, -10.7)).to((7, -10.7))
    d += (q := elm.NFet(bulk=False).reverse().anchor("drain").at((4, -10.7)).label("Q1\nAO3400A", loc="right", ofst=0.6))
    d += elm.Line().at(q.source).down(0.4)
    d += elm.Ground()
    d += elm.Resistor().at(q.gate).left(2.6).label("R1 100Ω")
    d += (g := elm.Dot())
    d += elm.Line().left(0.8)
    d += elm.Label().label("IO26", loc="left")
    d += elm.Resistor().down(2.2).at(g.center).label("R2 100k", loc="bot")
    d += elm.Ground()

    # ---------------- sensing
    d += elm.Label().at((13, 0)).label("SENSORS AND INPUTS", fontsize=13, halign="left")
    d += elm.Label().at((13.5, -1.2)).label("BAT+", halign="left")
    d += elm.Resistor().down().at((14.3, -1.5)).label("R3 100k")
    d += (vs := elm.Dot())
    d += elm.Line().right(2.4)
    d += elm.Label().label("IO33 (VBAT/2)", loc="right")
    d += elm.Resistor().down().at(vs.center).label("R4 100k")
    d += elm.Ground()
    d += elm.Line().at(vs.center).right(1.2)
    d += elm.Capacitor().down(2.0).label("C4 100n", loc="bot")
    d += elm.Ground()

    d += elm.Label().at((19.5, -1.2)).label("+3V3", halign="left")
    d += elm.Photoresistor().down().at((20.2, -1.5)).label("LDR (J4)")
    d += (lv := elm.Dot())
    d += elm.Line().right(1.2)
    d += elm.Label().label("IO36", loc="right")
    d += elm.Resistor().down().at(lv.center).label("R5 10k")
    d += elm.Ground()

    d += elm.Label().at((13.2, -8.3)).label("J3 soil probe: 1 IO34 (AOUT)  2 GND  3 IO32 (probe power)", halign="left")
    d += elm.Label().at((13.2, -9.1)).label("J5 float switch: IO27 to GND (closed = water)", halign="left")
    d += elm.Label().at((13.2, -9.9)).label("SW1 wake/water: IO25 to GND (RTC ext0 wake-up)", halign="left")
    d += elm.Label().at((13.2, -10.7)).label("J6 BME280, J7 OLED: +3V3  GND  SCL=IO22  SDA=IO21", halign="left")
    d += elm.Label().at((13.2, -11.5)).label("U2 ESP32 DevKit (DOIT 30-pin): powered on its 3V3 pin from U1", halign="left")

d.save("../docs/schematic.svg")
d.save("../docs/schematic.png", dpi=110)
print("saved")
