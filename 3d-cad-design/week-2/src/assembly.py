"""Assembly of the hand-cranked spur gear train, driven by mates and joints:
  mates  : shaft axis ≡ bore axis of both side plates; gear bore axis ≡ shaft axis, gear mid-plane ≡ assembly mid-plane;
           plates: bottom face on the base top face, inner faces at ±gap/2; collars against the plates' outer faces;
           crank hub on the input shaft, outside the rear collar
  joints : revolute joints on the 3 shafts, coupled by the gear ratios (idler = -z_in/z_idler, output = +z_in/z_out)
The mate solver below turns those relations into placements (location of every part), for any crank angle and an
optional explode factor. Exports STEP (whole assembly, with colours), STL per part, and results/assembly.json.
    python src/assembly.py"""
import json, math, os, sys
sys.path.insert(0, "src")
import cadquery as cq
from parts import P, centres, gear, shaft, side_plate, base_plate, collar, crank
PHASE = json.load(open("results/mesh-check.json"))["phases_deg"]        # tooth phasing found by src/mesh_check.py
XS, _ = centres(); AXIS_Z = P["base_t"] + P["shaft_height"]; GAP, T = P["plate_gap"], P["plate_t"]
MATERIAL = {"base": "aluminium_anodised", "plate": "aluminium_brushed", "shaft": "steel", "shaft_in": "steel", "gear_in": "brass", "gear_idler": "acetal_white",
            "gear_out": "brass", "collar": "steel_black", "crank": "aluminium_red"}
COLOR = {"aluminium_anodised": (0.20, 0.24, 0.30), "aluminium_brushed": (0.78, 0.79, 0.80), "steel": (0.62, 0.63, 0.65), "brass": (0.80, 0.62, 0.30),
         "acetal_white": (0.93, 0.93, 0.90), "steel_black": (0.12, 0.12, 0.13), "aluminium_red": (0.70, 0.12, 0.10)}
def shapes():
    """Each part in its own coordinate system (what you'd model in its own part file)."""
    return {"base": base_plate().val(), "plate": side_plate().val(), "shaft": shaft().val(), "shaft_in": shaft(extra=P["input_extra"]).val(), "gear_in": gear(P["z_in"]).val(),
            "gear_idler": gear(P["z_idler"]).val(), "gear_out": gear(P["z_out"]).val(), "collar": collar().val(), "crank": crank().val()}
def placements(theta=0.0, explode=0.0):
    """Solve the mates/joints -> list of (instance name, part, transform as (rot_x_deg, rot_axis_deg, translation)).
    Shafts, gears, collars and crank are built along +Z and turned so their axis is +Y (rot_x = -90), then spun
    about that axis by their joint angle, then moved onto their shaft axis."""
    z1, z2, z3 = P["z_in"], P["z_idler"], P["z_out"]
    ang = [theta, PHASE["idler"] - theta * z1 / z2, PHASE["output"] + theta * z1 / z3]       # coupled revolute joints
    e = explode; inst = [("base", "base", None, 0, (0, 0, 0))]
    inst += [("plate_front", "plate", None, 0, (0, -GAP / 2 - T - 40 * e, P["base_t"] + 10 * e)), ("plate_rear", "plate", None, 0, (0, GAP / 2 + 40 * e, P["base_t"] + 10 * e))]
    L = P["shaft_len"]
    for k, (x, a) in enumerate(zip(XS, ang)):
        ex = P["input_extra"] if k == 0 else 0      # the input shaft is longer at the front, so the crank clears the idler shaft
        inst.append((f"shaft_{k + 1}", "shaft_in" if k == 0 else "shaft", -90, a, (x, -L / 2 - ex - 75 * e, AXIS_Z + 60 * e)))
        gname = ["gear_in", "gear_idler", "gear_out"][k]
        inst.append((gname, gname, -90, a, (x, -P["face"] / 2, AXIS_Z + (95 + 25 * k) * e)))            # gear mid-plane on y = 0
        for side, y in (("f", -GAP / 2 - T - P["collar_len"] - 70 * e), ("r", GAP / 2 + T + 70 * e)):
            inst.append((f"collar_{k + 1}{side}", "collar", -90, a, (x, y, AXIS_Z + 60 * e)))
    inst.append(("crank", "crank", 90, -ang[0], (XS[0], -(GAP / 2 + T + P["collar_len"] + 9) - P["input_extra"] - 120 * e, AXIS_Z + 60 * e)))   # crank on the front, facing out
    return inst
def located(shp, rx, ra, t):
    s = shp
    if rx is not None: s = s.rotate(cq.Vector(), cq.Vector(1, 0, 0), rx)
    if ra: s = s.rotate(cq.Vector(), cq.Vector(0, 1, 0), ra)
    return s.translate(cq.Vector(*t))
def build(theta=0.0, explode=0.0, S=None):
    S = S or shapes(); return {n: (part, located(S[part], rx, ra, t)) for n, part, rx, ra, t in placements(theta, explode)}
if __name__ == "__main__":
    os.makedirs("cad/stl", exist_ok=True); S = shapes(); A = build(0, 0, S)
    assy = cq.Assembly(name="gear_train")
    for n, (part, shp) in A.items(): assy.add(cq.Workplane().add(shp), name=n, color=cq.Color(*COLOR[MATERIAL[part]]))
    assy.save("cad/gear_train_assembly.step")
    for part, shp in S.items(): cq.exporters.export(cq.Workplane().add(shp), f"cad/stl/{part}.stl", tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(cq.Workplane().add(S["plate"]), "cad/side_plate.step"); cq.exporters.export(cq.Workplane().add(S["gear_out"]), "cad/gear_out.step")
    # interference check between all assembled parts (should be zero except the designed contacts)
    names = list(A); clashes = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = A[names[i]][1], A[names[j]][1]
            if a.BoundingBox().xmin > b.BoundingBox().xmax or b.BoundingBox().xmin > a.BoundingBox().xmax: continue
            v = a.intersect(b).Volume()
            if v > 1e-3: clashes.append([names[i], names[j], round(v, 3)])
    mass = {}
    DENS = {"aluminium_anodised": 2.70, "aluminium_brushed": 2.70, "steel": 7.85, "brass": 8.50, "acetal_white": 1.41, "steel_black": 7.85, "aluminium_red": 2.70}   # g/cm³
    bom = {}
    for n, (part, shp) in A.items(): bom.setdefault(part, 0); bom[part] += 1
    for part, q in bom.items(): mass[part] = round(S[part].Volume() / 1000 * DENS[MATERIAL[part]], 1)
    bb = cq.Compound.makeCompound([s for _, s in A.values()]).BoundingBox()
    json.dump({"params": P, "shaft_x": XS, "axis_height": AXIS_Z, "phases_deg": PHASE, "bom": [{"part": p, "qty": q, "material": MATERIAL[p], "mass_g_each": mass[p]} for p, q in bom.items()],
               "total_mass_g": round(sum(mass[p] * q for p, q in bom.items()), 1), "envelope_mm": [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)], "clashes": clashes,
               "joints": [{"joint": "revolute", "part": "shaft_1 + gear_in + crank", "ratio": 1.0}, {"joint": "revolute (coupled)", "part": "shaft_2 + gear_idler", "ratio": -P["z_in"] / P["z_idler"]},
                          {"joint": "revolute (coupled)", "part": "shaft_3 + gear_out", "ratio": P["z_in"] / P["z_out"]}]}, open("results/assembly.json", "w"), indent=1)
    print("parts", len(A), "clashes", clashes, "envelope", [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)])
