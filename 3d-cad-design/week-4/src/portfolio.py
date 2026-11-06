"""Builds portfolio/: a single static page covering the CAD course (weeks 1-4), with downsized JPEG copies of the
renders so the folder can be hosted as-is (e.g. GitHub Pages).   python src/portfolio.py"""
import json, os, subprocess
from PIL import Image
IMG = {"stackr-hero": "renders/hero.png", "stackr-exploded": "renders/exploded.png", "stackr-concept": "concept/concept-sketches.png",
       "stackr-stress": "renders/stand-stress.png", "stackr-thermal": "renders/stand-thermal.png", "stackr-layers": "results/print-layer-preview.png",
       "gear-hero": "../week-2/renders/hero.png", "gear-exploded": "../week-2/renders/exploded.png", "gear-closeup": "../week-2/renders/closeup.png",
       "bracket": "../week-3/renders/bracket-stress.png", "bridge": "../week-3/renders/bridge-utilisation.png", "hdri": "../week-3/renders/product-shot-hdri.png"}
for k, p in IMG.items():
    im = Image.open(p).convert("RGB"); im.thumbnail((1600, 1600)); im.save(f"portfolio/img/{k}.jpg", quality=84, optimize=True)
for k, p in {"stackr": "anim/stackr-assembly.gif", "gears": "../week-3/anim/gear-train.gif"}.items():
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", p, "-vf", "scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse", f"portfolio/img/{k}.gif"], check=True)
subprocess.run(["node", "src/shot.js", "drawings/01-phone-stand.svg", "drawings/03-assembly.svg"], check=True)
for svg in ("01-phone-stand", "03-assembly"):
    im = Image.open(f"build/{svg}.png").convert("RGB"); im.thumbnail((1600, 1600)); im.save(f"portfolio/img/draw-{svg}.jpg", quality=88)
pr = json.load(open("results/print-report.json")); sim = json.load(open("results/sim.json")); asm = json.load(open("results/assembly.json"))
br = json.load(open("../week-3/results/bridge.json")) if os.path.exists("../week-3/results/bridge.json") else {}
html = open("src/portfolio.template.html").read()
for k, v in {"FIL": pr["total"]["filament_g"], "HRS": pr["total"]["print_time_h"], "SF": round(sim["structural"]["safety_factor_vs_50MPa"]),
             "VM": sim["structural"]["peak_von_mises_MPa"], "HEAT": sim["thermal"]["heat_through_stand_W"], "ENV": " × ".join(f"{x:g}" for x in asm["envelope_mm"])}.items():
    html = html.replace("{{" + k + "}}", str(v))
open("portfolio/index.html", "w").write(html); print("portfolio ok")
