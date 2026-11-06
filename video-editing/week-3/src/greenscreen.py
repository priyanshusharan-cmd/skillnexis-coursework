"""Green-screen exercise.
1. Shoots a stand-in green-screen clip (no studio here): an illustrated presenter in front of an unevenly lit green
   backdrop, with sensor noise, green spill on the edges, fine hair strands, a semi-transparent glass, and x264
   compression, i.e. the problems a real green-screen key has to solve.
2. Keys it two ways: a naive hard colour key, and a tuned chroma key (similarity / blend) + despill + a slight matte
   choke, then composites onto a new background (the colour-corrected café b-roll from week 2, blurred for depth).
3. Measures the result: green spill left on the subject's edge pixels, and holes in the matte.
    python src/greenscreen.py  -> exports/greenscreen-raw.mp4, greenscreen-composite.mp4, greenscreen-breakdown.mp4, results/greenscreen.json"""
import json, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
W, H, FPS, DUR = 1920, 1080, 30, 6.0; B = "build"; os.makedirs("results", exist_ok=True)
rng = np.random.default_rng(1)
yy, xx = np.mgrid[0:H, 0:W]; light = 1 - 0.38 * (((xx - W * .45) / W) ** 2 + ((yy - H * .4) / H) ** 2) ** .5 * 1.6   # hot spot, darker corners
GREEN = np.array([46, 177, 74], np.float32)
def subject(t):
    """RGBA presenter: hoodie, head, hair strands, a waving arm with a phone, a glass of chai on the desk."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx = 900 + 40 * math.sin(t * 1.3)
    d.polygon([(cx - 260, H), (cx - 200, 640), (cx + 200, 640), (cx + 260, H)], fill=(31, 42, 68, 255))            # hoodie
    d.rounded_rectangle((cx - 210, 600, cx + 210, 760), radius=90, fill=(31, 42, 68, 255))
    d.rectangle((cx - 45, 520, cx + 45, 620), fill=(176, 120, 88, 255))                                            # neck
    d.ellipse((cx - 120, 300, cx + 120, 570), fill=(196, 138, 102, 255))                                           # face
    d.chord((cx - 132, 270, cx + 132, 480), 180, 360, fill=(28, 22, 20, 255))                                     # hair
    for k in range(40):                                                                                            # loose strands (fine detail)
        a = math.pi * (1.05 + .9 * k / 40); r0 = 128; x0, y0 = cx + r0 * math.cos(a), 375 + 105 * math.sin(a)
        x1, y1 = x0 + 26 * math.cos(a + .3 * math.sin(t * 3 + k)), y0 + 30 * math.sin(a) - 6
        d.line((x0, y0, x1, y1), fill=(28, 22, 20, 255), width=2)
    for ex in (-45, 45): d.ellipse((cx + ex - 12, 420, cx + ex + 12, 444), fill=(30, 25, 24, 255))
    d.arc((cx - 45, 450, cx + 45, 520), 20, 160, fill=(120, 60, 50, 255), width=6)
    ang = -1.1 + .35 * math.sin(t * 4)                                                                             # waving arm with phone
    sx, sy = cx + 190, 680; ex_, ey = sx + 230 * math.cos(ang), sy + 230 * math.sin(ang)
    d.line((sx, sy, ex_, ey), fill=(31, 42, 68, 255), width=80); d.ellipse((ex_ - 40, ey - 40, ex_ + 40, ey + 40), fill=(196, 138, 102, 255))
    d.rounded_rectangle((ex_ - 38, ey - 150, ex_ + 38, ey - 10), radius=14, fill=(16, 24, 40, 255)); d.rounded_rectangle((ex_ - 30, ey - 140, ex_ + 30, ey - 20), radius=8, fill=(236, 241, 246, 255))
    d.rectangle((0, 940, W, H), fill=(120, 84, 58, 255))                                                           # desk edge
    d.rounded_rectangle((cx - 520, 760, cx - 400, 940), radius=10, fill=(235, 240, 245, 110))                       # glass: 43 % opaque
    d.rectangle((cx - 512, 830, cx - 408, 932), fill=(176, 110, 60, 200))                                           # chai inside
    return im
enc = ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p"]
p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *enc, "-crf", "23", f"{B}/gs.tmp.mp4"], stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)) if not os.path.exists("exports/greenscreen-raw.mp4") else []:
    t = i / FPS; s = subject(t); a = np.asarray(s, np.float32); al = a[..., 3:4] / 255
    bg = GREEN * light[..., None] + rng.normal(0, 4, (H, W, 1))
    inner = al * (1 - np.asarray(s.getchannel("A").filter(ImageFilter.GaussianBlur(9)), np.float32)[..., None] / 255 * al)  # near-edge zone inside the subject
    fg = a[..., :3] * (1 - .45 * inner) + GREEN * .45 * inner                                                        # green spill bouncing onto the edges
    frame = fg * al + bg * (1 - al)
    p.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    if i == 45: Image.fromarray((al[..., 0] * 255).astype(np.uint8)).save(f"{B}/gs_truth.png")                        # ground-truth matte for scoring
p.stdin.close(); p.wait()
if os.path.getsize(f"{B}/gs.tmp.mp4") > 1000: os.replace(f"{B}/gs.tmp.mp4", "exports/greenscreen-raw.mp4")

BGV = "../week-2/build/fix_coffee.mp4"
bgchain = f"[1:v]scale=2400:-2,crop={W}:{H},gblur=sigma=6,eq=brightness=-0.03[bg]"
NAIVE = "colorkey=0x2EB14A:0.20:0"                                          # hard key: one threshold, no blend, no despill
TUNED = "chromakey=0x2EB14A:0.10:0.02,despill=type=green:mix=0.6:expand=0.1"   # settings from src/tune_key.py + spill suppression
def comp(key, out):
    fc = f"{bgchain};[0:v]format=yuva420p,{key}[fg];[bg][fg]overlay=0:0:shortest=1,format=yuv420p[v]"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "exports/greenscreen-raw.mp4", "-stream_loop", "-1", "-i", BGV, "-filter_complex", fc, "-map", "[v]", "-t", str(DUR), *enc, "-crf", "18", out + ".tmp.mp4"], check=True)
    os.replace(out + ".tmp.mp4", out)
comp(NAIVE, f"{B}/gs_naive.mp4"); comp(TUNED, "exports/greenscreen-composite.mp4")
# mattes at frame 45 for scoring
def matte(key, name):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1.5", "-i", "exports/greenscreen-raw.mp4", "-frames:v", "1", "-vf", f"format=yuva420p,{key},format=rgba,alphaextract,format=gray", f"{B}/m_{name}.png"], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1.5", "-i", "exports/greenscreen-raw.mp4", "-frames:v", "1", "-vf", f"format=yuva420p,{key},format=rgba", f"{B}/k_{name}.png"], check=True)
truth = np.asarray(Image.open(f"{B}/gs_truth.png"), np.float32) / 255
edge = (truth > .5) & (np.asarray(Image.open(f"{B}/gs_truth.png").filter(ImageFilter.MinFilter(15)), np.float32) < 128)   # subject pixels within ~7 px of the edge
res = {}
for name, key in (("naive", NAIVE), ("tuned", TUNED)):
    matte(key, name); m = np.asarray(Image.open(f"{B}/m_{name}.png").convert("L"), np.float32) / 255
    k = np.asarray(Image.open(f"{B}/k_{name}.png").convert("RGBA"), np.float32)
    spill = np.clip(k[..., 1] - np.maximum(k[..., 0], k[..., 2]), 0, None)[edge & (m > .5)]
    solid = truth > .99
    res[name] = {"edge_green_excess_mean": round(float(spill.mean()), 1), "edge_pixels_visibly_green_pct": round(float((spill > 15).mean() * 100), 1),
                 "matte_mean_abs_error": round(float(np.abs(m - truth).mean()), 4), "holes_in_solid_subject_pct": round(float((m[solid] < .5).mean() * 100), 2),
                 "background_left_pct": round(float((m[truth < .01] > .5).mean() * 100), 2)}
json.dump({"filters": {"naive": NAIVE, "tuned": TUNED}, "frame": "t=1.5 s", **res}, open("results/greenscreen.json", "w"), indent=1); print(json.dumps(res, indent=1))
# 2x2 breakdown: raw | matte (tuned) / naive key | final
lab = lambda s: f"drawtext=fontfile=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf:text='{s}':fontsize=44:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=16:x=30:y=30"
fc = (f"[0:v]scale=960:540,{lab('1  Raw green screen')}[a];[1:v]format=yuva420p,{TUNED},format=rgba,alphaextract,format=gray,scale=960:540,format=yuv420p,{lab('2  Matte (alpha)')}[b];"
      f"[2:v]scale=960:540,{lab('3  Naive hard key')}[c];[3:v]scale=960:540,{lab('4  Tuned key + despill')}[d];[a][b]hstack[t];[c][d]hstack[u];[t][u]vstack,format=yuv420p[v]")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "exports/greenscreen-raw.mp4", "-i", "exports/greenscreen-raw.mp4", "-i", f"{B}/gs_naive.mp4", "-i", "exports/greenscreen-composite.mp4",
                "-filter_complex", fc, "-map", "[v]", *enc, "-crf", "18", "exports/greenscreen-breakdown.tmp.mp4"], check=True)
os.replace("exports/greenscreen-breakdown.tmp.mp4", "exports/greenscreen-breakdown.mp4")
