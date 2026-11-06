"""Task 4: photorealistic product shot lit only by an HDRI environment map (Mitsuba 3 path tracer).
No HDRI downloads are possible here, so a studio HDRI is generated: an equirectangular high-dynamic-range image with
two large softboxes (key a few hundred times brighter than the background), a rim strip behind and a soft overhead. It is saved as
renders/studio-hdri.exr so the shot is reproducible; any Poly Haven HDRI can be dropped in instead.
    python src/hdri_shot.py  -> renders/product-shot-hdri.png, renders/studio-hdri-preview.png"""
import math, os, sys
import numpy as np
W2 = os.path.abspath("../week-2"); here = os.getcwd(); sys.path.insert(0, W2 + "/src"); os.chdir(W2)
import mitsuba as mi
mi.set_variant("llvm_ad_rgb")
import render as R2                                        # week-2 PLY writer and materials
import assembly as AS
S = AS.shapes(); parts = AS.build(55.0, 0, S); os.chdir(here)
# ---------------- studio HDRI (equirectangular, linear radiance)
Wd, Hd = 2048, 1024; u = (np.arange(Wd) + .5) / Wd; v = (np.arange(Hd) + .5) / Hd; az, el = np.meshgrid((u - .5) * 2 * math.pi, (.5 - v) * math.pi)
env = np.zeros((Hd, Wd, 3), np.float32); base = np.clip(.035 + .05 * np.sin(np.maximum(el, 0)), 0, None); env[...] = base[..., None] * np.array([1.0, 1.0, 1.05])
env[el < 0] = np.array([.02, .02, .022])                                                    # dark floor reflection
def softbox(az0, el0, w, h, val, col):
    d_az = np.angle(np.exp(1j * (az - math.radians(az0)))); m = (np.abs(d_az) < math.radians(w) / 2) & (np.abs(el - math.radians(el0)) < math.radians(h) / 2)
    fall = np.exp(-((d_az / math.radians(w / 2)) ** 8 + ((el - math.radians(el0)) / math.radians(h / 2)) ** 8)); env[m] = np.maximum(env[m], (val * fall[m])[:, None] * np.array(col))
softbox(-50, 32, 40, 30, 16.0, [1.0, .96, .9]); softbox(70, 20, 30, 40, 7.0, [.9, .95, 1.0]); softbox(175, 25, 70, 6, 22.0, [1, 1, 1]); softbox(0, 80, 120, 15, 3.0, [1, 1, 1])
mi.Bitmap(env).write("renders/studio-hdri.exr")
prev = np.clip((env / (1 + env)) ** (1 / 2.2), 0, 1); from PIL import Image; Image.fromarray((prev * 255).astype(np.uint8)).resize((1024, 512)).save("renders/studio-hdri-preview.png")
# ---------------- scene: envmap lighting only, dark glossy floor
sc = {"type": "scene", "integrator": {"type": "path", "max_depth": 10},
      "sensor": {"type": "perspective", "fov": 22, "to_world": mi.ScalarTransform4f().look_at(origin=[-3.9, -5.0, 2.2], target=[0.0, 0, .45], up=[0, 0, 1]),
                 "film": {"type": "hdrfilm", "width": 1920, "height": 1080, "rfilter": {"type": "gaussian"}}, "sampler": {"type": "independent", "sample_count": 512}},
      "env": {"type": "envmap", "bitmap": mi.Bitmap(env), "to_world": mi.ScalarTransform4f().rotate([1, 0, 0], 90), "scale": 1.0},
      "floor": {"type": "rectangle", "to_world": mi.ScalarTransform4f().scale([300, 300, 1]), "bsdf": {"type": "principled", "base_color": {"type": "rgb", "value": [.05, .05, .055]}, "roughness": .18, "specular": .6}}}
os.makedirs("build", exist_ok=True)
for n, (part, shp) in parts.items():
    ply = f"build/{n}.ply"; R2.write_ply(shp, ply); prm = R2.BSDF[AS.MATERIAL[part]]
    b = {"type": "principled", "base_color": {"type": "rgb", "value": prm["base_color"]}, "metallic": prm["metallic"], "roughness": prm["roughness"]}
    if "specular" in prm: b["specular"] = prm["specular"]
    sc[n] = {"type": "ply", "filename": os.path.abspath(ply), "bsdf": b, "face_normals": False}
img = mi.render(mi.load_dict(sc)); R2.save(img, "renders/product-shot-hdri.png"); print("product shot done")
