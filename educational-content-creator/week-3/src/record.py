"""Records the source material ("the shoot") for the lesson-2 edit:
  head sections -> one raw take each (build/raw_<id>.wav/.mp4): pauses, flubs and restarts left in
  screen sections -> a clean screen capture with its narration (build/scr_<id>.mp4/.wav), real program output
  try section -> narration with a 10 s silent gap for the countdown
Writes build/materials.json for src/edit.py.   python src/record.py"""
import json, os, re, subprocess, sys
sys.path.insert(0, "src")
from engine import voice, voice_raw, capture, B
from timeline import build
from presenter import render
from script_ifelse import SECTIONS
def speech_regions(wav, noise="-40dB", d=0.6):
    """Automatic silence detection (what an editor's 'remove silences' does): returns the spoken regions."""
    e = subprocess.run(["ffmpeg", "-i", wav, "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", e)]; en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", e)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav], capture_output=True, text=True).stdout)
    edges, t = [], 0.0
    for a, b in zip(st, en + [dur] * (len(st) - len(en))):
        if a > t: edges.append((t, a))
        t = b
    if t < dur: edges.append((t, dur))
    return [(round(a, 3), round(b, 3)) for a, b in edges if b - a > .15], dur
M = {}
for s in SECTIONS:
    k, i = s["kind"], s["id"]
    if k == "head":
        wav, mp4 = f"{B}/raw_{i}.wav", f"{B}/raw_{i}.mp4"
        dur, subs, retakes = voice_raw(s["lines"], wav, flubs=s.get("flubs"))
        if not os.path.exists(mp4) or "--force" in sys.argv: render(wav, mp4, mode="full")
        regions, _ = speech_regions(wav)
        M[i] = dict(kind=k, video=mp4, wav=wav, dur=dur, subs=subs, retakes=retakes, speech=regions)
    elif k == "screen":
        wav, mp4 = f"{B}/scr_{i}.wav", f"{B}/scr_{i}.mp4"; dur, subs = voice([b[0] for b in s["beats"]], wav)
        files = sorted({a["name"] for _, acts in s["beats"] for a in acts if a["do"] == "file"}, key=lambda n: [a["name"] for _, acts in s["beats"] for a in acts if a["do"] == "file"].index(n))
        tl = build(s["beats"], [x[0] for x in subs], [x[1] for x in subs], files)
        if not os.path.exists(mp4) or "--force" in sys.argv: capture({"page": "src/editor.html", "kind": "editor", "tl": tl, "dur": dur, "fps": 15}, mp4)
        M[i] = dict(kind=k, video=mp4, wav=wav, dur=dur, subs=subs, tl=tl)
    elif k == "try":
        wav = f"{B}/try.wav"; dur, subs = voice([s["line"]], wav, pauses={0: s["pause"]}); M[i] = dict(kind=k, wav=wav, dur=dur, subs=subs)
    print("recorded", i, k, flush=True)
json.dump(M, open(f"{B}/materials.json", "w"), indent=1)
raw = sum(m["dur"] for m in M.values() if m["kind"] == "head"); print("raw talking-head footage", round(raw, 1), "s")
