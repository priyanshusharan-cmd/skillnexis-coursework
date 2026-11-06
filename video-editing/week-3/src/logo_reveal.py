"""5-second logo reveal built from keyframes with easing curves (the same model as After Effects / Premiere keyframes).
Each property has keyframes (time, value, easing into the next); frames are rendered by interpolating them.
    python src/logo_reveal.py  -> exports/logo-reveal.mp4, exports/logo-keyframes.png (the graph editor view)"""
import subprocess, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS, DUR = 1920, 1080, 30, 5.0
F = "/usr/share/fonts/opentype/inter/"
EASE = {"linear": lambda u: u, "out": lambda u: 1 - (1 - u) ** 3, "in": lambda u: u ** 3, "inout": lambda u: 3 * u * u - 2 * u ** 3,
        "back": lambda u: 1 + 2.7 * (u - 1) ** 3 + 1.7 * (u - 1) ** 2}            # overshoot then settle
KF = {  # property: [(t, value, ease_to_next)]
 "tile_scale": [(0, 0.0, "back"), (0.8, 1.0, "linear"), (5, 1.0, "linear")],
 "tile_rot": [(0, -90, "out"), (0.8, 0, "linear"), (5, 0, "linear")],
 "letter_y": [(0.5, 80, "out"), (1.1, 0, "linear"), (5, 0, "linear")],
 "letter_a": [(0.5, 0, "out"), (1.0, 1, "linear"), (5, 1, "linear")],
 "slide_x": [(1.2, 0, "inout"), (2.0, -330, "linear"), (5, -330, "linear")],     # tile slides left to make room for the word
 "word_reveal": [(1.6, 0, "out"), (2.6, 1, "linear"), (5, 1, "linear")],          # wipe mask uncovering the wordmark
 "tag_a": [(2.6, 0, "out"), (3.2, 1, "linear"), (5, 1, "linear")],
 "ring": [(0.6, 0, "out"), (1.6, 1, "linear"), (5, 1, "linear")],
 "fade_out": [(4.4, 1, "in"), (5.0, 0, "linear")],
}
def val(prop, t):
    k = KF[prop]
    if t <= k[0][0]: return k[0][1]
    for (t0, v0, e), (t1, v1, _) in zip(k, k[1:]):
        if t0 <= t <= t1: return v0 + (v1 - v0) * EASE[e]((t - t0) / (t1 - t0))
    return k[-1][1]
fw = ImageFont.truetype(F + "InterDisplay-ExtraBold.otf", 190); ft = ImageFont.truetype(F + "Inter-SemiBold.otf", 44); fl = ImageFont.truetype(F + "InterDisplay-ExtraBold.otf", 150)
BG, TEAL, MINT = (11, 59, 55), (15, 118, 110), (213, 245, 239)
p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16",
                      "-preset", "veryfast", "-pix_fmt", "yuv420p", "build/logo.tmp.mp4"], stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)):
    t = i / FPS; im = Image.new("RGB", (W, H), BG); cx, cy = W // 2 + val("slide_x", t), H // 2 - 30
    r = val("ring", t)
    if 0 < r < 1:                                   # expanding ring burst behind the tile
        R = 140 + 420 * r; d = ImageDraw.Draw(im); a = int(255 * (1 - r)); col = tuple(int(c1 * (a / 255) + c0 * (1 - a / 255)) for c1, c0 in zip(MINT, BG))
        d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=col, width=6)
    s = val("tile_scale", t)
    if s > 0.01:
        size = int(300 * s); tile = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
        td.rounded_rectangle((0, 0, 299, 299), radius=72, fill=TEAL)
        la = val("letter_a", t)
        if la > 0:
            layer = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); ImageDraw.Draw(layer).text((150, 150 + val("letter_y", t)), "h", font=fl, fill=MINT + (int(255 * la),), anchor="mm")
            tile = Image.alpha_composite(tile, layer)
        tile = tile.resize((max(1, size), max(1, size)), Image.LANCZOS).rotate(val("tile_rot", t), resample=Image.BICUBIC, expand=True)
        im.paste(tile, (int(cx - tile.width / 2), int(cy - tile.height / 2)), tile)
    wr = val("word_reveal", t)
    if wr > 0:
        word = Image.new("RGBA", (900, 260), (0, 0, 0, 0)); ImageDraw.Draw(word).text((0, 130), "Hisaab", font=fw, fill=(255, 255, 255, 255), anchor="lm")
        mask = Image.new("L", word.size, 0); ImageDraw.Draw(mask).rectangle((0, 0, int(900 * wr), 260), fill=255)
        word.putalpha(Image.composite(word.getchannel("A"), Image.new("L", word.size, 0), mask)); im.paste(word, (int(cx + 200), int(cy - 130)), word)
    ta = val("tag_a", t)
    if ta > 0:
        col = tuple(int(c1 * ta + c0 * (1 - ta)) for c1, c0 in zip(MINT, BG)); ImageDraw.Draw(im).text((W // 2, cy + 240), "Split it. Settle it.", font=ft, fill=col, anchor="mm")
    fo = val("fade_out", t)
    if fo < 1: im = Image.blend(Image.new("RGB", (W, H), BG), im, fo)
    p.stdin.write(im.tobytes())
p.stdin.close(); p.wait()
# soft whoosh + chime synced to the keyframes
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/logo.tmp.mp4", "-f", "lavfi", "-i", "anoisesrc=d=0.8:c=pink:a=0.25,afade=t=in:d=0.5,afade=t=out:st=0.5:d=0.3,lowpass=f=1800",
                "-f", "lavfi", "-i", "sine=f=880:d=1.6,afade=t=out:st=0.1:d=1.5,volume=0.25", "-f", "lavfi", "-i", "sine=f=1318.5:d=1.6,afade=t=out:st=0.1:d=1.5,volume=0.15",
                "-filter_complex", "[2:a][3:a]amix=inputs=2,adelay=1600|1600[ch];[1:a][ch]amix=inputs=2:duration=longest,apad,atrim=0:5[a]", "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "build/logo.mix.mp4"], check=True)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", "build/logo.mix.mp4", "-af", "loudnorm=I=-16:TP=-1.5", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart", "exports/logo-reveal.mp4"], check=True)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 4.2))
for prop in ("tile_scale", "letter_a", "word_reveal", "tag_a", "fade_out"):
    ts = [i / 100 for i in range(501)]; ax.plot(ts, [val(prop, t) for t in ts], label=prop, lw=2)
    ax.scatter([k[0] for k in KF[prop]], [k[1] for k in KF[prop]], s=18)
xs = [i / 100 for i in range(501)]; ax.plot(xs, [val("slide_x", t) / -330 for t in xs], label="slide_x (normalised)", lw=2, ls="--")
ax.set_xlabel("seconds"); ax.set_ylabel("value"); ax.set_title("Keyframes and easing curves (dots = keyframes; 'back' easing overshoots on the tile scale)", loc="left", fontsize=10)
ax.legend(frameon=False, fontsize=8, ncol=3); [ax.spines[s].set_visible(False) for s in ("top", "right")]; fig.tight_layout(); fig.savefig("exports/logo-keyframes.png", dpi=130)
print("ok")
