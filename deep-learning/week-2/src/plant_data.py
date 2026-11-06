"""PlantVillage tomato leaves (Hughes & Salathé 2015, github.com/spMohanty/PlantVillage-Dataset, raw/color): 400
images per class were sampled (seed 0) from each of the 10 tomato classes. A stratified 70/15/15 split is saved to
data/plant_split.json so every script uses the same train/validation/test images.
Caveat: PlantVillage photos were taken in lab conditions (one leaf, a plain background), so field photos are harder
than the test accuracy suggests."""
import json, os, random
ROOT = os.environ.get("PLANT_DIR", "/tmp/claude-0/pv/raw/color"); SPLIT = os.path.join(os.path.dirname(__file__), "..", "data", "plant_split.json")
FIVE = ["Tomato___healthy", "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___Leaf_Mold", "Tomato___Bacterial_spot"]
def pretty(c): return c.replace("Tomato___", "").replace("_", " ").replace("Spider mites Two-spotted spider mite", "Spider mites")
def make():
    classes = sorted(d for d in os.listdir(ROOT) if d.startswith("Tomato")); out = dict(classes=classes, train=[], val=[], test=[])
    for c in classes:
        fs = sorted(os.listdir(os.path.join(ROOT, c))); random.Random(1).shuffle(fs); n = len(fs); a, b = int(n * .7), int(n * .85)
        for part, sl in (("train", fs[:a]), ("val", fs[a:b]), ("test", fs[b:])): out[part] += [[f"{c}/{f}", c] for f in sl]
    json.dump(out, open(SPLIT, "w"), indent=0); return out
def split(classes=None):
    s = json.load(open(SPLIT)) if os.path.exists(SPLIT) else make()
    if classes: s = dict(classes=classes, **{k: [r for r in s[k] if r[1] in classes] for k in ("train", "val", "test")})
    return s
def arrays(rows, classes, size=224):
    import numpy as np
    from PIL import Image
    X = np.stack([np.asarray(Image.open(os.path.join(ROOT, p)).convert("RGB").resize((size, size), Image.BILINEAR)) for p, _ in rows])  # uint8: 4x less RAM; models rescale per batch
    return X, np.array([classes.index(c) for _, c in rows])
if __name__ == "__main__":
    s = make(); print({k: len(s[k]) for k in ("train", "val", "test")}, len(s["classes"]), "classes")
