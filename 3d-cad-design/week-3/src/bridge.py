"""Mini project: a 12 m steel through-truss footbridge (Warren truss), analysed with a 3D frame finite-element model
written from first principles (12-DOF Euler-Bernoulli beam elements, rigid joints), checked against hand statics.
Steel S355 (fy = 355 MPa, E = 210 GPa). Loads to EN 1990/1991 style: ULS 1.35 G + 1.5 Q, SLS deflection under Q.
    python src/bridge.py  -> results/bridge.json, renders/bridge-*.png, anim/bridge-deformation.mp4/.gif, cad/bridge_frame.step"""
import json, math, os, subprocess, sys
import numpy as np
import scipy.sparse as sp, scipy.sparse.linalg as spla
E, G, FY, RHO, GRAV = 210e9, 81e9, 355e6, 7850.0, 9.81
L, NP, H, B = 12.0, 8, 2.5, 2.0                       # span, panels, truss height, width (m)
def shs(b, h, t):
    """Hollow rectangular section b x h x t (m): A, Iy (about local y, bending in z), Iz, J, Wy, Wz."""
    A = b * h - (b - 2 * t) * (h - 2 * t); Iy = (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12; Iz = (h * b ** 3 - (h - 2 * t) * (b - 2 * t) ** 3) / 12
    J = 2 * t * (b - t) ** 2 * (h - t) ** 2 / (b + h - 2 * t); return dict(A=A, Iy=Iy, Iz=Iz, J=J, Wy=Iy / (h / 2), Wz=Iz / (b / 2), name=f"{'SHS' if b == h else 'RHS'} {b * 1e3:.0f}x{h * 1e3:.0f}x{t * 1e3:.1f}")
def chs(d, t):
    A = math.pi * (d ** 2 - (d - 2 * t) ** 2) / 4; I = math.pi * (d ** 4 - (d - 2 * t) ** 4) / 64
    return dict(A=A, Iy=I, Iz=I, J=2 * I, Wy=I / (d / 2), Wz=I / (d / 2), name=f"CHS {d * 1e3:.1f}x{t * 1e3:.1f}")
SEC_FIRST = {"bottom chord": shs(.12, .12, .0063), "top chord": shs(.12, .12, .0063), "diagonal": shs(.08, .08, .005), "floor beam": shs(.10, .15, .0063),
             "top strut": shs(.08, .08, .004), "plan bracing": chs(.0483, .0032)}            # first sizing (max utilisation 0.17: far too heavy)
SEC = {"bottom chord": shs(.08, .08, .004), "top chord": shs(.09, .09, .005), "diagonal": shs(.05, .05, .003), "floor beam": shs(.08, .12, .004),
       "top strut": shs(.05, .05, .003), "plan bracing": chs(.0337, .0026)}                  # second iteration (this model)
# ---------------- geometry: nodes and members
nodes, idx = [], {}
def node(key, xyz): idx[key] = len(nodes); nodes.append(xyz)
dx = L / NP
for s, y in (("L", -B / 2), ("R", B / 2)):
    for i in range(NP + 1): node(("b", s, i), (i * dx, y, 0.0))
    for j in range(NP): node(("t", s, j), (j * dx + dx / 2, y, H))
mem = []
for s in "LR":
    mem += [(idx[("b", s, i)], idx[("b", s, i + 1)], "bottom chord") for i in range(NP)]
    mem += [(idx[("t", s, j)], idx[("t", s, j + 1)], "top chord") for j in range(NP - 1)]
    for j in range(NP): mem += [(idx[("b", s, j)], idx[("t", s, j)], "diagonal"), (idx[("t", s, j)], idx[("b", s, j + 1)], "diagonal")]
for i in range(NP + 1):                                  # floor beams split at mid-span so the deck load bends them
    node(("m", i), (i * dx, 0.0, 0.0)); mem += [(idx[("b", "L", i)], idx[("m", i)], "floor beam"), (idx[("m", i)], idx[("b", "R", i)], "floor beam")]
mem += [(idx[("t", "L", j)], idx[("t", "R", j)], "top strut") for j in range(NP)]
for i in range(NP): mem += [(idx[("b", "L", i)], idx[("b", "R", i + 1)], "plan bracing"), (idx[("b", "R", i)], idx[("b", "L", i + 1)], "plan bracing")]
X = np.array(nodes); nn = len(X); ndof = 6 * nn
# ---------------- element stiffness
def frame_k(xi, xj, s):
    d = xj - xi; Le = np.linalg.norm(d); ex = d / Le; ref = np.array([0, 0, 1.0]) if abs(ex[2]) < .9 else np.array([1.0, 0, 0])
    ey = np.cross(ref, ex); ey /= np.linalg.norm(ey); ez = np.cross(ex, ey); R3 = np.vstack([ex, ey, ez])
    A, Iy, Iz, J = s["A"], s["Iy"], s["Iz"], s["J"]; k = np.zeros((12, 12))
    k[0, 0] = k[6, 6] = E * A / Le; k[0, 6] = k[6, 0] = -E * A / Le; k[3, 3] = k[9, 9] = G * J / Le; k[3, 9] = k[9, 3] = -G * J / Le
    for (v, th, I, sg) in ((1, 5, Iz, 1), (2, 4, Iy, -1)):          # bending in local xy (about z) and xz (about y)
        a, b_, c, d_ = 12 * E * I / Le ** 3, 6 * E * I / Le ** 2, 4 * E * I / Le, 2 * E * I / Le
        k[v, v] = k[v + 6, v + 6] = a; k[v, v + 6] = k[v + 6, v] = -a
        k[v, th] = k[th, v] = sg * b_; k[v, th + 6] = k[th + 6, v] = sg * b_; k[v + 6, th] = k[th, v + 6] = -sg * b_; k[v + 6, th + 6] = k[th + 6, v + 6] = -sg * b_
        k[th, th] = k[th + 6, th + 6] = c; k[th, th + 6] = k[th + 6, th] = d_
    T = np.kron(np.eye(4), R3); return T.T @ k @ T, k, T, Le, R3
rows, cols, vals, EL = [], [], [], []
for a, b, kind in mem:
    Kg, kl, T, Le, R3 = frame_k(X[a], X[b], SEC[kind]); dofs = np.r_[6 * a:6 * a + 6, 6 * b:6 * b + 6]
    rows += np.repeat(dofs, 12).tolist(); cols += np.tile(dofs, 12).tolist(); vals += Kg.ravel().tolist(); EL.append((a, b, kind, kl, T, Le, dofs))
K = sp.csr_matrix((vals, (rows, cols)), shape=(ndof, ndof))
# ---------------- supports: bearings at the 4 bottom-chord end nodes
fix = []
A0, B0, C0, D0 = idx[("b", "L", 0)], idx[("b", "R", 0)], idx[("b", "L", NP)], idx[("b", "R", NP)]
fix += [6 * A0 + 0, 6 * A0 + 1, 6 * A0 + 2, 6 * B0 + 0, 6 * B0 + 2, 6 * C0 + 1, 6 * C0 + 2, 6 * D0 + 2]   # fixed / guided / free-sliding bearings
free = np.setdiff1d(np.arange(ndof), fix)
# ---------------- loads (N)
self_w = sum(SEC[k]["A"] * Le * RHO * GRAV for _, _, k, _, _, Le, _ in EL)
deck_dead, live = 0.6e3, 5.0e3                       # timber deck + fixings (N/m²), crowd load (N/m²)
def load_vector(g_factor, q_factor):
    f = np.zeros(ndof)
    for _, _, k, _, _, Le, dofs in EL:                                    # self-weight lumped to member ends
        w = SEC[k]["A"] * Le * RHO * GRAV * g_factor / 2; f[dofs[2]] -= w; f[dofs[8]] -= w
    for i in range(NP + 1):                                                 # deck planks span between floor beams: UDL on each floor beam,
        w = dx * (.5 if i in (0, NP) else 1.0) * (deck_dead * g_factor + live * q_factor)   # lumped B/4 · B/2 · B/4 to its three nodes
        f[6 * idx[("b", "L", i)] + 2] -= w * B / 4; f[6 * idx[("b", "R", i)] + 2] -= w * B / 4; f[6 * idx[("m", i)] + 2] -= w * B / 2
    return f
def solve(f):
    u = np.zeros(ndof); u[free] = spla.spsolve(K[free][:, free].tocsc(), f[free]); return u
def member_results(u):
    out = []
    for a, b, kind, kl, T, Le, dofs in EL:
        fl = kl @ (T @ u[dofs]); s = SEC[kind]; N = -fl[0]                 # tension positive
        My = max(abs(fl[4]), abs(fl[10])); Mz = max(abs(fl[5]), abs(fl[11])); sig = abs(N) / s["A"] + My / s["Wy"] + Mz / s["Wz"]
        out.append(dict(a=a, b=b, kind=kind, N=N, My=My, Mz=Mz, sigma=sig, sigma_axial=N / s["A"], L=Le))
    return out
def buckling(r, kind):
    """EN 1993-1-1 flexural buckling, hollow sections (curve 'a', alpha = 0.21), effective length = member length."""
    s = SEC[kind]; i = math.sqrt(min(s["Iy"], s["Iz"]) / s["A"]); lam = r["L"] / i / (math.pi * math.sqrt(E / FY))
    phi = .5 * (1 + .21 * (lam - .2) + lam ** 2); chi = min(1, 1 / (phi + math.sqrt(phi ** 2 - lam ** 2))); Nbrd = chi * s["A"] * FY
    return chi, Nbrd, lam
if __name__ == "__main__":
    os.makedirs("anim", exist_ok=True)
    fu, fs = load_vector(1.35, 1.5), load_vector(0.0, 1.0)              # ULS combination; SLS live-load-only for deflection
    uu, us = solve(fu), solve(fs); R = member_results(uu)
    for r in R:
        r["util_stress"] = r["sigma"] / FY
        if r["N"] < 0: chi, Nb, lam = buckling(r, r["kind"]); r["util_buckling"] = -r["N"] / Nb; r["lambda_bar"] = lam
        r["util"] = max(r["util_stress"], r.get("util_buckling", 0))
    mid = [idx[("b", s, NP // 2)] for s in "LR"]; defl_sls = -us[[6 * m + 2 for m in mid]].mean(); defl_uls = -uu[[6 * m + 2 for m in mid]].mean()
    # hand check: each truss carries half the deck; midspan bottom-chord force ≈ M / h with M = w L² / 8
    w_truss = (fu[2::6].sum() * -1) / 2 / L; M = w_truss * L ** 2 / 8; N_hand = M / H
    mid_chords = [r for r in R if r["kind"] == "bottom chord" and abs((X[r["a"]][0] + X[r["b"]][0]) / 2 - (L / 2 - dx / 2)) < 1e-6]
    reactions = (K @ uu - fu)[fix]
    worst = sorted(R, key=lambda r: -r["util"])[:6]
    summary = dict(span_m=L, panels=NP, height_m=H, width_m=B, steel="S355", sections={k: v["name"] for k, v in SEC.items()}, members=len(EL), nodes=nn,
                   self_weight_kN=round(self_w / 1e3, 1), deck_dead_kN=round(deck_dead * L * B / 1e3, 1), live_kN=round(live * L * B / 1e3, 1),
                   uls_total_vertical_kN=round(-fu[2::6].sum() / 1e3, 1), sum_reactions_kN=round(float((K @ uu - fu)[[6 * n + 2 for n in (A0, B0, C0, D0)]].sum()) / 1e3, 1),
                   midspan_deflection_sls_mm=round(defl_sls * 1e3, 1), deflection_limit_L_400_mm=round(L / 400 * 1e3, 1), midspan_deflection_uls_mm=round(defl_uls * 1e3, 1),
                   hand_check_midspan_bottom_chord_kN=round(N_hand / 1e3, 1), fea_midspan_bottom_chord_kN=round(float(np.mean([r["N"] for r in mid_chords])) / 1e3, 1),
                   max_utilisation=round(worst[0]["util"], 3), critical=[dict(kind=r["kind"], x_mid_m=round((X[r["a"]][0] + X[r["b"]][0]) / 2, 2), N_kN=round(r["N"] / 1e3, 1),
                                                                               sigma_MPa=round(r["sigma"] / 1e6, 1), util=round(r["util"], 3), governed_by="buckling" if r.get("util_buckling", 0) > r["util_stress"] else "stress") for r in worst],
                   by_kind={k: dict(max_tension_kN=round(max([r["N"] for r in R if r["kind"] == k] + [0]) / 1e3, 1), max_compression_kN=round(-min([r["N"] for r in R if r["kind"] == k] + [0]) / 1e3, 1),
                                    max_util=round(max(r["util"] for r in R if r["kind"] == k), 3)) for k in SEC})
    json.dump(summary, open("results/bridge.json", "w"), indent=1); print(json.dumps({k: v for k, v in summary.items() if k not in ("by_kind", "critical", "sections")}, indent=1))
    np.save("build/bridge_u.npy", np.vstack([uu, us])); json.dump([dict(a=r["a"], b=r["b"], kind=r["kind"], N=r["N"], util=r["util"], sa=r["sigma_axial"]) for r in R], open("build/bridge_members.json", "w"))
    np.save("build/bridge_X.npy", X)
