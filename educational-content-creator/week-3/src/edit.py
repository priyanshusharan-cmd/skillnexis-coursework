"""The edit: assembles the lesson-2 long-form from the raw material in build/materials.json.
  * Talking head: silences removed automatically (silencedetect), flubbed takes cut using the editor's marks, and
    every jump cut alternated between a wide and a punched-in framing so the cut reads as intentional.
  * Transitions: dip-to-colour into chapter cards, push from card to content, short cross-dissolves elsewhere.
  * Text overlays: lower third, chapter chip, key-point panels beside the presenter, chapter cards, try-it countdown,
    progress bar.
  * Screen parts: zoom-ins that follow the action, and annotations (boxes around code or output, call-out labels).
  * Audio: clip audio with 10 ms fades at every cut, music bed ducked under the voice, -14 LUFS. SRT captions.
    python src/edit.py   -> exports/if-else-long-form.mp4, .srt, results/edl.json, results/edit-report.md"""
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "src")
from script_ifelse import SECTIONS
from engine import loudness, VOICE_CHAIN, B, SR
W, H, FPS = 1920, 1080, 30
F = "/usr/share/fonts/opentype/inter/"; MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
fnt = lambda n, s: ImageFont.truetype(F + n, s)
CREAM, NAVY, ORANGE, YELLOW, MUTED = (255, 248, 238), (20, 33, 61), (232, 89, 12), (255, 212, 59), (91, 100, 116)
M = json.load(open(f"{B}/materials.json")); smooth = lambda u: u * u * (3 - 2 * u)

# ------------------------------------------------------------------ edit decision list
def head_keeps(m, pre=.12, post=.22, merge=.3):
    """Spoken regions from silence detection, minus the marked retakes, padded so words aren't clipped."""
    keeps = []
    for a, b in m["speech"]:
        if any(a < r1 and b > r0 for r0, r1 in m["retakes"]): continue        # a flubbed take or the "sorry" restart
        a, b = max(0, a - pre), min(m["dur"], b + post)
        if keeps and a - keeps[-1][1] < merge: keeps[-1] = (keeps[-1][0], b)
        else: keeps.append((a, b))
    return keeps
EDL, t_out = [], 0.0
for s in SECTIONS:
    k, i = s["kind"], s["id"]; m = M.get(i, {})
    if k == "head":
        for j, (a, b) in enumerate(head_keeps(m)):
            EDL.append(dict(sec=i, kind="head", src=m["video"], wav=m["wav"], a=a, b=b, out=t_out, zoom=(1.0, .5, .5) if j % 2 == 0 else (1.16, .69, .36),
                            trans="fade" if j == 0 and EDL else None)); t_out += b - a
    elif k == "card": EDL.append(dict(sec=i, kind="card", a=0, b=2.6, out=t_out, trans="dip")); t_out += 2.6
    elif k == "screen":
        EDL.append(dict(sec=i, kind="screen", src=m["video"], wav=m["wav"], a=0, b=m["dur"], out=t_out, trans="push" if EDL[-1]["kind"] == "card" else "fade")); t_out += m["dur"]
    elif k == "try": EDL.append(dict(sec=i, kind="try", wav=m["wav"], a=0, b=m["dur"], out=t_out, trans="dip")); t_out += m["dur"]
TOTAL = t_out
def map_time(sec, src_t):
    """Source time in a section's raw material -> time in the finished edit (None if that moment was cut)."""
    for c in EDL:
        if c["sec"] == sec and c["a"] - 1e-6 <= src_t <= c["b"] + 1e-6: return c["out"] + src_t - c["a"]
    best = [c for c in EDL if c["sec"] == sec and c["a"] >= src_t]
    return best[0]["out"] if best else None

# ------------------------------------------------------------------ editor geometry (matches src/editor.html)
CODE_Y0, LH, CODE_X, CW = 134, 44.8, 462, 16.8
TERM_Y0, TLH, TERM_X, TCW = 698, 36.25, 406, 15.0
def code_at(tl, t):
    code = ""
    for e in tl["events"]:
        if e["t"] > t: break
        if e["type"] in ("file", "set"): code = e.get("text", "")
        if e["type"] == "type": code = e["base"] + e["text"] + e.get("after", "")
    return code
def term_at(tl, t):
    lines = []
    for e in tl["events"]:
        if e["t"] > t: break
        if e["type"] == "clear": lines = []
        if e["type"] == "run": lines += [f"$ {e['cmd']}"] + e["out"].split("\n")
    return lines[-9:]
def ann_rect(a, tl, t):
    if a["kind"] == "box":
        code = code_at(tl, t).split("\n"); l0, l1 = a["line"]
        if "cols" in a: x0, x1 = CODE_X + a["cols"][0] * CW - 6, CODE_X + a["cols"][1] * CW + 6
        else: x0, x1 = CODE_X - 10, CODE_X + max(len(code[n - 1]) for n in range(l0, l1 + 1)) * CW + 10
        return (x0, CODE_Y0 + (l0 - 1) * LH - 2, x1, CODE_Y0 + l1 * LH + 2)
    lines = term_at(tl, t)
    for r in range(len(lines) - 1, -1, -1):
        c = lines[r].find(a["text"])
        if c >= 0 and not lines[r].startswith("$"): return (TERM_X + c * TCW - 6, TERM_Y0 + r * TLH - 1, TERM_X + (c + len(a["text"])) * TCW + 6, TERM_Y0 + (r + 1) * TLH + 1)
    return None

# ------------------------------------------------------------------ drawing helpers
FL, FLS, FCH, FCARD, FNUM, FPANEL, FT = fnt("InterDisplay-Bold.otf", 34), fnt("Inter-SemiBold.otf", 24), fnt("Inter-SemiBold.otf", 26), fnt("InterDisplay-ExtraBold.otf", 110), fnt("InterDisplay-ExtraBold.otf", 260), ImageFont.truetype(MONO, 46), fnt("InterDisplay-Bold.otf", 50)
def label(d, x, y, text, age):
    q = min(1, age / .2); w = d.textlength(text, font=FL) + 40
    d.rounded_rectangle((x, y, x + w, y + 60), radius=16, fill=YELLOW + (int(255 * q),)); d.text((x + 20, y + 30), text, font=FL, fill=NAVY + (int(255 * q),), anchor="lm"); return w
def draw_ann(im, a, rect, age):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov); q = min(1, age / .25)
    d.rounded_rectangle(rect, radius=10, outline=ORANGE + (int(255 * q),), width=5)
    x0, y0, x1, y1 = rect
    if a["kind"] == "term": lx, ly = min(x0, W - 560), y0 - 80
    else: lx, ly = x1 + 60, (y0 + y1) / 2 - 30
    if lx + d.textlength(a["label"], font=FL) + 40 > W - 340 and a["kind"] != "term": lx, ly = x0, y1 + 16
    d.line((lx, ly + 30, x1 if lx > x1 else (x0 + x1) / 2, (y0 + y1) / 2 if lx > x1 else (y1 if ly > y1 else y0)), fill=YELLOW + (int(255 * q),), width=4)
    label(d, lx, ly, a["label"], age); im.alpha_composite(ov)
def zoom(im, z, cx, cy):
    if abs(z - 1) < 1e-3: return im
    w, h = W / z, H / z; x0 = min(max(0, cx * W - w / 2), W - w); y0 = min(max(0, cy * H - h / 2), H - h)
    return im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))
def zoom_at(keys, t):
    cur = (1.0, .5, .5)
    for kt, z, cx, cy in keys:
        if t < kt: break
        u = smooth(min(1, (t - kt) / .7)); cur = tuple(c + (n - c) * u for c, n in zip(cur, (z, cx, cy)))
    return cur
def card(sec, t):
    im = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(im); u = min(1, t / .4); e = 1 - (1 - u) ** 3
    d.text((160 - 60 * (1 - e), 560), sec["num"], font=FNUM, fill=ORANGE + (int(255 * u),), anchor="ls")
    v = min(1, max(0, (t - .2) / .4)); ev = 1 - (1 - v) ** 3
    d.text((420 + 80 * (1 - ev), 470), sec["title"], font=FCARD, fill=NAVY + (int(255 * v),), anchor="ls")
    d.rectangle((420, 520, 420 + int(500 * ev), 530), fill=ORANGE); d.text((420, 600), "Lesson 2 · If / else", font=FCH, fill=MUTED + (int(255 * v),))
    return im
def try_card(sec, t, timer_at):
    im = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(im)
    d.text((160, 160), "YOUR TURN", font=fnt("Inter-Bold.otf", 34), fill=ORANGE); d.text((160, 210), "Pause and try it", font=fnt("InterDisplay-ExtraBold.otf", 96), fill=NAVY)
    for k, line in enumerate(sec["task"]):
        if t > .5 + .5 * k:
            d.rounded_rectangle((160, 420 + 110 * k, 222, 482 + 110 * k), radius=16, fill=ORANGE); d.text((191, 451 + 110 * k), str(k + 1), font=fnt("Inter-Bold.otf", 34), fill="white", anchor="mm")
            d.text((250, 451 + 110 * k), line, font=fnt("Inter-SemiBold.otf", 46), fill=NAVY, anchor="lm")
    left = max(0, sec["pause"] - max(0, t - timer_at)); cx, cy, r = 1500, 560, 190
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 232, 214), width=18)
    d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * left / sec["pause"], fill=ORANGE, width=18)
    d.text((cx, cy), str(math.ceil(left)), font=fnt("InterDisplay-ExtraBold.otf", 170), fill=ORANGE, anchor="mm"); return im

class Reader:
    def __init__(self, path, start):
        self.start, self.i, self.cur = start, -1, None
        self.p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", path, "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    def get(self, t):
        want = max(0, int(round((t - self.start) * FPS)))
        while self.i < want:
            buf = self.p.stdout.read(W * H * 3)
            if len(buf) < W * H * 3: break
            self.cur = Image.frombuffer("RGB", (W, H), buf).convert("RGBA"); self.i += 1
        return self.cur.copy()
    def close(self): self.p.kill()

# ------------------------------------------------------------------ render
SEC = {s["id"]: s for s in SECTIONS}
first_head = EDL[0]
if __name__ == "__main__":
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", f"{B}/edit_v.mp4"], stdin=subprocess.PIPE)
    prev, f_out = Image.new("RGBA", (W, H), CREAM + (255,)), 0
    panels = {}
    for s in SECTIONS:
        if s["kind"] == "head" and "panel" in s:
            panels[s["id"]] = [(map_time(s["id"], M[s["id"]]["subs"][si][0]), txt, col) for si, txt, col in s["panel"]]
    for ci, c in enumerate(EDL):
        n = int(round((c["out"] + c["b"] - c["a"]) * FPS)) - int(round(c["out"] * FPS)); sec = SEC[c["sec"]]; m = M.get(c["sec"], {})
        rdr = Reader(c["src"], c["a"]) if c["kind"] in ("head", "screen") else None
        if c["kind"] == "screen":
            zk = [(m["subs"][si][0] + at, z, cx, cy) for si, at, z, cx, cy in sec["zoom"]]
            anns = [(a, m["subs"][a["s"]][0] + a["at"], (m["subs"][a["s"] + 1][0] if a["s"] + 1 < len(m["subs"]) else m["dur"]) + .3) for a in sec["ann"]]
        for k in range(n):
            tl_ = c["a"] + k / FPS; tg = (int(round(c["out"] * FPS)) + k) / FPS
            if c["kind"] == "card": im = card(sec, k / FPS)
            elif c["kind"] == "try": im = try_card(sec, k / FPS, m["subs"][0][1] + .3)
            else:
                im = rdr.get(tl_)
                if c["kind"] == "screen":
                    for a, a0, a1 in anns:
                        if a0 <= tl_ < a1:
                            r = ann_rect(a, m["tl"], tl_)
                            if r: draw_ann(im, a, r, tl_ - a0)
                    im = zoom(im, *zoom_at(zk, tl_))
                else: im = zoom(im, *c["zoom"])
            d = ImageDraw.Draw(im)
            if c["kind"] == "head" and c["sec"] in panels:                               # key points beside the presenter
                for j, (pt, txt, col) in enumerate(panels[c["sec"]]):
                    if pt is not None and tg >= pt:
                        q = min(1, (tg - pt) / .3); ImageDraw.Draw(im).text((120 + 40 * (1 - q), 300 + 86 * j), txt, font=FPANEL, fill=tuple(int(x) for x in Image.new("RGB", (1, 1), col).getpixel((0, 0))) + (int(255 * q),))
            if c["sec"] == "hook" and 1.0 < tg < 6.0:                                    # lower third
                q = min(1, (tg - 1.0) / .4); x = int(-640 + 700 * (1 - (1 - q) ** 3))
                d.rectangle((x, 840, x + 600, 960), fill=NAVY); d.rectangle((x, 840, x + 12, 960), fill=ORANGE)
                d.text((x + 40, 860), "Mina", font=FT, fill="white"); d.text((x + 40, 918), "Host, Code in Small Steps", font=FLS, fill=(255, 216, 184))
            if c["kind"] in ("screen", "head") and c["sec"] != "hook":                  # chapter chip
                tw = d.textlength(sec["chapter"], font=FCH) + 44; x0 = W - tw - 40 if c["kind"] == "head" else 1560 - tw
                d.rounded_rectangle((x0, 30, x0 + tw, 82), radius=26, fill=NAVY + (230,)); d.text((x0 + 22, 56), sec["chapter"], font=FCH, fill="white", anchor="lm")
            d.rectangle((0, H - 6, int(W * tg / TOTAL), H), fill=ORANGE)                 # progress bar
            u = k / FPS                                                                   # transitions (into this clip)
            if c.get("trans") == "fade" and u < .35: im = Image.blend(prev, im, smooth(u / .35))
            elif c.get("trans") == "dip" and u < .5:
                mid = Image.new("RGBA", (W, H), CREAM + (255,)); im = Image.blend(prev, mid, smooth(u / .25)) if u < .25 else Image.blend(mid, im, smooth((u - .25) / .25))
            elif c.get("trans") == "push" and u < .45:
                e = smooth(u / .45); out = Image.new("RGBA", (W, H)); out.paste(prev, (int(-e * W), 0)); out.paste(im, (int((1 - e) * W), 0)); im = out
            p.stdin.write(im.convert("RGB").tobytes()); f_out += 1; last = im
        prev = last
        if rdr: rdr.close()
        print(f"clip {ci + 1}/{len(EDL)}", c["sec"], c["kind"], flush=True)
    p.stdin.close(); p.wait()
    # ---------------- audio: clip audio in EDL order with 10 ms fades at each cut
    def wav_np(path):
        with wave.open(path) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    cache, out = {}, np.zeros(int((TOTAL + 1) * SR)); fade = int(.01 * SR)
    for c in EDL:
        i0 = int(round(c["out"] * SR)); n = int(round((c["b"] - c["a"]) * SR))
        if c["kind"] == "card": continue
        x = cache.setdefault(c["wav"], wav_np(c["wav"]))[int(c["a"] * SR):int(c["a"] * SR) + n].copy()
        x[:fade] *= np.linspace(0, 1, min(fade, len(x))); x[-fade:] *= np.linspace(1, 0, min(fade, len(x))); out[i0:i0 + len(x)] += x
    with wave.open(f"{B}/edit_vo.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.clip(out, -32767, 32767).astype(np.int16).tobytes())
    subprocess.run([sys.executable, "src/music.py", str(int(TOTAL) + 8)], check=True, capture_output=True)
    fc = (f"[1:a]{VOICE_CHAIN},aresample=44100,aformat=channel_layouts=stereo,asplit=2[v1][v2];[2:a]volume=0.4[m];[m][v1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=500[duck];"
          f"[duck][v2]amix=inputs=2:duration=first:normalize=0:weights='0.75 1.4',atrim=0:{TOTAL:.3f},afade=t=out:st={TOTAL - 2.5}:d=2.5,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{B}/edit_v.mp4", "-i", f"{B}/edit_vo.wav", "-i", f"{B}/music.wav", "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "exports/if-else-long-form.tmp.mp4"], check=True)
    os.replace("exports/if-else-long-form.tmp.mp4", "exports/if-else-long-form.mp4")
    # ---------------- captions, EDL, report
    subs = []
    for s in SECTIONS:
        if s["kind"] == "card": continue
        for a, b, text in M[s["id"]]["subs"]:
            oa = map_time(s["id"], a); ob = map_time(s["id"], b)
            if oa is not None: subs.append((oa, ob if ob else oa + (b - a), text))
    ts = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(x * 1000 % 1000):03d}"
    import textwrap; open("exports/if-else-long-form.srt", "w").write("\n".join(f"{k}\n{ts(a)} --> {ts(b)}\n{textwrap.fill(t, 42)}\n" for k, (a, b, t) in enumerate(sorted(subs), 1)))
    chapters = []
    for c in EDL:
        name = SEC[c["sec"]].get("chapter") if c["kind"] != "card" else f'{SEC[c["sec"]]["num"]}. {SEC[c["sec"]]["title"]}'
        if c["kind"] in ("card", "try") or c["sec"] in ("hook", "recap"):
            if not chapters or chapters[-1][1] != name: chapters.append((round(c["out"], 2), name if c["sec"] != "hook" else "Intro"))
    raw_head = sum(m["dur"] for m in M.values() if m["kind"] == "head"); kept_head = sum(c["b"] - c["a"] for c in EDL if c["kind"] == "head")
    stats = dict(total=TOTAL, clips=len(EDL), jump_cuts=sum(1 for c in EDL if c["kind"] == "head") - sum(1 for s in SECTIONS if s["kind"] == "head"),
                 raw_head=raw_head, kept_head=kept_head, retakes_removed=sum(len(m.get("retakes", [])) for m in M.values()),
                 transitions={t: sum(1 for c in EDL if c.get("trans") == t) for t in ("fade", "dip", "push")},
                 annotations=sum(len(s.get("ann", [])) for s in SECTIONS), zoom_moves=sum(len(s.get("zoom", [])) for s in SECTIONS) + sum(1 for c in EDL if c["kind"] == "head" and c["zoom"][0] > 1),
                 lufs=loudness("exports/if-else-long-form.mp4"), chapters=chapters)
    json.dump({"stats": stats, "edl": [{k: v for k, v in c.items() if k not in ("src", "wav")} | {"source": os.path.basename(c.get("src", c.get("wav", "generated")))} for c in EDL]}, open("results/edl.json", "w"), indent=1)
    print(json.dumps(stats, indent=1))
