"""Voiceover: one WAV per sentence (mbrola us2 via espeak-ng), concatenated per scene with natural pauses. Writes build/vo_<scene>.wav and build/timing.json"""
import json, os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from script import SCENES
B = os.path.join(os.path.dirname(__file__), "..", "build"); SR = 22050
def tts(text):
    p = os.path.join(B, "_s.wav"); subprocess.run(["espeak-ng", "-v", "mb-us2", "-s", "140", "-p", "45", "-w", p, text], check=True)
    with wave.open(p) as w: sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    if sr != SR: x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
    nz = np.where(np.abs(x) > 300)[0]; return x[nz[0]:nz[-1] + 1] if len(nz) else x
timing = {}
for sid, sents, _ in SCENES:
    parts, t, subs = [np.zeros(int(.35 * SR))], .35, []
    for s in sents:
        a = tts(s); d = len(a) / SR; subs.append((t, t + d, s)); parts += [a, np.zeros(int(.5 * SR))]; t += d + .5
    pad = 1.0 if sid in ("outro",) else .25
    parts.append(np.zeros(int(pad * SR))); x = np.concatenate(parts); x = x / max(1, np.abs(x).max()) * 0.9 * 32767
    with wave.open(os.path.join(B, f"vo_{sid}.wav"), "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.astype(np.int16).tobytes())
    timing[sid] = {"dur": len(x) / SR, "subs": subs}
json.dump(timing, open(os.path.join(B, "timing.json"), "w"), indent=1)
tot = sum(v["dur"] for v in timing.values()); print({k: round(v["dur"], 1) for k, v in timing.items()}, "total", round(tot, 1))
