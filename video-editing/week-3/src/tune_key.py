"""Grid search for the chroma-key settings: scores each (similarity, blend) against the ground-truth matte at t=1.5 s.
    python src/tune_key.py  -> results/key-tuning.csv (best first)"""
import subprocess, itertools, numpy as np
from PIL import Image
truth = np.asarray(Image.open("build/gs_truth.png"), np.float32) / 255; rows = []
for s, b in itertools.product([0.06, 0.08, 0.10, 0.13, 0.16, 0.20], [0.0, 0.02, 0.04, 0.06, 0.1]):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1.5", "-i", "exports/greenscreen-raw.mp4", "-frames:v", "1", "-vf",
                    f"format=yuva420p,chromakey=0x2EB14A:{s}:{b},format=rgba,alphaextract,format=gray", "build/_m.png"], check=True)
    m = np.asarray(Image.open("build/_m.png"), np.float32) / 255
    rows.append((round(float(np.abs(m - truth).mean()), 4), round(float((m[truth > .99] < .95).mean() * 100), 2), round(float((m[truth < .01] > .05).mean() * 100), 2), s, b))
rows.sort(); open("results/key-tuning.csv", "w").write("matte_mae,solid_not_opaque_pct,bg_not_clear_pct,similarity,blend\n" + "".join(",".join(map(str, r)) + "\n" for r in rows))
for r in rows[:6]: print(r)
