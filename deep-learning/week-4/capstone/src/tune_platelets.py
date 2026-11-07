"""Choose the platelet rule on the TRAIN+VAL images only (the test images are not touched): the minimum and maximum
component area, and the CNN probability needed to accept a candidate, by the mean absolute count error.
    python src/tune_platelets.py -> results/platelet_tuning.json"""
import json
import os, sys, numpy as np; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import bccd, cells
from analyze import CellClassifier, crop
clf = CellClassifier(); rows = []
for n in bccd.split("trainval"):
    rgb = np.asarray(Image.open(bccd.image_path(n)).convert("RGB")); gt = sum(c == "Platelets" for c, _ in bccd.boxes(n))
    H, W = rgb.shape[:2]; cand = []
    for x, y, w, h, a in cells.components(rgb):
        if 40 <= a < 3000: cand.append((a, clf(crop(rgb, cells.square(x, y, w, h, 1.6, W, H)))[2]))
    rows.append((gt, cand))
grid = []
for amin in (40, 100, 150, 200):
    for amax in (800, 1500, 2999):
        for th in (.5, .8, .9, .97, .99):
            e = [abs(sum(1 for a, p in c if amin <= a <= amax and p >= th) - g) for g, c in rows]; grid.append(dict(min_area=amin, max_area=amax, threshold=th, mae=round(float(np.mean(e)), 3)))
gts = [g for g, _ in rows]; best = min(grid, key=lambda r: (r["mae"], -r["threshold"]))
res = dict(images=len(rows), baseline_mae_mean_count=round(float(np.mean([abs(g - np.mean(gts)) for g in gts])), 3), best=best, grid=sorted(grid, key=lambda r: r["mae"]))
json.dump(res, open("results/platelet_tuning.json", "w"), indent=1); print(res["best"], res["baseline_mae_mean_count"])
