"""SEO titles, descriptions and tags for the long-form and the 3 shorts, checked against YouTube's limits
(title <= 100 chars with the keyword early, description <= 5000, chapters start at 0:00 / >= 3 / each >= 10 s,
tags <= 500 chars, <= 15 hashtags; Shorts <= 60 s). Writes results/seo.md and results/seo.json."""
import json
E = json.load(open("results/edl.json"))["stats"]; S = json.load(open("results/shorts.json"))
mmss = lambda s: f"{int(s // 60)}:{int(s % 60):02d}"
ch = E["chapters"]
LONG = dict(
 title="Python If Else Explained for Beginners (elif, and/or, Common Mistakes)",
 description="\n".join([
  "Learn Python if, else and elif in under 7 minutes, with real code you can run. You'll build a grade checker, see why the ORDER of elif conditions matters, fix the two most common beginner errors (IndentationError and = vs ==), and combine conditions with and/or.",
  "", "CHAPTERS"] + [f"{mmss(a)} {n}" for a, n in ch] + [
  "", "PRACTICE: write a program that stores an age and prints \"Can vote\" if it's 18 or more, otherwise \"Not yet\". The solution is at the end of the Try it chapter.",
  "", "Previous lesson: Python variables, labelled boxes for values.", "Next lesson: loops (for and while).",
  "", "Code in Small Steps: one useful coding idea at a time. The presenter is an illustrated character and the voice is synthetic; all code output shown is real (Python 3.13).",
  "", "#python #learnpython #codinglesson"]),
 tags=["python if else", "python elif", "python for beginners", "if else statement python", "python conditions", "python tutorial", "learn python",
       "indentationerror python", "python comparison operators", "python and or", "coding for beginners", "python course", "code in small steps"])
SH = {
 "short-1-equals-vs-double-equals": dict(title="= vs == in Python: the #1 if-statement mistake #shorts", description="One equals sign stores, two compare. Python even tells you which one you meant. Full lesson on if/else on the channel. #python #learnpython #shorts"),
 "short-2-elif-order-matters": dict(title="Why 95 marks printed a C: elif order matters in Python #shorts", description="Python stops at the first true condition, so put the strictest check first. From the full if/else lesson. #python #coding #shorts"),
 "short-3-indentation-error": dict(title="Python IndentationError: the 4 spaces that matter #shorts", description="Indentation tells Python which lines belong to the if. Here's the error you get without it, and the fix. #python #learnpython #shorts")}
chk = []
def check(n, ok): chk.append((n, bool(ok))); assert ok, n
check(f"title {len(LONG['title'])} <= 100 chars", len(LONG["title"]) <= 100); check("keyword 'Python If Else' in first 40 chars", "Python If Else" in LONG["title"][:40])
check(f"description {len(LONG['description'])} <= 5000", len(LONG["description"]) <= 5000); check("first chapter at 0:00", ch[0][0] == 0); check(f"{len(ch)} chapters >= 3", len(ch) >= 3)
lens = [b[0] - a[0] for a, b in zip(ch, ch[1:] + [(E["total"], "")])]; check(f"shortest chapter {min(lens):.1f} s >= 10 s", min(lens) >= 10)
tl = sum(map(len, LONG["tags"])) + 2 * (len(LONG["tags"]) - 1); check(f"tags {tl} chars <= 500", tl <= 500); check("<= 15 hashtags", LONG["description"].count("#") <= 15)
check(f"long-form length {mmss(E['total'])} in 5-8 min", 300 <= E["total"] <= 480)
for k, v in SH.items(): check(f"{k}: title {len(v['title'])} <= 100, length {S[k]['duration']} s in 30-60", len(v["title"]) <= 100 and 30 <= S[k]["duration"] <= 60)
json.dump({"long_form": LONG, "shorts": SH, "checks": chk}, open("results/seo.json", "w"), indent=1, ensure_ascii=False)
md = ["# SEO package", "", f"## Long-form: `if-else-long-form.mp4` ({mmss(E['total'])})", "", f"**Title** ({len(LONG['title'])} characters)", "", "```", LONG["title"], "```", "", "**Description**", "", "```", LONG["description"], "```", "",
      f"**Tags** ({tl} characters)", "", "```", ", ".join(LONG["tags"]), "```", "", "**Thumbnail:** `thumbnails/yt-if-else.png` · **Captions:** `exports/if-else-long-form.srt` · **End screen:** link the variables lesson and the loops lesson", "",
      "## Shorts", ""]
for k, v in SH.items(): md += [f"### `{k}.mp4` ({S[k]['duration']} s) · cover `thumbnails/{S[k]['cover']}`", "", f"**Title:** {v['title']}", "", f"**Description:** {v['description']}", "", "Related video: the long-form lesson.", ""]
md += ["## Checks", ""] + [f"* {'✅' if ok else '❌'} {n}" for n, ok in chk]
open("results/seo.md", "w").write("\n".join(md) + "\n"); print("\n".join(n for n, _ in chk))
