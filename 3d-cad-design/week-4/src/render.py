"""Product renders (Mitsuba 3, HDRI-lit with the week-3 studio HDRI): assembled with props (phone, pens, succulent),
and the modules slid back along their rails.   python src/render.py [hero|exploded]"""
import math, os, struct, sys
import numpy as np, trimesh
W2 = os.path.abspath("../week-2"); here = os.getcwd(); sys.path.insert(0, W2 + "/src"); os.chdir(W2)
import mitsuba as mi
mi.set_variant("llvm_ad_rgb")
import render as R2
os.chdir(here); sys.path.insert(0, "src")
import cadquery as cq
from assemble import parts, placements
from product import P
ENV = mi.Bitmap(os.path.abspath("../week-3/renders/studio-hdri.exr"))
MAT = {"base": ([0.10, 0.10, 0.11], 0.0, 0.55), "phone_stand": ([0.80, 0.32, 0.16], 0.0, 0.45), "pen_cup": ([0.42, 0.55, 0.43], 0.0, 0.45), "pebble_planter": ([0.88, 0.86, 0.80], 0.0, 0.6),
       "phone": ([0.02, 0.02, 0.025], 0.3, 0.08), "screen": ([0.03, 0.05, 0.08], 0.0, 0.03), "pen1": ([0.10, 0.25, 0.70], 0.0, 0.3), "pen2": ([0.85, 0.75, 0.15], 0.0, 0.3),
       "pen3": ([0.12, 0.12, 0.12], 0.6, 0.25), "plant": ([0.25, 0.48, 0.30], 0.0, 0.5), "soil": ([0.18, 0.12, 0.08], 0.0, 0.9)}
def mesh_ply(m, path, scale=.01):
    V = (m.vertices * scale).astype("<f4"); N = m.vertex_normals.astype("<f4"); F = m.faces.astype(np.int32)
    with open(path, "wb") as f:
        f.write(f"ply\nformat binary_little_endian 1.0\nelement vertex {len(V)}\nproperty float x\nproperty float y\nproperty float z\nproperty float nx\nproperty float ny\nproperty float nz\nelement face {len(F)}\nproperty list uchar int vertex_indices\nend_header\n".encode())
        f.write(np.hstack([V, N]).tobytes()); f.write(b"".join(struct.pack("<B3i", 3, *t) for t in F))
def props(sx):
    """Simple props placed relative to the phone stand position: a phone leaning on it, three pens, a succulent."""
    a = math.radians(P["back_angle"]); out = {}
    ph = cq.Workplane("XY").box(71, 8, 146).edges("|Y").fillet(9).edges().fillet(1.5).val()
    ph = ph.rotate(cq.Vector(), cq.Vector(1, 0, 0), -(90 - P["back_angle"])).translate(cq.Vector(sx, -26 - 4 / math.tan(a) + 2, P["base_t"] + 4 + 73 * math.sin(a)))
    out["phone"] = ph
    for i, (dx, dy, tilt, L) in enumerate(((-12, 6, 8, 140), (10, -6, -10, 132), (4, 12, 4, 125))):
        pen = cq.Workplane("XY").circle(4.5).extrude(L).faces(">Z").chamfer(2).val().rotate(cq.Vector(), cq.Vector(1, 0, 0), tilt).translate(cq.Vector(dx, dy, P["base_t"] + 4))
        out[f"pen{i + 1}"] = pen
    return out
def scene(slide, cam, target, fov, spp=384, w=1920):
    sc = {"type": "scene", "integrator": {"type": "path", "max_depth": 10},
          "sensor": {"type": "perspective", "fov": fov, "to_world": mi.ScalarTransform4f().look_at(origin=cam, target=target, up=[0, 0, 1]),
                     "film": {"type": "hdrfilm", "width": w, "height": w * 9 // 16, "rfilter": {"type": "gaussian"}}, "sampler": {"type": "independent", "sample_count": spp}},
          "env": {"type": "envmap", "bitmap": ENV, "to_world": mi.ScalarTransform4f().rotate([1, 0, 0], 90) @ mi.ScalarTransform4f().rotate([0, 1, 0], 25), "scale": 1.3},
          "desk": {"type": "rectangle", "to_world": mi.ScalarTransform4f().scale([300, 300, 1]), "bsdf": {"type": "principled", "base_color": {"type": "rgb", "value": [.55, .42, .30]}, "roughness": .5}}}
    S = parts(); pl = placements(slide); os.makedirs("build", exist_ok=True)
    def add(name, shp, mat, tr=(0, 0, 0)):
        ply = os.path.abspath(f"build/{name}.ply"); R2.write_ply(shp.translate(cq.Vector(*tr)), ply); c, met, r = MAT[mat]
        sc[name] = {"type": "ply", "filename": ply, "face_normals": False, "bsdf": {"type": "principled", "base_color": {"type": "rgb", "value": c}, "metallic": met, "roughness": r}}
    for n, s in S.items(): add(n, s, n, pl[n])
    peb = trimesh.load("cad/stl/pebble_planter.stl"); peb.apply_translation(pl["pebble_planter"]); mesh_ply(peb, os.path.abspath("build/peb.ply"))
    c, met, r = MAT["pebble_planter"]; sc["pebble"] = {"type": "ply", "filename": os.path.abspath("build/peb.ply"), "face_normals": False, "bsdf": {"type": "principled", "base_color": {"type": "rgb", "value": c}, "roughness": r}}
    if slide == 0:
        for n, s in props(pl["phone_stand"][0]).items(): add(n, s if n == "phone" else s.translate(cq.Vector(*pl["pen_cup"][:2], 0)), n)
        px, py, pz = pl["pebble_planter"]; soil = cq.Workplane("XY").circle(22).extrude(2).val().translate(cq.Vector(px + 3, py, pz + 33)); add("soil", soil, "soil")
        for i in range(9):                                          # succulent rosette: tilted ellipsoid leaves
            ang = i * 40; leaf = cq.Workplane("XY").sphere(1).val().scale(1.0)
            lf = cq.Solid.makeSphere(7).transformGeometry(cq.Matrix([[1, 0, 0, 0], [0, .45, 0, 0], [0, 0, 1.8, 0]])) if False else cq.Workplane("XY").ellipse(6, 3).extrude(14).edges().fillet(1.4).val()
            lf = lf.rotate(cq.Vector(), cq.Vector(1, 0, 0), 35 + 15 * (i % 2)).rotate(cq.Vector(), cq.Vector(0, 0, 1), ang).translate(cq.Vector(px + 3, py, pz + 34)); add(f"leaf{i}", lf, "plant")
    return mi.load_dict(sc)
SHOTS = {"hero": (0.0, [-4.6, -3.6, 2.6], [0.1, 0.15, .5], 34), "exploded": (1.0, [-1.6, -5.2, 3.6], [0.0, 1.0, .3], 36)}
if __name__ == "__main__":
    for v in (sys.argv[1:] or SHOTS):
        slide, cam, tgt, fov = SHOTS[v]; prev = os.environ.get("PREVIEW")
        img = mi.render(scene(slide, cam, tgt, fov, *((32, 640) if prev else ()))); v = v + ("-preview" if prev else ""); R2.save(img, f"renders/{v}.png"); print("rendered", v, flush=True)
