"""Task 3: animation of the week-2 gear train: 2.5 s assembling from the exploded view, then the crank turns one full
revolution while the coupled joints drive the idler (-15/25) and output (+15/40). Uses the week-2 parametric parts
and mate solver unchanged; each frame re-solves the placements.   python src/animate_gears.py -> anim/gear-train.mp4/.gif"""
import math, os, subprocess, sys
import numpy as np, pyvista as pv
pv.OFF_SCREEN = True
W2 = os.path.abspath("../week-2"); here = os.getcwd(); sys.path.insert(0, W2 + "/src"); os.chdir(W2)
import assembly as AS                                   # week-2 assembly (reads its mesh-check phases)
S = AS.shapes(); os.chdir(here)
COL = {"aluminium_anodised": ("#2B3442", .35), "aluminium_brushed": ("#C9CCD1", .7), "steel": ("#A8ACB3", .9), "brass": ("#D2A24C", .9),
       "acetal_white": ("#EEEEE8", .25), "steel_black": ("#1E1F22", .5), "aluminium_red": ("#B3241B", .6)}
def poly(shape):
    v, t = shape.tessellate(0.05, 0.15); V = np.array([p.toTuple() for p in v]); F = np.hstack([np.full((len(t), 1), 3), np.array(t)]).ravel()
    return pv.PolyData(V, F).compute_normals(split_vertices=True, feature_angle=35)
MESH = {k: poly(s) for k, s in S.items()}
def matrix(rx, ra, t):
    M = np.eye(4)
    if rx is not None:
        c, s = math.cos(math.radians(rx)), math.sin(math.radians(rx)); M = np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]) @ M
    if ra:
        c, s = math.cos(math.radians(ra)), math.sin(math.radians(ra)); M = np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]) @ M
    M[:3, 3] += t; return M
FPS, T_ASM, T_TURN = 30, 2.5, 6.0
pl = pv.Plotter(off_screen=True, window_size=(1600, 900)); pl.set_background("#EDEFF2", top="#FFFFFF")
pl.add_mesh(pv.Plane(center=(0, 0, -.5), direction=(0, 0, 1), i_size=6000, j_size=6000), color="#E3E6EA", ambient=.45)
actors = {}
for n, part, rx, ra, t in AS.placements(0, 1):
    col, spec = COL[AS.MATERIAL[part]]; actors[n] = pl.add_mesh(MESH[part], color=col, smooth_shading=True, specular=spec, specular_power=40, ambient=.18, diffuse=.85)
txt = pl.add_text("", position=(36, 700), font_size=15, color="#14213D")
pl.camera_position = [(-290, -410, 260), (0, 0, 55), (0, 0, 1)]; pl.enable_anti_aliasing("ssaa"); pl.enable_shadows()
os.makedirs("anim", exist_ok=True); os.makedirs("build/frames", exist_ok=True)
ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "image2pipe", "-c:v", "png", "-framerate", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                       "-pix_fmt", "yuv420p", "anim/gear-train.tmp.mp4"], stdin=subprocess.PIPE)
n_frames = int((T_ASM + 0.5 + T_TURN) * FPS)
for f in range(n_frames):
    t = f / FPS; e = max(0.0, 1 - t / T_ASM); e = e * e * (3 - 2 * e)                # ease the explode factor 1 -> 0
    th = 0.0 if t < T_ASM + .5 else 360.0 * (t - T_ASM - .5) / T_TURN
    for n, part, rx, ra, tr in AS.placements(th, e): actors[n].user_matrix = matrix(rx, ra, tr)
    z1, z2, z3 = AS.P["z_in"], AS.P["z_idler"], AS.P["z_out"]
    txt.SetInput(("Assembling (mates solved each frame)" if t < T_ASM else "Coupled revolute joints") +
                 f"\ncrank / input  θ = {th:6.1f}°\nidler  −θ·15/25 = {-th * z1 / z2 + 0.0:7.1f}°\noutput +θ·15/40 = {th * z1 / z3:6.1f}°")
    pl.render()
    img = pl.screenshot(return_img=True); from PIL import Image; import io; b = io.BytesIO(); Image.fromarray(img).save(b, "PNG"); ff.stdin.write(b.getvalue())
ff.stdin.close(); ff.wait(); os.replace("anim/gear-train.tmp.mp4", "anim/gear-train.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "anim/gear-train.mp4", "-vf", "fps=15,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse", "anim/gear-train.gif"], check=True)
print("animation", n_frames, "frames")
