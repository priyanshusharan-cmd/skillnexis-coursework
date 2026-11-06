""""Stackr": a modular, 3D-printable desk organiser (PLA). A base rail plate takes three modules that slide on
60° dovetails: an angled phone stand with a cable pass-through, a hexagonal pen cup, and a sculpted pebble planter
(organic model, src/organic.py). Fully parametric (PARAMS); print-fit clearance is built into the dovetails."""
import math
import cadquery as cq
PARAMS = dict(base_l=210.0, base_w=96.0, base_t=9.0, corner_r=10.0, rail_pitch=68.0,
              dt_top=10.0, dt_depth=4.0, dt_angle=60.0, fit=0.25,                     # dovetail: narrow width at the top, depth, flank angle, print clearance
              stand_w=62.0, stand_d=80.0, stand_h=92.0, back_angle=65.0, lip_h=14.0, wall=3.2, cable_w=14.0,
              cup_af=60.0, cup_h=96.0, cup_wall=2.4, cup_floor=3.0, foot_h=6.0)
P = PARAMS
def dovetail_profile(top, depth, angle, grow=0.0):
    """Trapezoid (x, z): narrow at z = 0, widening with depth (the groove opens downward into the base top face)."""
    w_bot = top + 2 * depth / math.tan(math.radians(angle))
    t, b = top / 2 + grow, w_bot / 2 + grow
    return [(-t, 0), (t, 0), (b, -depth), (-b, -depth)]
def base(p=P):
    b = cq.Workplane("XY").box(p["base_l"], p["base_w"], p["base_t"], centered=(True, True, False)).edges("|Z").fillet(p["corner_r"]).faces(">Z").edges().fillet(1.2)
    for k in (-1, 0, 1):                                                     # three dovetail grooves running front to back (along Y)
        prof = [(x + k * p["rail_pitch"], z + p["base_t"]) for x, z in dovetail_profile(p["dt_top"], p["dt_depth"], p["dt_angle"])]
        b = b.cut(cq.Workplane("XZ").polyline(prof).close().extrude(p["base_w"] / 2 + 1, both=True))
    b = b.faces("<Z").workplane().pushPoints([(x, y) for x in (-90, 90) for y in (-35, 35)]).hole(10, 1.2)    # recesses for rubber feet
    return b
def key(length, p=P):
    """Dovetail key under a module: the groove profile (narrow at the module's bottom face, widening downward) shrunk by
    the print clearance on every flank, so it slides in and locks against lifting."""
    prof = dovetail_profile(p["dt_top"], p["dt_depth"] - p["fit"], p["dt_angle"], -p["fit"])
    return cq.Workplane("XZ").polyline(prof).close().extrude(length / 2, both=True).rotate((0, 0, 0), (0, 0, 1), 90).rotate((0, 0, 0), (0, 0, 1), -90)
def stand_profile(p=P):
    from shapely.geometry import Polygon
    d, h, a, t, tw, lip = p["stand_d"], p["stand_h"], math.radians(p["back_angle"]), 4.0, p["wall"] + .8, p["lip_h"]
    F0 = (-26.0, t); F1 = (F0[0] + (h - t) / math.tan(a), h); B1 = (F1[0] + tw / math.sin(a), h)
    outer = [(-d / 2, 0), (d / 2, 0), (d / 2, t), B1, F1, F0, (-34.0, t), (-34.0, lip), (-d / 2, lip)]
    wedge = Polygon([F0, (d / 2, t), B1, F1]); window = wedge.buffer(-5.0, join_style=2)          # lightening window, 5 mm webs all round
    return outer, list(window.exterior.coords)[:-1]
def phone_stand(p=P):
    """Angled phone stand: 65° back, front lip with a cable notch, open A-frame (back support + rear strut), dovetail key."""
    w = p["stand_w"]; outer, window = stand_profile(p)
    s = cq.Workplane("XZ").polyline(outer).close().extrude(w / 2, both=True)
    s = s.cut(cq.Workplane("XZ").polyline(window).close().extrude(w / 2 + 1, both=True))            # open A-frame (v2): v1 kept 6 mm side cheeks, see results/sim.json
    s = s.cut(cq.Workplane("XY").box(12, p["cable_w"], 20).translate((-37, 0, 4 + 10)))                 # cable notch in the lip
    s = s.rotate((0, 0, 0), (0, 0, 1), 90)                                                              # depth along Y, lip at the front (-Y)
    return s.union(key(p["stand_d"] * .8))
def pen_cup(p=P):
    af, h, wl = p["cup_af"], p["cup_h"], p["cup_wall"]; r = af / math.sqrt(3)
    c = cq.Workplane("XY").polygon(6, 2 * r).extrude(h).edges("|Z").fillet(4)
    c = c.cut(cq.Workplane("XY").workplane(offset=p["cup_floor"]).polygon(6, 2 * r - 2 * wl / math.cos(math.radians(30))).extrude(h).edges("|Z").fillet(2.5))
    c = c.faces(">Z").edges().fillet(.8)
    return c.union(key(af * .8))
