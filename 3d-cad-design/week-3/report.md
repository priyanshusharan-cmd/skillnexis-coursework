# FEA report: 12 m steel footbridge (Warren through-truss)

**Author:** Priyanshu Sharan · **Date:** 6 Nov 2026 · **Model:** `src/bridge.py` (3D frame FEA, written from first
principles) · **Results:** `results/bridge.json`

## 1. Objective
Size the members of a 12 m pedestrian through-truss, verify strength and stiffness under crowd loading, and show
where the structure works hardest.

## 2. Model
| Item | Value |
|---|---|
| Geometry | span 12.0 m, 8 panels × 1.5 m, depth 2.5 m, width 2.0 m. Two Warren trusses; floor beams at every bottom node; top struts; X plan bracing in the deck plane |
| Elements | 104 Euler–Bernoulli 3D beam elements (12 degrees of freedom each, rigid joints) on 43 nodes. Floor beams are split at mid-span so deck loads bend them |
| Material | S355 steel: E = 210 GPa, G = 81 GPa, f_y = 355 MPa, ρ = 7850 kg/m³ |
| Sections | bottom chord SHS 80×80×4 · top chord SHS 90×90×5 · diagonals SHS 50×50×3 · floor beams RHS 80×120×4 · top struts SHS 50×50×3 · plan bracing CHS 33.7×2.6 |
| Supports | four bearings: fixed (x, y, z), guided (x, z), guided (y, z) and free-sliding (z), so the bridge can expand freely without a mechanism |

## 3. Loads and combinations
| Load | Value | Total |
|---|---|---|
| G1: self-weight of the steel | computed from member lengths × area × ρg | 12.2 kN |
| G2: timber deck and fixings | 0.6 kN/m² | 14.4 kN |
| Q: crowd load | 5.0 kN/m² (the EN 1991-2 pedestrian crowd value) | 120.0 kN |
| ULS | 1.35 (G1 + G2) + 1.5 Q | 216.0 kN |
| SLS | Q only (for live-load deflection) | 120.0 kN |

The deck planks span between floor beams. Each floor beam's share is applied as a uniform load, lumped B/4 · B/2 ·
B/4 to its end and mid-span nodes.

## 4. Checks performed on the model
* **Equilibrium:** the sum of vertical reactions, 216.0 kN, equals the applied ULS load of 216.0 kN.
* **Hand statics:**
  * each truss takes half the load: w = 9.0 kN/m;
  * the mid-span bottom chord force is about M/h = wL²/8 ÷ h = **64.8 kN**;
  * FEA gives **60.4 kN**.

  The member checked lies between nodes at 4.5–6.0 m, where M is 1.6 % below the maximum. Rigid joints and the plan
  bracing also share part of the force, so a few percent less is expected. A difference of 6.8 % confirms that the
  model behaves like the truss it represents.
* **Sense of forces:** the bottom chord is in tension and the top chord in compression. The diagonals alternate
  tension and compression, with the largest forces at the supports, where the shear is largest. The top struts carry
  almost nothing under vertical load, as expected; they exist for wind and lateral stability.

## 5. Results (ULS unless stated)
| Member group | Max tension | Max compression | Max utilisation |
|---|---|---|---|
| Bottom chord | 60.4 kN | — | 0.15 |
| Top chord | — | 64.7 kN | 0.12 |
| Diagonals | 48.5 kN | 49.3 kN | **0.89** (end diagonals, buckling) |
| Floor beams | — | 6.1 kN | 0.33 (bending) |
| Plan bracing | 3.9 kN | — | 0.08 |

How utilisation was calculated:
* **Stress:** utilisation = max(σ / f_y, N_Ed / N_b,Rd), where σ = |N|/A + |M_y|/W_y + |M_z|/W_z.
* **Buckling:** N_b,Rd uses EN 1993-1-1 §6.3.1 with buckling curve *a* (hot-finished hollow sections). The effective
  length is the member length, which is conservative for diagonals.

**Deflection:** **4.3 mm** under SLS crowd load, against an L/400 limit of 30 mm, so the bridge is very stiff. ULS
deflection is 7.7 mm.

Figures:
* `renders/bridge-axial-stress.png`: axial stress, tension blue and compression red, deformation ×80
* `renders/bridge-utilisation.png`: utilisation heat map
* `anim/bridge-deformation.mp4`: load cycling 0 → ULS → 0, deformation ×80

## 6. Design iteration
The first sizing (chords SHS 120×120×6.3, diagonals SHS 80×80×5) gave a maximum utilisation of only **0.17**. That
is roughly 6× stronger than needed and more than doubles the steel. After resizing:
* the maximum utilisation is **0.89**;
* steel self-weight falls from 26.6 kN to 12.2 kN (**−54 %**);
* deflection stays well inside the limit.

The end diagonals now govern, through buckling. If more margin is wanted, the next step is SHS 60×60×3 at the two
end panels only.

## 7. Limitations and next steps
* **Interaction check:** combined bending + compression (EN 1993-1-1 §6.3.3) wasn't done. The diagonals' bending
  stresses from joint rigidity are small (σ ≈ 117 MPa total vs 355), but a full check is needed.
* **Missing load cases:** wind (lateral and on the deck underside), thermal, and an accidental service vehicle.
* **Vibration:** the footbridge's natural frequencies weren't checked. Vertical modes should be above 5 Hz, or a
  dynamic crowd analysis done (Sétra/HiVoSS).
* **Connections and lateral stability:** connection design and the lateral-torsional stability of the top chord as
  a U-frame weren't covered.
* **Validation:** the same frame code was checked only by statics and equilibrium here. The solid FEA code was
  validated separately against beam theory (README §1).
