"""Mini project: AI content repurposer. Blog post URL -> scrape -> AI -> X/Twitter thread, LinkedIn post, Instagram caption
-> one formatted Word document (+ Markdown and JSON). Platform rules are enforced after generation, whatever produced
the text: 280 characters per post (links count as 23, as on X), LinkedIn 3,000 characters with the hook in the first
~210 characters (what shows before "see more"), Instagram 2,200 characters and at most 30 hashtags.
    python src/repurpose.py URL [--posts 6] [--out outputs/]"""
import argparse, datetime, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import llm
from extract import article
from summarize import summarise, slug
PROMPT = """You are a social media editor. Repurpose the blog post below. Stay faithful to it: no invented facts, numbers or quotes.
Return JSON with exactly these keys:
{{"thread": ["{n} posts for X/Twitter, each under 260 characters; post 1 is a hook ending with 🧵, the last post points to the source link"],
  "linkedin": "a LinkedIn post: a hook line under 200 characters, a blank line, 2 short context sentences, 3 takeaways as lines starting with ✅, and a closing question; then 3 hashtags",
  "instagram": "an Instagram caption: 2 punchy lines, 3 short takeaways with emoji bullets, a 'save this' call to action, then 10-15 relevant hashtags"}}

TITLE: {title}
SOURCE LINK: {url}
POST:
{text}"""
def xlen(s): return len(re.sub(r"https?://\S+", "x" * 23, s))
def hashtags(kws, k):
    tags = []
    for w in kws:
        t = "#" + re.sub(r"[^a-z0-9]", "", w.title().replace(" ", ""), flags=re.I)
        if len(t) > 3 and t.lower() not in [x.lower() for x in tags]: tags.append(t)
    return tags[:k]
def offline(a, n):
    s = summarise(a, max(n - 1, 4) + 1); kw = llm.keywords(a["text"], 14); title = a["title"] or "this post"
    pts = [p for p in s["key_points"] if llm.shorten(p, 200) != s["tldr"]]
    thread = [llm.shorten(f"{title}: {s['tldr']}", 255) + " 🧵"]
    for i, p in enumerate(pts[: n - 2], 2): thread.append(llm.shorten(f"{i}/ {p}", 270))
    thread.append(f"{n}/ Full post, worth reading in full: {a['url']}")
    tl = hashtags(kw, 3); lead = llm.shorten(s["tldr"], 200)
    linkedin = "\n".join([lead, "", llm.shorten(f"I just read \"{title}\" and the core idea is worth sharing.", 200) + " Three takeaways:", ""] +
                         [f"✅ {llm.shorten(p, 180)}" for p in pts[:3]] + ["", f"Which of these matches your experience with {kw[0]}?", "", " ".join(tl)])
    insta = "\n".join([llm.shorten(title, 90) + " 👇", llm.shorten(s["tldr"], 160), ""] + [f"{e} {llm.shorten(p, 120)}" for e, p in zip(("💡", "🔍", "🚀"), pts[:3])] +
                      ["", "📌 Save this for later and share it with a friend who needs it.", "🔗 Full post: link in bio", "", " ".join(hashtags(kw, 14))])
    return dict(thread=thread, linkedin=linkedin, instagram=insta, engine=s["engine"].split(" ")[0] + " + templates", summary=s)
def generate(a, n):
    try:
        out, engine = llm.chat(PROMPT.format(n=n, title=a["title"], url=a["url"], text=a["text"][:20000]), temperature=.7, max_tokens=1600, json_mode=True)
        d = llm.parse_json(out); d["engine"] = engine; d["summary"] = summarise(a)
    except RuntimeError:
        d = offline(a, n)
    return enforce(d, a)
def enforce(d, a):
    """Platform limits, applied to any engine's output; records what was checked."""
    fixed = []
    for i, p in enumerate(d["thread"]):
        if xlen(p) > 280: d["thread"][i] = llm.shorten(p, 279 - (xlen(p) - len(p))); fixed.append(f"thread post {i + 1} shortened")
    if a["url"] not in " ".join(d["thread"]): d["thread"].append(f"Source: {a['url']}"); fixed.append("source link added to thread")
    li = d["linkedin"]; d["linkedin"] = li[:3000]
    tags = re.findall(r"#\w+", d["instagram"])
    if len(tags) > 30:
        for t in tags[30:]: d["instagram"] = d["instagram"].replace(" " + t, "")
        fixed.append("instagram hashtags trimmed to 30")
    d["instagram"] = d["instagram"][:2200]
    d["checks"] = dict(thread_posts=len(d["thread"]), max_post_chars=max(map(xlen, d["thread"])), linkedin_chars=len(d["linkedin"]),
                       linkedin_hook_chars=len(d["linkedin"].split("\n")[0]), instagram_chars=len(d["instagram"]), instagram_hashtags=len(re.findall(r"#\w+", d["instagram"])), fixes=fixed)
    return d
def to_docx(a, d, path):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor, Cm
    doc = Document(); st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11)
    for s in doc.sections: s.left_margin = s.right_margin = Cm(2.2)
    h = doc.add_heading("Content repurposing pack", 0)
    p = doc.add_paragraph(); r = p.add_run(a["title"]); r.bold = True; r.font.size = Pt(14)
    meta = doc.add_paragraph(); meta.add_run(f"Source: {a['url']}\nGenerated {datetime.date.today():%d %b %Y} · engine: {d['engine']} · {a['words']} words in source").font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    doc.add_heading("Summary", 1); doc.add_paragraph(d["summary"]["tldr"])
    for kp in d["summary"]["key_points"]: doc.add_paragraph(kp, style="List Bullet")
    doc.add_heading(f"X / Twitter thread ({len(d['thread'])} posts)", 1)
    t = doc.add_table(rows=1, cols=3); t.style = "Light Grid Accent 1"; hdr = t.rows[0].cells; hdr[0].text, hdr[1].text, hdr[2].text = "#", "Post", "Chars"
    for i, post in enumerate(d["thread"], 1):
        c = t.add_row().cells; c[0].text, c[1].text, c[2].text = str(i), post, str(xlen(post))
    t.autofit = False
    for i, w in enumerate((Cm(1), Cm(13.5), Cm(1.6))):
        t.columns[i].width = w
        for c in t.columns[i].cells: c.width = w
    doc.add_heading("LinkedIn post", 1)
    for line in d["linkedin"].split("\n"): doc.add_paragraph(line)
    doc.add_paragraph(f"{d['checks']['linkedin_chars']} characters; hook {d['checks']['linkedin_hook_chars']} characters (shown before 'see more').").runs[0].italic = True
    doc.add_heading("Instagram caption", 1)
    for line in d["instagram"].split("\n"): doc.add_paragraph(line)
    doc.add_paragraph(f"{d['checks']['instagram_chars']} characters · {d['checks']['instagram_hashtags']} hashtags").runs[0].italic = True
    doc.add_heading("Checks", 1)
    for k, v in d["checks"].items(): doc.add_paragraph(f"{k}: {v}", style="List Bullet")
    doc.save(path)
def to_md(a, d):
    L = [f"# Repurposed: {a['title']}", "", f"Source: {a['url']} · engine: `{d['engine']}`", "", "## X / Twitter thread", ""]
    L += [f"{i}. {p}  *({xlen(p)} chars)*" for i, p in enumerate(d["thread"], 1)]
    L += ["", "## LinkedIn", "", "```", d["linkedin"], "```", "", "## Instagram", "", "```", d["instagram"], "```", "", "## Checks", "", "```json", json.dumps(d["checks"], indent=1, ensure_ascii=False), "```"]
    return "\n".join(L) + "\n"
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("url"); ap.add_argument("--posts", type=int, default=6); ap.add_argument("--out", default="outputs"); o = ap.parse_args()
    a = article(o.url); d = generate(a, o.posts); base = os.path.join(o.out, "repurposed-" + slug(a["title"])); os.makedirs(o.out, exist_ok=True)
    to_docx(a, d, base + ".docx"); open(base + ".md", "w").write(to_md(a, d))
    json.dump({k: v for k, v in d.items() if k != "summary"} | {"source": a["url"], "title": a["title"]}, open(base + ".json", "w"), indent=1, ensure_ascii=False)
    print(to_md(a, d)); print("saved", base + ".docx/.md/.json")
