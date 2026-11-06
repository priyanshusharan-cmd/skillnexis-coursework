"""Small vertical-video compositor (1080x1920, 30 fps) used for the Reel and the three Shorts.
Everything an NLE does for short-form, written out so each effect is explicit:
  * speed ramps: a time-remap curve per clip (relative speeds, smoothly interpolated, scaled so the chosen source range
    exactly fills the clip; fast through idle moments, slow-motion on the payoff)
  * zoom keyframes (punch-ins / slow push), eased
  * transitions: whip pan (motion-blurred slide), zoom punch + flash, RGB-split glitch, white flash
  * word-by-word captions (current word highlighted), hook titles, stickers, all inside the Reels/Shorts safe zone
  * audio: voice-over, original beat (ducked under the voice), whoosh SFX on every transition, -14 LUFS
"""
import json, math, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS, SR = 1080, 1920, 30, 44100
F = "/usr/share/fonts/opentype/inter/"; W2 = "../week-2/build/"
FONT = lambda name, size: ImageFont.truetype(F + name, size)
CAP = FONT("InterDisplay-ExtraBold.otf", 88); HOOK = FONT("InterDisplay-ExtraBold.otf", 96); TAG = FONT("InterDisplay-Bold.otf", 54); SMALL = FONT("Inter-SemiBold.otf", 36)
BRAND, MINT, YELLOW, PINK = (11, 59, 55), (213, 245, 239), (255, 216, 77), (232, 160, 166)
SAFE = (80, 260, 920, 1480)          # x0, y0, x1, y1 kept clear of the platform UI (top bar, caption/buttons at bottom and right)
CAP_Y = 1230                        # caption centre line (other projects can move it)
GS = "exports/greenscreen-raw.mp4"   # the keyed green-screen plate (week 4 points this at week 3's copy)
PHONE = "crop=552:982:404:49,scale=1080:1920:flags=lanczos"     # the phone in the 1920x1080 prototype recordings
smooth = lambda u: u * u * (3 - 2 * u)
ease_out = lambda u: 1 - (1 - u) ** 3

class Reader:
    """Sequential frame reader; get(src_t) returns the frame at a (monotonically increasing) source time."""
    def __init__(self, path, start, vf, loop=False, extra_in=(), fc=None):
        self.start, self.i, self.cur = start, -1, None
        args = ["ffmpeg", "-loglevel", "error", "-ss", f"{start:.3f}"] + (["-stream_loop", "-1"] if loop else []) + ["-i", path, *extra_in]
        args += ["-filter_complex", fc, "-map", "[o]"] if fc else ["-vf", f"{vf},fps={FPS}"]
        self.p = subprocess.Popen(args + ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    def get(self, src_t):
        want = max(0, int(round((src_t - self.start) * FPS)))
        while self.i < want:
            buf = self.p.stdout.read(W * H * 3)
            if len(buf) < W * H * 3: break                  # end of source: hold the last frame
            self.cur = Image.frombuffer("RGB", (W, H), buf); self.i += 1
        return self.cur.copy()
    def close(self): self.p.kill()

def interp(keys, u, f=smooth):
    """keys: [(rel_t, value...)] -> eased interpolation at rel time u."""
    if u <= keys[0][0]: return keys[0][1:]
    for a, b in zip(keys, keys[1:]):
        if a[0] <= u <= b[0]:
            k = f((u - a[0]) / max(1e-6, b[0] - a[0])); return tuple(x + (y - x) * k for x, y in zip(a[1:], b[1:]))
    return keys[-1][1:]

def remap(clip, n):
    """Source time for each of the clip's n output frames: integrate the (relative) speed curve, then scale so the
    clip uses exactly the source range [a, b]. Returns times and the actual speeds for the README table."""
    ramp = clip.get("ramp", [(0, 1), (1, 1)])
    v = np.array([interp(ramp, (k + .5) / n)[0] for k in range(n)]); cum = np.concatenate([[0], np.cumsum(v)])[:-1]
    scale = (clip["b"] - clip["a"]) / v.sum(); return clip["a"] + cum * scale, v * scale * FPS            # speed = source seconds per output second

def zoom(im, z, cx, cy):
    if abs(z - 1) < 1e-3 and abs(cx - .5) < 1e-3 and abs(cy - .5) < 1e-3: return im
    w, h = W / z, H / z; x0 = min(max(0, cx * W - w / 2), W - w); y0 = min(max(0, cy * H - h / 2), H - h)
    return im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))

def hblur(im, k):
    """Horizontal motion blur by squashing and stretching (cheap and directional)."""
    return im if k < 2 else im.resize((max(8, int(W / k)), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)

def transition(kind, prev, cur, u):
    if kind == "whip":
        e = smooth(u); out = Image.new("RGB", (W, H)); out.paste(prev, (int(-e * W), 0)); out.paste(cur, (int((1 - e) * W), 0))
        return hblur(out, 1 + 40 * math.sin(math.pi * u))
    if kind == "punch":
        im = zoom(cur, 1 + .35 * (1 - ease_out(u)), .5, .5)
        return Image.blend(im, Image.new("RGB", (W, H), "white"), max(0, .7 * (1 - u * 3))) if u < .34 else im
    if kind == "glitch":
        a = np.asarray(cur if u > .25 else prev).copy(); s = int(40 * (1 - u)); rng = np.random.default_rng(int(u * 1000))
        a[..., 0] = np.roll(a[..., 0], s, 1); a[..., 2] = np.roll(a[..., 2], -s, 1)
        for _ in range(int(8 * (1 - u))):
            y = rng.integers(0, H - 80); hgt = rng.integers(20, 80); a[y:y + hgt] = np.roll(a[y:y + hgt], rng.integers(-120, 120), 1)
        return Image.fromarray(a)
    if kind == "flash":
        return Image.blend(prev if u < .5 else cur, Image.new("RGB", (W, H), "white"), 1 - abs(u - .5) * 2)
    return cur

def text_img(words, font, hi=None, fill=(255, 255, 255), hi_fill=YELLOW, stroke=8):
    """One line of words; word index `hi` drawn in the highlight colour."""
    sp = font.getlength(" "); ws = [font.getlength(w) for w in words]; tw = int(sum(ws) + sp * (len(words) - 1)) + 2 * stroke + 4
    asc, desc = font.getmetrics(); im = Image.new("RGBA", (tw, asc + desc + 2 * stroke), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = stroke
    for k, (w, wl) in enumerate(zip(words, ws)):
        d.text((x, stroke), w, font=font, fill=hi_fill if k == hi else fill, stroke_width=stroke, stroke_fill=(0, 0, 0)); x += wl + sp
    return im

def paste_center(frame, im, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    frame.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

def hook_img(text):
    """Hook title on a solid yellow block (reads on any footage)."""
    lines = wrap_lines(text, HOOK, 820); lh = 116; w = int(max(HOOK.getlength(" ".join(l)) for l in lines)) + 80
    im = Image.new("RGBA", (w, lh * len(lines) + 50), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.rounded_rectangle((0, 0, w - 1, im.height - 1), radius=34, fill=YELLOW)
    for k, l in enumerate(lines): d.text((w / 2, 25 + lh * k + lh / 2), " ".join(l), font=HOOK, fill=(16, 24, 40), anchor="mm")
    return im

def wrap_lines(text, font, maxw):
    lines, cur = [], []
    for w in text.split():
        if cur and font.getlength(" ".join(cur + [w])) > maxw: lines.append(cur); cur = []
        cur.append(w)
    return lines + [cur]

def sticker(frame, text, cx, cy, age, bg=YELLOW, fg=(16, 24, 40), font=TAG):
    """Rounded label that pops in with an overshoot over its first 0.25 s."""
    tw = int(font.getlength(text)); im = Image.new("RGBA", (tw + 64, 96), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw + 63, 95), radius=26, fill=bg); d.text(((tw + 64) / 2, 48), text, font=font, fill=fg, anchor="mm")
    q = min(1, age / .25); s = 1 + 2.7 * (q - 1) ** 3 + 1.7 * (q - 1) ** 2; paste_center(frame, im, cx, cy, max(.05, s))

# ---------------------------------------------------------------- voice-over and word timings
def tts(text, voice="mb-us1", speed=150, pitch=55):
    subprocess.run(["espeak-ng", "-v", voice, "-s", str(speed), "-p", str(pitch), "-w", "build/_t.wav", text], check=True)
    with wave.open("build/_t.wav") as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x); nz = np.where(np.abs(x) > 300)[0]; return x[nz[0]:nz[-1] + 1]

def voiceover(lines, gap=.35, lead=.25, **kw):
    """Speaks each line, places them back to back; word times are estimated by weighting each word's length inside its
    line's measured audio span (espeak does not export word timings), good enough for 2-3 word caption chunks."""
    t, segs, words = lead, [], []
    for text in lines:
        a = tts(text, **kw); d = len(a) / SR; segs.append((t, t + d, text, a))
        ws = text.split(); wt = np.array([len(w.strip(".,!?")) + 2.5 for w in ws]); edges = np.concatenate([[0], np.cumsum(wt)]) / wt.sum() * d
        words += [(t + edges[k], t + edges[k + 1], w) for k, w in enumerate(ws)]; t += d + gap
    return segs, words, t

def chunks(words, maxw=3, maxc=15):
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or len(" ".join(x[2] for x in cur + [w])) > maxc or cur[-1][2][-1] in ".,!?"): out.append(cur); cur = []
        cur.append(w)
    return out + [cur] if cur else out

# ---------------------------------------------------------------- render
def render(name, clips, total, captions=None, vo=None, music_offset=8.0, music_gain=.5, hook=None, end_pad=0):
    """clips: list of dicts {src|card, a, b, dur, ramp, zoom, trans, tdur, texts}. Writes exports/<name>.mp4."""
    n_total = int(round(total * FPS)); starts = np.cumsum([0] + [c["dur"] for c in clips]); edl = []
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                          "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", f"build/{name}_v.mp4"], stdin=subprocess.PIPE)
    caps = chunks(captions) if captions else []; prev_last = Image.new("RGB", (W, H), BRAND); f = 0; sfx_at = []
    for ci, c in enumerate(clips):
        n = int(round(starts[ci + 1] * FPS)) - int(round(starts[ci] * FPS)); rdr = None
        if "src" in c:
            if c["src"].startswith("rec_"): rdr = Reader(W2 + c["src"] + ".webm", max(0, c["a"] - .05), PHONE)
            elif c["src"] == "gs": rdr = Reader(GS, 0, None, loop=True, extra_in=["-f", "lavfi", "-i", f"color=c=0x{BRAND[0]:02X}{BRAND[1]:02X}{BRAND[2]:02X}:s=1920x1080:r=30"],
                                               fc="[0:v]format=yuva420p,chromakey=0x2EB14A:0.10:0.02,despill=type=green:mix=0.6:expand=0.1[k];[1:v][k]overlay=shortest=1,crop=760:1080:520:0,scale=1080:1535,pad=1080:1920:0:385:color=0x0B3B37,fps=30[o]")
            else: rdr = Reader(c["src"], max(0, c["a"] - .05), c.get("vf", "scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x0B3B37"))
            times, speeds = remap(c, n) if c["src"] != "gs" else (np.arange(n) / FPS, np.ones(n))
            edl.append({"clip": ci, "src": c["src"], "out_start": round(float(starts[ci]), 2), "out_dur": round(c["dur"], 2), "src_range": [c.get("a", 0), c.get("b", c["dur"])],
                        "speed_min": round(float(speeds.min()), 2), "speed_max": round(float(speeds.max()), 2), "transition_in": c.get("trans")})
        else: edl.append({"clip": ci, "src": "card", "out_start": round(float(starts[ci]), 2), "out_dur": round(c["dur"], 2), "transition_in": c.get("trans")})
        if c.get("trans") and ci: sfx_at.append((float(starts[ci]), c["trans"]))
        for k in range(n):
            u = (k + .5) / n; tl = k / FPS; tg = f / FPS
            if rdr: im = rdr.get(times[k])
            else: im = Image.new("RGB", (W, H), c.get("bg", BRAND)); c["card"](im, tl, c["dur"])
            if "zoom" in c: im = zoom(im, *interp(c["zoom"], u))
            td = c.get("tdur", .3)
            if c.get("trans") and ci and tl < td: im = transition(c["trans"], prev_last, im, tl / td)
            for (a, b, text, *style) in c.get("texts", []):          # stickers, in clip-relative seconds
                if a <= tl < b: sticker(im, text, W / 2 + (style[1] if len(style) > 1 else 0), style[0] if style else 420, tl - a)
            if hook and tg < hook[1]:                                  # hook title: top of the safe zone, pops in, fades out
                a = min(1, (hook[1] - tg) / .25); paste_center(im, hook_img(hook[0]), W / 2, 420, 1 + .25 * (1 - ease_out(min(1, tg / .3))), a)
            for ch in caps:                                            # word-by-word captions
                if ch[0][0] - .05 <= tg < ch[-1][1] + .12:
                    hi = max([i for i, w in enumerate(ch) if w[0] <= tg] or [0]); age = tg - ch[0][0]
                    paste_center(im, text_img([w[2] for w in ch], CAP, hi), W / 2, CAP_Y, .86 + .14 * ease_out(min(1, max(0, age) / .1))); break
            p.stdin.write(im.tobytes()); f += 1
        prev_last = im
        if rdr: rdr.close()
    p.stdin.close(); p.wait()
    # ---- audio: whooshes on transitions, VO, ducked beat, loudness normalised
    sfx = np.zeros(int((total + 1) * SR)); rng = np.random.default_rng(5)
    for t0, kind in sfx_at:
        d = .35 if kind != "glitch" else .2; nn = int(d * SR); env = np.sin(np.pi * np.arange(nn) / nn) ** 2; noise = rng.normal(0, 1, nn)
        if kind == "glitch": noise = np.sign(np.sin(np.arange(nn) * 2 * np.pi * 220 / SR)) * (rng.random(nn) > .5)
        else: noise = np.convolve(noise, np.ones(6) / 6, "same")
        i = int(max(0, t0 - d / 2) * SR); sfx[i:i + nn] += noise[:len(sfx) - i] * env[:len(sfx) - i] * .25
    voc = np.zeros(int((total + 1) * SR))
    for (a, b, text, aud) in (vo or []): i = int(a * SR); voc[i:i + len(aud)] += aud[:len(voc) - i] / 32768 * .9
    for arr, nm in ((sfx, "sfx"), (voc, "vo")):
        with wave.open(f"build/{name}_{nm}.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(arr, -1, 1) * 32767).astype(np.int16).tobytes())
    fc = (f"[1:a]atrim={music_offset}:{music_offset + total},asetpts=PTS-STARTPTS,volume={music_gain},afade=t=out:st={total - 1.2}:d=1.2[m];"
          f"[2:a]aformat=channel_layouts=stereo,asplit=2[v1][v2];[m][v1]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=300[duck];"
          f"[3:a]aformat=channel_layouts=stereo[s];[duck][v2][s]amix=inputs=3:duration=first:normalize=0:weights='1 1.5 1',atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    tmp = f"exports/{name}.tmp.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"build/{name}_v.mp4", "-i", "build/beat.wav", "-i", f"build/{name}_vo.wav", "-i", f"build/{name}_sfx.wav", "-filter_complex", fc,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, f"exports/{name}.mp4"); return edl
