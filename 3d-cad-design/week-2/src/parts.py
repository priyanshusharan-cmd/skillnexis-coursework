"""Parametric parts for a 3-gear hand-cranked spur gear train (CadQuery). All dimensions in mm.
Every part is a function of the PARAMS dictionary, so changing one number (module, a tooth count, plate thickness)
regenerates every part, the assembly and the drawings consistently."""
import math
import cadquery as cq
PARAMS = dict(
    module=2.0, pressure_angle=20.0, backlash=0.10, face=10.0,      # gear set
    z_in=15, z_idler=25, z_out=40,                                  # tooth counts: drive pinion, idler, output
    shaft_d=8.0, shaft_len=74.0, input_extra=12.0, bore_clear=0.05, key_w=2.0, key_h=1.0,
    plate_t=6.0, plate_gap=36.0, plate_h=64.0, plate_margin=18.0, shaft_height=46.0,   # side plates
    base_l=200.0, base_w=80.0, base_t=8.0, mount_hole=5.5, fillet=3.0,
    hub_d=18.0, hub_len=6.0, collar_d=14.0, collar_len=5.0,
    crank_arm=40.0, crank_t=6.0, knob_d=14.0, knob_len=24.0,
)
P = PARAMS
def centres(p=P):
    """Shaft x-positions: centre distance a = m (z1 + z2) / 2 for each meshing pair (standard, no profile shift)."""
    m = p["module"]; a1 = m * (p["z_in"] + p["z_idler"]) / 2; a2 = m * (p["z_idler"] + p["z_out"]) / 2
    x0 = -(a1 + a2) / 2; return [x0, x0 + a1, x0 + a1 + a2], (a1, a2)

def involute_gear_profile(z, m, pa_deg=20.0, backlash=0.1, n_inv=14):
    """2D outline points of a standard involute spur gear (addendum m, dedendum 1.25 m, backlash on tooth thickness)."""
    pa = math.radians(pa_deg); r = m * z / 2; rb = r * math.cos(pa); ra = r + m; rf = r - 1.25 * m
    inv = lambda a: math.tan(a) - a
    s_half = (math.pi * m / 2 - backlash) / (2 * r)                    # half tooth angle at the pitch circle
    half_base = s_half + inv(pa)                                        # half tooth angle measured at the base circle
    r_start = max(rb, rf)
    def flank(sign):
        pts = []
        for k in range(n_inv + 1):
            rr = r_start + (ra - r_start) * (k / n_inv) ** 1.3
            phi = math.acos(min(1.0, rb / rr)); th = half_base - inv(phi)
            pts.append((rr, sign * th))
        return pts
    pts, pitch = [], 2 * math.pi / z
    for i in range(z):
        c = i * pitch
        right = [(rr, c - th) for rr, th in flank(1)]; left = [(rr, c + th) for rr, th in flank(1)][::-1]
        root_a = c - half_base - (pitch / 2 - half_base) if rf < rb else c - right[0][1]
        tooth = [(rf, c - half_base)] if rf < rb else []
        tooth += right
        tip0, tip1 = right[-1][1], left[0][1]
        tooth += [(ra, tip0 + (tip1 - tip0) * t / 4) for t in range(1, 4)]
        tooth += left
        if rf < rb: tooth += [(rf, c + half_base)]
        tooth += [(rf, c + half_base + (pitch - 2 * half_base) * t / 4) for t in range(1, 4)]   # root land
        pts += tooth
    return [(rr * math.cos(a), rr * math.sin(a)) for rr, a in pts]

def gear(z, p=P, hub=True):
    """Spur gear: involute teeth, hub, bore with keyway, lightening holes on larger gears."""
    m = p["module"]; prof = involute_gear_profile(z, m, p["pressure_angle"], p["backlash"])
    g = cq.Workplane("XY").polyline(prof).close().extrude(p["face"])
    rf = m * z / 2 - 1.25 * m
    if z >= 30:                                                          # web with lightening holes
        rim_in, hub_out = rf - 4, p["hub_d"] / 2 + 3
        g = g.cut(cq.Workplane("XY").workplane(offset=3).circle(rim_in).circle(hub_out).extrude(p["face"] - 3))
        rc = (rim_in + hub_out) / 2; d = min(rim_in - hub_out - 4, 16)
        g = g.cut(cq.Workplane("XY").polarArray(rc, 0, 360, 5).circle(d / 2).extrude(p["face"]))
    if hub: g = g.union(cq.Workplane("XY").workplane(offset=p["face"]).circle(p["hub_d"] / 2).extrude(p["hub_len"]))
    L = p["face"] + (p["hub_len"] if hub else 0); b = p["shaft_d"] / 2 + p["bore_clear"]
    g = g.cut(cq.Workplane("XY").circle(b).extrude(L))
    g = g.cut(cq.Workplane("XY").center(b + p["key_h"] / 2 - .2, 0).rect(p["key_h"] + .4, p["key_w"]).extrude(L))   # keyway
    return g

def shaft(p=P, extra=0.0):
    s = cq.Workplane("XY").circle(p["shaft_d"] / 2).extrude(p["shaft_len"] + extra).faces(">Z or <Z").chamfer(.5)
    return s

def side_plate(p=P):
    """Gearbox side plate (the dimensioned 'parametric sketch' part): rounded outline enclosing the three bores,
    bores at the exact centre distances, two mounting tabs with slots."""
    xs, _ = centres(p); h, t, mg = p["plate_h"], p["plate_t"], p["plate_margin"]
    L = xs[-1] - xs[0] + 2 * mg + 30
    sk = (cq.Sketch().push([(0, h / 2)]).rect(L, h).reset().vertices(">Y").fillet(14).reset())
    plate = cq.Workplane("XZ").placeSketch(sk).extrude(-t)            # plate lies in XZ, thickness along +Y
    bores = [(x, p["shaft_height"]) for x in xs]
    plate = plate.cut(cq.Workplane("XZ").pushPoints(bores).circle(p["shaft_d"] / 2 + .1).extrude(-t))
    plate = plate.cut(cq.Workplane("XZ").pushPoints([((xs[0] + xs[1]) / 2, 20), ((xs[1] + xs[2]) / 2, 20)]).slot2D(16, 7).extrude(-t))   # lightening slots
    return plate.edges("|Y").fillet(2)

def base_plate(p=P):
    b = cq.Workplane("XY").box(p["base_l"], p["base_w"], p["base_t"], centered=(True, True, False)).edges("|Z").fillet(p["fillet"] * 2)
    b = b.faces(">Z").workplane().rect(p["base_l"] - 20, p["base_w"] - 20, forConstruction=True).vertices().hole(p["mount_hole"])
    return b

def collar(p=P):
    return cq.Workplane("XY").circle(p["collar_d"] / 2).circle(p["shaft_d"] / 2 + .05).extrude(p["collar_len"]).faces(">Z or <Z").edges().chamfer(.4)

def crank(p=P):
    """Hand crank: arm with a blind-bored hub on the input shaft (pinned), and a fluted grip."""
    a = p["crank_arm"]; t = p["crank_t"]
    arm = cq.Workplane("XY").slot2D(a + 16, 16, 0).extrude(t).translate((a / 2, 0, 0))
    hub = cq.Workplane("XY").circle(8).circle(p["shaft_d"] / 2 + .05).extrude(-8)
    knob = cq.Workplane("XY").center(a, 0).circle(p["knob_d"] / 2).extrude(t + p["knob_len"]).edges(">Z").fillet(4)
    for k in range(12):                                                  # grip flutes
        ang = 2 * math.pi * k / 12
        knob = knob.cut(cq.Workplane("XY").workplane(offset=t + 4).center(a + 7.4 * math.cos(ang), 7.4 * math.sin(ang)).circle(1.0).extrude(p["knob_len"] - 10))
    return arm.union(hub).union(knob)
