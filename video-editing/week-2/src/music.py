"""Original lo-fi background track, synthesised so there are no licensing questions: 78 bpm, Cmaj7-Am7-Fmaj7-G6 pads, soft bass, brushed hats.
    python src/music.py [seconds]  -> build/music.wav (44.1 kHz stereo)"""
import sys, wave, numpy as np
SR, BPM = 44100, 78; dur = float(sys.argv[1]) if len(sys.argv) > 1 else 200
n = int(dur * SR); t = np.arange(n) / SR; beat = 60 / BPM; bar = 4 * beat
f = lambda m: 440 * 2 ** ((m - 69) / 12)
CH = [[48, 60, 64, 67, 71], [45, 57, 60, 64, 67], [41, 53, 57, 60, 64], [43, 55, 59, 62, 64]]
L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(3)
for k in range(int(dur / bar) + 1):
    s = int(k * bar * SR); e = min(n, int((k + 1) * bar * SR)); ch = CH[k % 4]; tt = t[s:e] - k * bar
    env = np.minimum(1, tt / .4) * np.exp(-tt / 6)
    pad = sum(np.sin(2 * np.pi * f(m) * tt + .3 * np.sin(2 * np.pi * .5 * tt)) * (.5 if m > 50 else 0) for m in ch[1:]) * env * .05
    bass = np.sin(2 * np.pi * f(ch[0]) * tt) * np.exp(-((tt % (2 * beat)) / .8)) * .14
    L[s:e] += pad * 1.05 + bass; R[s:e] += pad * .95 + bass
    for b in range(8):                                   # brushed eighth-note hats, swung
        hs = s + int((b * beat / 2 + (.06 if b % 2 else 0)) * SR); he = min(n, hs + int(.08 * SR))
        if hs < n:
            noise = rng.normal(0, 1, he - hs) * np.exp(-np.arange(he - hs) / (SR * .015)) * (.035 if b % 2 else .05)
            L[hs:he] += noise * .9; R[hs:he] += noise * 1.1
    ks = s; ke = min(n, ks + int(.25 * SR)); kt = np.arange(ke - ks) / SR          # soft kick on 1 and 3
    for off in (0, 2 * beat):
        a = s + int(off * SR); b2 = min(n, a + len(kt)); kk = np.sin(2 * np.pi * (55 + 60 * np.exp(-kt[:b2 - a] * 30)) * kt[:b2 - a]) * np.exp(-kt[:b2 - a] * 12) * .25
        L[a:b2] += kk; R[a:b2] += kk
fade = np.minimum(1, np.minimum(t / 2, (dur - t) / 3)); L *= fade; R *= fade
x = np.stack([L, R], 1); x = x / np.abs(x).max() * .8
with wave.open("build/music.wav", "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
print("music", dur, "s")
