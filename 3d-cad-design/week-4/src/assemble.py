"""Stackr assembly: modules slide onto the base's dovetail rails (mate: key flanks ≡ groove flanks, module bottom ≡
base top). Exports STEP/STL per part and the assembly, and checks fit: key-vs-groove clearance and clashes.
    python src/assemble.py"""
import json, sys
import numpy as np, trimesh
sys.path.insert(0, "src")
import cadquery as cq
from product import base, phone_stand, pen_cup, key, dovetail_profile, P
RAILS = {"phone_stand": -P["rail_pitch"], "pen_cup": 0.0, "pebble_planter": P["rail_pitch"]}
def parts():
    return {"base": base().val(), "phone_stand": phone_stand().val(), "pen_cup": pen_cup().val()}
def mesh_of(shape):
    v, t = shape.tessellate(.04, .15); return trimesh.Trimesh(np.array([p.toTuple() for p in v]), np.array(t))
def placements(slide=0.0):
    """slide: 0 = assembled; 1 = every module pulled 120 mm back along its rail (and lifted clear for the animation)."""
    return {"base": (0, 0, 0), **{k: (x, 120 * slide * (1 + .35 * i), P["base_t"] + 40 * max(0, slide - .6)) for i, (k, x) in enumerate(RAILS.items())}}
if __name__ == "__main__":
    S = parts()
    for n, s in S.items():
        cq.exporters.export(cq.Workplane().add(s), f"cad/{n}.step"); cq.exporters.export(cq.Workplane().add(s), f"cad/stl/{n}.stl", tolerance=.03, angularTolerance=.1)
    M = {n: mesh_of(s) for n, s in S.items()}; M["pebble_planter"] = trimesh.load("cad/stl/pebble_planter.stl")
    pl = placements(0); placed = {n: m.copy().apply_translation(pl[n]) for n, m in M.items()}
    trimesh.util.concatenate(list(placed.values())).export("cad/stackr_assembly.stl")
    assy = cq.Assembly(name="stackr")
    for n, s in S.items(): assy.add(cq.Workplane().add(s), name=n, loc=cq.Location(cq.Vector(*pl[n])))
    assy.save("cad/stackr_assembly.step")
    clashes = {}
    names = list(placed)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            v = trimesh.boolean.intersection([placed[names[i]], placed[names[j]]], engine="manifold").volume
            clashes[f"{names[i]} × {names[j]}"] = round(float(v), 3)
    w_bot = P["dt_top"] + 2 * P["dt_depth"] / np.tan(np.radians(P["dt_angle"]))
    fit = dict(groove_top_mm=P["dt_top"], groove_bottom_mm=round(w_bot, 2), key_top_mm=P["dt_top"] - 2 * P["fit"], clearance_per_flank_mm=P["fit"],
               vertical_gap_mm=P["fit"], note="0.25 mm per flank suits a 0.4 mm nozzle; tune ±0.05 mm after a test print")
    json.dump({"clash_volumes_mm3": clashes, "dovetail_fit": fit, "volumes_cm3": {n: round(m.volume / 1000, 1) for n, m in M.items()},
               "envelope_mm": np.round(trimesh.util.concatenate(list(placed.values())).extents, 1).tolist()}, open("results/assembly.json", "w"), indent=1)
    print(clashes, fit)
