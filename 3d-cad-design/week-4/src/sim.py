"""Simulation of the phone stand (PLA: E = 3.5 GPa, ν = 0.36, tensile strength ~50 MPa, k = 0.13 W/m·K):
  1. structural: phone resting (200 g) + a 10 N finger tap pushing on the top of the back support, normal to it
  2. thermal: a phone at 38 °C while charging, against the back support; still air h = 10 W/m²·K at 25 °C elsewhere
    python src/sim.py  -> results/sim.json, renders/stand-stress.png, renders/stand-thermal.png"""
import json, math, sys
import numpy as np
sys.path.insert(0, "src")
import cadquery as cq, skfem as fem
from skfem.helpers import dot, grad
import scipy.sparse.linalg as spla
from product import stand_profile, P
from fea import mesh_from_cq, Model
from viz import grid, heatmap
import pyvista as pv
a = math.radians(P["back_angle"]); F0 = (-26.0, 4.0)
w = P["stand_w"]; outer, window = stand_profile()
body = cq.Workplane("XZ").polyline(outer).close().extrude(w / 2, both=True).cut(cq.Workplane("XZ").polyline(window).close().extrude(w / 2 + 1, both=True))
body = body.rotate((0, 0, 0), (0, 0, 1), 90).val()                      # same orientation as the product (lip at -Y); key omitted, base face fixed instead
def s_front(x):                                                          # signed distance from the back support's front face (positive toward the phone)
    xp, zp = x[1], x[2]; return (xp - F0[0]) * (-math.sin(a)) + (zp - F0[1]) * math.cos(a)
m = mesh_from_cq(body, 2.5)
# ---------------- 1. structural
E, NU, UTS = 3500.0, 0.36, 50.0; tap = 10.0; phone = 0.2 * 9.81
mod = Model(m, E, NU); mod.fix(lambda x: x[2] < 1e-6)
n_into = np.array([0, math.sin(a), -math.cos(a)])                       # pushing the support backward (into it)
mod.traction(lambda x: (np.abs(s_front(x)) < .3) & (x[2] > 70) & (x[2] < 88) & (np.abs(x[0]) < 26), tap * n_into)
mod.traction(lambda x: (np.abs(s_front(x)) < .3) & (x[2] > 10) & (x[2] < 60) & (np.abs(x[0]) < 26), phone * math.cos(a) * n_into + np.array([0, 0, -phone * math.sin(a)]) * 0)
mod.solve(); vm = mod.von_mises(); u = mod.nodal_disp(); tip = np.linalg.norm(u[:, m.p[2] > 90], axis=0).max()
base_band = m.p[2] > 1.0                                                  # ignore the fixed-face singular strip
peak = float(vm[base_band].max()); pk = int(np.argmax(np.where(base_band, vm, -1)))
heatmap(grid(m, vm, u, 20), "renders/stand-stress.png", f"Phone stand (PLA) · 10 N tap at the top + phone weight · deformation x20 · peak {peak:.2f} MPa (strength ~50 MPa → SF {UTS / peak:.0f})",
        cam=[(210, -190, 160), (0, 0, 40), (0, 0, 1)], ghost=grid(m), annotate=[(m.p[:, pk] + 20 * u[:, pk], f"peak {peak:.2f} MPa")], fmt="%.2f")
# ---------------- 2. thermal (P1 tetrahedra, Robin convection, Dirichlet phone contact)
k, h, Tamb, Tphone = 0.13e-3, 10e-6, 25.0, 38.0                          # W/mm·K and W/mm²·K
b = fem.Basis(m, fem.ElementTetP1())
contact = m.facets_satisfying(lambda x: (np.abs(s_front(x)) < .3) & (x[2] > 15) & (x[2] < 88) & (np.abs(x[0]) < 30), boundaries_only=True)
others = np.setdiff1d(m.boundary_facets(), contact); fb = fem.FacetBasis(m, b.elem, facets=others)
K = fem.asm(fem.BilinearForm(lambda u, v, w: k * dot(grad(u), grad(v))), b) + fem.asm(fem.BilinearForm(lambda u, v, w: h * u * v), fb)
f = fem.asm(fem.LinearForm(lambda v, w: h * Tamb * v), fb); D = b.get_dofs(contact).all()
T = fem.solve(*fem.condense(K, f, x=np.full(b.N, Tphone), D=D))
Tf = fb.interpolate(T); Q = fem.asm(fem.Functional(lambda w: h * (w["T"] - Tamb)), fb, T=Tf)          # heat leaving by convection (W)
g = grid(m); g.point_data["T"] = T
p = pv.Plotter(off_screen=True, window_size=(1600, 1000)); p.set_background("#F4F1EA", top="#FFFFFF")
p.add_mesh(g.extract_surface(algorithm="dataset_surface"), scalars="T", cmap="inferno", clim=(25, 38), smooth_shading=True,
           scalar_bar_args=dict(title="temperature (°C)", vertical=True, position_x=.86, position_y=.15, height=.7, width=.05, color="#14213D", title_font_size=18, label_font_size=16, fmt="%.0f"))
p.add_text(f"Phone at 38 °C against the stand, still air 25 °C · heat through the stand {Q:.2f} W · base stays at {T[m.p[2] < 4.5].mean():.1f} °C", position="upper_left", font_size=13, color="#14213D")
p.camera_position = [(-210, 190, 160), (0, 0, 40), (0, 0, 1)]; p.enable_anti_aliasing("ssaa"); p.screenshot("renders/stand-thermal.png"); p.close()
res = dict(v1_solid_cheeks=dict(volume_cm3=121.6, peak_von_mises_MPa=0.14, top_deflection_mm=0.002), volume_cm3=round(body.Volume() / 1000, 1), mesh=dict(elements=int(m.nelements), dofs=int(mod.ndofs())), structural=dict(tap_N=tap, phone_N=round(phone, 2), peak_von_mises_MPa=round(peak, 2), safety_factor_vs_50MPa=round(UTS / peak, 1),
           top_deflection_mm=round(float(tip), 3)), thermal=dict(phone_C=Tphone, ambient_C=Tamb, heat_through_stand_W=round(float(Q), 3), base_mean_C=round(float(T[m.p[2] < 4.5].mean()), 2),
           max_C=round(float(T.max()), 2), note="PLA softens near 55-60 °C: 38 °C contact is safe; PLA insulates, so the stand barely helps cool the phone"))
json.dump(res, open("results/sim.json", "w"), indent=1); print(json.dumps(res, indent=1))
