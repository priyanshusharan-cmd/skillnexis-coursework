"""The smear analyser used by the API, the UI and the evaluation: candidates (cells.py) -> CNN (TFLite) -> result.
  WBC: each large purple component, confirmed by the CNN (p(WBC) >= 0.5)
  platelets: small purple components the CNN calls Platelets with p >= 0.97 (chosen on train+val, tune_platelets.py)
  RBC: not counted. BCCD's RBC boxes are incomplete and RBCs overlap heavily, so a count would not be trustworthy."""
import os
import numpy as np
from PIL import Image, ImageDraw
import cells
HERE = os.path.dirname(os.path.abspath(__file__)); CLASSES = ["RBC", "WBC", "Platelets"]; S = 96
class CellClassifier:
    def __init__(self, path=os.path.join(HERE, "..", "models", "cells.tflite")):
        from ai_edge_litert.interpreter import Interpreter
        self.it = Interpreter(model_path=path, num_threads=1); self.it.allocate_tensors()
        self.i, self.o = self.it.get_input_details()[0]["index"], self.it.get_output_details()[0]["index"]
    def __call__(self, crop96):
        self.it.set_tensor(self.i, crop96[None].astype("float32")); self.it.invoke(); return self.it.get_tensor(self.o)[0]
def crop(rgb, box, margin=.1):
    x1, y1, x2, y2 = box; cx, cy = (x1 + x2) / 2, (y1 + y2) / 2; s = max(x2 - x1, y2 - y1) * (1 + margin) / 2; H, W = rgb.shape[:2]
    a, b, c, d = int(max(0, cx - s)), int(max(0, cy - s)), int(min(W, cx + s)), int(min(H, cy + s))
    return np.asarray(Image.fromarray(rgb[b:d, a:c]).resize((S, S), Image.BILINEAR))
PLT_TH = .97
def analyze(rgb, clf, th=.5, plt_th=PLT_TH):
    wbc_c, plt_c = cells.candidates(rgb); found = []
    for kind, boxes in (("WBC", wbc_c), ("Platelets", plt_c)):
        for b in boxes:
            p = clf(crop(rgb, b)); k = CLASSES.index(kind)
            found.append(dict(box=b, candidate=kind, probabilities=dict(zip(CLASSES, [round(float(v), 3) for v in p])), accepted=bool(p[k] >= (th if kind == "WBC" else plt_th))))
    acc = [f for f in found if f["accepted"]]
    return dict(wbc_count=sum(f["candidate"] == "WBC" for f in acc), platelet_count=sum(f["candidate"] == "Platelets" for f in acc), cells=acc,
                rejected_candidates=len(found) - len(acc), image_size=[rgb.shape[1], rgb.shape[0]])
def draw(rgb, result):
    im = Image.fromarray(rgb).copy(); d = ImageDraw.Draw(im)
    for c in result["cells"]:
        col = (37, 99, 235) if c["candidate"] == "WBC" else (234, 88, 12); d.rectangle(c["box"], outline=col, width=3)
        d.text((c["box"][0] + 3, c["box"][1] + 2), f"{'WBC' if c['candidate'] == 'WBC' else 'PLT'} {c['probabilities'][c['candidate']]:.2f}", fill=col)
    return im
