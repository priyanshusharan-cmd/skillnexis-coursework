"""Heat maps and deformation animation for the footbridge frame model (results from src/bridge.py)."""
import io, json, math, subprocess
import numpy as np, pyvista as pv
from PIL import Image
pv.OFF_SCREEN = True
X = np.load("build/bridge_X.npy"); U = np.load("build/bridge_u.npy")[0]; M = json.load(open("build/bridge_members.json")); D = U.reshape(-1, 6)[:, :3]
def tubes(scale, field):
    P = X + scale * D; segs = []
    for m in M:
        ln = pv.Line(P[m["a"]], P[m["b"]], resolution=8); ln.point_data["v"] = np.full(ln.n_points, m[field]); segs.append(ln)
    mesh = segs[0].merge(segs[1:]); return mesh.tube(radius=0.045 if field else .04, n_sides=14)
def scene(scale, field, clim, cmap, title, bar, size=(1600, 900)):
    p = pv.Plotter(off_screen=True, window_size=size); p.set_background("#F4F1EA", top="#FFFFFF")
    p.add_mesh(tubes(0, field), color="#B8BEC6", opacity=.25)                                 # undeformed ghost
    p.add_mesh(tubes(scale, field), scalars="v", cmap=cmap, clim=clim, smooth_shading=True,
               scalar_bar_args=dict(title=bar, vertical=True, position_x=.87, position_y=.15, height=.7, width=.04, color="#14213D", title_font_size=16, label_font_size=14, fmt="%.0f"))
    deck = pv.Plane(center=(6, 0, -.06), direction=(0, 0, 1), i_size=12, j_size=2); p.add_mesh(deck, color="#8B6B4A", opacity=.35)
    for x, y in ((0, -1), (0, 1), (12, -1), (12, 1)): p.add_mesh(pv.Cone(center=(x, y, -.25), direction=(0, 0, 1), height=.35, radius=.2), color="#14213D")
    p.add_text(title, position="upper_left", font_size=12, color="#14213D"); p.camera_position = [(-6.5, -15.5, 8.5), (6, 0, .9), (0, 0, 1)]; p.enable_anti_aliasing("ssaa")
    return p
for m in M: m["sa_MPa"] = m["sa"] / 1e6; m["util_pct"] = 100 * m["util"]
lim = max(abs(m["sa_MPa"]) for m in M)
p = scene(80, "sa_MPa", (-lim, lim), "RdBu", "Axial stress under ULS load (1.35G + 1.5Q) · blue = tension, red = compression · deformation x80", "axial stress (MPa)"); p.screenshot("renders/bridge-axial-stress.png"); p.close()
p = scene(80, "util_pct", (0, 100), "turbo", "Utilisation (stress or EN 1993 flexural buckling, whichever governs) · deformation x80", "utilisation (%)"); p.screenshot("renders/bridge-utilisation.png"); p.close()
# deformation animation: load ramps 0 -> ULS and back, twice (3 s), utilisation colouring
p = scene(0, "util_pct", (0, 100), "turbo", "Deformation under ULS load, exaggerated x80", "utilisation (%)"); act = None
ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "image2pipe", "-c:v", "png", "-framerate", "30", "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "anim/bridge-deformation.tmp.mp4"], stdin=subprocess.PIPE)
actors = list(p.renderer.actors.values()); deformed = actors[1]
for f in range(120):
    s = 80 * (0.5 - 0.5 * math.cos(2 * math.pi * f / 60)); p.remove_actor(deformed)
    deformed = p.add_mesh(tubes(s, "util_pct"), scalars="v", cmap="turbo", clim=(0, 100), smooth_shading=True, show_scalar_bar=False); p.render()
    b = io.BytesIO(); Image.fromarray(p.screenshot(return_img=True)).save(b, "PNG"); ff.stdin.write(b.getvalue())
ff.stdin.close(); ff.wait(); p.close()
import os; os.replace("anim/bridge-deformation.tmp.mp4", "anim/bridge-deformation.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "anim/bridge-deformation.mp4", "-vf", "fps=15,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse", "anim/bridge-deformation.gif"], check=True)
print("bridge viz done")
