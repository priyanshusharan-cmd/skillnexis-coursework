"""Dialogue sequence for J-cuts and L-cuts, plus 3 text animations (title, lower third, subtitles).

Two "cameras" (one per speaker) run for the whole conversation, like a real two-camera shoot: each shows its speaker,
whose ring pulses with their own voice. The edit decides which camera we see.
  dialogue_straight.mp4  video cuts exactly when the speaker changes (hard cuts)
  dialogue_jl.mp4        J-cuts (we hear the next speaker before we see them) and L-cuts (we stay on the listener's
                         reaction while the speaker finishes): the cuts film editors use to make conversation flow
    python src/dialogue.py
"""
import json, os, subprocess, textwrap, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
B, E, SR, FPS, W, H = "build", "exports", 22050, 30, 1920, 1080
F = "/usr/share/fonts/opentype/inter/"
LINES = [("Diya", "Kabir, did you pay me back for the Wi-Fi?"), ("Kabir", "I thought I did. Wasn't that last week?"),
         ("Diya", "That was the cab. The Wi-Fi was two hundred and sixty six."), ("Kabir", "Okay, okay. Let me just settle it on Hisaab right now."),
         ("Diya", "Thank you! See, that wasn't so awkward."), ("Kabir", "Says the person who reminded me three times.")]
VOICE = {"Diya": ("mb-us1", "60"), "Kabir": ("mb-us2", "42")}
LOOK = {"Diya": ((70, 22, 40), (232, 160, 166), "D"), "Kabir": ((11, 59, 55), (213, 245, 239), "K")}
TITLE = 3.0                                     # title card length before the conversation

def tts(text, who):
    v, p = VOICE[who]; f = f"{B}/_d.wav"
    subprocess.run(["espeak-ng", "-v", v, "-s", "150", "-p", p, "-w", f, text], check=True)
    with wave.open(f) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    if sr != SR: x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
    nz = np.where(np.abs(x) > 300)[0]; return x[nz[0]:nz[-1] + 1]

# ---------- audio: each line on its own track, natural 0.35 s gaps
clips, t, spans = [], TITLE, []
for who, text in LINES:
    a = tts(text, who); spans.append((who, t, t + len(a) / SR, text)); clips.append((t, a, who)); t += len(a) / SR + .35
TOTAL = t + 1.0
tracks = {w: np.zeros(int(TOTAL * SR)) for w in VOICE}
for st, a, who in clips: i = int(st * SR); tracks[who][i:i + len(a)] += a
mixd = sum(tracks.values()); mixd = mixd / np.abs(mixd).max() * .9
with wave.open(f"{B}/dialogue.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mixd * 32767).astype(np.int16).tobytes())

def rms(who, sec):
    i = int(sec * SR); seg = tracks[who][max(0, i - 700):i + 700]
    return float(np.sqrt(np.mean(seg ** 2))) / 6000 if len(seg) else 0

# ---------- the two cameras
big = ImageFont.truetype(F + "InterDisplay-ExtraBold.otf", 220)
def camera(who):
    bg, accent, letter = LOOK[who]; cx = 1180 if who == "Diya" else 740       # opposite sides: shot / reverse-shot (180° rule)
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", f"{B}/cam_{who}.mp4"], stdin=subprocess.PIPE)
    base = Image.new("RGB", (W, H), bg); d0 = ImageDraw.Draw(base)
    for r in range(900, 0, -60): d0.ellipse((cx - r, 520 - r, cx + r, 520 + r), fill=tuple(min(255, c + (900 - r) // 40) for c in bg))
    sm = 0
    for k in range(int(TOTAL * FPS)):
        sm = .6 * sm + .4 * min(1.0, rms(who, k / FPS)); im = base.copy(); d = ImageDraw.Draw(im)
        R = 230 + int(55 * sm)
        d.ellipse((cx - R, 520 - R, cx + R, 520 + R), outline=accent, width=10 + int(14 * sm))
        d.ellipse((cx - 210, 310, cx + 210, 730), fill=accent)
        d.text((cx, 520), letter, font=big, fill=bg, anchor="mm")
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
for who in VOICE:
    if not os.path.exists(f"{B}/cam_{who}.mp4"): camera(who)

# ---------- edit decision lists
def straight():
    cuts = [(0, spans[0][0])]
    for i in range(1, len(spans)): cuts.append(((spans[i - 1][2] + spans[i][1]) / 2, spans[i][0]))
    return cuts
def jl():
    # 1→2 J-cut (Kabir's voice starts over Diya's shot) · 2→3 straight · 3→4 L-cut (cut to Kabir listening while Diya
    # finishes) · 4→5 J-cut · 5→6 straight (the punchline lands on the speaker's face). No shot shorter than 1.5 s.
    cuts = [(0, spans[0][0])]; kinds = []
    for i, kind in zip(range(1, len(spans)), ["J", "cut", "L", "J", "cut"]):
        prev_end, nxt = spans[i - 1][2], spans[i][1]
        at = nxt + .7 if kind == "J" else (prev_end - .9 if kind == "L" else (prev_end + nxt) / 2)
        cuts.append((at, spans[i][0])); kinds.append((at, kind))
    return cuts, kinds

def edit(cuts, out, labels=()):
    segs = [(a, cuts[i + 1][0] if i + 1 < len(cuts) else TOTAL, w) for i, (a, w) in enumerate(cuts)]
    inputs = ["-i", f"{B}/cam_Diya.mp4", "-i", f"{B}/cam_Kabir.mp4", "-i", f"{B}/dialogue.wav"]; idx = {"Diya": 0, "Kabir": 1}
    fc = "".join(f"[{idx[w]}:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[s{k}];" for k, (a, b, w) in enumerate(segs))
    fc += "".join(f"[s{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0[v0];"
    fd = lambda a, b, f=.35: f"if(lt(t,{a}),0,if(lt(t,{a + f}),(t-{a})/{f},if(lt(t,{b - f}),1,if(lt(t,{b}),({b}-t)/{f},0))))"
    txt = []
    def tf(s, n): p = f"{B}/dlg_{n}.txt"; open(p, "w").write(s); return p
    # 1) animated title: scales up while fading in (over a dimmed frame)
    txt.append(f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.6:t=fill:enable='lt(t,{TITLE})'")
    txt.append(f"drawtext=fontfile={F}InterDisplay-ExtraBold.otf:textfile={tf('Room 214, 11:40 pm', 'title')}:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:"
               f"fontsize='60+40*min(1,t/0.8)':alpha='{fd(0.1, TITLE)}'")
    # 2) lower thirds: slide in from the left the first time each person appears
    seen = set(); n = 0
    for who, a, b, text in spans:
        if who in seen: continue
        seen.add(who); n += 1; s0, s1 = a - .2, a + 3.2
        x = f"'if(lt(t,{s0}+0.45),-700+760*(1-pow(1-(t-{s0})/0.45,3)),60)'"
        txt.append(f"drawbox=x='if(lt(t,{s0}+0.45),-720+780*(1-pow(1-(t-{s0})/0.45,3)),60)-20':y=740:w=520:h=130:color=white@0.92:t=fill:enable='between(t,{s0},{s1})'")
        txt.append(f"drawtext=fontfile={F}InterDisplay-Bold.otf:textfile={tf(who, f'n{n}')}:fontsize=52:fontcolor=0x101828:x={x}:y=755:enable='between(t,{s0},{s1})'")
        txt.append(f"drawtext=fontfile={F}Inter-Medium.otf:textfile={tf('Roommate, Room 214', f'r{n}')}:fontsize=30:fontcolor=0x5D6B82:x={x}:y=820:enable='between(t,{s0},{s1})'")
    # 3) subtitles: fade per line, bottom centre
    for k, (who, a, b, text) in enumerate(spans):
        txt.append(f"drawtext=fontfile={F}Inter-Medium.otf:textfile={tf(who + ': ' + text, f's{k}')}:fontsize=40:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=22:"
                   f"x=(w-text_w)/2:y=h-120:alpha='{fd(a, b + .3, .2)}':enable='between(t,{a},{b + .3})'")
    for at, kind in labels:
        if kind in "JL":
            txt.append(f"drawtext=fontfile={F}InterDisplay-Bold.otf:textfile={tf(kind + '-cut', f'l{at:.1f}')}:fontsize=40:fontcolor=0x101828:box=1:boxcolor=0xFEF0C7:boxborderw=16:x=w-text_w-60:y=60:enable='between(t,{at - .8},{at + 1.2})'")
    fc += "[v0]" + ",".join(txt) + ",format=yuv420p[v]"
    tmp = out[:-4] + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + inputs + ["-filter_complex", fc, "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", tmp], check=True); os.replace(tmp, out)
    return segs

s1 = edit(straight(), f"{E}/dialogue_straight.mp4")
_c, _k = jl(); _len = [(_c[i + 1][0] if i + 1 < len(_c) else TOTAL) - _c[i][0] for i in range(len(_c))]
assert min(_len) >= 1.5, f"shot too short: {min(_len):.2f}s"
cuts, kinds = jl(); s2 = edit(cuts, f"{E}/dialogue_jl.mp4", kinds)
json.dump({"spans": spans, "straight": s1, "jl": s2, "kinds": kinds, "total": TOTAL}, open(f"{B}/dialogue_edl.json", "w"), indent=1)

# ---------- timeline diagram (what an NLE timeline would show)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 1, figsize=(12, 4.2), sharex=True); col = {"Diya": "#E8A0A6", "Kabir": "#0F766E"}
for ax, segs, name in ((axes[0], s1, "Straight cuts"), (axes[1], s2, "J- and L-cuts")):
    for a, b, w in segs: ax.barh(1, b - a, left=a, color=col[w], edgecolor="white", height=.6)
    for w, a, b, _ in spans: ax.barh(0, b - a, left=a, color=col[w], alpha=.55, height=.6)
    ax.set_yticks([0, 1], ["A1 audio", "V1 video"]); ax.set_title(name, loc="left", fontsize=11)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
for at, k in kinds:
    if k in "JL": axes[1].annotate(f"{k}-cut", (at, 1.35), ha="center", fontsize=9, color="#7A4D00")
axes[1].set_xlabel("seconds"); handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in col.values()]
fig.legend(handles, col.keys(), loc="upper right", frameon=False); fig.tight_layout(); fig.savefig(f"{E}/dialogue-timeline.png", dpi=130)
print("dialogue", round(TOTAL, 1), "s; cuts:", kinds)
