"""YouTube SEO package for the long-form video and the 3 Shorts, checked against YouTube's limits:
title <= 100 chars (front-load the keyword in the first ~60, the part shown in search), description <= 5000 chars,
chapters (first at 0:00, at least 3, each at least 10 s long), tags <= 500 chars in total, at most 15 hashtags.
Also writes the long-form script with real timestamps.
    python src/seo.py  -> exports/youtube-metadata.md, exports/youtube-metadata.json, scripts/video-a-script.md"""
import json, sys
sys.path.insert(0, "src"); from script_a import SCENES, TITLE
C = json.load(open("build/chapters.json")); total = C["total"]
mmss = lambda s: f"{int(s // 60)}:{int(s % 60):02d}"
chapters = [(a, c) for a, c in C["chapters"] if c != "Intro"]          # the 5 s logo sting isn't worth a chapter
LONG = {
 "title": "5 Money Habits That Keep Hostel Friendships Alive (Split Expenses Without the Awkwardness)",
 "description": "\n".join([
  "Splitting expenses in a hostel room shouldn't cost you friends. Here are 5 simple money habits that stopped our room from arguing about who paid for what, from logging expenses the moment you pay to a weekly UPI settle day.",
  "", "They work with any app, or even a notebook. I show each one in Hisaab, a concept expense-splitting app I designed for students (a course project, not a real product yet).",
  "", "CHAPTERS"] + [f"{mmss(a)} {c}" for a, c in chapters] + [
  "", "THE 5 HABITS", "1. Log it the moment you pay", "2. Split fairly, not equally", "3. Pick one settle day", "4. Let the app send the reminder", "5. Know where the money goes",
  "", "Next video: how I designed Hisaab in one week, from research to a clickable prototype.",
  "", "Music: original track made for this channel. Voice: synthetic (espeak-ng + MBROLA). Spending figures are sample prototype data.",
  "", "#hostellife #moneytips #studentlife"]),
 "tags": ["split expenses", "hostel life", "student money tips", "roommate expenses", "how to split bills with roommates", "upi", "splitwise alternative",
          "money habits", "college students india", "expense tracker", "hostel tips", "shared expenses", "budgeting for students", "hisaab app"],
 "category": "Education", "language": "English (India)", "captions": "long-form.srt (upload as English subtitles)",
 "thumbnail": "thumbnails/long-form.png", "end_screen": "last 20 s: 'Next video' element top-right + Subscribe button (placeholders are drawn in the video)",
 "playlist": "Hostel money habits", "audience": "Not made for kids", "license": "Standard YouTube licence"}
SHORTS = {
 "short-a-settle-sunday.mp4": {"title": "Settle money every Sunday, not at month end #shorts", "cover": "cover-short-a.png"},
 "short-b-fair-not-equal.mp4": {"title": "Split bills fairly, not equally #shorts", "cover": "cover-short-b.png"},
 "short-c-app-asks.mp4": {"title": "Hate asking friends for money? Let the app ask #shorts", "cover": "cover-short-c.png"}}
for v in SHORTS.values(): v["description"] = "One habit from my long-form video: 5 money habits that keep hostel friendships alive (linked as the related video). #hostellife #moneytips #shorts"
# ---- checks
chk = []
def check(name, ok): chk.append((name, bool(ok))); assert ok, name
check(f"long title {len(LONG['title'])} <= 100 chars", len(LONG["title"]) <= 100)
check("keyword 'Money Habits' within the first 60 chars", "Money Habits" in LONG["title"][:60])
check(f"description {len(LONG['description'])} <= 5000 chars", len(LONG["description"]) <= 5000)
check("first chapter at 0:00", chapters[0][0] == 0)
check(f"{len(chapters)} chapters >= 3", len(chapters) >= 3)
lens = [b[0] - a[0] for a, b in zip(chapters, chapters[1:] + [(total, "")])]; check(f"shortest chapter {min(lens):.1f} s >= 10 s", min(lens) >= 10)
tl = sum(len(t) for t in LONG["tags"]) + 2 * (len(LONG["tags"]) - 1); check(f"tags {tl} chars <= 500", tl <= 500)
tags_in_desc = LONG["description"].count("#"); check(f"{tags_in_desc} hashtags <= 15", tags_in_desc <= 15)
check(f"video length {mmss(total)} >= 5:00", total >= 300)
for k, v in SHORTS.items(): check(f"{k} title {len(v['title'])} <= 100", len(v["title"]) <= 100)
json.dump({"long_form": LONG, "shorts": SHORTS, "checks": chk}, open("exports/youtube-metadata.json", "w"), indent=1, ensure_ascii=False)
md = [f"# YouTube upload sheet", "", "## Long-form: `long-form.mp4` ({})".format(mmss(total)), "", f"**Title** ({len(LONG['title'])} chars)", "", "```", LONG["title"], "```", "",
      "**Description**", "", "```", LONG["description"], "```", "", "**Tags** ({} chars)".format(tl), "", "```", ", ".join(LONG["tags"]), "```", ""]
md += [f"* **{k.replace('_', ' ').capitalize()}:** {LONG[k]}" for k in ("category", "language", "captions", "thumbnail", "end_screen", "playlist", "audience", "license")]
md += ["", "## Shorts", "", "| File | Title | Cover |", "|---|---|---|"] + [f"| `{k}` | {v['title']} | `{v['cover']}` |" for k, v in SHORTS.items()]
md += ["", "Shorts description (all three):", "", "```", next(iter(SHORTS.values()))["description"], "```", "",
       "## Checks (run by `src/seo.py`)", ""] + [f"* {'✅' if ok else '❌'} {n}" for n, ok in chk]
open("exports/youtube-metadata.md", "w").write("\n".join(md) + "\n")
# ---- script A with timestamps
starts = {}
for s in C["shots"]: starts.setdefault(s["sid"], float(s["start"]))
part = {"hook": "HOOK", "logo": "INTRO", "promise": "BODY · setup", "recap": "BODY · recap", "outro": "CTA", "mistakes": "BODY"}
out = [f"# Script A: {TITLE}", "", f"Long-form, {mmss(total)}. Rendered from [`src/script_a.py`](../src/script_a.py); timestamps are from the final edit.", "",
       "Structure: **HOOK** (a real, specific problem in the first 15 s) → **promise** (what you'll get, and a reason to stay: \"stick around for habit four\") → "
       "**BODY** (5 habits; each one is *why* on the presenter, then *how* on screen) → **recap** → **CTA** (subscribe + the next video, timed to the end screen).", ""]
for sid, chap, shots, _ in SCENES:
    out += [f"## [{mmss(starts[sid])}] {chap} — {part.get(sid, 'BODY')}", ""]
    for kind, sents in shots:
        vis = {"host": "PRESENTER (green screen, café background)", "chart": "ANIMATED CHART", "logo": "LOGO STING (5 s)"}.get(kind[0]) or (f"SCREEN: prototype, {kind[1]} flow" if kind[0] == "rec" else f"TEXT CARD: {kind[1]}")
        out += [f"**{vis}**", ""] + [f"> {s}" for s in sents] + [""]
open("scripts/video-a-script.md", "w").write("\n".join(out))
print("\n".join(f"{'ok ' if ok else 'FAIL'} {n}" for n, ok in chk))
