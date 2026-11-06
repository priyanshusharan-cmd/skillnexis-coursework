"""3D-print preparation for every part (PLA, 0.4 mm nozzle, 0.2 mm layers):
  * wall thickness: rays cast inward from surface samples measure local thickness (minimum allowed: 2 perimeters = 0.9 mm)
  * overhangs: downward faces steeper than 45° from vertical need support (bed-contact faces excluded)
  * slicing: the mesh is cut every 0.2 mm; perimeters, 15 % grid infill and 4 solid top/bottom layers give extrusion
    length, filament mass and a print-time estimate (60 mm/s, +25 % travel/accel), plus a layer preview image.
    python src/print_prep.py  -> results/print-report.json, results/print-*.png"""
import json, math
import numpy as np, trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
LH, LW, PERIM, INFILL, SOLID, SPEED, DENS = 0.2, 0.45, 2, 0.15, 4, 60.0, 1.24
PARTS = {"base": "flat, top face up (groove flanks are 30° from vertical, self-supporting)", "phone_stand": "upright; tree supports under the module floor beside the key and under the A-frame apex",
         "pen_cup": "upright; supports under the floor beside the key", "pebble_planter": "upright; supports under the floor beside the key"}
def thickness(m, n=4000, seed=1):
    pts, fi = trimesh.sample.sample_surface_even(m, n, seed=seed); nrm = m.face_normals[fi]
    loc, idx_ray, _ = m.ray.intersects_location(pts - nrm * 1e-3, -nrm, multiple_hits=False)
    d = np.full(len(pts), np.inf); d[idx_ray] = np.linalg.norm(loc - pts[idx_ray], axis=1); return d[np.isfinite(d)]
def overhang(m, limit=45):
    z0 = m.bounds[0, 2]; down = m.face_normals[:, 2] < -math.cos(math.radians(limit)); onbed = m.triangles_center[:, 2] < z0 + .3
    return float(m.area_faces[down & ~onbed].sum())
def slice_stats(m, name):
    z0, z1 = m.bounds[:, 2]; zs = np.arange(z0 + LH / 2, z1, LH); secs = m.section_multiplane(plane_origin=[0, 0, 0], plane_normal=[0, 0, 1], heights=list(zs))
    length = 0.0; areas = []; polys_for_preview = {}
    for k, s in enumerate(secs):
        if s is None: areas.append(0); continue
        polys = [Polygon(p) for p in s.polygons_full] if hasattr(s, "polygons_full") else []
        geom = unary_union(polys) if polys else Polygon(); A = geom.area; areas.append(A); L = geom.length
        solid = k < SOLID or k >= len(secs) - SOLID
        inner = geom.buffer(-PERIM * LW); ia = inner.area if not inner.is_empty else 0
        length += PERIM * L + (ia / LW if solid else ia * INFILL * 2 / LW / 2 * 2)
        if k in (int(len(secs) * .1), int(len(secs) * .5), int(len(secs) * .85)): polys_for_preview[round(float(zs[k]), 1)] = geom
    vol_cm3 = length * LW * LH / 1000; return dict(layers=len(secs), extrusion_m=round(length / 1000, 1), filament_g=round(vol_cm3 * DENS, 1),
                                                   print_time_h=round(length / SPEED / 3600 * 1.25, 2), solid_volume_cm3=round(m.volume / 1000, 1)), polys_for_preview
if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    rep = {}; fig, axes = plt.subplots(len(PARTS), 3, figsize=(10, 3.2 * len(PARTS)))
    for r, (name, orient) in enumerate(PARTS.items()):
        m = trimesh.load(f"cad/stl/{name}.stl"); m.apply_translation([0, 0, -m.bounds[0, 2]])
        t = thickness(m); st, prev = slice_stats(m, name)
        rep[name] = dict(orientation=orient, watertight=bool(m.is_watertight), min_wall_mm=round(float(np.percentile(t, 2)), 2), median_wall_mm=round(float(np.median(t)), 2),
                         thin_below_0p9mm_pct=round(float((t < .9).mean() * 100), 2), support_area_cm2=round(overhang(m) / 100, 1), **st)
        for c, (z, g) in enumerate(prev.items()):
            ax = axes[r, c]; gs = g.geoms if isinstance(g, MultiPolygon) else [g]
            for p in gs:
                if p.is_empty: continue
                x, y = p.exterior.xy; ax.fill(x, y, color="#E8590C", alpha=.35); ax.plot(x, y, color="#E8590C", lw=1)
                for h in p.interiors: hx, hy = h.xy; ax.fill(hx, hy, color="white"); ax.plot(hx, hy, color="#E8590C", lw=1)
            ax.set_aspect("equal"); ax.axis("off"); ax.set_title(f"{name}  z = {z} mm", fontsize=9, loc="left")
        print(name, rep[name], flush=True)
    fig.tight_layout(); fig.savefig("results/print-layer-preview.png", dpi=110)
    tot = dict(filament_g=round(sum(v["filament_g"] for v in rep.values()), 1), print_time_h=round(sum(v["print_time_h"] for v in rep.values()), 1))
    json.dump({"settings": dict(layer_mm=LH, line_width_mm=LW, perimeters=PERIM, infill=INFILL, solid_layers=SOLID, speed_mm_s=SPEED, material="PLA 1.24 g/cm3"), "parts": rep, "total": tot},
              open("results/print-report.json", "w"), indent=1); print(tot)
