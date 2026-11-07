"""Finding cells to classify (classic image processing, no training needed).
In Wright/Giemsa-stained smears, WBC nuclei and platelets take up the purple-blue stain strongly, while RBCs are pale
pink. So: HSV saturation > 70 and hue in the purple-blue range -> clean up (opening, then closing to merge nucleus
lobes) -> connected components.
  * large components (>= 3,000 px) are WBC nuclei; the cell box is the nucleus box scaled by 1.25 (the scale was
    chosen on the train+val images only; see evaluate.py)
  * small components (150 - 1,500 px) are platelet CANDIDATES; the CNN decides which ones really are platelets
    (area range and CNN threshold chosen on train+val by tune_platelets.py; smaller blobs are mostly stain debris)
Returns boxes in [x1, y1, x2, y2] pixel coordinates."""
import cv2, numpy as np
S_MIN, H_RANGE, WBC_MIN_AREA, PLT_AREA, WBC_SCALE = 70, (100, 175), 3000, (150, 1500), 1.25
def components(rgb):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    m = ((hsv[..., 1] > S_MIN) & (hsv[..., 0] > H_RANGE[0]) & (hsv[..., 0] < H_RANGE[1])).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    n, _, st, _ = cv2.connectedComponentsWithStats(m); return [tuple(int(v) for v in st[i]) for i in range(1, n)]
def square(x, y, w, h, k, W, H):
    cx, cy, s = x + w / 2, y + h / 2, max(w, h) * k / 2
    return [int(max(0, cx - s)), int(max(0, cy - s)), int(min(W, cx + s)), int(min(H, cy + s))]
def candidates(rgb):
    H, W = rgb.shape[:2]; wbc, plt = [], []
    for x, y, w, h, a in components(rgb):
        if a >= WBC_MIN_AREA: wbc.append(square(x, y, w, h, WBC_SCALE, W, H))
        elif PLT_AREA[0] <= a <= PLT_AREA[1]: plt.append(square(x, y, w, h, 1.6, W, H))
    return wbc, plt
