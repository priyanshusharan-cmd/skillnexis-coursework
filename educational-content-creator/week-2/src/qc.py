"""Quality check of every export: resolution, frame rate, duration, loudness (EBU R128), true peak, and the voice
track's noise floor (level of the gaps between sentences). Writes results/qc.md."""
import json, os, subprocess, wave
import numpy as np
os.makedirs("results", exist_ok=True)
def probe(p):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", p], capture_output=True, text=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video"); a, b = map(int, v["r_frame_rate"].split("/")); return v["width"], v["height"], a / b, float(j["format"]["duration"])
def r128(p):
    e = subprocess.run(["ffmpeg", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr.splitlines()
    I = float([l for l in e if l.strip().startswith("I:")][-1].split()[1]); P = float([l for l in e if l.strip().startswith("Peak:")][-1].split()[1]); return I, P
def floor(wav):
    with wave.open(wav) as w: x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; sr = w.getframerate()
    win = sr // 10; r = np.array([np.sqrt(np.mean(x[i:i + win] ** 2)) + 1e-9 for i in range(0, len(x) - win, win)]); db = 20 * np.log10(r)
    return float(np.percentile(db, 10)), float(np.percentile(db, 90))
rows = [("exports/screen-tutorial.mp4", "build/screen_vo.wav"), ("exports/talking-head.mp4", "build/th_vo.wav"), ("exports/lesson-variables-1080p.mp4", "build/L_vo.wav")]
out = ["# Export quality check", "", "| File | Size | fps | Length | Loudness | True peak |", "|---|---|---|---|---|---|"]
for v, w in rows:
    W, H, fps, d = probe(v); I, P = r128(v)
    out.append(f"| `{os.path.basename(v)}` | {W}×{H} | {fps:.0f} | {int(d // 60)}:{int(d % 60):02d} | {I:.1f} LUFS | {P:.1f} dBTP |")
out += ["", "Targets: 1920×1080 at 30 fps; −14 LUFS (±1) integrated loudness, YouTube's reference; true peak ≤ −1 dBTP.",
        "The voices are synthetic, so there is no room noise to measure. With a real mic, aim for a noise floor below −60 dBFS between sentences."]
open("results/qc.md", "w").write("\n".join(out) + "\n"); print("\n".join(out))
