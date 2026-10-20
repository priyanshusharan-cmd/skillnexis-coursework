"""Create a local HTML digest from a JSON list: [{"title":"...","url":"...","summary":"..."}]."""
import html, json, sys
from pathlib import Path
src=Path(sys.argv[1] if len(sys.argv)>1 else "items.json")
items=json.loads(src.read_text(encoding="utf-8"))
if not isinstance(items,list): raise SystemExit("Expected a JSON list")
parts=[]
for item in items:
    title=html.escape(str(item.get("title","Untitled")))
    summary=html.escape(str(item.get("summary","")))
    url=html.escape(str(item.get("url","")),quote=True)
    link=f'<a href="{url}">{title}</a>' if url.startswith(("https://","http://")) else title
    parts.append(f"<article><h2>{link}</h2><p>{summary}</p></article>")
out="<!doctype html><meta charset='utf-8'><title>Daily digest</title><h1>Daily digest</h1>"+"".join(parts)
Path("digest.html").write_text(out,encoding="utf-8")
print("Wrote digest.html; no email was sent.")
