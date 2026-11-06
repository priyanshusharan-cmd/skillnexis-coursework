# Channel analytics

## 1 · Pre-launch quality check (measured)

| Video | Length | Loudness (target −14 LUFS) | True peak | Speech captioned | Title / 100 | Description / 5000 | Tags / 500 |
|---|---|---|---|---|---|---|---|
| `01-python-variables.mp4` | 5:23 | -13.9 LUFS | -1.5 dBTP | 84 % of content time | 56 | 1102 | 228 |
| `02-read-python-errors.mp4` | 3:24 | -14.1 LUFS | -1.7 dBTP | 91 % of content time | 70 | 923 | 219 |
| `03-python-if-else.mp4` | 5:24 | -14.3 LUFS | -1.5 dBTP | 82 % of content time | 70 | 963 | 237 |

| Short | Length (30–60 s) |
|---|---|
| `short-1-equals-vs-double-equals.mp4` | 34.3 s ✅ |
| `short-2-elif-order-matters.mp4` | 44.7 s ✅ |
| `short-3-indentation-error.mp4` | 45.4 s ✅ |
| `short-4-why-5-plus-2-is-52.mp4` | 57.9 s ✅ |
| `short-5-read-errors-bottom-up.mp4` | 44.9 s ✅ |

## 2 · First-week performance

**Not available yet.** These numbers only exist after the videos are public on a real channel, and none are invented here.
After 7 days: YouTube Studio → Analytics → *Advanced mode* → Content → set the date range to the first 7 days → Export → CSV.
Save `Table data.csv` as `analytics/first-week.csv`, then run `python src/analytics.py`.

**What to read first and what counts as good for a new channel's first week** (no subscriber base yet):

| Metric | Where | Healthy first-week sign | If it's low |
|---|---|---|---|
| Impressions click-through rate | Reach tab | 4–10 % | Test the second thumbnail or title (Studio's *Test & compare*) |
| Average percentage viewed | Engagement tab | ≥ 40 % for a 5-minute lesson | Check the retention graph for the first drop; tighten the intro |
| First-30-seconds retention | Retention graph | ≥ 60 % still watching | Hook too slow: start with the puzzle, not the greeting |
| Shorts: viewed vs swiped away | Shorts analytics | ≥ 60 % viewed | Rework the first 2 s (hook text and movement) |
| Playlist continuation (01 → 03) | Playlist report | Rising week on week | Strengthen the end-screen call to action |
| Comments with practice answers | Comments | Any | Ask a specific question pinned in the comments |
