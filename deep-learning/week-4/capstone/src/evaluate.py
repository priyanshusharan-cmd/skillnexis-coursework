"""Capstone evaluation of the whole pipeline on the 72 official TEST images (never used for any choice).
  1. WBC localisation: a predicted WBC box is correct if IoU >= 0.5 with an annotated WBC (each annotation matched
     once) -> precision, recall, mean IoU. The box scale (1.25) was picked on train+val: see results/wbc_scale.json.
  2. Platelet counting: predicted count vs annotated count per image -> mean absolute error and exact-match rate,
     next to a naive baseline (always predict the train-set mean count).
    python src/evaluate.py -> results/pipeline.json, results/examples.png"""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__)); import bccd, cells
from analyze import CellClassifier, analyze, draw
def wbc_eval(names, scale):
    old = cells.WBC_SCALE; cells.WBC_SCALE = scale; tp = fp = fn = 0; ious = []
    for n in names:
        rgb = np.asarray(Image.open(bccd.image_path(n)).convert("RGB")); gt = [b for c, b in bccd.boxes(n) if c == "WBC"]; used = set()
        for p in cells.candidates(rgb)[0]:
            j = max(range(len(gt)), key=lambda i: bccd.iou(p, gt[i])) if gt else None
            if j is not None and j not in used and bccd.iou(p, gt[j]) >= .5: tp += 1; used.add(j); ious.append(bccd.iou(p, gt[j]))
            else: fp += 1
        fn += len(gt) - len(used)
    cells.WBC_SCALE = old; return dict(precision=round(tp / max(1, tp + fp), 3), recall=round(tp / max(1, tp + fn), 3), mean_iou=round(float(np.mean(ious)), 3) if ious else None)
if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    tv = bccd.split("trainval"); scales = {str(k): wbc_eval(tv, k) for k in (1.0, 1.1, 1.25, 1.4, 1.6)}
    best = max(scales, key=lambda k: (scales[k]["recall"] + scales[k]["precision"], scales[k]["mean_iou"] or 0)); json.dump(dict(trainval=scales, chosen=float(best)), open("results/wbc_scale.json", "w"), indent=1)
    print("scale chosen on train+val:", best, scales[best]); cells.WBC_SCALE = float(best)
    clf = CellClassifier(); test = bccd.split("test"); res = dict(test_images=len(test)); errs = []; exact = 0; rows = []
    train_mean = np.mean([sum(c == "Platelets" for c, _ in bccd.boxes(n)) for n in bccd.split("train")])
    tp = fp = fn = 0; ious = []
    for n in test:
        rgb = np.asarray(Image.open(bccd.image_path(n)).convert("RGB")); r = analyze(rgb, clf); g = bccd.boxes(n)
        gw = [b for c, b in g if c == "WBC"]; used = set()
        for c in r["cells"]:
            if c["candidate"] != "WBC": continue
            j = max(range(len(gw)), key=lambda i: bccd.iou(c["box"], gw[i])) if gw else None
            if j is not None and j not in used and bccd.iou(c["box"], gw[j]) >= .5: tp += 1; used.add(j); ious.append(bccd.iou(c["box"], gw[j]))
            else: fp += 1
        fn += len(gw) - len(used)
        gp = sum(c == "Platelets" for c, _ in g); errs.append(abs(r["platelet_count"] - gp)); exact += r["platelet_count"] == gp
        rows.append(dict(image=n, wbc_pred=r["wbc_count"], wbc_true=len(gw), plt_pred=r["platelet_count"], plt_true=gp, rejected=r["rejected_candidates"]))
    gps = [x["plt_true"] for x in rows]
    res["wbc_localisation"] = dict(precision=round(tp / max(1, tp + fp), 3), recall=round(tp / max(1, tp + fn), 3), mean_iou=round(float(np.mean(ious)), 3), scale=float(best))
    res["wbc_localisation_candidates_only"] = wbc_eval(test, float(best))
    res["platelet_count"] = dict(mae=round(float(np.mean(errs)), 3), exact_match=round(exact / len(test), 3), baseline_mae_train_mean=round(float(np.mean([abs(train_mean - g) for g in gps])), 3),
                                 mean_true=round(float(np.mean(gps)), 2), mean_pred=round(float(np.mean([x["plt_pred"] for x in rows])), 2))
    res["per_image"] = rows; json.dump(res, open("results/pipeline.json", "w"), indent=1); print(json.dumps({k: v for k, v in res.items() if k != "per_image"}, indent=1))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 3, figsize=(15, 8))
    for a, n in zip(ax.ravel(), test[::12][:6]):
        rgb = np.asarray(Image.open(bccd.image_path(n)).convert("RGB")); r = analyze(rgb, clf); a.imshow(draw(rgb, r)); a.axis("off")
        gp = sum(c == "Platelets" for c, _ in bccd.boxes(n)); a.set_title(f"{n}: WBC {r['wbc_count']}, platelets {r['platelet_count']} (annotated {gp})", fontsize=9)
    fig.suptitle("Test smears: blue = WBC, orange = platelet (CNN-confirmed)"); fig.tight_layout(); fig.savefig("results/examples.png", dpi=110)
