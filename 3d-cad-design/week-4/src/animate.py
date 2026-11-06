"""Assembly animation: the modules drop onto their rails and slide in (placements(slide) from assemble.py, eased),
a turntable orbit, then a rearrangement: the pen cup and the planter swap rails.   python src/animate.py
-> anim/stackr-assembly.mp4 / .gif"""
import io, math, os, subprocess, sys
import numpy as np, pyvista as pv, trimesh
from PIL import Image
pv.OFF_SCREEN = True; sys.path.insert(0, "src")
from assemble import parts, placements, RAILS
from product import P
COL = {"base": "#2A2A2E", "phone_stand": "#D06A3E", "pen_cup": "#7FA584", "pebble_planter": "#ECE8DD"}
def poly(m):
    return pv.PolyData(m.vertices, np.hstack([np.full((len(m.faces), 1), 3), m.faces]).ravel()).compute_normals(split_vertices=True, feature_angle=35)
def tri(s):
    v, t = s.tessellate(.04, .15); return trimesh.Trimesh(np.array([p.toTuple() for p in v]), np.array(t))
M = {n: tri(s) for n, s in parts().items()}; M["pebble_planter"] = trimesh.load("cad/stl/pebble_planter.stl")
FPS = 30; T1, H1, T2, H2, T3, H3 = 4.0, .6, 5.0, .3, 5.0, 1.0
ease = lambda u: (lambda c: c * c * (3 - 2 * c))(min(1.0, max(0.0, u)))
def swap(u, x0, x1, lift):
    """5 equal phases: pull back 110 mm along the rail, lift, traverse to the other rail, lower, slide in."""
    a, b, c, d, e = (ease(u * 5 - k) for k in range(5))
    return (x0 + (x1 - x0) * c, 110 * a * (1 - e), P["base_t"] + lift * b * (1 - d))
pl = pv.Plotter(off_screen=True, window_size=(1600, 900)); pl.set_background("#EFE9E1", top="#FFFFFF")
pl.add_mesh(pv.Plane(center=(0, 40, -.3), direction=(0, 0, 1), i_size=3000, j_size=3000), color="#E4DCD1", ambient=.5)
A = {n: pl.add_mesh(poly(m), color=COL[n], smooth_shading=True, specular=.25, specular_power=25, ambient=.2, diffuse=.85) for n, m in M.items()}
txt = pl.add_text("", position=(36, 820), font_size=15, color="#222222")
pl.enable_anti_aliasing("ssaa"); pl.enable_shadows()
FOC = np.array([0, 30, 40.0]); R0, EL = 420.0, 30.0
def cam(az):
    a, e = math.radians(az), math.radians(EL); return [tuple(FOC + R0 * np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])), tuple(FOC), (0, 0, 1)]
os.makedirs("anim", exist_ok=True)
ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                       "-pix_fmt", "yuv420p", "anim/stackr.tmp.mp4"], stdin=subprocess.PIPE)
total = T1 + H1 + T2 + H2 + T3 + H3; N = int(total * FPS); xc, xp = RAILS["pen_cup"], RAILS["pebble_planter"]
for f in range(N):
    t = f / FPS; az = 235.0
    if t < T1:                                                       # modules arrive one after another
        pos = {"base": (0, 0, 0)}
        for i, n in enumerate(RAILS):
            u = ease((t - i * .7) / (T1 - 1.4)); pos[n] = placements(1 - u)[n]
        label = "1 · modules drop onto their dovetail rails and slide in"
    elif t < T1 + H1 + T2:
        pos = placements(0); az = 235.0 + 360 * ease((t - T1 - H1) / T2); label = "2 · assembled: 210 × 96 × 105 mm, 219 g of PLA"
    else:
        u = (t - T1 - H1 - T2 - H2) / T3; pos = placements(0)
        pos["pen_cup"] = swap(u, xc, xp, 0.0); pos["pebble_planter"] = swap(u, xp, xc, 130.0); label = "3 · rearrange: any module fits any rail"
    for n, a in A.items():
        Mx = np.eye(4); Mx[:3, 3] = pos[n]; a.user_matrix = Mx
    pl.camera_position = cam(az); txt.SetInput(label); pl.render()
    b = io.BytesIO(); Image.fromarray(pl.screenshot(return_img=True)).save(b, "JPEG", quality=92); ff.stdin.write(b.getvalue())
ff.stdin.close(); ff.wait(); os.replace("anim/stackr.tmp.mp4", "anim/stackr-assembly.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "anim/stackr-assembly.mp4", "-vf", "fps=12,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse", "anim/stackr-assembly.gif"], check=True)
print("frames", N, "seconds", total)
