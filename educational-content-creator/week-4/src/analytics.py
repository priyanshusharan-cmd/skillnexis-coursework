"""Channel analytics. Before launch it measures what can be measured honestly (pre-launch QC of every upload: length,
loudness, caption coverage, metadata limits). After the first week, export YouTube Studio → Analytics → Advanced mode
→ Content → Export → CSV, save the "Table data.csv" as analytics/first-week.csv and rerun: it builds the first-week
report (views, watch time, average view duration, % viewed, impressions CTR, subscribers) with charts.
    python src/analytics.py -> analytics/report.md (+ analytics/first-week.png once data exists)"""
import csv, glob, json, os, re, subprocess
def probe(p, k): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", f"format={k}", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
def lufs(p):
    e = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(e[e.rindex("{"):e.rindex("}") + 1]); return float(j["input_i"]), float(j["input_tp"])
def caption_cover(srt, dur):
    t = 0.0
    for a, b in re.findall(r"(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)", open(srt).read()):
        f = lambda s: sum(float(x) * m for x, m in zip(s.replace(",", ".").split(":"), (3600, 60, 1))); t += f(b) - f(a)
    return t / dur
rows = []
for j in sorted(glob.glob("upload/0*.json")):
    m = json.load(open(j)); i, tp = lufs(m["file"]); c = m["end_screen"]["start_s"]
    rows.append(dict(video=os.path.basename(m["file"]), length=f"{int(m['duration_s']) // 60}:{int(m['duration_s']) % 60:02d}", lufs=i, tp=tp,
                     captions=caption_cover(m["captions"], c), title=len(m["title"]), desc=len(m["description"]), tags=len(", ".join(m["tags"])), chapters=m["description"].count("\n0:") + m["description"].count("\n1:") + m["description"].count("\n2:") + m["description"].count("\n3:") + m["description"].count("\n4:")))
shorts = [(os.path.basename(p), probe(p, "duration")) for p in sorted(glob.glob("../week-3/exports/short-*.mp4") + glob.glob("exports/short-*.mp4"))]
L = ["# Channel analytics", "", "## 1 · Pre-launch quality check (measured)", "",
     "| Video | Length | Loudness (target −14 LUFS) | True peak | Speech captioned | Title / 100 | Description / 5000 | Tags / 500 |", "|---|---|---|---|---|---|---|---|"]
L += [f"| `{r['video']}` | {r['length']} | {r['lufs']:.1f} LUFS | {r['tp']:.1f} dBTP | {r['captions'] * 100:.0f} % of content time | {r['title']} | {r['desc']} | {r['tags']} |" for r in rows]
L += ["", "| Short | Length (30–60 s) |", "|---|---|"] + [f"| `{n}` | {d:.1f} s {'✅' if 30 <= d <= 60 else '❌'} |" for n, d in shorts]
data = "analytics/first-week.csv"
L += ["", "## 2 · First-week performance", ""]
if os.path.exists(data):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    R = [r for r in csv.DictReader(open(data, encoding="utf-8-sig")) if r.get("Content") not in ("Total", "")]
    num = lambda r, k: float(str(r.get(k, 0) or 0).replace(",", "").replace("%", ""))
    L += ["| Video | Views | Watch time (h) | Avg. view duration | Impressions | CTR | Subscribers |", "|---|---|---|---|---|---|---|"]
    L += [f"| {r['Video title'][:50]} | {num(r, 'Views'):.0f} | {num(r, 'Watch time (hours)'):.1f} | {r.get('Average view duration', '')} | {num(r, 'Impressions'):.0f} | {num(r, 'Impressions click-through rate (%)'):.1f} % | {num(r, 'Subscribers'):+.0f} |" for r in R]
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.5)); t = [r["Video title"][:22] + "…" for r in R]
    for a, k in zip(ax, ("Views", "Impressions click-through rate (%)", "Watch time (hours)")):
        a.barh(t, [num(r, k) for r in R], color="#E8590C"); a.set_title(k); a.invert_yaxis()
    fig.tight_layout(); fig.savefig("analytics/first-week.png", dpi=130); L += ["", "![First week](first-week.png)"]
else:
    L += ["**Not available yet.** These numbers only exist after the videos are public on a real channel, and none are invented here.",
          "After 7 days: YouTube Studio → Analytics → *Advanced mode* → Content → set the date range to the first 7 days → Export → CSV.",
          "Save `Table data.csv` as `analytics/first-week.csv`, then run `python src/analytics.py`.", "",
          "**What to read first and what counts as good for a new channel's first week** (no subscriber base yet):", "",
          "| Metric | Where | Healthy first-week sign | If it's low |", "|---|---|---|---|",
          "| Impressions click-through rate | Reach tab | 4–10 % | Test the second thumbnail or title (Studio's *Test & compare*) |",
          "| Average percentage viewed | Engagement tab | ≥ 40 % for a 5-minute lesson | Check the retention graph for the first drop; tighten the intro |",
          "| First-30-seconds retention | Retention graph | ≥ 60 % still watching | Hook too slow: start with the puzzle, not the greeting |",
          "| Shorts: viewed vs swiped away | Shorts analytics | ≥ 60 % viewed | Rework the first 2 s (hook text and movement) |",
          "| Playlist continuation (01 → 03) | Playlist report | Rising week on week | Strengthen the end-screen call to action |",
          "| Comments with practice answers | Comments | Any | Ask a specific question pinned in the comments |"]
open("analytics/report.md", "w").write("\n".join(L) + "\n"); print("\n".join(L[:14]))
