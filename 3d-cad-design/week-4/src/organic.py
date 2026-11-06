"""Organic / sculpted module: a pebble-shaped succulent planter, modelled as a signed distance field (two blended
ellipsoids + gentle surface ripples), hollowed to a 2.4 mm wall, flattened at the base, meshed with marching cubes,
then joined to the CAD dovetail key with a manifold boolean. (The CAD-vs-sculpt split is how product designers
combine Fusion-style solids with ZBrush/Blender sculpts.)   python src/organic.py -> cad/stl/pebble_planter.stl"""
import sys
import numpy as np, trimesh
from skimage.measure import marching_cubes
sys.path.insert(0, "src")
import cadquery as cq
from product import key, P
def smin(a, b, k):                                       # polynomial smooth minimum: blends two shapes with a fillet of size k
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)
def ellipsoid(x, y, z, c, r):
    q = np.sqrt(((x - c[0]) / r[0]) ** 2 + ((y - c[1]) / r[1]) ** 2 + ((z - c[2]) / r[2]) ** 2); return (q - 1) * min(r)
def pebble_sdf(x, y, z):
    d = smin(ellipsoid(x, y, z, (-1, 2, 22), (30, 27, 26)), ellipsoid(x, y, z, (12, -5, 16), (22, 21, 19)), 9.0)
    ang = np.arctan2(y, x); d += .55 * np.sin(7 * ang + .08 * z) * np.clip(z / 40, 0, 1)                   # sculpted ripples, fading to the base
    return d
WALL, TOP = 2.4, 40.0
h = .55; xs = np.arange(-40, 40, h); ys = np.arange(-40, 40, h); zs = np.arange(-1, 52, h)
X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij"); outer = pebble_sdf(X, Y, Z)
shell = np.maximum(outer, -(outer + WALL))                                   # hollow: inside the outer skin, outside the inner offset
shell = np.where(Z < WALL, outer, shell)                                     # solid floor
shell = np.maximum(shell, -Z); shell = np.maximum(shell, Z - TOP)            # flat base at z = 0, cut open at the top
v, f, n, _ = marching_cubes(shell, 0.0, spacing=(h, h, h)); v += np.array([xs[0], ys[0], zs[0]])
m = trimesh.Trimesh(v, f, process=True); m = trimesh.smoothing.filter_taubin(m, iterations=12); m.vertices[:, 2] = np.maximum(m.vertices[:, 2], 0.0)   # keep the base flat after smoothing
k = key(56); kv, kt = k.val().tessellate(.05, .2); km = trimesh.Trimesh(np.array([p.toTuple() for p in kv]), np.array(kt))
km.apply_translation((0, 0, .3))                                                                       # overlap the floor slightly for a clean union
out = trimesh.boolean.union([m, km], engine="manifold")
out = out.simplify_quadric_decimation(face_count=60000)                    # keep the print file light (detail stays below 0.1 mm)
out.export("cad/stl/pebble_planter.stl")
print("pebble", "watertight", out.is_watertight, "volume cm3", round(out.volume / 1000, 1), "bounds", np.round(out.bounds, 1).tolist(), "faces", len(out.faces))
