"""Shared production helpers (copied from week 2, plus a deliberately unedited "raw take" recorder): voice-over with timings, real code output, deterministic screen
capture, the picture-in-picture camera, audio mix (voice cleaned up, music ducked, -14 LUFS) and SRT captions."""
import json, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw
SR = 22050; B = "build"; os.makedirs(B, exist_ok=True)
SANDBOX = "/home/mina/code-in-small-steps"          # where the demo programs really run (paths in tracebacks are real)

def tts(text, voice="mb-us1", speed=138, pitch=58):
    p = f"{B}/_tts.wav"; subprocess.run(["espeak-ng", "-v", voice, "-s", str(speed), "-p", str(pitch), "-w", p, text], check=True)
    with wave.open(p) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    if sr != SR: x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
    nz = np.where(np.abs(x) > 300)[0]; return x[nz[0]:nz[-1] + 1]

def voice(sentences, out, lead=.4, gap=.5, tail=.6, pauses=None, speed=138):
    """Speaks sentences back to back. pauses = {index: extra seconds after that sentence}. Returns (duration, [(start, end, text)])."""
    parts, t, subs = [np.zeros(int(lead * SR))], lead, []
    for k, s in enumerate(sentences):
        a = tts(s, speed=speed); d = len(a) / SR; subs.append((t, t + d, s)); g = gap + (pauses or {}).get(k, 0)
        parts += [a, np.zeros(int(g * SR))]; t += d + g
    parts.append(np.zeros(int(tail * SR))); x = np.concatenate(parts); x = x / max(1, np.abs(x).max()) * .9 * 32767
    with wave.open(out, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.astype(np.int16).tobytes())
    return len(x) / SR, subs

def run_python(name, code):
    """Runs the program for real and returns what the terminal would show (stdout and stderr interleaved)."""
    os.makedirs(SANDBOX, exist_ok=True); open(f"{SANDBOX}/{name}", "w").write(code)
    r = subprocess.run(["python3", "-u", name], cwd=SANDBOX, capture_output=True, text=True, timeout=20, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    # stderr arrives after stdout here; for these demos stdout always precedes the crash, so the order is preserved
    return (r.stdout + r.stderr).rstrip("\n")

def capture(job, out):
    job = {**job, "out": out}; jp = out + ".json"; json.dump(job, open(jp, "w")); subprocess.run(["node", "src/capture.js", jp], check=True)

def circle_mask(size, path):
    m = Image.new("L", (size * 4, size * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    m.resize((size, size), Image.LANCZOS).save(path)

def pip(screen, cam, out, pos="tr", size=360):
    """Overlays the presenter camera as a round bubble (Loom style) with a white ring."""
    circle_mask(size, f"{B}/mask.png"); circle_mask(size + 12, f"{B}/ring.png")
    x, y = {"tr": (1920 - size - 60, 90), "br": (1920 - size - 40, 1080 - size - 40)}[pos]
    fc = (f"[1:v]scale={size}:{size}[c];[2:v]format=gray[m];[c][m]alphamerge[cm];[3:v]format=gray[r];color=white:s={size + 12}x{size + 12}:r=30[w];[w][r]alphamerge[ring];"
          f"[0:v][ring]overlay={x - 6}:{y - 6}:shortest=1[v1];[v1][cm]overlay={x}:{y}:shortest=1,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", screen, "-i", cam, "-loop", "1", "-i", f"{B}/mask.png", "-loop", "1", "-i", f"{B}/ring.png", "-filter_complex", fc, "-map", "[v]",
                    "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30", out[:-4] + ".tmp.mp4"], check=True); os.replace(out[:-4] + ".tmp.mp4", out)

VOICE_CHAIN = "highpass=f=80,lowpass=f=12000,acompressor=threshold=0.1:ratio=3:attack=10:release=150:makeup=1.5"   # clean, even speech
def mix(video, vo_wav, out, music=None, music_gain=.35):
    """Voice cleaned up (high-pass, compression), music ducked under it, loudness-normalised to -14 LUFS."""
    if music:
        fc = (f"[1:a]{VOICE_CHAIN},aresample=44100,aformat=channel_layouts=stereo,asplit=2[v1][v2];[2:a]volume={music_gain}[m];"
              f"[m][v1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];[duck][v2]amix=inputs=2:duration=longest:normalize=0:weights='0.8 1.4',loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        ins = ["-i", video, "-i", vo_wav, "-i", music]
    else:
        fc = f"[1:a]{VOICE_CHAIN},aresample=44100,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11[a]"; ins = ["-i", video, "-i", vo_wav]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *ins, "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out[:-4] + ".tmp.mp4"], check=True); os.replace(out[:-4] + ".tmp.mp4", out)

def srt(subs, path, offset=0.0):
    ts = lambda s: f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d},{int(s * 1000 % 1000):03d}"
    import textwrap; open(path, "w").write("\n".join(f"{k}\n{ts(a + offset)} --> {ts(b + offset)}\n{textwrap.fill(t, 42)}\n" for k, (a, b, t) in enumerate(subs, 1)))

def loudness(path):
    r = subprocess.run(["ffmpeg", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float([l for l in r.splitlines() if l.strip().startswith("I:")][-1].split()[1])

def voice_raw(sentences, out, flubs=None, seed=11, speed=138):
    """A deliberately unedited A-roll take: long, uneven pauses between sentences, and flubbed lines that are restarted
    ("sorry, let me say that again") before the clean retake. Returns (duration, sentence spans, retake spans to cut)."""
    rng = np.random.default_rng(seed); parts, t, subs, retakes = [np.zeros(int(1.2 * SR))], 1.2, [], []
    for k, s in enumerate(sentences):
        if flubs and k in flubs:
            a0 = t
            for bad in (flubs[k], "Sorry, let me say that again."):
                a = tts(bad, speed=speed); parts += [a, np.zeros(int(.7 * SR))]; t += len(a) / SR + .7
            retakes.append((a0, t))
        a = tts(s, speed=speed); d = len(a) / SR; subs.append((t, t + d, s)); g = float(rng.uniform(1.0, 2.6))
        parts += [a, np.zeros(int(g * SR))]; t += d + g
    x = np.concatenate(parts); x = x / max(1, np.abs(x).max()) * .9 * 32767
    with wave.open(out, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.astype(np.int16).tobytes())
    return len(x) / SR, subs, retakes
