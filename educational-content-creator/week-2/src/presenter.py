"""Illustrated talking-head presenter ("Mina", host of Code in Small Steps), lip-synced to a voice track.
No camera here, so the presenter is drawn, but the craft the brief asks about is applied:
  * three-point lighting: warm key light from camera-left (bright side of the face and wall), soft fill on the shadow
    side, and a cool rim light separating hair and shoulders from the background; shallow depth of field behind
  * framing: eyes on the upper third line, head room, the subject on the right third so text can sit on the left
  * performance: the mouth opens with loudness and changes shape with brightness of the sound (wide "ee" vs round
    "oh"), blinks every few seconds, small head motion that follows speech energy, breathing
    from presenter import render;  render("build/x.wav", "build/x.mp4", mode="full" | "cam")
"""
import math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
FPS = 30
SKIN, SKIN_SH, HAIR, TOP, TOP_SH = (214, 160, 128), (176, 120, 94), (38, 28, 26), (30, 64, 120), (22, 46, 90)
def analyse(wav_path, n):
    with wave.open(wav_path) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if x.ndim > 1: x = x.mean(1)
    hop = sr // FPS; rms, bright = np.zeros(n), np.zeros(n)
    for i in range(n):
        seg = x[i * hop:(i + 1) * hop + hop // 2]
        if len(seg) < 32: continue
        rms[i] = np.sqrt(np.mean(seg ** 2)); spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); f = np.fft.rfftfreq(len(seg), 1 / sr)
        bright[i] = (spec * f).sum() / (spec.sum() + 1e-9)
    rms = rms / (np.percentile(rms[rms > 0], 95) + 1e-9) if (rms > 0).any() else rms
    sm = np.zeros(n); b = np.zeros(n)
    for i in range(n): sm[i] = .55 * (sm[i - 1] if i else 0) + .45 * min(1.2, rms[i]); b[i] = .7 * (b[i - 1] if i else 1500) + .3 * bright[i]
    return sm, b
def background(W, H, s, ox):
    """Studio corner: warm wall with key-light falloff, shelf with books and a plant, all defocused."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    key = np.exp(-(((xx - .25 * W) / (.75 * W)) ** 2 + ((yy - .2 * H) / (.9 * H)) ** 2))
    base = np.array([226, 214, 200], np.float32) * (.62 + .45 * key[..., None]); base[..., 2] *= .97
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    sx = ox - 760 * s; sy = 300 * s
    d.rectangle((sx, sy + 260 * s, sx + 520 * s, sy + 285 * s), fill=(120, 92, 70))                    # shelf
    cols = [(196, 84, 60), (64, 108, 160), (230, 180, 70), (90, 140, 110), (150, 90, 140), (60, 70, 90)]
    x = sx + 20 * s
    for k in range(9):
        w_ = (34 + 9 * (k % 3)) * s; h_ = (150 + 40 * ((k * 7) % 3)) * s; d.rectangle((x, sy + 260 * s - h_, x + w_, sy + 260 * s), fill=cols[k % 6]); x += w_ + 6 * s
    px, py = sx + 430 * s, sy + 190 * s; d.rectangle((px - 40 * s, py, px + 40 * s, py + 70 * s), fill=(180, 110, 80))   # plant
    for a in range(9): ang = math.pi * (1.1 + .8 * a / 8); d.ellipse((px + 110 * s * math.cos(ang) - 34 * s, py + 110 * s * math.sin(ang) - 18 * s, px + 110 * s * math.cos(ang) + 34 * s, py + 110 * s * math.sin(ang) + 18 * s), fill=(70, 130, 80))
    d.ellipse((W - 380 * s, -200 * s, W + 200 * s, 300 * s), fill=(250, 240, 222))                        # practical lamp glow
    return im.filter(ImageFilter.GaussianBlur(14 * s))                                                    # shallow depth of field
def body(s):
    """Shoulders + neck + head base (no eyes/mouth) at 2x, with fill shading and a rim light. Returns RGBA at 1x."""
    S = 2 * s; im = Image.new("RGBA", (int(900 * S), int(1400 * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = 450 * S
    rim = (190, 220, 255, 255)
    d.rounded_rectangle((c - 330 * S + 6 * S, 700 * S - 4 * S, c + 330 * S + 6 * S, 1400 * S), radius=150 * S, fill=rim)      # rim on shoulders (camera right)
    d.rounded_rectangle((c - 330 * S, 700 * S, c + 330 * S, 1400 * S), radius=150 * S, fill=TOP)
    d.polygon([(c + 40 * S, 700 * S), (c + 330 * S, 760 * S), (c + 330 * S, 1400 * S), (c + 60 * S, 1400 * S)], fill=TOP_SH)      # fill side shadow
    d.rectangle((c - 60 * S, 560 * S, c + 60 * S, 720 * S), fill=SKIN_SH); d.chord((c - 110 * S, 640 * S, c + 110 * S, 780 * S), 0, 180, fill=SKIN_SH)
    d.polygon([(c - 70 * S, 705 * S), (c, 790 * S), (c + 70 * S, 705 * S)], fill=(240, 236, 228))                              # collar
    return im
def head_base(s):
    S = 2 * s; im = Image.new("RGBA", (int(560 * S), int(640 * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = 280 * S
    d.ellipse((c - 205 * S + 7 * S, 40 * S - 6 * S, c + 205 * S + 7 * S, 420 * S), fill=(190, 220, 255))                       # rim on hair
    d.ellipse((c - 205 * S, 40 * S, c + 205 * S, 470 * S), fill=HAIR)                                                          # hair back
    d.rounded_rectangle((c - 200 * S, 230 * S, c + 200 * S, 590 * S), radius=int(90 * S), fill=HAIR)
    for ex in (-1, 1): d.ellipse((c + ex * 168 * S - 26 * S, 290 * S, c + ex * 168 * S + 26 * S, 370 * S), fill=SKIN if ex < 0 else SKIN_SH)   # ears
    d.ellipse((c - 160 * S, 110 * S, c + 160 * S, 520 * S), fill=SKIN)                                                          # face
    sh = Image.new("L", im.size, 0); ImageDraw.Draw(sh).ellipse((c - 20 * S, 110 * S, c + 220 * S, 540 * S), fill=95)          # fill-side shadow
    sh = sh.filter(ImageFilter.GaussianBlur(40 * S)); m = Image.new("L", im.size, 0); ImageDraw.Draw(m).ellipse((c - 160 * S, 110 * S, c + 160 * S, 520 * S), fill=255)
    from PIL import ImageChops; sh = ImageChops.multiply(sh, m); im.paste(Image.new("RGBA", im.size, SKIN_SH + (255,)), (0, 0), sh)
    d = ImageDraw.Draw(im)
    d.chord((c - 180 * S, 60 * S, c + 190 * S, 330 * S), 160, 380, fill=HAIR)                                                  # fringe
    d.polygon([(c - 160 * S, 200 * S), (c - 60 * S, 170 * S), (c - 140 * S, 300 * S)], fill=HAIR)
    d.ellipse((c - 18 * S, 330 * S, c + 18 * S, 372 * S), fill=SKIN_SH)                                                         # nose shadow
    for ex in (-1, 1): d.ellipse((c + ex * 95 * S - 34 * S, 380 * S, c + ex * 95 * S + 34 * S, 410 * S), fill=(226, 150, 130))  # cheeks
    return im
def features(s, openness, wide, blink, brow):
    """Eyes, brows, mouth on a 2x canvas aligned with head_base."""
    S = 2 * s; im = Image.new("RGBA", (int(560 * S), int(640 * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = 280 * S
    for ex in (-1, 1):
        x = c + ex * 70 * S; y = 300 * S
        if blink > .5: d.arc((x - 30 * S, y - 10 * S, x + 30 * S, y + 14 * S), 20, 160, fill=(40, 30, 28), width=int(6 * S))
        else:
            d.ellipse((x - 30 * S, y - 20 * S, x + 30 * S, y + 20 * S), fill=(250, 248, 244)); d.ellipse((x - 16 * S, y - 17 * S, x + 16 * S, y + 17 * S), fill=(70, 48, 36))
            d.ellipse((x - 8 * S, y - 9 * S, x + 8 * S, y + 9 * S), fill=(18, 14, 14)); d.ellipse((x - 12 * S, y - 13 * S, x - 4 * S, y - 5 * S), fill=(255, 255, 255))   # catch light from the key
        by = y - 48 * S - brow * 10 * S; d.line((x - 34 * S, by + 6 * S, x, by - 2 * S, x + 34 * S, by + 6 * S), fill=HAIR, width=int(9 * S), joint="curve")
    mx, my = c, 440 * S; w_ = (44 + 26 * wide - 10 * (1 - wide) * openness) * S; h_ = (4 + 46 * openness) * S
    if openness < .08: d.arc((mx - w_, my - 14 * S, mx + w_, my + 14 * S), 20, 160, fill=(150, 70, 70), width=int(7 * S))
    else:
        d.rounded_rectangle((mx - w_, my - h_ / 2, mx + w_, my + h_ / 2), radius=int(min(w_, h_ / 2)), fill=(110, 40, 46))
        if h_ > 18 * S: d.rectangle((mx - w_ * .7, my - h_ / 2, mx + w_ * .7, my - h_ / 2 + 9 * S), fill=(248, 246, 240))          # teeth
        d.rounded_rectangle((mx - w_ * .5, my + h_ / 2 - 12 * S, mx + w_ * .5, my + h_ / 2), radius=int(6 * S), fill=(206, 96, 100))  # tongue
    return im
def render(wav_path, out, mode="full", seconds=None, W=1920, H=1080):
    """mode full: 1920x1080, presenter on the right third. mode cam: 720x720 head-and-shoulders crop for picture-in-picture."""
    with wave.open(wav_path) as w: dur = w.getnframes() / w.getframerate()
    dur = seconds or dur; n = int(round(dur * FPS)); rms, bright = analyse(wav_path, n)
    if mode == "cam": W, H, s, cx, top = 720, 720, .75, 360, -40
    else: s, cx, top = 1.0, 1330, -60
    bg = background(W, H, s, cx if mode == "cam" else cx + 1100).convert("RGBA")   # full shot: shelf moves right, keeping the left clean for text
    bd = body(s).resize((int(900 * s), int(1400 * s)), Image.LANCZOS); hb = head_base(s)
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", out[:-4] + ".tmp.mp4"], stdin=subprocess.PIPE)
    rng = np.random.default_rng(3); blinks = set(); t = 1.2
    while t < dur: blinks.update(range(int(t * FPS), int(t * FPS) + 4)); t += rng.uniform(2.5, 5.0)
    feat_cache = {}
    for i in range(n):
        t = i / FPS; e = rms[i]; op = 0 if e < .12 else min(1, (e - .12) * 1.4)
        wide = float(np.clip((bright[i] - 900) / 1600, 0, 1)); bl = 1 if i in blinks else 0; brow = min(1, e * .8)
        breathe = 4 * math.sin(t * 1.6); bob_y = breathe * s + 6 * s * math.sin(t * 2.3) * e; bob_x = 8 * s * math.sin(t * .7)
        key = (round(op * 12), round(wide * 4), bl, round(brow * 4))
        if key not in feat_cache:
            f = hb.copy(); f.alpha_composite(features(s, key[0] / 12, key[1] / 4, key[2], key[3] / 4)); feat_cache[key] = f.resize((int(560 * s), int(640 * s)), Image.LANCZOS)
        fr = bg.copy(); fr.alpha_composite(bd, (int(cx - 450 * s + bob_x * .4), int(top + 50 * s + breathe * s)))
        fr.alpha_composite(feat_cache[key], (int(cx - 280 * s + bob_x), int(top + 110 * s + bob_y)))
        p.stdin.write(fr.convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    import os; os.replace(out[:-4] + ".tmp.mp4", out); return dur
