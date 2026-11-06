"""Renders the 3-minute tutorial "Split hostel expenses in 3 minutes (and settle with UPI)".
One encoded file per scene (1920x1080, 30 fps, x264 CRF 18), joined with the concat demuxer, then the audio mix:
voiceover + original music ducked under the voice (sidechain compression), loudness-normalised to -14 LUFS.
    python src/render.py    -> exports/tutorial.mp4, exports/tutorial.srt
"""
import json, os, subprocess, sys, textwrap
sys.path.insert(0, os.path.dirname(__file__)); from script import SCENES
B, E = "build", "exports"; os.makedirs(E, exist_ok=True)
T = json.load(open(f"{B}/timing.json")); OFF = json.load(open(f"{B}/rec_offsets.json"))
F = "/usr/share/fonts/opentype/inter/"; DB, DX, SB, MD = F + "InterDisplay-ExtraBold.otf", F + "InterDisplay-Bold.otf", F + "Inter-SemiBold.otf", F + "Inter-Medium.otf"
ENC = ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30"]
n_txt = [0]

def tf(text):
    n_txt[0] += 1; p = f"{B}/txt_{n_txt[0]}.txt"; open(p, "w").write(text); return p

def fade(a, b, f=.3):
    return f"if(lt(t,{a}),0,if(lt(t,{a + f}),(t-{a})/{f},if(lt(t,{b - f}),1,if(lt(t,{b}),({b}-t)/{f},0))))"

def dt(text, font, size, color, x, y, a, b, box=None, extra=""):
    s = f"drawtext=fontfile={font}:textfile={tf(text)}:fontsize={size}:fontcolor={color}:x={x}:y={y}:alpha='{fade(a, b)}':enable='between(t,{a},{b})':line_spacing=10"
    if box: s += f":box=1:boxcolor={box}:boxborderw=28"
    return s + extra

SCREEN = {"onboard", "home", "add", "saved", "settle", "extras"}

def subs(sid, dur, start_shift=0.0):
    """Captions: centred at the bottom on full-frame scenes; in the right-hand column on screen recordings (never over the phone)."""
    out = []
    for a, b, text in T[sid]["subs"]:
        if sid in SCREEN:
            lines = textwrap.wrap(text, 40); x, y = "1100", f"{560}"
        else:
            lines = textwrap.wrap(text, 58); x, y = "(w-text_w)/2", f"h-{80 + 48 * len(lines)}"
        out.append(dt("\n".join(lines), MD, 38, "white", x, y, a + start_shift, min(dur, b + .25), "black@0.55"))
    return out

def callouts(sid, dur):
    out = []
    for text, a, b in next(s[2] for s in SCENES if s[0] == sid):
        b = min(b, dur - .2)
        # slides in from the right edge: x eases from w to its final position over 0.4 s
        x = f"'if(lt(t,{a}+0.4), 1100 + (w-1100)*pow(1-(t-{a})/0.4,3), 1100)'"
        out.append(dt(text, DX, 54, "0x0B3B37", x, 300 if sid in SCREEN else 640, a, b, "0xD5F5EF"))
    return out

def run(args, out):
    tmp = out[:-4] + ".tmp.mp4"; subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + args + [tmp], check=True); os.replace(tmp, out)

def bg_brand(dur):
    return ["-f", "lavfi", "-i", f"color=c=0x0B3B37:s=1920x1080:r=30:d={dur}"]

files = []
for i, (sid, _, _) in enumerate(SCENES):
    dur = T[sid]["dur"]; out = f"{B}/scene_{i:02d}_{sid}.mp4"; vf = []
    if sid == "hook":     # colour-corrected b-roll (from the colour exercise), darkened, kinetic words synced to the narration
        inp = ["-stream_loop", "-1", "-i", f"{B}/fix_coffee.mp4"]
        vf = ["eq=brightness=-0.12:saturation=0.9", "boxblur=2"]
        for k, (a, b, text) in enumerate(T[sid]["subs"]):
            vf.append(dt("\n".join(textwrap.wrap(text.rstrip(".:"), 22)), DB, 104 if k < 3 else 150, "white" if k < 3 else "0xE8A0A6", "(w-text_w)/2", "(h-text_h)/2-60", a, b + .35 if k < 3 else dur))
    elif sid == "intro":
        inp = bg_brand(dur)
        vf = [dt("Split hostel expenses\nin 3 minutes", DB, 104, "white", 140, 300, .2, dur), dt("and settle up with UPI", DX, 56, "0xE8A0A6", 140, 560, .8, dur)] + callouts(sid, dur)
    elif sid == "why":
        inp = bg_brand(dur); items = [("₹60  chai", 2.5), ("₹480  cab to the station", 4.5), ("₹799  Wi-Fi recharge", 6.5), ("₹360  late-night Maggi", 8.0)]
        vf = [dt(t, DX, 64, "white", 160, 260 + 110 * k, a, dur) for k, (t, a) in enumerate(items)] + callouts(sid, dur)
    elif sid == "outro":
        inp = bg_brand(dur + 5); dur += 5
        vf = [dt("Add.  Split.  Settle.", DB, 110, "white", "(w-text_w)/2", 260, .3, dur),
              dt("  SUBSCRIBE  ", DB, 64, "white", "(w-text_w)/2", 520, 8.0, dur, "0xD7263D", ":boxborderw=34"),
              dt("for more student money tips", MD, 44, "0xD5F5EF", "(w-text_w)/2", 660, 8.4, dur),
              dt("Hisaab is a concept app designed for a course project", MD, 28, "0x9FC9C2", "(w-text_w)/2", 60, 1, dur)]
    else:                  # screen recording of the prototype, trimmed to the scene
        inp = ["-ss", f"{OFF[sid]:.2f}", "-i", f"{B}/rec_{sid}.webm"]
        vf = ["fps=30"] + callouts(sid, dur)
    vf += subs(sid, T[sid]["dur"]) if sid != "hook" else []   # the hook's kinetic words are its captions
    vf += [f"fade=t=in:st=0:d=0.25", f"fade=t=out:st={dur - .25}:d=0.25", "format=yuv420p"]
    run(inp + ["-t", f"{dur:.3f}", "-vf", ",".join(vf), "-an"] + ENC, out)
    files.append((out, dur)); print("rendered", out, round(dur, 1))

open(f"{B}/list.txt", "w").write("".join(f"file '{os.path.basename(f)}'\n" for f, _ in files))
run(["-f", "concat", "-safe", "0", "-i", f"{B}/list.txt", "-c", "copy"], f"{B}/video.mp4")

# voiceover track with the same scene lengths (outro is 5 s longer for the end screen)
vo = [f"{B}/vo_{sid}.wav" for sid, _, _ in SCENES]
fc = "".join(f"[{k}:a]" for k in range(len(vo))) + f"concat=n={len(vo)}:v=0:a=1,apad=pad_dur=5[vo]"
run(sum([["-i", v] for v in vo], []) + ["-filter_complex", fc, "-map", "[vo]", "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", "-f", "mov"], f"{B}/vo_full.mp4")
total = sum(d for _, d in files)
mix = ("[1:a]aformat=channel_layouts=stereo,asplit=2[v1][v2];[2:a]volume=0.55[m];[m][v1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];"
       f"[duck][v2]amix=inputs=2:duration=first:weights='1 1.6',atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11[a]")
run(["-i", f"{B}/video.mp4", "-i", f"{B}/vo_full.mp4", "-i", f"{B}/music.wav", "-filter_complex", mix, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"], f"{E}/tutorial.mp4")

# soft subtitles (SRT) for upload
def ts(s): return f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d},{int(s * 1000 % 1000):03d}"
srt, t0, k = [], 0.0, 1
for (sid, _, _), (_, d) in zip(SCENES, files):
    for a, b, text in T[sid]["subs"]:
        srt.append(f"{k}\n{ts(t0 + a)} --> {ts(t0 + b)}\n{text}\n"); k += 1
    t0 += d
open(f"{E}/tutorial.srt", "w").write("\n".join(srt))
print("done", round(total, 1), "s")
