"""Draws the 1024 x 500 feature graphic used in the store listing draft. Run from the week-4 folder."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

fig = plt.figure(figsize=(10.24, 5.0), dpi=100)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1024); ax.set_ylim(0, 500); ax.axis("off")
for i in range(50):  # sky gradient
    t = i / 49
    ax.add_patch(Rectangle((0, 500 - (i + 1) * 10), 1024, 10, color=(0.43 + 0.37 * t, 0.78 + 0.15 * t, 1.0 - 0.02 * t)))
ax.add_patch(Polygon([[0, 120], [180, 230], [330, 140], [520, 260], [700, 150], [860, 240], [1024, 130], [1024, 0], [0, 0]], color="#4a6b8a"))
ax.add_patch(Rectangle((0, 0), 1024, 90, color="#5b4636")); ax.add_patch(Rectangle((0, 84), 1024, 12, color="#59b34a"))
for x in (250, 470, 700):
    ax.add_patch(Circle((x, 195 + (x % 3) * 15), 22, color="#ffd23f")); ax.add_patch(Circle((x, 195 + (x % 3) * 15), 22, fill=False, ec="#b8860b", lw=3))
ax.add_patch(Rectangle((120, 96), 44, 56, color="#ff9f1c")); ax.add_patch(Rectangle((120, 128), 44, 16, color="#2a9d8f"))
ax.add_patch(Rectangle((148, 112), 10, 10, color="white")); ax.add_patch(Rectangle((152, 114), 5, 5, color="#111"))
ax.add_patch(Rectangle((820, 96), 8, 130, color="white")); ax.add_patch(Polygon([[828, 224], [880, 205], [828, 186]], color="#ff4d6d"))
ax.text(512, 380, "GEM RUN", ha="center", va="center", fontsize=64, weight="bold", color="#14171f")
ax.text(512, 320, "Jump, dodge, stomp. Three levels.", ha="center", va="center", fontsize=22, color="#14171f")
fig.savefig("store/feature-graphic-1024x500.png", dpi=100)
print("wrote store/feature-graphic-1024x500.png")
