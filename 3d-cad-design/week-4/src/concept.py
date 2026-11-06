"""Concept sheet: three hand-sketched directions, the evaluation matrix and why C was picked.
Sketch style via matplotlib's xkcd mode (wobbly strokes), drawn in isometric.   python src/concept.py"""
import math, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))
Z = [3]
def zo():
    Z[0] += 1; return Z[0]
iso = lambda x, y, z: (x * C30 - y * C30, x * S30 + y * S30 + z)
def box(ax, x, y, z, w, d, h, c="k", fill=None):
    P = lambda a, b, cc: iso(x + a, y + b, z + cc)
    faces = [[P(0, 0, h), P(w, 0, h), P(w, d, h), P(0, d, h)], [P(0, 0, 0), P(w, 0, 0), P(w, 0, h), P(0, 0, h)], [P(0, 0, 0), P(0, d, 0), P(0, d, h), P(0, 0, h)]]
    for f, s in zip(faces, (1.0, .82, .68)):
        xs, ys = zip(*(f + [f[0]]))
        if fill: ax.fill(xs, ys, color=tuple(np.array(matplotlib.colors.to_rgb(fill)) * s), lw=0, zorder=zo())
        ax.plot(xs, ys, c, lw=1.6)
def cyl(ax, x, y, z, r, h, fill=None):
    if r == 0: return
    front = np.linspace(math.radians(135), math.radians(315), 30); full = np.linspace(0, 2 * np.pi, 48)
    bot = [iso(x + r * math.cos(a), y + r * math.sin(a), z) for a in front]; top = [iso(x + r * math.cos(a), y + r * math.sin(a), z + h) for a in full]
    side = bot + [iso(x + r * math.cos(a), y + r * math.sin(a), z + h) for a in front[::-1]]
    ax.fill(*zip(*side), color=fill or "#fbf8f1", alpha=.9 if fill else 1, lw=0, zorder=zo()); ax.fill(*zip(*top), color=fill or "#fbf8f1", lw=0, zorder=zo())
    if fill: ax.fill(*zip(*top), color="white", alpha=.35, lw=0, zorder=zo())
    ax.plot(*zip(*top), "k", lw=1.6, zorder=zo()); ax.plot(*zip(*bot), "k", lw=1.6, zorder=zo())
    for a in (front[0], front[-1]): ax.plot(*zip(iso(x + r * math.cos(a), y + r * math.sin(a), z), iso(x + r * math.cos(a), y + r * math.sin(a), z + h)), "k", lw=1.6, zorder=zo())
def note(ax, xy, txt, dxy):
    ax.annotate(txt, xy, xytext=(xy[0] + dxy[0], xy[1] + dxy[1]), fontsize=10, arrowprops=dict(arrowstyle="->", lw=1.1), zorder=900)
with plt.xkcd(scale=.7, length=120, randomness=2):
    fig = plt.figure(figsize=(16.5, 11.7), dpi=110); fig.patch.set_facecolor("#fbf8f1")
    fig.text(.03, .955, "STACKR · desk organiser · concept sketches", fontsize=24); fig.text(.03, .925, "brief: one printable kit that holds a phone, pens and a small plant, rearrangeable, fits a 21 cm shelf, ≤ 250 g PLA", fontsize=12)
    titles = ["A · monolithic block", "B · pegboard + hooks", "C · rail + slide-in modules  ✓ chosen"]
    for i, t in enumerate(titles):
        ax = fig.add_axes([.03 + i * .32, .40, .30, .48]); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(t, fontsize=15, loc="left")
        if i == 0:
            box(ax, 0, 0, 0, 200, 90, 70, fill="#b9b2a6"); cyl(ax, 40, 45, 70, 0, 0)
            for cx in (30, 60): cyl(ax, cx, 45, 40, 12, 30)
            box(ax, 120, 10, 70, 70, 20, 40, fill="#c96b4b")
            note(ax, iso(200, 45, 35), "one 9 h print,\nfail = start over", (40, -60)); note(ax, iso(155, 20, 110), "phone slot\nfixed angle", (20, 30))
        if i == 1:
            box(ax, 0, 70, 0, 200, 10, 150, fill="#b9b2a6")
            for gx in range(20, 200, 30):
                for gz in range(20, 150, 30): ax.plot(*iso(gx, 70, gz), "ko", ms=3, zorder=zo())
            box(ax, 30, 40, 60, 50, 30, 50, fill="#6f8f73"); box(ax, 120, 40, 20, 50, 30, 10, fill="#c96b4b")
            note(ax, iso(200, 75, 140), "wall-hung: needs\ndrilling / adhesive", (10, 30)); note(ax, iso(80, 40, 60), "hooks wobble\nunder a phone tap", (40, -70))
        if i == 2:
            box(ax, 0, 0, 0, 210, 96, 9, fill="#2a2a2e")
            for rx in (37, 105, 173): ax.plot(*zip(iso(rx, 0, 9), iso(rx, 96, 9)), "w", lw=1.2, zorder=zo())
            cyl(ax, 173, 48, 9, 24, 34, fill="#e3dfd4"); cyl(ax, 105, 48, 9, 30, 96, fill="#6f8f73"); box(ax, 10, 10, 9, 55, 75, 90, fill="#c96b4b")
            note(ax, iso(105, 2, 9), "dovetail rails,\n0.25 mm fit", (-40, -45)); note(ax, iso(105, 48, 105), "swap / reorder\nmodules", (55, 15)); note(ax, iso(190, 48, 25), "organic pebble\nplanter (SDF)", (25, -75))
    ax = fig.add_axes([.04, .04, .55, .30]); ax.axis("off")
    crit = ["printability (support needed)", "rearrangeable", "stability (phone taps)", "filament ≤ 250 g", "no tools / no wall"]
    S = [[2, 1, 3, 2, 3], [3, 3, 1, 3, 1], [2, 3, 3, 3, 3]]
    ax.text(0, 1.0, "evaluation (1 poor … 3 good)", fontsize=14, transform=ax.transAxes)
    for r, c in enumerate(crit): ax.text(0, .82 - r * .14, c, fontsize=12, transform=ax.transAxes)
    for j, n in enumerate("ABC"):
        ax.text(.62 + j * .12, .9, n, fontsize=14, transform=ax.transAxes)
        for r in range(5): ax.text(.62 + j * .12, .82 - r * .14, "●" * S[j][r], fontsize=12, color="#c0392b" if j == 2 else "k", transform=ax.transAxes)
        ax.text(.6 + j * .12, .08, f"Σ {sum(S[j])}", fontsize=13, transform=ax.transAxes)
    ax2 = fig.add_axes([.62, .04, .35, .30]); ax2.axis("off"); ax2.text(0, 1.0, "phone-stand side profile, two tries", fontsize=14, transform=ax2.transAxes)
    a = math.radians(65)
    for k, (ox, lab) in enumerate(((0, "v1 solid cheeks · 122 cm³"), (130, "v2 open A-frame · 98 cm³ ✓"))):
        pts = [(ox, 0), (ox + 80, 0), (ox + 80 - 92 / math.tan(a), 92), (ox + 10, 6), (ox + 10, 0)] if False else [(ox, 0), (ox + 80, 0), (ox + 80 - 92 / math.tan(a), 92), (ox + 6, 14), (ox + 6, 0)]
        ax2.fill(*zip(*pts), color="#c96b4b", alpha=.5); ax2.plot(*zip(*(pts + [pts[0]])), "k", lw=1.6, zorder=zo())
        if k: ax2.fill([ox + 24, ox + 64, ox + 52], [8, 8, 50], color="#fbf8f1"); ax2.plot([ox + 24, ox + 64, ox + 52, ox + 24], [8, 8, 50, 8], "k", lw=1.4, zorder=zo())
        ax2.text(ox, -22, lab, fontsize=11); ax2.text(ox + 62, 70, "65°", fontsize=11)
    ax2.set_xlim(-10, 230); ax2.set_ylim(-35, 110); ax2.set_aspect("equal")
    fig.savefig("concept/concept-sketches.png", facecolor=fig.get_facecolor()); print("ok")
