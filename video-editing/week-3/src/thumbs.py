"""YouTube thumbnails (1280x720) and matching Shorts/Reels covers (1080x1920), built from the same brand kit and footage.
Also renders them at the size people actually see them (search results ~ 246x138 px on mobile) to check legibility.
    python src/thumbs.py  -> exports/thumbnails/*.png, exports/thumbnails/at-small-size.png"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
F = "/usr/share/fonts/opentype/inter/"; O = "exports/thumbnails"; os.makedirs(O, exist_ok=True); W2 = "../week-2/build/"
BRAND, TEAL, MINT, YELLOW, INK, RED = (11, 59, 55), (15, 118, 110), (213, 245, 239), (255, 216, 77), (16, 24, 40), (215, 38, 61)
fnt = lambda s, n="InterDisplay-ExtraBold.otf": ImageFont.truetype(F + n, s)
def grab(src, t, out, vf):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf", vf, out], check=True); return Image.open(out).convert("RGBA")
PH = "crop=432:946:464:66"                     # the phone screen only
phone_add = grab(W2 + "rec_add.webm", 6, "build/t_add.png", PH); phone_home = grab(W2 + "rec_home.webm", 2, "build/t_home.png", PH)
phone_settle = grab(W2 + "rec_settle.webm", 13, "build/t_settle.png", PH)
person = grab("exports/greenscreen-raw.mp4", 1.5, "build/t_person.png", "format=yuva420p,chromakey=0x2EB14A:0.10:0.02,despill=type=green:mix=0.6:expand=0.1,format=rgba,crop=880:940:560:0")
comp = grab("exports/greenscreen-composite.mp4", 1.5, "build/t_comp.png", "null"); raw = grab("exports/greenscreen-raw.mp4", 1.5, "build/t_raw.png", "null")

def shadow(im, r=24, off=(0, 18), a=110):
    sh = Image.new("RGBA", (im.width + 4 * r, im.height + 4 * r), (0, 0, 0, 0)); sh.paste((0, 0, 0, a), (2 * r, 2 * r), im.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(r)); out = sh.copy(); out.alpha_composite(im, (2 * r - off[0], 2 * r - off[1])); return out
def rounded(im, r=40):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=r, fill=255); im = im.copy(); im.putalpha(m); return im
def outlined(d, xy, text, font, fill, stroke=0, sfill=INK, anchor="la"):
    d.text(xy, text, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill, anchor=anchor)
def bg(size, glow=(700, 360)):
    im = Image.new("RGBA", size, BRAND + (255,)); d = ImageDraw.Draw(im)
    for r in range(900, 0, -40): c = tuple(min(255, v + (900 - r) // 30) for v in BRAND); d.ellipse((glow[0] - r, glow[1] - r, glow[0] + r, glow[1] + r), fill=c + (255,))
    return im
def badge(d, xy, text, size=44, fill=RED, fg="white"):
    f = fnt(size); w = f.getlength(text); x, y = xy; d.rounded_rectangle((x, y, x + w + 44, y + size + 30), radius=18, fill=fill); d.text((x + 22, y + 13), text, font=f, fill=fg)
def arrow(d, a, b, w=16, col=YELLOW):
    import math
    d.line((a, b), fill=col, width=w); ang = math.atan2(b[1] - a[1], b[0] - a[0])
    p = [b, (b[0] - 50 * math.cos(ang - .5), b[1] - 50 * math.sin(ang - .5)), (b[0] - 50 * math.cos(ang + .5), b[1] - 50 * math.sin(ang + .5))]; d.polygon(p, fill=col)

# ---------------- YouTube thumbnails, 1280x720
def yt1():   # week-2 tutorial
    im = bg((1280, 720), (950, 360)); d = ImageDraw.Draw(im)
    ph = shadow(rounded(phone_add.resize((300, 657)), 34)).rotate(-6, expand=True, resample=Image.BICUBIC); im.alpha_composite(ph, (800, 40))
    outlined(d, (60, 120), "SPLIT", fnt(150), "white"); outlined(d, (60, 270), "₹360", fnt(190), YELLOW); outlined(d, (64, 490), "in 3 minutes", fnt(70, "InterDisplay-Bold.otf"), MINT)
    badge(d, (66, 600), "UPI · FREE", 40, TEAL); arrow(d, (640, 330), (860, 210)); return im
def yt2():   # "stop being the group's bank"
    im = bg((1280, 720), (900, 420)); d = ImageDraw.Draw(im)
    p = person.resize((int(person.width * .78), int(person.height * .78))); im.alpha_composite(p, (1280 - p.width + 140, 720 - p.height + 20))
    outlined(d, (56, 80), "STOP", fnt(130), "white"); outlined(d, (56, 210), "BEING THE", fnt(80), "white"); outlined(d, (56, 300), "GROUP'S", fnt(130), YELLOW); outlined(d, (56, 430), "BANK", fnt(130), YELLOW)
    badge(d, (60, 600), "+ ₹854 owed", 46, RED); return im
def yt3():   # green-screen breakdown
    im = Image.new("RGBA", (1280, 720)); r = raw.resize((1280, 720)); c = comp.resize((1280, 720)); im.paste(c, (0, 0))
    m = Image.new("L", (1280, 720), 0); ImageDraw.Draw(m).polygon([(0, 0), (700, 0), (520, 720), (0, 720)], fill=255); im.paste(r, (0, 0), m)
    d = ImageDraw.Draw(im); d.line((700, 0, 520, 720), fill="white", width=14)
    d.rectangle((0, 520, 1280, 720), fill=(0, 0, 0, 0)); ov = Image.new("RGBA", (1280, 230), (11, 59, 55, 235)); im.alpha_composite(ov, (0, 490))
    outlined(d, (50, 505), "GREEN SCREEN", fnt(118), "white"); outlined(d, (54, 630), "with free tools only", fnt(56, "InterDisplay-Bold.otf"), MINT)
    badge(d, (900, 40), "BEFORE → AFTER", 40, YELLOW, INK); return im
# ---------------- Shorts / Reels covers, 1080x1920 (text kept in the centre 1080x1350 so the 4:5 grid crop still reads)
def cover(title_lines, hi, art, art_xy, sub=None):
    im = bg((1080, 1920), (540, 1100)); d = ImageDraw.Draw(im); im.alpha_composite(art, art_xy)
    y = 330
    for k, ln in enumerate(title_lines):
        f = fnt(160 if len(ln) <= 7 else 124); outlined(d, (540, y), ln, f, YELLOW if k in hi else "white", 10, INK, "ma"); y += f.size + 18
    if sub: badge(d, (540 - fnt(46).getlength(sub) / 2 - 22, y + 20), sub, 46, TEAL)
    return im
def c1(): ph = shadow(rounded(phone_add.resize((560, 1226)), 50)); return cover(["SPLIT ₹360", "IN 10 SEC"], {0}, ph, (540 - ph.width // 2, 700))
def c2(): ph = shadow(rounded(phone_settle.resize((500, 1095)), 46)); return cover(["3", "MONEY", "RULES"], {0}, ph, (540 - ph.width // 2, 900), "for hostel life")
def c3(): p = person.resize((int(person.width * 1.15), int(person.height * 1.15))); return cover(["STOP BEING", "THE GROUP'S", "BANK"], {2}, p, (540 - p.width // 2, 1920 - p.height))
outs = {"yt-1-split-hostel-expenses.png": yt1(), "yt-2-group-bank.png": yt2(), "yt-3-green-screen.png": yt3(),
        "cover-short-1.png": c1(), "cover-short-2.png": c2(), "cover-short-3.png": c3()}
for n, im in outs.items(): im.convert("RGB").save(f"{O}/{n}", optimize=True)
# legibility check: thumbnails as seen in mobile search (246x138) and covers as seen in the profile grid (4:5 crop, 180x225)
sheet = Image.new("RGB", (3 * 266 + 20, 138 + 245 + 60), "white"); d = ImageDraw.Draw(sheet)
for k, n in enumerate([n for n in outs if n.startswith("yt")]): sheet.paste(outs[n].convert("RGB").resize((246, 138), Image.LANCZOS), (20 + 266 * k, 20))
for k, n in enumerate([n for n in outs if n.startswith("cover")]):
    c = outs[n].convert("RGB").crop((0, 285, 1080, 1635)).resize((180, 225), Image.LANCZOS); sheet.paste(c, (60 + 266 * k, 190))
sheet.save(f"{O}/at-small-size.png"); print("thumbnails:", list(outs))
