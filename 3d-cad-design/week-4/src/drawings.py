"""Manufacturing drawings for Stackr (A3, first-angle, mm), reusing the week-2 drawing engine (OCC hidden-line
removal + dimensioning). The sculpted planter has no B-rep, so it is drawn as its projected outline.
    python src/drawings.py  -> drawings/*.svg, drawings/stackr-drawings.pdf"""
import json, math, os, sys
import numpy as np, trimesh
from shapely.geometry import MultiPoint
W2 = os.path.abspath("../week-2"); here = os.getcwd(); sys.path.insert(0, W2 + "/src"); os.chdir(W2)
import drawing as DW
os.chdir(here); sys.path.insert(0, "src")
import cadquery as cq
from product import base, phone_stand, pen_cup, stand_profile, dovetail_profile, P
DW.VIEWS.update({"side": ((-1, 0, 0), (0, -1, 0)), "front": ((0, -1, 0), (1, 0, 0)), "top": ((0, 0, 1), (1, 0, 0)), "iso": ((-1, -1, 1), (1, -1, 0)), "lside": ((1, 0, 0), (0, 1, 0))})
def title(s, t, n, of, sc, mat, pn): S = DW.Sheet(t, n, of, sc, mat, pn); return S
os.makedirs("drawings", exist_ok=True)
# ---------------- sheet 1: phone stand
st = phone_stand().val(); a = P["back_angle"]
s1 = DW.Sheet("PHONE STAND MODULE", 1, 3, "1:1", "PLA, FDM 0.2 mm layers", "SK-101")
Sd = s1.view(st, "side", 120, 150, 1.0, label="SIDE VIEW (from left)", label_dy=26)
Fr = s1.view(st, "front", 255, 150, 1.0, label="FRONT VIEW", label_dy=26)
Tp = s1.view(st, "top", 340, 150, 0.8, hidden=False, label="TOP VIEW (0.8 : 1)", label_dy=26)
# side view coordinates: model y -> paper x reversed (view x-axis is -Y), z up
yz = lambda y, z: Sd(-y, z)
s1.dim(yz(40, 0), yz(-40, 0), -12, txt="80", orient="h"); s1.dim(yz(-40, 0), yz(-40, P["stand_h"]), -10, P["stand_h"], "v")
s1.dim(yz(40, 0), yz(40, P["lip_h"]), 8, P["lip_h"], "v")
F0 = (-26.0, 4.0); s1.leader(yz(F0[0] + 20 / math.tan(math.radians(a)), 24), yz(-5, 48), f"back support {a:g}° to the base")
xz = lambda x, z: Fr(x, z); s1.dim(xz(-P["stand_w"] / 2, 0), xz(P["stand_w"] / 2, 0), -12, P["stand_w"], "h")
s1.leader(xz(P["cable_w"] / 2, 10), xz(30, 30), f"cable notch {P['cable_w']:g} wide")
s1.leader(xz(4, -2.5), xz(20, -22), f"dovetail key {P['dt_top'] - 2 * P['fit']:g} / {P['dt_depth'] - P['fit']:g} deep, {P['dt_angle']:g}° (fit {P['fit']:g})")
s1.text(30, 262, "Print upright, 0.2 mm layers, 2 perimeters, 15 % infill. Tree supports under the floor beside the key and under the apex.", 3.0)
s1.text(30, 268, "FEA: 10 N tap at the top + phone weight → peak 0.28 MPa (results/sim.json). The open A-frame saves 19 % material vs v1.", 3.0)
s1.svg("drawings/01-phone-stand.svg")
# ---------------- sheet 2: base with dovetail detail
bs = base().val(); s2 = DW.Sheet("BASE RAIL PLATE", 2, 3, "1:1.5", "PLA, FDM 0.2 mm layers", "SK-100"); k = 1 / 1.5
Tb = s2.view(bs, "top", 120, 100, k, label="TOP VIEW", label_dy=24); Fb = s2.view(bs, "front", 120, 185, k, label="FRONT VIEW", label_dy=20)
s2.dim(Tb(-P["base_l"] / 2, -P["base_w"] / 2), Tb(P["base_l"] / 2, -P["base_w"] / 2), -10, P["base_l"], "h")
s2.dim(Tb(P["base_l"] / 2, -P["base_w"] / 2), Tb(P["base_l"] / 2, P["base_w"] / 2), 8, P["base_w"], "v")
s2.dim(Tb(-P["rail_pitch"], P["base_w"] / 2), Tb(0, P["base_w"] / 2), 8, P["rail_pitch"], "h"); s2.dim(Tb(0, P["base_w"] / 2), Tb(P["rail_pitch"], P["base_w"] / 2), 8, P["rail_pitch"], "h")
s2.dim(Fb(P["base_l"] / 2, 0), Fb(P["base_l"] / 2, P["base_t"]), 8, P["base_t"], "v")
for x in (-P["rail_pitch"], 0, P["rail_pitch"]): s2.centre(Tb(x, -P["base_w"] / 2 - 4), Tb(x, P["base_w"] / 2 + 4))
# detail of the dovetail groove at 5:1
D = 5.0; ox, oy = 300, 120; prof = dovetail_profile(P["dt_top"], P["dt_depth"], P["dt_angle"]); pts = [(ox + D * x, oy - D * z) for x, z in prof]
s2.el.append('<polyline class="vis" points="' + " ".join(f"{a_:.2f},{b_:.2f}" for a_, b_ in [(ox - 60, oy)] + pts[:1] + pts[3:] [::-1][:0] + [pts[0], pts[3], pts[2], pts[1], (ox + 60, oy)]) + '"/>')
s2.dim(pts[0], pts[1], 8, P["dt_top"], "h"); s2.dim(pts[3], pts[2], -10, round(P["dt_top"] + 2 * P["dt_depth"] / math.tan(math.radians(P["dt_angle"])), 2), "h")
s2.dim(pts[1], (pts[1][0], pts[2][1]), 30, P["dt_depth"], "v"); s2.leader(((pts[1][0] + pts[2][0]) / 2, (pts[1][1] + pts[2][1]) / 2), (ox + 52, oy + 40), f"{P['dt_angle']:g}° flanks")
s2.text(ox, oy + 62, "DETAIL A: DOVETAIL GROOVE (5 : 1)", 3.5, "middle", "lbl"); s2.text(ox, oy + 69, f"Module keys are this profile minus {P['fit']:g} mm on every face (sliding fit).", 2.8, "middle")
s2.leader(Tb(90, 35), Tb(115, 60), "4× Ø10 × 1.2 recess (rubber feet), underside")
s2.svg("drawings/02-base.svg")
# ---------------- sheet 3: assembly
s3 = DW.Sheet("STACKR DESK ORGANISER: ASSEMBLY", 3, 3, "1:2", part_no="SK-000")
pl = {"base": (0, 0, 0), "phone_stand": (-P["rail_pitch"], 0, P["base_t"]), "pen_cup": (0, 0, P["base_t"])}
comp = cq.Compound.makeCompound([s.translate(cq.Vector(*pl[n])) for n, s in {"base": bs, "phone_stand": st, "pen_cup": pen_cup().val()}.items()])
Fa = s3.view(comp, "front", 120, 120, .5, hidden=False, label="FRONT VIEW", label_dy=16); Ta = s3.view(comp, "top", 120, 190, .5, hidden=False, label="TOP VIEW", label_dy=16)
peb = trimesh.load("cad/stl/pebble_planter.stl"); peb.apply_translation((P["rail_pitch"], 0, P["base_t"]))
for view, f_ in (("front", Fa), ("top", Ta)):
    pts2 = [f_(*DW.to2d(view, v)) for v in peb.vertices[::25]]; hull = MultiPoint(pts2).convex_hull
    s3.el.append('<polygon class="vis" fill="none" points="' + " ".join(f"{x:.2f},{y:.2f}" for x, y in hull.exterior.coords) + '"/>')
s3.dim(Fa(-P["base_l"] / 2, 0), Fa(P["base_l"] / 2, 0), -8, P["base_l"], "h"); s3.dim(Fa(P["base_l"] / 2, 0), Fa(P["base_l"] / 2, P["base_t"] + P["cup_h"]), 8, P["base_t"] + P["cup_h"], "v")
pr = json.load(open("results/print-report.json"))["parts"] if os.path.exists("results/print-report.json") else {}
rows = [["ITEM", "PART", "QTY", "MATERIAL", "FILAMENT g", "PRINT h"]]
for i, (n, label) in enumerate((("base", "Base rail plate"), ("phone_stand", "Phone stand module"), ("pen_cup", "Hex pen cup module"), ("pebble_planter", "Pebble planter (sculpted)")), 1):
    rows.append([i, label, 1, "PLA", pr.get(n, {}).get("filament_g", "-"), pr.get(n, {}).get("print_time_h", "-")])
rows.append([5, "Rubber foot Ø10 × 2", 4, "silicone", "-", "-"]); s3.table(225, 60, rows, [12, 52, 11, 22, 24, 20], h=6)
s3.text(225, 112, "Modules slide onto the rails from the back and can be swapped or reordered.", 3.0)
s3.svg("drawings/03-assembly.svg")
DW.to_pdf(["drawings/01-phone-stand.svg", "drawings/02-base.svg", "drawings/03-assembly.svg"], os.path.abspath("drawings/stackr-drawings.pdf")); print("drawings done")
