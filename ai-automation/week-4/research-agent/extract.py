"""Fetch a URL (or local file) and return the article: title, author, date, clean text. HTML goes through trafilatura's
main-content extraction (drops navigation, ads, footers); Markdown has its front matter, link syntax and code fences
cleaned. Polite fetching: a descriptive User-Agent, a timeout, and retries with back-off."""
import re, time
import requests
UA = "skillnexis-coursework-bot/1.0 (+https://github.com/priyanshusharan-cmd/skillnexis-coursework)"
def fetch(url, tries=3):
    if not url.startswith("http"): return open(url, encoding="utf-8").read(), "text/html" if url.endswith((".html", ".htm")) else "text/plain"
    for k in range(tries):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=20); r.raise_for_status()
            return r.text, r.headers.get("content-type", "")
        except requests.RequestException:
            if k == tries - 1: raise
            time.sleep(2 ** k)
def from_markdown(md):
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line: k, v = line.split(":", 1); meta[k.strip()] = v.strip().strip('"')
        md = md[m.end():]
    md = re.sub(r"```.*?```", " ", md, flags=re.S)                          # code blocks are not prose
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md); md = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"<[^>]+>", " ", md); md = re.sub(r"^#+\s*(.*)$", r"\n\1\n", md, flags=re.M); md = re.sub(r"[*_`]{1,3}", "", md)
    md = re.sub(r"^(\s*\d+)\.\s*$", "", md, flags=re.M)
    return dict(title=meta.get("title", ""), author=meta.get("author", ""), date=meta.get("date", "")[:10], text=re.sub(r"[ \t]+", " ", md).strip())
def from_rst(rst):
    """reStructuredText (e.g. Python PEPs): RFC-822 style header fields, ===/--- underlines, directives, roles, literal blocks."""
    head, _, body = rst.partition("\n\n"); meta = {}
    for line in head.splitlines():
        if re.match(r"^[A-Z][\w-]*:\s", line): k, v = line.split(":", 1); meta[k.strip().lower()] = v.strip()
    body = re.sub(r"::\n\n((?:[ \t]+.*\n|\n)+)", ".\n\n", body)                     # literal (code) blocks
    lines, keep, skip_ind = body.split("\n"), [], None                                    # directives (incl. indented ones) + their bodies
    for ln in lines:
        ind = len(ln) - len(ln.lstrip())
        if skip_ind is not None:
            if not ln.strip() or ind > skip_ind: continue
            skip_ind = None
        if re.match(r"^\s*\.\. ", ln): skip_ind = ind; continue
        keep.append(ln)
    body = "\n".join(keep)
    body = re.sub(r"^([=\-~^\"'`#*+]{3,})\s*$", "", body, flags=re.M)                  # section underlines
    body = re.sub(r":\w+:`([^`<]*?)\s*(?:<[^>]*>)?`", r"\1", body)                      # :pep:`text <7>` -> text
    body = re.sub(r"`([^`<]+?)\s*<[^>]+>`_+", r"\1", body); body = re.sub(r"``([^`]+)``", r"\1", body); body = re.sub(r"\[\d+\]_|`", "", body); body = re.sub(r"(?<!\w)\*{1,2}([^*\n]+)\*{1,2}", r"\1", body)
    return dict(title=meta.get("title", ""), author=re.sub(r"\s*<[^>]+>", "", meta.get("author", "")), date=meta.get("created", ""), text=body.strip())
def article(url):
    raw, ctype = fetch(url)
    if "html" in ctype or raw.lstrip().lower().startswith(("<!doctype", "<html")):
        import trafilatura
        doc = trafilatura.bare_extraction(raw, url=url if url.startswith("http") else None, include_comments=False, include_tables=False, with_metadata=True)
        d = doc.as_dict() if hasattr(doc, "as_dict") else dict(doc)
        out = dict(title=d.get("title") or "", author=d.get("author") or "", date=d.get("date") or "", text=d.get("text") or "")
    elif url.endswith(".rst") or re.match(r"^PEP: \d+", raw):
        out = from_rst(raw)
    else:
        out = from_markdown(raw)
    out["url"] = url; out["words"] = len(out["text"].split())
    if out["words"] < 80: raise ValueError(f"only {out['words']} words extracted from {url}; is it an article page?")
    return out
