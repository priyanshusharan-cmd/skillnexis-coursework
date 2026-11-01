"""Draws the app icons (192 and 512 px) with Matplotlib. Run from the week-3 folder: python3 tools/make_icons.py"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

for size in (192, 512):
    fig = plt.figure(figsize=(size / 100, size / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, color="#14171f"))                      # full-bleed background, safe for maskable icons
    ax.add_patch(Circle((0.5, 0.5), 0.3, color="#ffcb47"))
    ax.add_patch(Circle((0.5, 0.5), 0.3, fill=False, ec="#b8860b", lw=size / 40))
    ax.add_patch(Polygon([[0.42, 0.34], [0.42, 0.66], [0.68, 0.5]], color="#14171f"))
    fig.savefig(f"icon-{size}.png", dpi=100)
    plt.close(fig)
print("wrote icon-192.png and icon-512.png")
