"""BCCD blood-smear dataset (Shenggan/BCCD_Dataset on GitHub, MIT licence): 364 light-microscope images (640x480)
of stained peripheral blood smears with VOC-format boxes for RBC, WBC and Platelets, plus official train/val/test
image lists. Splits are by IMAGE, so no cell from a test image is ever seen in training.
    git clone --depth 1 https://github.com/Shenggan/BCCD_Dataset.git  (or set BCCD_DIR)"""
import os, xml.etree.ElementTree as ET
import numpy as np
ROOT = os.environ.get("BCCD_DIR", "/tmp/claude-0/bccd/BCCD")
CLASSES = ["RBC", "WBC", "Platelets"]
def split(name): return [l.strip() for l in open(os.path.join(ROOT, "ImageSets", "Main", f"{name}.txt")) if l.strip()]
def image_path(n): return os.path.join(ROOT, "JPEGImages", f"{n}.jpg")
def boxes(n):
    """[(class, [x1, y1, x2, y2]), ...] from the VOC XML (a few files have float coordinates or boxes past the edge)."""
    r = ET.parse(os.path.join(ROOT, "Annotations", f"{n}.xml")).getroot(); W, H = int(r.find("size/width").text), int(r.find("size/height").text); out = []
    for o in r.findall("object"):
        b = o.find("bndbox"); x1, y1, x2, y2 = [int(float(b.find(k).text)) for k in ("xmin", "ymin", "xmax", "ymax")]
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(W, x2), min(H, y2)
        if x2 - x1 >= 4 and y2 - y1 >= 4: out.append((o.find("name").text.strip(), [x1, y1, x2, y2]))
    return out
def crop(img, box, size=96, margin=.1):
    """Square crop around a box with a small margin (img: RGB uint8 array), resized to size x size."""
    from PIL import Image
    x1, y1, x2, y2 = box; cx, cy = (x1 + x2) / 2, (y1 + y2) / 2; s = max(x2 - x1, y2 - y1) * (1 + margin) / 2; H, W = img.shape[:2]
    a, b, c, d = int(max(0, cx - s)), int(max(0, cy - s)), int(min(W, cx + s)), int(min(H, cy + s))
    return np.asarray(Image.fromarray(img[b:d, a:c]).resize((size, size), Image.BILINEAR))
def crops(names, size=96):
    from PIL import Image
    X, y = [], []
    for n in names:
        img = np.asarray(Image.open(image_path(n)).convert("RGB"))
        for c, b in boxes(n): X.append(crop(img, b, size)); y.append(CLASSES.index(c))
    return np.stack(X), np.array(y)
def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1])); i = ix * iy
    return i / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i + 1e-9)
