"""Verifies the gear geometry: (1) the two meshing pairs never overlap through a full tooth cycle when each gear is
rotated by its ratio (OCC boolean intersection volume), (2) centre distances, ratios and contact ratio.
    python src/mesh_check.py  -> results/mesh-check.json, results/gear-mesh.png"""
import json, math, sys
sys.path.insert(0, "src")
import cadquery as cq
from parts import gear, centres, involute_gear_profile, P
xs, (a1, a2) = centres()
G = {z: gear(z, hub=False).val() for z in (P["z_in"], P["z_idler"], P["z_out"])}
def placed(z, x, ang): return G[z].rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), ang).translate(cq.Vector(x, 0, 0))
def phase(z): return 180 / z if z % 2 == 0 else 0        # puts a tooth gap on the line of centres facing the left neighbour
res = {"centre_distances_mm": [a1, a2], "steps": []}
z1, z2, z3 = P["z_in"], P["z_idler"], P["z_out"]
def gap_at_180(z):
    """Rotation that puts a tooth space (not a tooth) at 180 deg, facing a neighbour on the left whose tooth points at it."""
    pitch = 360 / z; k = math.floor(180 / pitch - .5); return 180 - (k + .5) * pitch
off2 = gap_at_180(z2)
best = None                                                # output phase: searched finely (depends on the idler's phase)
for i in range(60):
    o = i * (360 / z3) / 60; v = placed(z2, xs[1], off2).intersect(placed(z3, xs[2], o)).Volume()
    if best is None or v < best[0] - 1e-9: best = (v, o)
off3 = best[1]
worst = 0.0
for k in range(9):                                       # one full tooth pitch of the input gear in 9 steps
    th = (360 / z1) * k / 8
    a_in, a_id, a_out = th, off2 - th * z1 / z2, off3 + th * z1 / z3   # idler turns the opposite way, output same way as input
    v1 = placed(z1, xs[0], a_in).intersect(placed(z2, xs[1], a_id)).Volume(); v2 = placed(z2, xs[1], a_id).intersect(placed(z3, xs[2], a_out)).Volume()
    worst = max(worst, v1, v2); res["steps"].append([round(th, 2), round(v1, 4), round(v2, 4)])
m, pa = P["module"], math.radians(P["pressure_angle"])
def contact_ratio(za, zb):
    ra, rb_ = m * za / 2 + m, m * za / 2 * math.cos(pa); rc, rd = m * zb / 2 + m, m * zb / 2 * math.cos(pa); a = m * (za + zb) / 2
    return (math.sqrt(ra ** 2 - rb_ ** 2) + math.sqrt(rc ** 2 - rd ** 2) - a * math.sin(pa)) / (math.pi * m * math.cos(pa))
res.update(worst_overlap_mm3=round(worst, 4), overall_ratio=round(z3 / z1, 4), output_direction="same as input (idler reverses twice)",
           contact_ratio=[round(contact_ratio(z1, z2), 3), round(contact_ratio(z2, z3), 3)], phases_deg={"idler": round(off2, 3), "output": round(off3, 3)},
           pitch_diameters_mm=[m * z for z in (z1, z2, z3)], outside_diameters_mm=[m * (z + 2) for z in (z1, z2, z3)])
json.dump(res, open("results/mesh-check.json", "w"), indent=1); print(json.dumps({k: v for k, v in res.items() if k != "steps"}, indent=1))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(11, 5))
for z, x, ang, col in ((z1, xs[0], 0, "#E8590C"), (z2, xs[1], off2, "#2F6DB5"), (z3, xs[2], off3, "#2B8A3E")):
    pts = involute_gear_profile(z, m, P["pressure_angle"], P["backlash"]); c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    X = [x + px * c - py * s for px, py in pts] + [x + pts[0][0] * c - pts[0][1] * s]; Y = [px * s + py * c for px, py in pts] + [pts[0][0] * s + pts[0][1] * c]
    ax.fill(X, Y, color=col, alpha=.25); ax.plot(X, Y, color=col, lw=.8); ax.add_patch(plt.Circle((x, 0), m * z / 2, fill=False, ls="--", lw=.6, color="k"))
    ax.text(x, -m * z / 2 - 8, f"z={z}  d={m * z:.0f}", ha="center", fontsize=9)
ax.set_aspect("equal"); ax.set_title(f"Gear train, module {m}, 20° PA: pitch circles dashed; max overlap over one tooth cycle = {worst:.3f} mm³", fontsize=10, loc="left")
ax.axis("off"); fig.tight_layout(); fig.savefig("results/gear-mesh.png", dpi=150)
