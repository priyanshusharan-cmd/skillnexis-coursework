"""PEP loader: Python Enhancement Proposals are public domain or CC0, so they make a legal, realistic corpus
(design documents with real technical content). Parses the RFC-822 header and turns reST into clean text."""
import glob, os, re
from langchain_core.documents import Document
def clean_rst(body):
    lines, keep, skip = body.split("\n"), [], None
    for ln in lines:
        ind = len(ln) - len(ln.lstrip())
        if skip is not None:
            if not ln.strip() or ind > skip: continue
            skip = None
        if re.match(r"^\s*\.\. ", ln): skip = ind; continue
        keep.append(ln)
    t = "\n".join(keep)
    t = re.sub(r"^([=\-~^\"'`#*+]{3,})\s*$", "", t, flags=re.M); t = re.sub(r":\w+:`([^`<]*?)\s*(?:<[^>]*>)?`", r"\1", t)
    t = re.sub(r"`([^`<]+?)\s*<[^>]+>`_+", r"\1", t); t = re.sub(r"``([^`]+)``", r"\1", t); t = re.sub(r"\[\d+\]_|`", "", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()
def load_peps(folder):
    docs = []
    for p in sorted(glob.glob(os.path.join(folder, "pep-*.rst"))):
        raw = open(p, encoding="utf-8").read(); head, _, body = raw.partition("\n\n"); meta = {}
        for line in head.splitlines():
            m = re.match(r"^([A-Z][\w-]*):\s*(.*)$", line)
            if m: meta[m.group(1).lower()] = m.group(2).strip()
        n = int(meta.get("pep", "0")); docs.append(Document(page_content=clean_rst(body), metadata=dict(source=f"PEP {n}", pep=n, title=meta.get("title", ""), status=meta.get("status", ""),
                                                   type=meta.get("type", ""), created=meta.get("created", ""), url=f"https://peps.python.org/pep-{n:04d}/")))
    return docs
