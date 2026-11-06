"""2-minute showreel of my best edits from weeks 2-4, cut to an original 120 bpm track: every cut lands on a beat,
the montage starts on the drop (8.0 s), and each clip carries a small label saying what the skill is.
Vertical clips are shown at full height over a blurred, zoomed copy of themselves (no black bars).
    python ../week-3/src/beat.py 124 && python src/showreel.py  -> exports/showreel.mp4"""
import json, os, subprocess
B, E = "build", "exports"; F = "/usr/share/fonts/opentype/inter/"; W2, W3 = "../week-2/exports/", "../week-3/exports/"
ENC = ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30"]
BEAT = json.load(open(f"{B}/beats.json"))["beat"]                       # 0.5 s
# (source, start s, length in beats, label, vertical?)
CLIPS = [
 (W2 + "tutorial.mp4", 1.0, 8, "Kinetic typography · tutorial hook", 0),
 (W3 + "reel-30s.mp4", 7.6, 8, "Beat-synced Reel · whip transitions", 1),
 (W2 + "color-correction.mp4", 1.0, 8, "Colour correction · before / after", 0),
 ("exports/long-form.mp4", 4.0, 8, "Green-screen presenter · long-form", 0),
 (W3 + "short-1-split-in-10s.mp4", 9.4, 8, "Speed ramp 8× → 0.5× slow-mo", 1),
 (W2 + "dialogue_jl.mp4", 5.6, 8, "J-cuts and L-cuts · dialogue edit", 0),
 (W3 + "logo-reveal.mp4", 0.3, 8, "Keyframed logo reveal", 0),
 (W3 + "greenscreen-breakdown.mp4", 1.0, 8, "Chroma key · matte · despill", 0),
 ("exports/short-b-fair-not-equal.mp4", 3.6, 8, "Word-by-word captions", 1),
 ("exports/long-form.mp4", 205.0, 8, "Animated data chart", 0),
 (W2 + "tutorial.mp4", 74.0, 8, "Screen recording + call-outs", 0),
 (W3 + "reel-30s.mp4", 12.2, 4, "Glitch transition", 1),
 (W3 + "reel-30s.mp4", 18.0, 4, "Zoom punch", 1),
 (W2 + "text-animations.mp4", 3.6, 8, "Lower thirds · title animation", 0),
 ("exports/short-c-app-asks.mp4", 0.2, 8, "Hook titles for Shorts", 1),
 (W3 + "short-2-money-rules.mp4", 8.6, 8, "Stickers · slow-motion payoff", 1),
 ("exports/long-form.mp4", 112.0, 8, "Long-form: habits, chapters, SEO", 0),
 ("exports/short-a-settle-sunday.mp4", 9.0, 8, "Repurposing long-form into Shorts", 1),
 (W2 + "tutorial.mp4", 14.0, 8, "Motion title · brand intro", 0),
 (W3 + "short-3-group-bank.mp4", 0.6, 8, "Keyed presenter in a vertical frame", 1),
 (W2 + "color-correction.mp4", 9.0, 8, "Exposure and white-balance fix", 0),
 (W3 + "reel-30s.mp4", 20.4, 8, "Speed-ramped payoff on the beat", 1),
 ("exports/long-form.mp4", 245.0, 8, "Kinetic text cards", 0),
 (W3 + "short-1-split-in-10s.mp4", 0.4, 8, "Shorts hook in the first second", 1),
 ("exports/long-form.mp4", 140.0, 8, "Talking-head scene design", 0),
 (W2 + "tutorial.mp4", 176.0, 8, "End screen · CTA", 0),
 ("exports/long-form.mp4", 300.0, 8, "YouTube end-screen layout", 0)]
INTRO, OUTRO = 16, 16                                                     # beats (8.0 s up to the drop, 8.0 s end card)
def tf(t, n): p = f"{B}/sr_{n}.txt"; open(p, "w").write(t); return p
def label(text, n, d): return (f"drawtext=fontfile={F}InterDisplay-Bold.otf:textfile={tf(text, n)}:fontsize=34:fontcolor=white:"
                              f"box=1:boxcolor=0x0B3B37@0.88:boxborderw=18:x=60:y=48:alpha='min(1,t/0.25)*min(1,({d}-t)/0.15)'")
def run(args, out):
    tmp = out[:-4] + ".tmp.mp4"; subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + args + [tmp], check=True); os.replace(tmp, out)
files = []
def card(n, lines, d):
    vf = []
    for k, (txt, size, col, y, at) in enumerate(lines):
        vf.append(f"drawtext=fontfile={F}InterDisplay-ExtraBold.otf:textfile={tf(txt, f'{n}{k}')}:fontsize={size}:fontcolor={col}:x=(w-text_w)/2:y={y}:alpha='min(1,max(0,(t-{at})/0.4))'")
    out = f"{B}/sr_{n}.mp4"; run(["-f", "lavfi", "-i", f"color=c=0x0B3B37:s=1920x1080:r=30:d={d}", "-vf", ",".join(vf) + f",fade=t=out:st={d - .3}:d=0.3", *ENC], out); files.append(out)
card("intro", [("PRIYANSHU SHARAN", 120, "white", 380, .5), ("Video editing showreel", 64, "0xD5F5EF", 540, 2.0),
               ("Edits · motion graphics · colour · Shorts · YouTube", 40, "0xFFD84D", 650, 4.0)], INTRO * BEAT)
for i, (src, st, beats, lab, vert) in enumerate(CLIPS):
    d = beats * BEAT; out = f"{B}/sr_{i:02d}.mp4"
    if vert: fc = f"[0:v]split[a][b];[a]scale=1920:-2,crop=1920:1080,gblur=sigma=30,eq=brightness=-0.15[bg];[b]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0,setsar=1"
    else: fc = "[0:v]scale=1920:1080,setsar=1"
    run(["-ss", f"{st}", "-i", src, "-filter_complex", fc + "," + label(lab, i, d) + "[v]", "-map", "[v]", "-t", f"{d:.3f}", "-an", *ENC], out); files.append(out)
card("outro", [("Thanks for watching", 96, "white", 360, .2), ("github.com/priyanshusharan-cmd/skillnexis-coursework", 40, "0xD5F5EF", 520, .8),
               ("Made with free tools only: ffmpeg · Python · Playwright", 36, "0xFFD84D", 600, 1.4)], OUTRO * BEAT)
open(f"{B}/sr_list.txt", "w").write("".join(f"file '{os.path.basename(f)}'\n" for f in files))
run(["-f", "concat", "-safe", "0", "-i", f"{B}/sr_list.txt", "-c", "copy"], f"{B}/sr_video.mp4")
total = (INTRO + OUTRO + sum(c[2] for c in CLIPS)) * BEAT
run(["-i", f"{B}/sr_video.mp4", "-i", f"{B}/beat.wav", "-filter_complex", f"[1:a]atrim=0:{total},afade=t=out:st={total - 2.5}:d=2.5,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
     "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"], f"{E}/showreel.mp4")
cuts = [INTRO * BEAT]; [cuts.append(cuts[-1] + c[2] * BEAT) for c in CLIPS]
json.dump({"total": total, "cuts": cuts, "clips": [{"src": c[0], "start": c[1], "beats": c[2], "label": c[3]} for c in CLIPS]}, open("results/showreel-edl.json", "w"), indent=1)
print("showreel", total, "s,", len(CLIPS), "clips, first cut on the drop at", cuts[0], "s")
