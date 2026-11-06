"""Validation: a 200 x 20 x 10 mm cantilever (aluminium), fixed at x = 0, 100 N tip load spread over the end face.
Compares tip deflection with Timoshenko beam theory and the bending stress at x = L/2 with M c / I, for several
mesh sizes. A solver that can't match a textbook beam can't be trusted on a bracket.
    python src/validate_cantilever.py  -> results/cantilever-validation.json, results/cantilever-convergence.png"""
import json, sys, time
import numpy as np
sys.path.insert(0, "src")
import cadquery as cq
from fea import mesh_from_cq, Model
L, H, B, P, E, NU = 200.0, 20.0, 10.0, 100.0, 69000.0, 0.33
beam = cq.Workplane("XY").box(L, B, H, centered=(False, True, True)).val()
I = B * H ** 3 / 12; G = E / (2 * (1 + NU)); kappa = 10 * (1 + NU) / (12 + 11 * NU)      # Cowper shear coefficient, rectangle
d_eb = P * L ** 3 / (3 * E * I); d_timo = d_eb + P * L / (kappa * G * B * H)
sig_half = P * (L / 2) * (H / 2) / I
rows = []
for h in (10, 6, 4, 3, 2.2):
    t0 = time.time(); m = mesh_from_cq(beam, h); mod = Model(m, E, NU)
    mod.fix(lambda x: x[0] < 1e-6); mod.traction(lambda x: x[0] > L - 1e-6, [0, 0, -P]); mod.solve(); vm = mod.von_mises(); u = mod.nodal_disp()
    tip = np.abs(u[2][m.p[0] > L - 1e-6]).mean()
    near = (np.abs(m.p[0] - L / 2) < h) & (np.abs(np.abs(m.p[2]) - H / 2) < 1e-6)                     # top/bottom surface at mid-span
    rows.append(dict(h=h, elements=int(m.nelements), dofs=int(mod.ndofs()), tip_mm=round(float(tip), 5), err_tip_pct=round(100 * (tip - d_timo) / d_timo, 2),
                     sigma_mid_MPa=round(float(vm[near].mean()), 3), err_sigma_pct=round(100 * (vm[near].mean() - sig_half) / sig_half, 2), seconds=round(time.time() - t0, 1)))
    print(rows[-1], flush=True)
res = dict(analytic=dict(tip_euler_bernoulli_mm=round(d_eb, 5), tip_timoshenko_mm=round(d_timo, 5), sigma_mid_MPa=round(sig_half, 3)), runs=rows)
json.dump(res, open("results/cantilever-validation.json", "w"), indent=1)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(11, 4)); d = [r["dofs"] for r in rows]
ax[0].semilogx(d, [r["tip_mm"] for r in rows], "o-", color="#2F6DB5"); ax[0].axhline(d_timo, ls="--", color="#E8590C", label=f"Timoshenko {d_timo:.4f} mm"); ax[0].set_title("Tip deflection", loc="left")
ax[1].semilogx(d, [r["sigma_mid_MPa"] for r in rows], "o-", color="#2F6DB5"); ax[1].axhline(sig_half, ls="--", color="#E8590C", label=f"Mc/I = {sig_half:.2f} MPa"); ax[1].set_title("Bending stress at mid-span (surface)", loc="left")
for a in ax: a.set_xlabel("degrees of freedom"); a.legend(frameon=False); [a.spines[s].set_visible(False) for s in ("top", "right")]
fig.tight_layout(); fig.savefig("results/cantilever-convergence.png", dpi=140)
