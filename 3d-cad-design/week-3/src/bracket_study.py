"""Task 1 + 2: stress analysis of a shelf bracket with a mesh-convergence study and a fillet-radius design study.
Bracket: Al 6061-T6 (E = 69 GPa, ν = 0.33, yield 276 MPa), 30 mm wide, 6 mm thick; vertical flange bolted to a wall
by 2× M6 (bolt bores fixed); 86 mm arm; 200 N downward on the last 10 mm of the arm.
    python src/bracket_study.py  -> results/bracket-*.json/png, renders/bracket-stress.png"""
import json, sys, time
import numpy as np
sys.path.insert(0, "src")
import cadquery as cq
from fea import mesh_from_cq, Model
from viz import grid, heatmap
E, NU, YIELD, F = 69000.0, 0.33, 276.0, 200.0; W, T, ARM, WALL = 30.0, 6.0, 86.0, 60.0
def bracket(r):
    b = (cq.Workplane("XZ").polyline([(0, 0), (ARM, 0), (ARM, T), (T, T), (T, WALL), (0, WALL)]).close().extrude(W / 2, both=True))
    b = b.edges("|Y").edges(cq.selectors.NearestToPointSelector((T, 0, T))).fillet(r)                     # inner corner fillet
    b = b.faces("<X").workplane(centerOption="CenterOfBoundBox").pushPoints([(0, 20 - WALL / 2), (0, 45 - WALL / 2)]).hole(6.5)
    return b.val()
def run(r, h):
    m = mesh_from_cq(bracket(r), h); mod = Model(m, E, NU)
    mod.fix(lambda x: (x[0] < T + 1e-6) & (np.hypot(x[1], x[2] - 20) < 3.3) | (x[0] < T + 1e-6) & (np.hypot(x[1], x[2] - 45) < 3.3))
    mod.traction(lambda x: (x[2] > T - 1e-6) & (x[0] > ARM - 10 - 1e-6), [0, 0, -F]); mod.solve(); vm = mod.von_mises(); u = mod.nodal_disp()
    dc = np.hypot(m.p[0] - (T + r), m.p[2] - (T + r)); corner = (np.abs(dc - r) < .6) & (m.p[0] < T + r + .1) & (m.p[2] < T + r + .1) & (m.p[0] > T - .1) & (m.p[2] > T - .1)   # nodes on the fillet surface
    holes = (m.p[0] < T + 1e-6) & ((np.hypot(m.p[1], m.p[2] - 20) < 4.5) | (np.hypot(m.p[1], m.p[2] - 45) < 4.5))
    tip = -u[2][m.p[0] > ARM - 1e-6].mean()
    return m, mod, vm, u, dict(r=r, h=h, elements=int(m.nelements), dofs=int(mod.ndofs()), fillet_max_MPa=round(float(vm[corner].max()), 2), global_max_MPa=round(float(vm.max()), 2), bolt_hole_max_MPa=round(float(vm[holes].max()), 2),
                              tip_deflection_mm=round(float(tip), 4), safety_factor=round(YIELD / float(vm[corner].max()), 2))
if __name__ == "__main__":
    nominal = F * (ARM - 5 - T) * (T / 2) / (W * T ** 3 / 12)                         # M c / I at the arm root, no stress concentration
    conv = []
    for h in (6, 4, 3, 2.2, 1.6):   # same geometry, refined mesh
        t0 = time.time(); *_, r_ = run(4.0, h); r_["seconds"] = round(time.time() - t0, 1); conv.append(r_); print(r_, flush=True)
    design = []
    for r in (1.0, 4.0, 8.0):
        m, mod, vm, u, r_ = run(r, 2.2); design.append(r_); print(r_, flush=True)
        if r == 4.0: keep = (m, vm, u, r)
    json.dump({"nominal_root_stress_MPa": round(nominal, 2), "convergence_R4": conv, "fillet_study_h2.2": design}, open("results/bracket-study.json", "w"), indent=1)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(14, 4)); d = [c["dofs"] for c in conv]
    ax[0].semilogx(d, [c["fillet_max_MPa"] for c in conv], "o-", color="#2F6DB5"); ax[0].set_title("Peak von Mises in the fillet (R4)", loc="left")
    ax[1].semilogx(d, [c["tip_deflection_mm"] for c in conv], "o-", color="#2F6DB5"); ax[1].set_title("Tip deflection (mm)", loc="left")
    for a in ax[:2]: a.set_xlabel("degrees of freedom")
    rr = [x["r"] for x in design]; ax[2].bar([f"R{x:g}" for x in rr], [x["fillet_max_MPa"] for x in design], color=["#C92A2A", "#2F6DB5", "#2B8A3E"])
    ax[2].axhline(YIELD, ls="--", color="k", lw=1); ax[2].text(2.4, YIELD + 4, "yield 276", ha="right", fontsize=9); ax[2].axhline(nominal, ls=":", color="#E8590C"); ax[2].text(2.4, nominal + 4, f"nominal Mc/I {nominal:.0f}", ha="right", fontsize=9, color="#E8590C")
    ax[2].set_title("Peak stress vs inner fillet radius", loc="left")
    for a in ax: [a.spines[s].set_visible(False) for s in ("top", "right")]
    fig.tight_layout(); fig.savefig("results/bracket-convergence-and-fillets.png", dpi=140)
    m, vm, u, r = keep; dc = np.hypot(m.p[0] - (T + r), m.p[2] - (T + r)); mask = (np.abs(dc - r) < .6) & (m.p[0] > T - .1) & (m.p[2] > T - .1) & (m.p[0] < T + r + .1) & (m.p[2] < T + r + .1)
    pk = int(np.argmax(np.where(mask, vm, -1))); sc = 15
    heatmap(grid(m, vm, u, sc), "renders/bracket-stress.png", f"Shelf bracket, Al 6061-T6, 200 N at the tip · deformation x{sc} · fillet peak {vm[pk]:.0f} MPa (safety factor {YIELD / vm[pk]:.1f})",
            cam=[(150, -170, 120), (40, 0, 20), (0, 0, 1)], ghost=grid(m), clim=(0, 140), annotate=[(m.p[:, pk] + sc * u[:, pk], f"fillet peak {vm[pk]:.0f} MPa")])
