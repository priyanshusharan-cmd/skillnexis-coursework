"""3 short-form clips (30-60 s, 1080x1920) cut from the finished long-form, reframed for vertical:
presenter shots cropped to the presenter, screen shots cropped to the code and terminal, captions burned in word by
word (most short-form viewing is muted), a hook title in the first seconds, and the long-form's own audio.
Uses the vertical compositor from video-editing/week-3.   python src/shorts.py  -> exports/short-*.mp4"""
import json, os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, "src"); sys.path.insert(0, "../../video-editing/week-3/src")
import edit as LF                                    # EDL and time mapping of the long-form
import vertical as V
V.CAP_Y = 1440                                       # captions below the reframed content
LONG = "exports/if-else-long-form.mp4"; B = "build"; os.makedirs(B, exist_ok=True)
if not os.path.exists(f"{B}/beat.wav"): subprocess.run(["cp", "../../video-editing/week-3/build/beat.wav", f"{B}/beat.wav"], check=True)
CROP = {"head": ("crop=1000:1080:830:0,scale=1080:1166", 140, "0x14213D"), "screen": ("crop=1100:990:400:90,scale=1080:972", 300, "0x1E1E2E"),
        "card": ("crop=1500:1080:100:0,scale=1080:778", 340, "0xFFF8EE"), "try": ("crop=1700:1080:100:0,scale=1080:686", 380, "0xFFF8EE")}
def sec_span(sec):
    cs = [c for c in LF.EDL if c["sec"] == sec]; return cs[0]["out"], cs[-1]["out"] + cs[-1]["b"] - cs[-1]["a"]
def sub_out(sec, idx, end=False):
    a, b, _ = LF.M[sec]["subs"][idx]; return LF.map_time(sec, b if end else a)
SHORTS = {
 "short-1-equals-vs-double-equals": dict(start=sec_span("c4")[0], end=sec_span("eq")[1], hook="= vs == : the #1 if mistake", cover="cover-equals.png",
     stickers=[("one = stores", .78), ("two == compare", .86)]),
 "short-2-elif-order-matters": dict(start=sec_span("c3")[0], end=sec_span("elif")[1], hook="Why 95 marks gave a C", cover="cover-elif.png", stickers=[("strictest check first", .9)]),
 "short-3-indentation-error": dict(start=sec_span("demo")[0], end=sec_span("indent")[1], hook="if / else + the 4 spaces Python needs", cover="cover-indent.png", stickers=[("indent = belongs to the if", .75)]),
}
def build_base(name, start, end):
    """Vertical base video: every long-form clip in the range reframed with the crop for its shot type."""
    parts, k = [], 0
    for c in LF.EDL:
        c0, c1 = c["out"], c["out"] + c["b"] - c["a"]; a, b = max(start, c0), min(end, c1)
        if b - a < 1 / 30: continue
        vf, y, bg = CROP[c["kind"]]; out = f"{B}/{name}_p{k:02d}.mp4"; k += 1
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", LONG, "-vf", f"{vf},pad=1080:1920:0:{y}:color={bg},fps=30,format=yuv420p",
                        "-an", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", out], check=True); parts.append(out)
    open(f"{B}/{name}_list.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{B}/{name}_list.txt", "-c", "copy", f"{B}/{name}_base.mp4"], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", LONG, "-ac", "1", "-ar", "44100", f"{B}/{name}_a.wav"], check=True)
    with wave.open(f"{B}/{name}_a.wav") as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
def words_in(start, end):
    """Caption words from the long-form's sentence timings (word times weighted by length inside each sentence)."""
    out = []
    for s in LF.SECTIONS:
        if s["kind"] == "card": continue
        for a, b, text in LF.M[s["id"]]["subs"]:
            oa, ob = LF.map_time(s["id"], a), LF.map_time(s["id"], b)
            if oa is None or ob is None or oa < start - .05 or ob > end + .3: continue
            ws = text.split(); wt = np.array([len(w.strip(".,!?")) + 2.5 for w in ws]); e = np.concatenate([[0], np.cumsum(wt)]) / wt.sum() * (ob - oa)
            out += [(oa - start + e[i], oa - start + e[i + 1], w) for i, w in enumerate(ws)]
    return out
report = {}
for name, s in SHORTS.items():
    dur = s["end"] - s["start"]; assert 30 <= dur <= 60, f"{name}: {dur:.1f} s is outside 30-60 s"
    aud = build_base(name, s["start"], s["end"])
    clip = dict(src=f"{B}/{name}_base.mp4", a=0, b=dur, dur=dur, vf="null", texts=[(f * dur, f * dur + 3.0, t, 1620) for t, f in s["stickers"]])
    V.render(name, [clip], dur, captions=words_in(s["start"], s["end"]), vo=[(0, dur, "", aud)], hook=(s["hook"], 2.6), music_offset=8.0, music_gain=0.0)
    report[name] = dict(source_range=[round(s["start"], 2), round(s["end"], 2)], duration=round(dur, 1), cover=s["cover"])
    print(name, round(dur, 1), "s", flush=True)
json.dump(report, open("results/shorts.json", "w"), indent=1)
