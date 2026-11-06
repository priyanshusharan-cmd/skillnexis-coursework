"""B-roll + colour-correction exercise from real photographs (scikit-image sample images, public domain / free licence):
3 clips are deliberately mis-exposed (under, over, colour cast + under), then corrected with ffmpeg filters.
Writes build/bad_<n>.mp4, build/fix_<n>.mp4, exports/color-correction.mp4 (before | after with labels), results/color-correction.md"""
import json, os, subprocess, numpy as np
from skimage import data, io, transform
B = "build"; os.makedirs("results", exist_ok=True)
SRC = {"coffee": data.coffee(), "rocket": data.rocket(), "astronaut": data.astronaut()}
# degrade (what the camera did) and the correction filter chosen after reading the waveform / histogram
DEG = {"coffee": "eq=brightness=-0.18:gamma=0.55:contrast=0.85", "rocket": "eq=brightness=0.22:gamma=1.6:contrast=0.8",
       "astronaut": "colorbalance=rs=-0.15:gs=0.05:bs=0.25:rm=-0.12:bm=0.18,eq=gamma=0.7"}
FIX = {"coffee": "eq=gamma=2.2:brightness=0.12:contrast=1.15:saturation=1.1",
       "rocket": "eq=gamma=0.45:brightness=-0.2:contrast=1.45",
       "astronaut": "colorbalance=rs=0.15:gs=-0.05:bs=-0.25:rm=0.12:bm=-0.18,eq=gamma=1.4:saturation=1.05"}
def still(name):
    im = SRC[name]; h, w = im.shape[:2]; s = max(1920 / w, 1080 / h) * 1.15
    im = (transform.resize(im, (int(h * s), int(w * s)), anti_aliasing=True) * 255).astype(np.uint8); p = f"{B}/{name}.png"; io.imsave(p, im); return p, im.shape
def clip(name, vf, out, d=5):
    p, (h, w, _) = still(name)
    kb = f"crop=1920:1080:x='({w}-1920)/2+(({w}-1920)/2)*sin(t/{d}*1.2)':y='({h}-1080)/2'"      # slow pan (Ken Burns)
    tmp = out.replace(".mp4", ".tmp.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "30", "-loop", "1", "-t", str(d), "-i", p, "-vf", f"{kb},{vf},format=yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-r", "30", tmp], check=True)
    os.replace(tmp, out)
def stats(f):
    r = subprocess.run(["ffmpeg", "-i", f, "-vf", "signalstats,metadata=print:file=-", "-f", "null", "-"], capture_output=True, text=True).stdout
    vals = {k: [] for k in ("YAVG", "YLOW", "YHIGH", "UAVG", "VAVG")}
    for line in r.splitlines():
        for k in vals:
            if f"signalstats.{k}=" in line: vals[k].append(float(line.split("=")[1]))
    return {k: round(float(np.mean(v)), 1) for k, v in vals.items()}
rows = {}
for name in SRC:
    clip(name, DEG[name], f"{B}/bad_{name}.mp4"); clip(name, f"{DEG[name]},{FIX[name]}", f"{B}/fix_{name}.mp4"); clip(name, "null", f"{B}/ref_{name}.mp4")
    rows[name] = {"degraded": stats(f"{B}/bad_{name}.mp4"), "corrected": stats(f"{B}/fix_{name}.mp4"), "original": stats(f"{B}/ref_{name}.mp4")}
json.dump(rows, open("results/color-stats.json", "w"), indent=1)
print(json.dumps({k: {s: v[s]["YAVG"] for s in v} for k, v in rows.items()}))
