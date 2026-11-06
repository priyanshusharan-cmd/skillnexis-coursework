"""Original upbeat track for the Reel and Shorts (stand-in for trending audio, which is licensed and only added inside
Instagram / YouTube from their audio libraries). 120 bpm, 4-on-the-floor kick, claps on 2 and 4, off-beat hats, a
plucked synth hook, a riser into a drop at bar 5. Also writes the beat grid so cuts can land on beats.
    python src/beat.py [seconds]  -> build/beat.wav, build/beats.json"""
import sys, json, wave, numpy as np
SR, BPM = 44100, 120; dur = float(sys.argv[1]) if len(sys.argv) > 1 else 64
n = int(dur * SR); beat = 60 / BPM; L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(7)
f = lambda m: 440 * 2 ** ((m - 69) / 12)
def add(start, sig, pan=0.0):
    a = int(start * SR); b = min(n, a + len(sig))
    if a >= n: return
    L[a:b] += sig[:b - a] * (1 - pan); R[a:b] += sig[:b - a] * (1 + pan)
kt = np.arange(int(.3 * SR)) / SR; KICK = np.sin(2 * np.pi * (50 + 120 * np.exp(-kt * 35)) * kt) * np.exp(-kt * 9) * .55
ct = np.arange(int(.2 * SR)) / SR; CLAP = rng.normal(0, 1, len(ct)) * np.exp(-ct * 25) * .22
ht = np.arange(int(.06 * SR)) / SR; HAT = rng.normal(0, 1, len(ht)) * np.exp(-ht * 70) * .09
HAT = HAT - np.convolve(HAT, np.ones(8) / 8, "same")                     # crude high-pass so hats sound bright
PROG = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]            # Am F C G
HOOK = [76, 74, 72, 74, 76, 79, 76, 74]                                    # 8 eighth-notes per bar
bars = int(dur / (4 * beat)) + 1; DROP = 4                                 # bars 0-3 intro (filtered, no kick), drop at bar 4 (8.0 s)
for bar in range(bars):
    t0 = bar * 4 * beat; ch = PROG[bar % 4]; full = bar >= DROP
    for b in range(4):
        tb = t0 + b * beat
        if full: add(tb, KICK)
        if full and b % 2 == 1: add(tb, CLAP, .1)
        add(tb + beat / 2, HAT * (1 if full else .5), -.2)
    pt = np.arange(int(4 * beat * SR)) / SR                                # pad chord
    pad = sum(np.sign(np.sin(2 * np.pi * f(m) * pt)) * .3 + np.sin(2 * np.pi * f(m) * pt) for m in ch) * np.minimum(1, pt / .05) * np.exp(-pt * .4) * (.035 if full else .025)
    add(t0, pad)
    bt = np.arange(int(beat / 2 * SR)) / SR                                # off-beat bass
    for b in range(4):
        if full: add(t0 + b * beat + beat / 2, np.sin(2 * np.pi * f(ch[0] - 24) * bt) * np.exp(-bt * 8) * .3)
    st = np.arange(int(beat / 2 * SR)) / SR                                # plucked hook (from bar 2)
    if bar >= 2:
        for k, m in enumerate(HOOK):
            add(t0 + k * beat / 2, (np.sin(2 * np.pi * f(m) * st) + .4 * np.sin(4 * np.pi * f(m) * st)) * np.exp(-st * 10) * .09, .3 if k % 2 else -.3)
rt = np.arange(int(4 * beat * SR)) / SR                                    # riser + reverse-swell into the drop
riser = rng.normal(0, 1, len(rt)) * (rt / rt[-1]) ** 2 * .12
add((DROP - 1) * 4 * beat, riser)
t = np.arange(n) / SR; fade = np.minimum(1, np.minimum(t / .05, (dur - t) / 1.5)); L *= fade; R *= fade
x = np.stack([L, R], 1); x = x / np.abs(x).max() * .85
with wave.open("build/beat.wav", "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
json.dump({"bpm": BPM, "beat": beat, "drop": DROP * 4 * beat, "beats": [round(i * beat, 3) for i in range(int(dur / beat))]}, open("build/beats.json", "w"))
print("beat", dur, "s, drop at", DROP * 4 * beat)
