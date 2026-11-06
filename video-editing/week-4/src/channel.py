"""Channel kit and thumbnails for the week-4 project.
  channel/banner.png 2560x1440 (all text inside YouTube's 1546x423 safe area) + banner-preview.png (TV / desktop / mobile crops)
  channel/profile.png 800x800 (reads inside the circle crop), channel/watermark.png 150x150 (transparent, for the video watermark)
  exports/thumbnails/long-form.png 1280x720, cover-short-a/b/c.png 1080x1920, at-small-size.png
    python src/channel.py"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
F = "/usr/share/fonts/opentype/inter/"; os.makedirs("channel", exist_ok=True); os.makedirs("exports/thumbnails", exist_ok=True)
BRAND, TEAL, MINT, YELLOW, INK, RED = (11, 59, 55), (15, 118, 110), (213, 245, 239), (255, 216, 77), (16, 24, 40), (215, 38, 61)
fnt = lambda s, n="InterDisplay-ExtraBold.otf": ImageFont.truetype(F + n, s)
NAME, TAGLINE = "Room 214", "Student money, without the awkwardness"
def glow(size, c):
    im = Image.new("RGBA", size, BRAND + (255,)); d = ImageDraw.Draw(im); R = max(size)
    for r in range(R, 0, -max(8, R // 40)): v = tuple(min(255, x + (R - r) * 28 // R) for x in BRAND); d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=v + (255,))
    return im
def tile(size):
    t = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(t); d.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 4, fill=TEAL)
    d.text((size / 2, size / 2), "214", font=fnt(int(size * .36)), fill=MINT, anchor="mm"); return t
def grab(src, t, vf):
    out = "build/_g.png"; subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf", vf, out], check=True); return Image.open(out).convert("RGBA")
person = grab("../week-3/exports/greenscreen-raw.mp4", 1.5, "format=yuva420p,chromakey=0x2EB14A:0.10:0.02,despill=type=green:mix=0.6:expand=0.1,format=rgba,crop=880:940:560:0")
phone = lambda name, t: grab(f"../week-2/build/rec_{name}.webm", t, "crop=432:946:464:66")
def rounded(im, r):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=r, fill=255); im = im.copy(); im.putalpha(m); return im
def shadow(im, r=24):
    sh = Image.new("RGBA", (im.width + 4 * r, im.height + 4 * r), (0, 0, 0, 0)); sh.paste((0, 0, 0, 120), (2 * r, 2 * r), im.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(r)); sh.alpha_composite(im, (2 * r, 2 * r - 16)); return sh

# ---- banner: safe area 1546x423 centred at (1280, 720)
b = glow((2560, 1440), (1280, 720)); d = ImageDraw.Draw(b); sx, sy = (2560 - 1546) // 2, (1440 - 423) // 2
b.alpha_composite(tile(300), (sx + 30, sy + 62))
d.text((sx + 380, sy + 70), NAME, font=fnt(150), fill="white"); d.text((sx + 386, sy + 245), TAGLINE, font=fnt(52, "InterDisplay-Bold.otf"), fill=MINT)
d.text((sx + 386, sy + 325), "New videos every Sunday  ·  hacks, habits and the app I'm designing", font=fnt(34, "Inter-SemiBold.otf"), fill=YELLOW)
for k in range(14):                                                                       # decorative ₹ chips outside the safe area (TV only)
    x, y = 120 + (k * 397) % 2400, 120 + (k * 263) % 1200
    if not (sx - 80 < x < sx + 1546 + 80 and sy - 80 < y < sy + 423 + 80): d.rounded_rectangle((x, y, x + 150, y + 70), radius=35, outline=(40, 110, 102), width=4)
b.convert("RGB").save("channel/banner.png", optimize=True)
pv = Image.new("RGB", (1280 + 40, 720 + 211 + 211 + 120), "white"); dp = ImageDraw.Draw(pv); f = fnt(26, "Inter-SemiBold.otf")
pv.paste(b.convert("RGB").resize((1280, 720)), (20, 40)); dp.text((20, 8), "TV (full 2560x1440)", font=f, fill=INK)
dt_ = b.crop((0, sy, 2560, sy + 423)).convert("RGB").resize((1280, 211)); pv.paste(dt_, (20, 800)); dp.text((20, 768), "Desktop (2560x423)", font=f, fill=INK)
mb = b.crop((sx, sy, sx + 1546, sy + 423)).convert("RGB").resize((773, 211)); pv.paste(mb, (20, 1050)); dp.text((20, 1018), "Mobile / safe area (1546x423)", font=f, fill=INK)
pv.save("channel/banner-preview.png")
# ---- profile picture and watermark
pr = glow((800, 800), (400, 400)); pr.alpha_composite(tile(520), (140, 140)); pr.convert("RGB").save("channel/profile.png")
ck = pr.copy(); m = Image.new("L", (800, 800), 0); ImageDraw.Draw(m).ellipse((0, 0, 799, 799), fill=255); ck.putalpha(m); ck.save("build/profile-circle.png")
wm = tile(150); wm.putalpha(wm.getchannel("A").point(lambda v: int(v * .85))); wm.save("channel/watermark.png")

# ---- long-form thumbnail
th = glow((1280, 720), (900, 420)); d = ImageDraw.Draw(th)
p = person.resize((int(person.width * .8), int(person.height * .8))); th.alpha_composite(p, (1280 - p.width + 120, 720 - p.height + 30))
d.text((56, 70), "5", font=fnt(330), fill=YELLOW); d.text((290, 120), "MONEY", font=fnt(120), fill="white"); d.text((290, 245), "HABITS", font=fnt(120), fill="white")
d.text((60, 440), "that save", font=fnt(70, "InterDisplay-Bold.otf"), fill=MINT); d.text((60, 520), "friendships", font=fnt(96), fill=YELLOW)
d.rounded_rectangle((800, 40, 1230, 120), radius=20, fill=RED); d.text((1015, 80), "HOSTEL EDITION", font=fnt(44), fill="white", anchor="mm")
th.convert("RGB").save("exports/thumbnails/long-form.png", optimize=True)
# ---- shorts covers
def cover(lines, hi, art, xy, out):
    im = glow((1080, 1920), (540, 1100)); d = ImageDraw.Draw(im); im.alpha_composite(art, xy); y = 330
    for k, ln in enumerate(lines):
        f = fnt(160 if len(ln) <= 7 else 124); d.text((540, y), ln, font=f, fill=YELLOW if k in hi else "white", stroke_width=10, stroke_fill=INK, anchor="ma"); y += f.size + 18
    im.convert("RGB").save(out, optimize=True); return im
ph = lambda n, t, w: shadow(rounded(phone(n, t).resize((w, int(w * 946 / 432))), 46))
ca = cover(["SETTLE", "EVERY", "SUNDAY"], {2}, ph("settle", 13, 500), (290 - 48, 920), "exports/thumbnails/cover-short-a.png")
cb = cover(["FAIR,", "NOT EQUAL"], {0}, ph("add", 17.5, 540), (270 - 48, 760), "exports/thumbnails/cover-short-b.png")
pp = person.resize((int(person.width * 1.15), int(person.height * 1.15)))
cc = cover(["LET THE APP", "BE THE", "BAD GUY"], {2}, pp, (540 - pp.width // 2, 1920 - pp.height), "exports/thumbnails/cover-short-c.png")
s = Image.new("RGB", (3 * 266 + 20, 138 + 245 + 60), "white"); s.paste(th.convert("RGB").resize((246, 138), Image.LANCZOS), (20, 20)); s.paste(ck.convert("RGB").resize((88, 88)), (300, 45))
s.paste(b.crop((sx, sy, sx + 1546, sy + 423)).convert("RGB").resize((420, 115)), (410, 30))
for k, c in enumerate((ca, cb, cc)): s.paste(c.convert("RGB").crop((0, 285, 1080, 1635)).resize((180, 225), Image.LANCZOS), (60 + 266 * k, 190))
s.save("exports/thumbnails/at-small-size.png"); print("channel kit + thumbnails done")
