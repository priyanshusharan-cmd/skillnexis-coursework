"""Generates hardware/agri-node.kicad_pcb with KiCad's pcbnew Python API (KiCad 7).

Board: 85 x 62 mm, 2 layers. A carrier for a 30-pin ESP32 DevKit (DOIT V1) with the pump driver,
3.3 V LDO for a 1-cell Li-ion battery, battery-voltage divider, button and sensor connectors.
GND is a copper pour on both layers; every signal track is placed explicitly below.

  python3 make_pcb.py            (then: kicad-cli pcb drc agri-node.kicad_pcb)
"""
import pcbnew
from pcbnew import FromMM as mm, VECTOR2I

LIB = "/usr/share/kicad/footprints/"
board = pcbnew.BOARD()
nets = {}


def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n
    return nets[name]


def P(x, y):
    return VECTOR2I(mm(x), mm(y))


def place(lib, name, ref, value, x, y, rot=0, pad_nets=None):
    fp = pcbnew.FootprintLoad(LIB + lib + ".pretty", name)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(P(x, y))
    if rot:
        fp.SetOrientationDegrees(rot)
    board.Add(fp)
    for pad in fp.Pads():
        if pad_nets and pad.GetNumber() in pad_nets:
            pad.SetNet(net(pad_nets[pad.GetNumber()]))
    fp.Value().SetVisible(False)
    return fp


def pad_xy(fp, number, index=0):
    pads = [p for p in fp.Pads() if p.GetNumber() == number]
    p = pads[index].GetPosition()
    return round(pcbnew.ToMM(p.x), 3), round(pcbnew.ToMM(p.y), 3)


def track(netname, pts, width=0.3, layer=pcbnew.F_Cu):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(P(x1, y1))
        t.SetEnd(P(x2, y2))
        t.SetWidth(mm(width))
        t.SetLayer(layer)
        t.SetNet(net(netname))
        board.Add(t)


def via(netname, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(x, y))
    v.SetDrill(mm(0.4))
    v.SetWidth(mm(0.8))
    v.SetNet(net(netname))
    board.Add(v)


def text(s, x, y, size=1.0, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(P(x, y))
    t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    board.Add(t)


B = pcbnew.B_Cu
W, H = 85, 62

# ---------------------------------------------------------------- outline and mounting holes
for (x1, y1), (x2, y2) in [((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))]:
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(x1, y1))
    s.SetEnd(P(x2, y2))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(0.1))
    board.Add(s)
for i, (x, y) in enumerate([(4, 4), (81, 4), (4, 58), (81, 58)]):
    place("MountingHole", "MountingHole_3.2mm_M3", f"H{i+1}", "M3", x, y)

# ---------------------------------------------------------------- ESP32 DevKit sockets (DOIT 30-pin, rows 22.86 mm apart)
LEFT = {"2": "IO36", "4": "IO34", "6": "IO32", "7": "IO33", "8": "IO25", "9": "IO26", "10": "IO27", "14": "GND"}
RIGHT = {"2": "SCL", "5": "SDA", "14": "GND", "15": "+3V3"}
JL = place("Connector_PinSocket_2.54mm", "PinSocket_1x15_P2.54mm_Vertical", "U2A", "ESP32 DevKit left", 30, 6, pad_nets=LEFT)
JR = place("Connector_PinSocket_2.54mm", "PinSocket_1x15_P2.54mm_Vertical", "U2B", "ESP32 DevKit right", 52.86, 6, pad_nets=RIGHT)
row = lambda i: 6 + 2.54 * i  # y of socket pin i (0-based)

# ---------------------------------------------------------------- left-side sensors: one straight lane per GPIO row
place("Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical", "J4", "LDR", 9.5, 6, pad_nets={"1": "+3V3", "2": "IO36"})
track("IO36", [(9.5, row(1)), (30, row(1))])
R5 = place("Resistor_SMD", "R_0805_2012Metric", "R5", "10k", 18, 10.0, rot=270, pad_nets={"1": "IO36", "2": "GND"})
r5_io, r5_gnd = pad_xy(R5, "1"), pad_xy(R5, "2")
assert r5_io[1] < r5_gnd[1], "R5 pad 1 must face the IO36 lane"
track("IO36", [r5_io, (18, row(1))])
track("GND", [r5_gnd, (19.8, r5_gnd[1])])
via("GND", 19.8, r5_gnd[1])

place("Connector_PinHeader_2.54mm", "PinHeader_1x03_P2.54mm_Vertical", "J3", "SOIL", 8, row(3),
      pad_nets={"1": "IO34", "2": "GND", "3": "IO32"})
track("IO34", [(8, row(3)), (30, row(3))])
track("IO32", [(8, row(5)), (30, row(5))])

track("IO33", [(30, row(6)), (8, row(6)), (8, 44)])                 # battery sense lane, down to the divider
track("IO25", [(30, row(7)), (13, row(7)), (13, 34), (9.5, 34)])    # button lane
track("IO26", [(30, row(8)), (18, row(8)), (18, 46.05)])            # pump gate lane

place("Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical", "J5", "FLOAT", 23, row(9), pad_nets={"1": "IO27", "2": "GND"})
track("IO27", [(23, row(9)), (30, row(9))])

place("Button_Switch_THT", "SW_PUSH_6mm", "SW1", "WAKE/WATER", 3, 34, pad_nets={"1": "IO25", "2": "GND"})
track("IO25", [(3, 34), (9.5, 34)], layer=B)   # both "1" pads, joined on the bottom layer

# ---------------------------------------------------------------- battery divider (BAT+ / 2 -> IO33) with filter cap
place("Resistor_SMD", "R_0805_2012Metric", "R3", "100k", 6, 44, pad_nets={"1": "BAT+", "2": "IO33"})
R4 = place("Resistor_SMD", "R_0805_2012Metric", "R4", "100k", 10, 44, pad_nets={"1": "IO33", "2": "GND"})
track("IO33", [(6.91, 44), (9.09, 44)])
track("GND", [(10.91, 44), (12.0, 44)])
via("GND", 12.0, 44)
place("Capacitor_SMD", "C_0805_2012Metric", "C4", "100n", 8, 47, rot=-90, pad_nets={"1": "IO33", "2": "GND"})
track("IO33", [(8, 44), (8, 46.09)])
track("GND", [(8, 47.91), (8, 49.3)])
via("GND", 8, 49.3)

# ---------------------------------------------------------------- power in, pump driver
place("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal", "J1", "BAT 1S Li-ion", 12, 56,
      pad_nets={"1": "BAT+", "2": "GND"})
place("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal", "J2", "PUMP", 41, 56,
      pad_nets={"1": "BAT+", "2": "PUMP-"})
track("BAT+", [(12, 56), (12, 52)], width=0.8)
track("BAT+", [(5.09, 44), (5.09, 52), (32, 52), (32, 51)], width=0.8)

R1 = place("Resistor_SMD", "R_0805_2012Metric", "R1", "100R", 26, 46.05, pad_nets={"1": "IO26", "2": "GATE"})
track("IO26", [(18, 46.05), (25.09, 46.05)])
Q1 = place("Package_TO_SOT_SMD", "SOT-23", "Q1", "AO3400A", 36, 47, pad_nets={"1": "GATE", "2": "GND", "3": "PUMP-"})
track("GATE", [(26.91, 46.05), (35.06, 46.05)])
place("Resistor_SMD", "R_0805_2012Metric", "R2", "100k", 33.5, 43.9, pad_nets={"1": "GATE", "2": "GND"})
track("GATE", [(32.59, 43.9), (32.59, 46.05)])
track("GND", [(34.41, 43.9), (35.9, 43.9)])
via("GND", 35.9, 43.9)
track("GND", [(35.06, 47.95), (33.4, 47.95)], width=0.6)
via("GND", 33.4, 47.95)
place("Diode_SMD", "D_SMA", "D1", "SS14", 34, 51, pad_nets={"1": "BAT+", "2": "PUMP-"})   # flyback: K to BAT+
track("PUMP-", [(36.94, 47), (39, 47), (39, 51), (46, 51), (46, 56)], width=0.8)
track("PUMP-", [(36, 51), (39, 51)], width=0.8)
track("BAT+", [(41, 52), (41, 56)], width=0.8, layer=B)                 # pump + from the bottom-layer BAT+ run

# ---------------------------------------------------------------- 3.3 V LDO (ME6211C33 / AP2112K-3.3 pinout, 500-600 mA)
track("BAT+", [(32, 52), (60.5, 52)], width=0.8, layer=B)
via("BAT+", 32, 52)
via("BAT+", 60.5, 52)
place("Package_TO_SOT_SMD", "SOT-23-5", "U1", "ME6211C33", 64, 50, pad_nets={"1": "BAT+", "2": "GND", "3": "BAT+", "5": "+3V3"})
track("BAT+", [(60.5, 52), (60.5, 49.05), (62.86, 49.05)], width=0.8)
track("BAT+", [(60.5, 50.95), (62.86, 50.95)])                       # EN tied high
track("BAT+", [(60.5, 49.05), (60.5, 46.5)], width=0.8)
place("Capacitor_SMD", "C_0805_2012Metric", "C1", "10u", 61, 46.5, pad_nets={"1": "BAT+", "2": "GND"})
track("GND", [(61.91, 46.5), (63.2, 46.5)])
via("GND", 63.2, 46.5)
track("+3V3", [(65.14, 49.05), (66.5, 49.05), (66.5, 44.5)], width=0.6)
place("Capacitor_SMD", "C_0805_2012Metric", "C2", "10u", 68.5, 47, pad_nets={"1": "+3V3", "2": "GND"})
track("+3V3", [(66.5, 47), (67.59, 47)])
track("GND", [(69.41, 47), (70.8, 47)])
via("GND", 70.8, 47)
place("Capacitor_SMD", "CP_Elec_6.3x5.8", "C3", "470u", 72, 53, pad_nets={"1": "+3V3", "2": "GND"})
track("+3V3", [(66.5, 49.05), (66.5, 53), (69.3, 53)], width=0.6)
track("+3V3", [(66.5, 44.5), (52.86, 44.5), (52.86, 41.56)], width=0.6)  # to the DevKit 3V3 pin
via("+3V3", 66.5, 44.5)

# ---------------------------------------------------------------- I2C headers (BME280, OLED) on the right edge
place("Connector_PinHeader_2.54mm", "PinHeader_1x04_P2.54mm_Vertical", "J6", "BME280", 80, 14,
      pad_nets={"1": "+3V3", "2": "GND", "3": "SCL", "4": "SDA"})
place("Connector_PinHeader_2.54mm", "PinHeader_1x04_P2.54mm_Vertical", "J7", "OLED", 80, 26,
      pad_nets={"1": "+3V3", "2": "GND", "3": "SCL", "4": "SDA"})
track("SCL", [(52.86, row(1)), (83, row(1)), (83, 31.08), (80, 31.08)])
track("SCL", [(83, 19.08), (80, 19.08)])
track("SDA", [(52.86, row(4)), (76, row(4)), (76, 33.62), (80, 33.62)])
track("SDA", [(76, 21.62), (80, 21.62)])
track("+3V3", [(80, 14), (78, 14), (78, 44.5), (66.5, 44.5)], width=0.5, layer=B)
track("+3V3", [(80, 26), (78, 26)], width=0.5, layer=B)
# 3V3 for the LDR header, on the bottom layer under the DevKit and between two socket pins
track("+3V3", [(52.86, 41.56), (41, 41.56), (41, 7.27), (12, 7.27), (12, 6), (9.5, 6)], width=0.3, layer=B)

# ---------------------------------------------------------------- GND pours, antenna keep-out
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net("GND"))
    z.SetLocalClearance(mm(0.3))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)]:
        ol.Append(mm(x), mm(y))
    board.Add(z)
ko = pcbnew.ZONE(board)
ko.SetIsRuleArea(True)
ko.SetDoNotAllowCopperPour(True)
ko.SetDoNotAllowTracks(True)
ko.SetDoNotAllowVias(True)
ko.SetLayerSet(pcbnew.LSET(pcbnew.F_Cu).AddLayer(pcbnew.B_Cu))
ol = ko.Outline()
ol.NewOutline()
for x, y in [(27, 0), (56, 0), (56, 4.6), (27, 4.6)]:
    ol.Append(mm(x), mm(y))
board.Add(ko)
for x, y in [(20, 38), (65, 30), (70, 58), (24, 47.5), (75, 40), (60, 10), (16, 30), (55, 56)]:  # stitching
    via("GND", x, y)

# ---------------------------------------------------------------- silkscreen
text("SMART AGRI NODE v1.0", 64, 59.5, 1.2)
text("ESP32 DEVKIT (DOIT 30-PIN) - ANTENNA THIS WAY", 41.4, 2.2, 0.8)
for s, x, y in [("LDR", 6.5, 9.5), ("SOIL", 3.6, 16), ("FLOAT", 23, 34), ("WATER", 6.2, 41.2), ("BAT 3.0-4.2V", 26, 49.6),
                ("PUMP", 43.5, 60.4), ("BME280", 74.5, 12.3), ("OLED", 75.5, 24.3), ("+  -", 14.5, 59.6)]:
    text(s, x, y, 0.9)

ds = board.GetDesignSettings()
ds.SetCopperLayerCount(2)
board.Save("agri-node.kicad_pcb")
# filling zones on a board built in memory crashes KiCad 7's standalone API; reloading from disk works
board = pcbnew.LoadBoard("agri-node.kicad_pcb")
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save("agri-node.kicad_pcb")
print("nets:", len(nets), "footprints:", len(board.GetFootprints()), "tracks+vias:", len(board.GetTracks()))
