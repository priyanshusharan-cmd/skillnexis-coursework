"""Pick correction settings by measurement: grid-search eq gamma/brightness/contrast so the corrected frame's
average luma and luma range match the original photo (what a colourist does by eye with the waveform)."""
import itertools, json, subprocess, sys
sys.path.insert(0, "src")
import broll  # noqa: reuses DEG and still images (also regenerates clips; fine)
def st(name, vf):
    r = subprocess.run(["ffmpeg", "-i", f"build/{name}.png", "-vf", f"{vf},signalstats,metadata=print:file=-", "-frames:v", "1", "-f", "null", "-"], capture_output=True, text=True).stdout
    d = {l.split("=")[0].split(".")[-1]: float(l.split("=")[1]) for l in r.splitlines() if "signalstats." in l}
    return d["YAVG"], d["YLOW"], d["YHIGH"]
best = {}
for name in ("coffee", "rocket"):
    ref = st(name, "null"); top = None
    for g, b, c in itertools.product([.45, .55, .65, .8, 1.0, 1.3, 1.6, 1.9, 2.2, 2.6], [-.2, -.12, -.06, 0, .06, .12], [.9, 1.0, 1.15, 1.3, 1.45]):
        fix = f"eq=gamma={g}:brightness={b}:contrast={c}"; y = st(name, f"{broll.DEG[name]},{fix}")
        err = abs(y[0] - ref[0]) + .5 * abs(y[1] - ref[1]) + .5 * abs(y[2] - ref[2])
        if top is None or err < top[0]: top = (err, fix, y)
    best[name] = top[1]; print(name, "ref", ref, "->", top)
json.dump(best, open("build/fix_tuned.json", "w"))
