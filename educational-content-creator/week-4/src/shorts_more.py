"""Shorts 4 and 5 (the brief asks for 5; shorts 1-3 come from week 3's lesson 2). Cut from week 2's finished videos and
reframed for 9:16 with the same vertical compositor: slides cropped to the slide content, screen shots cropped to the
code and terminal, word-by-word captions from the videos' own .srt timings, a hook title, the original audio.
    python src/shorts_more.py  -> exports/short-4-*.mp4, exports/short-5-*.mp4, results/shorts-4-5.json"""
import json, os, re, subprocess, sys, wave
import numpy as np
from PIL import Image
sys.path.insert(0, "../../video-editing/week-3/src")
import vertical as V
V.CAP_Y = 1440
W2 = "../week-2/exports/"; B = "build"
CROP = {"slide": ("crop=1800:1080:100:0,scale=1080:648", 400, "0xFFF8EE"), "screen": ("crop=1100:990:380:90,scale=1080:972", 300, "0x1E1E2E")}
SHORTS = {
 "short-4-why-5-plus-2-is-52": dict(src=W2 + "lesson-variables-1080p.mp4", srt=W2 + "lesson-variables.srt", start=142.68, end=200.63,
     hook='Why "5" + "2" = "52" in Python', stickers=[("the type decides what + does", .12), ('int("5") fixes it', .9)]),
 "short-5-read-errors-bottom-up": dict(src=W2 + "screen-tutorial.mp4", srt=W2 + "screen-tutorial.srt", start=18.12, end=63.0,
     hook="Read Python errors from the BOTTOM", stickers=[("last line = what went wrong", .42), ("one line up = where", .62)]),
}
def srt(path):
    out = []
    for blk in open(path).read().strip().split("\n\n"):
        L = blk.splitlines(); m = re.findall(r"(\d+):(\d+):(\d+),(\d+)", L[1])
        a, b = [int(h) * 3600 + int(mi) * 60 + int(s) + int(ms) / 1000 for h, mi, s, ms in m]; out.append((a, b, " ".join(L[2:])))
    return out
def kind_at(src, t):
    """Shot type from the frame itself: the slides have a cream background, the editor is dark."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-vf", "crop=200:60:860:980", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return "slide" if np.frombuffer(raw, np.uint8).mean() > 160 else "screen"
def segments(src, start, end, step=.2):
    ts = np.arange(start, end, step); ks = [kind_at(src, t) for t in ts]; segs = []
    for t, k in zip(ts, ks):
        if segs and segs[-1][2] == k: segs[-1][1] = min(end, t + step)
        else: segs.append([t, min(end, t + step), k])
    segs[-1][1] = end; return segs
def build_base(name, s):
    parts = []
    for i, (a, b, k) in enumerate(segments(s["src"], s["start"], s["end"])):
        vf, y, bg = CROP[k]; out = f"{B}/{name}_p{i:02d}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", s["src"], "-vf", f"{vf},pad=1080:1920:0:{y}:color={bg},fps=30,format=yuv420p",
                        "-an", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", out], check=True); parts.append((out, k, round(b - a, 1)))
    open(f"{B}/{name}_list.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p, _, _ in parts))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{B}/{name}_list.txt", "-c", "copy", f"{B}/{name}_base.mp4"], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{s['start']:.3f}", "-t", f"{s['end'] - s['start']:.3f}", "-i", s["src"], "-ac", "1", "-ar", "44100", f"{B}/{name}_a.wav"], check=True)
    with wave.open(f"{B}/{name}_a.wav") as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32), parts
def words(s):
    out = []
    for a, b, text in srt(s["srt"]):
        if a < s["start"] - .05 or b > s["end"] + .3: continue
        ws = text.split(); wt = np.array([len(w.strip(".,!?")) + 2.5 for w in ws]); e = np.concatenate([[0], np.cumsum(wt)]) / wt.sum() * (b - a)
        out += [(a - s["start"] + e[i], a - s["start"] + e[i + 1], w) for i, w in enumerate(ws)]
    return out
report = json.load(open("results/shorts-4-5.json")) if os.path.exists("results/shorts-4-5.json") else {}
for name, s in SHORTS.items():
    if len(sys.argv) > 1 and not any(a in name for a in sys.argv[1:]): continue
    dur = s["end"] - s["start"]; assert 30 <= dur <= 60, (name, dur)
    aud, parts = build_base(name, s)
    clip = dict(src=f"{B}/{name}_base.mp4", a=0, b=dur, dur=dur, vf="null", texts=[(f * dur, f * dur + 3.0, t, 1620) for t, f in s["stickers"]])
    V.render(name, [clip], dur, captions=words(s), vo=[(0, dur, "", aud)], hook=(s["hook"], 2.6), music_offset=8.0, music_gain=0.0)
    report[name] = dict(source=os.path.basename(s["src"]), source_range=[s["start"], s["end"]], duration=round(dur, 1), shots=[(k, d) for _, k, d in parts])
    print(name, round(dur, 1), "s", flush=True)
json.dump(report, open("results/shorts-4-5.json", "w"), indent=1)
