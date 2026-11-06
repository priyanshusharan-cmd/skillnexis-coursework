"""Photorealistic renders with Mitsuba 3 (physically based path tracer): PBR materials (brass, brushed and anodised
aluminium, steel, acetal), a three-point area-light setup, soft ground shadows, 1920x1080.
    python src/render.py [hero|exploded|closeup ...]  -> renders/*.png"""
import os, struct, sys
import numpy as np
sys.path.insert(0, "src")
import mitsuba as mi
mi.set_variant("llvm_ad_rgb")
from assembly import build, shapes, MATERIAL
B = "build"; os.makedirs("renders", exist_ok=True)
BSDF = {  # principled BSDF parameters per material
    "aluminium_anodised": dict(base_color=[0.11, 0.13, 0.17], metallic=0.6, roughness=0.42), "aluminium_brushed": dict(base_color=[0.86, 0.87, 0.88], metallic=1.0, roughness=0.28),
    "steel": dict(base_color=[0.72, 0.73, 0.75], metallic=1.0, roughness=0.18), "brass": dict(base_color=[0.88, 0.68, 0.34], metallic=1.0, roughness=0.22),
    "acetal_white": dict(base_color=[0.90, 0.90, 0.87], metallic=0.0, roughness=0.45, specular=0.4), "steel_black": dict(base_color=[0.05, 0.05, 0.055], metallic=0.7, roughness=0.35),
    "aluminium_red": dict(base_color=[0.62, 0.07, 0.05], metallic=0.5, roughness=0.3)}
def write_ply(shape, path, tol=0.03, ang=0.12):
    verts, tris = shape.tessellate(tol, ang); V = np.array([v.toTuple() for v in verts], np.float32) / 100.0   # mm -> scene units (1 = 100 mm)
    Fc = np.array(tris, np.int32); N = np.zeros_like(V)
    fn = np.cross(V[Fc[:, 1]] - V[Fc[:, 0]], V[Fc[:, 2]] - V[Fc[:, 0]])
    for k in range(3): np.add.at(N, Fc[:, k], fn)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    with open(path, "wb") as f:
        f.write(f"ply\nformat binary_little_endian 1.0\nelement vertex {len(V)}\nproperty float x\nproperty float y\nproperty float z\nproperty float nx\nproperty float ny\nproperty float nz\nelement face {len(Fc)}\nproperty list uchar int vertex_indices\nend_header\n".encode())
        f.write(np.hstack([V, N]).astype("<f4").tobytes()); f.write(b"".join(struct.pack("<B3i", 3, *t) for t in Fc))
def scene(parts, cam_origin, cam_target, fov=28, spp=384):
    sc = {"type": "scene", "integrator": {"type": "path", "max_depth": 8},
          "sensor": {"type": "perspective", "fov": fov, "to_world": mi.ScalarTransform4f().look_at(origin=cam_origin, target=cam_target, up=[0, 0, 1]),
                     "film": {"type": "hdrfilm", "width": 1920, "height": 1080, "rfilter": {"type": "gaussian"}}, "sampler": {"type": "independent", "sample_count": spp}},
          "env": {"type": "constant", "radiance": {"type": "rgb", "value": [0.16, 0.17, 0.19]}},
          "ground": {"type": "rectangle", "to_world": mi.ScalarTransform4f().scale([400, 400, 1]), "bsdf": {"type": "principled", "base_color": {"type": "rgb", "value": [0.55, 0.56, 0.58]}, "roughness": 0.6}}}
    def light(name, pos, target, size, rgb):
        sc[name] = {"type": "rectangle", "to_world": mi.ScalarTransform4f().look_at(origin=pos, target=target, up=[0, 0, 1]) @ mi.ScalarTransform4f().scale([size, size, 1]),
                    "emitter": {"type": "area", "radiance": {"type": "rgb", "value": rgb}}, "bsdf": {"type": "null"}}   # lights are invisible from behind
    light("key", [-3.5, -4.5, 5.0], [0, 0, 0.5], 1.6, [9.0, 8.4, 7.6]); light("fill", [5.0, -3.0, 2.5], [0, 0, 0.5], 2.0, [1.6, 1.8, 2.1]); light("rim", [0.5, 5.5, 4.0], [0, 0, 0.6], 1.2, [7.5, 7.8, 8.4])
    for n, (part, shp) in parts.items():
        ply = f"{B}/{n}.ply"; write_ply(shp, ply)
        bsdf = {"type": "principled"}; prm = BSDF[MATERIAL[part]]
        bsdf.update({"base_color": {"type": "rgb", "value": prm["base_color"]}, "metallic": prm["metallic"], "roughness": prm["roughness"]})
        if "specular" in prm: bsdf["specular"] = prm["specular"]
        sc[n] = {"type": "ply", "filename": ply, "bsdf": bsdf, "face_normals": False}
    return mi.load_dict(sc)
def save(img, path):
    bmp = mi.Bitmap(img).convert(mi.Bitmap.PixelFormat.RGB, mi.Struct.Type.UInt8, srgb_gamma=True); bmp.write(path)
VIEWS = {"hero": dict(theta=0, explode=0, origin=[-3.0, -4.4, 2.6], target=[0, 0, .5], fov=26),
         "exploded": dict(theta=0, explode=1.0, origin=[4.8, -6.9, 4.3], target=[0, -0.15, 1.15], fov=33),
         "closeup": dict(theta=0, explode=0, origin=[-0.9, -2.2, 1.95], target=[-0.25, 0, .55], fov=24)}
if __name__ == "__main__":
    S = shapes()
    for v in (sys.argv[1:] or VIEWS):
        c = VIEWS[v]; parts = build(c["theta"], c["explode"], S)
        if v == "closeup": parts = {k: p for k, p in parts.items() if not k.startswith("plate_front")}   # see the mesh through the open side
        sc = scene(parts, c["origin"], c["target"], c["fov"]); img = mi.render(sc); save(img, f"renders/{v}.png"); print("rendered", v, flush=True)
