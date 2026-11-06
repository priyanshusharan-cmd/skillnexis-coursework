"""Portfolio page: every finished edit from weeks 2-4, with a poster frame, what it shows, and the skill behind it.
    python src/portfolio.py  -> portfolio/index.html, portfolio/posters/*.jpg"""
import html, os, subprocess
ITEMS = [  # (path relative to video-editing/, poster time, title, what it demonstrates, vertical?)
 ("week-4/exports/showreel.mp4", 3, "Showreel (2:00)", "27 clips cut on a 120 bpm grid; the montage starts on the drop.", 0),
 ("week-4/exports/long-form.mp4", 100, "5 Money Habits That Keep Hostel Friendships Alive (5:10)", "Long-form YouTube video: scripted hook → 5 habits → recap → CTA; green-screen presenter, screen recordings, animated chart, chapters, captions, end screen.", 0),
 ("week-4/exports/short-a-settle-sunday.mp4", 9, "Short: Settle every Sunday", "Repurposed from the long-form: speed ramps, word-by-word captions, hook title.", 1),
 ("week-4/exports/short-b-fair-not-equal.mp4", 6, "Short: Fair, not equal", "Zoom punch-ins on the UI, glitch transition, stickers.", 1),
 ("week-4/exports/short-c-app-asks.mp4", 1.5, "Short: Let the app be the bad guy", "Keyed presenter in a vertical frame, then UI close-ups.", 1),
 ("week-3/exports/reel-30s.mp4", 9, "Instagram Reel (30 s)", "Beat-synced montage: whip, punch, glitch and flash transitions with SFX.", 1),
 ("week-3/exports/short-1-split-in-10s.mp4", 12, "Short: Split ₹360 in 10 seconds", "8.3× → 0.5× speed ramp onto the payoff.", 1),
 ("week-3/exports/greenscreen-breakdown.mp4", 1.5, "Green screen breakdown", "Raw plate, matte, naive key vs tuned key + despill; scored against the true matte.", 0),
 ("week-3/exports/logo-reveal.mp4", 3, "Keyframed logo reveal (5 s)", "Eased keyframes with overshoot, mask wipe, synced sound.", 0),
 ("week-2/exports/tutorial.mp4", 70, "Tutorial: Split hostel expenses in 3 minutes", "Voice-over synced to screen recordings, call-outs, ducked music, −14 LUFS.", 0),
 ("week-2/exports/dialogue_jl.mp4", 6, "Dialogue edit with J- and L-cuts", "Same footage as a straight-cut version, so the difference is audible.", 0),
 ("week-2/exports/color-correction.mp4", 2, "Colour correction before / after", "Exposure, white balance and contrast, tuned by grid search against reference scopes.", 0),
 ("week-2/exports/text-animations.mp4", 3, "Text animations", "Animated title, sliding lower thirds and fading subtitles.", 0)]
cards = []
for path, t, title, desc, vert in ITEMS:
    poster = "posters/" + os.path.basename(path).replace(".mp4", ".jpg")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", "../" + path, "-frames:v", "1", "-vf", "scale=-2:540" if vert else "scale=960:-2", "-q:v", "4", "portfolio/" + poster], check=True)
    cards.append(f'<article class="{"v" if vert else "h"}"><video controls preload="none" poster="{poster}" src="../../{path}"></video>'
                 f'<h3>{html.escape(title)}</h3><p>{html.escape(desc)}</p><a href="../../{path}">Open file</a></article>')
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Video Editing Portfolio</title><style>
:root{{--bg:#0B3B37;--card:#0F4A45;--ink:#fff;--muted:#BFE3DC;--accent:#FFD84D}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 Inter,system-ui,sans-serif}}
header{{max-width:1180px;margin:0 auto;padding:56px 16px 24px}}h1{{font-size:clamp(32px,5vw,56px);margin:0 0 8px;letter-spacing:-.02em}}
header p{{color:var(--muted);max-width:720px;margin:0}}.tags{{margin-top:16px;display:flex;flex-wrap:wrap;gap:8px}}
.tags span{{background:rgba(255,255,255,.08);border-radius:999px;padding:4px 12px;font-size:14px}}
main{{max-width:1180px;margin:0 auto;padding:16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:20px;grid-auto-flow:dense}}
article{{background:var(--card);border-radius:16px;padding:14px}}article.h{{grid-column:span 2}}@media(max-width:760px){{article.h{{grid-column:auto}}}}
video{{width:100%;border-radius:10px;background:#000;display:block}}article.v video{{aspect-ratio:9/16;max-height:620px;object-fit:contain}}
h3{{margin:12px 0 4px;font-size:18px}}p{{margin:0 0 8px;color:var(--muted);font-size:15px}}a{{color:var(--accent)}}
footer{{max-width:1180px;margin:0 auto;padding:24px 16px 56px;color:var(--muted);font-size:14px}}</style></head><body>
<header><h1>Priyanshu Sharan · Video Editing</h1><p>Edits from my SkillNexis video-editing internship (weeks 2–4): tutorials, dialogue, colour, motion graphics, green screen, Reels, Shorts and a long-form YouTube video. Everything was made with free tools: ffmpeg, Python and Playwright.</p>
<div class="tags"><span>Long-form YouTube</span><span>Shorts &amp; Reels</span><span>Motion graphics</span><span>Chroma key</span><span>Colour correction</span><span>Sound mixing (−14 LUFS)</span><span>Thumbnails</span></div></header>
<main>{''.join(cards)}</main>
<footer>Source code and project files: <a href="https://github.com/priyanshusharan-cmd/skillnexis-coursework/tree/main/video-editing">github.com/priyanshusharan-cmd/skillnexis-coursework</a>. Hisaab is a concept app designed for a course project; voices are synthetic and the presenter is an illustration.</footer></body></html>"""
open("portfolio/index.html", "w").write(page); print(len(ITEMS), "items")
