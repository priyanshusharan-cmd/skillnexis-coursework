"""Task 1: summarise any article URL with an AI API (Gemini or OpenAI-compatible; offline TextRank fallback).
    python src/summarize.py URL [--bullets 5] -> prints the summary and saves outputs/summary-<slug>.md"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import llm
from extract import article
PROMPT = """Summarise the article below for a busy reader.
Return JSON: {{"tldr": "one sentence, max 30 words", "key_points": ["{n} bullets, each max 25 words, concrete, no fluff"], "who_should_read": "one short sentence"}}
Use only facts from the article.

TITLE: {title}
ARTICLE:
{text}"""
def summarise(a, n=5):
    text = a["text"][:24000]
    try:
        out, engine = llm.chat(PROMPT.format(n=n, title=a["title"], text=text), system="You write accurate, faithful summaries.", json_mode=True)
        d = llm.parse_json(out); d["engine"] = engine; return d
    except RuntimeError:
        pts = llm.textrank(text, n); kw = llm.keywords(text, 6)
        return dict(tldr=llm.shorten(llm.textrank.best, 200), key_points=[llm.shorten(p, 220) for p in pts], who_should_read="Anyone interested in " + ", ".join(kw[:3]) + ".",
                    keywords=kw, engine="offline:textrank (extractive: key points are the article's own most central sentences)")
def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "article"
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("url"); ap.add_argument("--bullets", type=int, default=5); a_ = ap.parse_args()
    a = article(a_.url); s = summarise(a, a_.bullets)
    md = [f"# Summary: {a['title']}", "", f"*Source:* {a['url']}  ", f"*Length:* {a['words']} words · *Engine:* `{s['engine']}`", "", f"**TL;DR:** {s['tldr']}", "", "**Key points**", ""]
    md += [f"- {p}" for p in s["key_points"]] + ["", f"**Who should read it:** {s['who_should_read']}"]
    os.makedirs("outputs", exist_ok=True); path = f"outputs/summary-{slug(a['title'])}.md"; open(path, "w").write("\n".join(md) + "\n")
    print("\n".join(md)); print("\nsaved", path)
