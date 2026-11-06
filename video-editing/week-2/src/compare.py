"""Colour-correction deliverable: before | after for 3 clips, with labels and measured luma, plus waveform scopes.
    python src/compare.py  -> exports/color-correction.mp4, exports/color-scopes.png, results/color-correction.md"""
import json, subprocess
st = json.load(open("results/color-stats.json"))
LAB = {"coffee": "Underexposed", "rocket": "Overexposed", "astronaut": "Colour cast + underexposed"}
F = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
parts = []
for i, n in enumerate(st):
    d, c = st[n]["degraded"], st[n]["corrected"]
    lab = lambda s, x: f"drawtext=fontfile={F}:text='{s}':fontsize=44:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=16:x={x}:y=40"
    sub = lambda s: f"drawtext=fontfile={F}:text='{s}':fontsize=30:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=12:x=40:y=h-80"
    fc = (f"[0:v]scale=960:540,{lab('BEFORE: ' + LAB[n], 40)},{sub(f'Mean luma {d[chr(89)+chr(65)+chr(86)+chr(71)]:.0f}  (range {d[chr(89)+chr(76)+chr(79)+chr(87)]:.0f}-{d[chr(89)+chr(72)+chr(73)+chr(71)+chr(72)]:.0f})')}[a];"
          f"[1:v]scale=960:540,{lab('AFTER', 40)},{sub(f'Mean luma {c[chr(89)+chr(65)+chr(86)+chr(71)]:.0f}  (range {c[chr(89)+chr(76)+chr(79)+chr(87)]:.0f}-{c[chr(89)+chr(72)+chr(73)+chr(71)+chr(72)]:.0f})')}[b];"
          f"[a][b]hstack,pad=1920:1080:0:270:color=0x111111,format=yuv420p[v]")
    out = f"build/cmp_{i}.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"build/bad_{n}.mp4", "-i", f"build/fix_{n}.mp4", "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-r", "30", out], check=True)
    parts.append(out)
open("build/cmp.txt", "w").write("".join(f"file '{p.split('/')[1]}'\n" for p in parts))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", "build/cmp.txt", "-c", "copy", "-movflags", "+faststart", "exports/color-correction.mp4"], check=True)
# waveform scopes (luma distribution by column) before vs after, all three clips
rows = []
for n in st:
    for kind in ("bad", "fix"):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "2", "-i", f"build/{kind}_{n}.mp4", "-frames:v", "1", "-vf",
                        "split[a][b];[a]scale=480:270[x];[b]waveform=g=green:fl=numbers,scale=480:270[y];[x][y]vstack", f"build/scope_{kind}_{n}.png"], check=True)
    rows.append(f"[{len(rows) * 2}][{len(rows) * 2 + 1}]hstack[r{len(rows)}]")
ins = sum([["-i", f"build/scope_{k}_{n}.png"] for n in st for k in ("bad", "fix")], [])
subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + ins + ["-filter_complex", ";".join(rows) + ";[r0][r1][r2]vstack=inputs=3", "exports/color-scopes.png"], check=True)
md = ["| Clip | Problem | Correction (ffmpeg) | Mean luma before → after (original) | Luma range before → after (original) |", "|---|---|---|---|---|"]
import sys; sys.path.insert(0, "src"); from broll import FIX
for n in st:
    d, c, o = st[n]["degraded"], st[n]["corrected"], st[n]["original"]
    md.append(f"| {n} | {LAB[n]} | `{FIX[n]}` | {d['YAVG']:.0f} → **{c['YAVG']:.0f}** ({o['YAVG']:.0f}) | {d['YLOW']:.0f}–{d['YHIGH']:.0f} → **{c['YLOW']:.0f}–{c['YHIGH']:.0f}** ({o['YLOW']:.0f}–{o['YHIGH']:.0f}) |")
open("results/color-correction.md", "w").write("\n".join(md) + "\n"); print("\n".join(md))
