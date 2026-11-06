"""Renders the 5-minute long-form video from src/script_a.py.
One encoded file per shot (1920x1080, 30 fps, x264 CRF 18), joined with the concat demuxer; audio = voice-over +
lo-fi bed ducked under the voice + the logo sting, loudness-normalised to -14 LUFS. Also writes the SRT captions and
the chapter list used in the YouTube description.
    python src/music.py 360 && python src/longform.py  -> exports/long-form.mp4, exports/long-form.srt, build/chapters.json"""
import json, os, subprocess, sys, textwrap, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__)); from script_a import SCENES, TITLE
B, E, SR = "build", "exports", 22050; W2, W3 = "../week-2/build/", "../week-3/exports/"
F = "/usr/share/fonts/opentype/inter/"; DB, DX, MD = F + "InterDisplay-ExtraBold.otf", F + "InterDisplay-Bold.otf", F + "Inter-Medium.otf"
ENC = ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30"]
END_SCREEN = 20.0                                   # YouTube end screens run in the last 5-20 s
n_txt = [0]
def tf(t): n_txt[0] += 1; p = f"{B}/lt_{n_txt[0]}.txt"; open(p, "w").write(t); return p
def fade(a, b, f=.3): return f"if(lt(t,{a}),0,if(lt(t,{a + f}),(t-{a})/{f},if(lt(t,{b - f}),1,if(lt(t,{b}),({b}-t)/{f},0))))"
def dt(text, font, size, color, x, y, a, b, box=None, bw=26):
    s = f"drawtext=fontfile={font}:textfile={tf(text)}:fontsize={size}:fontcolor={color}:x={x}:y={y}:alpha='{fade(a, b)}':enable='between(t,{a},{b})':line_spacing=12"
    return s + (f":box=1:boxcolor={box}:boxborderw={bw}" if box else "")
def run(args, out):
    tmp = out[:-4] + ".tmp.mp4"; subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + args + [tmp], check=True); os.replace(tmp, out)

# ---------------- voice-over per shot
def tts(text):
    p = f"{B}/_s.wav"; subprocess.run(["espeak-ng", "-v", "mb-us2", "-s", "138", "-p", "45", "-w", p, text], check=True)
    with wave.open(p) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    if sr != SR: x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
    nz = np.where(np.abs(x) > 300)[0]; return x[nz[0]:nz[-1] + 1]
shots = []
for si, (sid, chapter, shotlist, callouts) in enumerate(SCENES):
    for k, (kind, sents) in enumerate(shotlist):
        if kind[0] == "logo": shots.append(dict(sid=sid, chapter=chapter, kind=kind, dur=5.0, subs=[], first=k == 0)); continue
        parts, t, subs = [np.zeros(int(.3 * SR))], .3, []
        for s in sents:
            a = tts(s); d = len(a) / SR; subs.append((t, t + d, s)); parts += [a, np.zeros(int(.45 * SR))]; t += d + .45
        if sid == "outro": parts.append(np.zeros(int(END_SCREEN * SR)))
        x = np.concatenate(parts); x = x / max(1, np.abs(x).max()) * .9 * 32767; wp = f"{B}/vo_{sid}_{k}.wav"
        with wave.open(wp, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.astype(np.int16).tobytes())
        shots.append(dict(sid=sid, chapter=chapter, kind=kind, dur=len(x) / SR, subs=subs, wav=wp, first=k == 0, callouts=callouts if kind[0] == "rec" else []))
print("narration", round(sum(s["dur"] for s in shots), 1), "s")

# ---------------- shot renderers
BG = ["-f", "lavfi", "-i", "color=c=0x0B3B37:s=1920x1080:r=30"]
habit_no = {f"h{i}": i for i in range(1, 6)}
def host(s, out):
    """Presenter keyed from the week-3 green-screen plate, on the blurred café background; scene title on the right."""
    d = s["dur"]; label = s["chapter"]
    fc = ("[1:v]scale=2400:-2,crop=1920:1080,gblur=sigma=7,eq=brightness=-0.12:saturation=0.85[bg];"
          "[0:v]format=yuva420p,chromakey=0x2EB14A:0.10:0.02,despill=type=green:mix=0.6:expand=0.1[k];[bg][k]overlay=x=-430:y=0[v0];"
          "[v0]drawbox=x=1010:y=0:w=910:h=1080:color=0x0B3B37@0.82:t=fill")
    txt = []
    if s["sid"] in habit_no:
        txt += [dt(f"HABIT {habit_no[s['sid']]} OF 5", DX, 44, "0xFFD84D", 1090, 330, .2, d), dt(textwrap.fill(label.split(': ')[1], 16), DB, 92, "white", 1090, 410, .5, d)]
    elif s["sid"] == "outro":
        txt += [dt("Thanks for watching", DB, 84, "white", 1090, 140, .3, d)]
    else:
        txt += [dt(textwrap.fill({"hook": "Who paid for the Wi-Fi?", "promise": "5 habits that fixed it", "mistakes": "Same fix for all three"}[s["sid"]], 16), DB, 92, "white", 1090, 380, .4, d)]
    if s["first"] and s["sid"] in ("hook", "promise"):                     # lower third: who is talking
        txt += [f"drawbox=x='if(lt(t,0.9),-640+700*(1-pow(1-(t-0.5)/0.4,3)),60)':y=860:w=560:h=120:color=white@0.94:t=fill:enable='between(t,0.5,5.5)'",
                dt("Priyanshu", DX, 50, "0x101828", 90, 872, .7, 5.5), dt("Student · designer of Hisaab", MD, 28, "0x5D6B82", 90, 932, .7, 5.5)]
    if s["sid"] == "outro":                                               # end-screen placeholders for YouTube's end-screen elements
        a = d - END_SCREEN
        txt += [f"drawbox=x=1090:y=300:w=720:h=405:color=white@0.9:t=4:enable='gte(t,{a})'", dt("Next video:\nHow I designed Hisaab in 1 week", DX, 44, "white", 1120, 450, a + .3, d + 1),
                f"drawbox=x=1290:y=760:w=320:h=320:color=white@0.0:t=fill:enable='gte(t,{a})'", dt("  SUBSCRIBE  ", DB, 54, "white", 1265, 800, a + .5, d + 1, "0xD7263D", 30),
                dt("end-screen elements are placed here in YouTube Studio", MD, 26, "0x9FC9C2", 1090, 1010, a + .5, d + 1)]
    run(["-stream_loop", "-1", "-i", W3 + "greenscreen-raw.mp4", "-stream_loop", "-1", "-i", W2 + "fix_coffee.mp4", "-filter_complex", fc + "," + ",".join(txt) + f",fade=t=in:d=0.2,fade=t=out:st={d - .2}:d=0.2,format=yuv420p[v]",
         "-map", "[v]", "-t", f"{d:.3f}", "-an"] + ENC, out)
def rec(s, out):
    """Prototype screen recording; holds its last frame if the narration runs longer; call-outs in the right column."""
    d = s["dur"]; name, start = s["kind"][1], s["kind"][2]; txt = ["fps=30", f"tpad=stop_mode=clone:stop_duration={d}"]
    for text, a, b in s["callouts"]:
        b = min(b, d - .2); x = f"'if(lt(t,{a}+0.4), 1100 + (w-1100)*pow(1-(t-{a})/0.4,3), 1100)'"
        txt.append(dt(text, DX, 58, "0x0B3B37", x, 300 if text.startswith("Habit") else 470, a, b, "0xD5F5EF"))
    txt.append(dt(f"{habit_no[s['sid']]} / 5", DX, 34, "0xD5F5EF", 1760, 60, 0, d, "0x0F766E", 16))
    run(["-ss", f"{start}", "-i", f"{W2}rec_{name}.webm", "-vf", ",".join(txt) + f",fade=t=in:d=0.2,fade=t=out:st={d - .2}:d=0.2,format=yuv420p", "-t", f"{d:.3f}", "-an"] + ENC, out)
def card(s, out):
    d = s["dur"]; title, lines = s["kind"][1], s["kind"][2]; step = min(1.6, (d - 2) / max(1, len(lines)))
    txt = [dt(title, DB, 110, "white", 140, 150, .2, d)] + [dt(l, DX, 64, "0xFFD84D" if l[0].isdigit() or l[0] == "₹" else "0xD5F5EF", 160, 360 + 110 * i, 1 + step * i, d) for i, l in enumerate(lines)]
    run(BG + ["-vf", ",".join(txt) + f",fade=t=in:d=0.2,fade=t=out:st={d - .2}:d=0.2,format=yuv420p", "-t", f"{d:.3f}"] + ENC, out)
def chart(s, out):
    """Animated horizontal bars: a sample month (the prototype's insight numbers), bars grow with an ease-out."""
    d = s["dur"]; data = [("Food & chai", 2340, (232, 160, 166)), ("Travel", 1480, (96, 165, 250)), ("Room & bills", 920, (94, 234, 212)), ("Other", 360, (167, 139, 250))]
    fb, fm, fs = ImageFont.truetype(DB, 96), ImageFont.truetype(DX, 52), ImageFont.truetype(MD, 34); tot = sum(v for _, v, _ in data)
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", "30", "-i", "-"] + ENC + [out[:-4] + ".tmp.mp4"], stdin=subprocess.PIPE)
    for i in range(int(round(d * 30))):
        t = i / 30; im = Image.new("RGB", (1920, 1080), (11, 59, 55)); dr = ImageDraw.Draw(im)
        dr.text((140, 110), "Where ₹5,100 went in October", font=fb, fill="white"); dr.text((144, 230), "Sample month for one student (prototype data)", font=fs, fill=(159, 201, 194))
        for k, (lab, v, col) in enumerate(data):
            u = min(1, max(0, (t - .8 - .35 * k) / .9)); u = 1 - (1 - u) ** 3; y = 360 + 150 * k
            dr.text((140, y + 18), lab, font=fm, fill="white"); w = int(1000 * v / data[0][1] * u)
            dr.rounded_rectangle((560, y, 560 + max(w, 1), y + 90), radius=16, fill=col)
            if u > .05: dr.text((580 + w, y + 18), f"₹{int(v * u):,}  ·  {round(100 * v / tot * u)}%", font=fm, fill="white")
        a = min(1, max(0, (t - .2) / .2)); fr = np.asarray(im, np.float32) * a + np.array([11, 59, 55]) * (1 - a)
        p.stdin.write(fr.astype(np.uint8).tobytes())
    p.stdin.close(); p.wait(); os.replace(out[:-4] + ".tmp.mp4", out)
def logo(s, out): run(["-i", W3 + "logo-reveal.mp4", "-an", "-vf", "format=yuv420p"] + ENC, out)
R = {"host": host, "rec": rec, "card": card, "chart": chart, "logo": logo}
files, t0, chapters, srt = [], 0.0, [], []
for i, s in enumerate(shots):
    out = f"{B}/shot_{i:02d}_{s['sid']}.mp4"
    if s["first"]: chapters.append((round(t0, 2), s["chapter"]))
    for a, b, text in s["subs"]: srt.append((t0 + a, t0 + b, text))
    if not os.path.exists(out) or "--force" in sys.argv: R[s["kind"][0]](s, out)
    s["start"] = t0; files.append(out); t0 += s["dur"]
TOTAL = t0; open(f"{B}/list.txt", "w").write("".join(f"file '{os.path.basename(f)}'\n" for f in files))
run(["-f", "concat", "-safe", "0", "-i", f"{B}/list.txt", "-c", "copy"], f"{B}/video.mp4")
# ---------------- audio
vo = np.zeros(int((TOTAL + 1) * SR))
for s in shots:
    if "wav" in s:
        with wave.open(s["wav"]) as w: x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        i = int(round(s["start"] * SR)); vo[i:i + len(x)] += x[:len(vo) - i]
with wave.open(f"{B}/vo_full.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.clip(vo, -32767, 32767).astype(np.int16).tobytes())
logo_at = next(s["start"] for s in shots if s["kind"][0] == "logo"); ms = int(logo_at * 1000)
fc = (f"[1:a]aresample=44100,aformat=channel_layouts=stereo,asplit=2[v1][v2];[2:a]volume=0.5[m];[m][v1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];"
      f"[3:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume=1.4[logo];"
      f"[duck][v2][logo]amix=inputs=3:duration=first:normalize=0:weights='0.8 1.6 1',atrim=0:{TOTAL:.3f},afade=t=out:st={TOTAL - 3}:d=3,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
run(["-i", f"{B}/video.mp4", "-i", f"{B}/vo_full.wav", "-i", f"{B}/music.wav", "-i", W3 + "logo-reveal.mp4", "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"], f"{E}/long-form.mp4")
def ts(x): return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(x * 1000 % 1000):03d}"
open(f"{E}/long-form.srt", "w").write("\n".join(f"{k}\n{ts(a)} --> {ts(b)}\n{textwrap.fill(t, 46)}\n" for k, (a, b, t) in enumerate(srt, 1)))
json.dump({"title": TITLE, "total": TOTAL, "chapters": chapters, "shots": [{k: v for k, v in s.items() if k not in ("subs",)} for s in shots]}, open(f"{B}/chapters.json", "w"), indent=1, default=str)
print("long-form", round(TOTAL, 1), "s;", len(shots), "shots;", [(f"{int(a // 60)}:{int(a % 60):02d}", c) for a, c in chapters])
