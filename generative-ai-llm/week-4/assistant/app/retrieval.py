"""Knowledge base + hybrid retrieval, in memory (no external vector DB needed to deploy).
  * base corpus: 66 Python Enhancement Proposals (public domain / CC0) chunked to ~1,200 characters
  * user documents: PDFs, images (OCR) and text a user uploads, searchable only by that user
  * retrieval: BM25 (exact terms like ':=' or 'strict') + LSA embeddings (TF-IDF -> 256-d SVD; paraphrases),
    merged with reciprocal-rank fusion, at most 2 chunks per source document. With GEMINI_API_KEY you could swap in
    a hosted embedding model; LSA keeps the service free and offline.
The 'relevance' of a result (0-1) is reported so the domain guardrail can refuse questions the corpus can't answer."""
import glob, os, re, threading
import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from .text import content_words, words
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.environ.get("PEP_DIR", os.path.join(HERE, "..", "data", "peps"))
def clean_rst(body):
    keep, skip = [], None
    for ln in body.split("\n"):
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
def load_peps(folder=DATA):
    out = []
    for p in sorted(glob.glob(os.path.join(folder, "pep-*.rst"))):
        raw = open(p, encoding="utf-8").read(); head, _, body = raw.partition("\n\n"); meta = {}
        for line in head.splitlines():
            m = re.match(r"^([A-Z][\w-]*):\s*(.*)$", line)
            if m: meta[m.group(1).lower()] = m.group(2).strip()
        n = int(meta.get("pep", "0")); out.append(dict(source=f"PEP {n}", title=meta.get("title", ""), url=f"https://peps.python.org/pep-{n:04d}/", text=clean_rst(body)))
    return out
def chunk(text, size=1200, overlap=200):
    paras, out, cur = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()], [], ""
    for p in paras:
        while len(p) > size: out.append((cur + "\n\n" + p[:size]).strip() if cur else p[:size]); cur = ""; p = p[size - overlap:]
        if len(cur) + len(p) + 2 > size and cur: out.append(cur); cur = cur[-overlap:] + "\n\n" + p
        else: cur = (cur + "\n\n" + p).strip()
    if cur: out.append(cur)
    return out
class KnowledgeBase:
    def __init__(self, docs=None):
        docs = docs if docs is not None else load_peps(); self.lock = threading.Lock()
        self.chunks = [dict(source=d["source"], title=d["title"], url=d.get("url"), page=None, owner=None, text=c) for d in docs for c in chunk(d["text"])]
        self.vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english")
        X = self.vec.fit_transform([c["text"] for c in self.chunks]); self.svd = TruncatedSVD(256, random_state=0).fit(X)
        self._rebuild()
    def embed(self, texts):
        E = self.svd.transform(self.vec.transform(texts)); return E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
    def _rebuild(self):
        self.E = self.embed([c["text"] for c in self.chunks]); self.bm25 = BM25Okapi([content_words(c["text"]) or ["_"] for c in self.chunks])
    def add(self, owner, source, pieces, title=None):
        """pieces: [(text, page or None)] -> chunks visible only to `owner`. Returns the number of chunks added."""
        new = [dict(source=source, title=title or source, url=None, page=pg, owner=owner, text=c) for t, pg in pieces for c in chunk(t)]
        with self.lock: self.chunks += new; self._rebuild()
        return len(new)
    def remove(self, owner, source):
        with self.lock:
            n = len(self.chunks); self.chunks = [c for c in self.chunks if not (c["owner"] == owner and c["source"] == source)]; self._rebuild()
        return n - len(self.chunks)
    def documents(self, owner): return sorted({(c["source"], c["page"] is not None) for c in self.chunks if c["owner"] == owner})
    def search(self, q, owner=None, k=5):
        visible = np.array([c["owner"] in (None, owner) for c in self.chunks])
        sem = self.E @ self.embed([q])[0]; qt = content_words(q); bm = self.bm25.get_scores(qt) if qt else np.zeros(len(self.chunks))
        sem[~visible] = -9; bm[~visible] = -9; rrf = {}
        for r, i in enumerate(np.argsort(-sem)[:30]): rrf[i] = rrf.get(i, 0) + 1 / (60 + r)
        for r, i in enumerate(np.argsort(-bm)[:30]):
            rrf[i] = rrf.get(i, 0) + (2 if self.chunks[i]["owner"] is not None else 1) / (60 + r)   # user docs count twice here: LSA wasn't fitted on them
        pinned = set()
        for n in set(re.findall(r"\bPEP[\s-]*(\d{1,4})\b", q, re.I)):                 # an explicit "PEP 8" pins that document's best chunks
            own = [i for i, c in enumerate(self.chunks) if c["source"] == f"PEP {int(n)}" and visible[i]]
            for i in sorted(own, key=lambda i: -sem[i])[:2]: rrf[i] = rrf.get(i, 0) + 1 / 60; pinned.add(i)
        qs, out, per = set(qt), [], {}
        for i, _ in sorted(rrf.items(), key=lambda x: -x[1]):
            c = self.chunks[i]
            if per.get(c["source"], 0) >= 2: continue
            per[c["source"]] = per.get(c["source"], 0) + 1
            overlap = len(qs & set(content_words(c["text"]))) / (len(qs) or 1)            # share of the question's key words present
            rel = .5 * max(sem[i], 0) + .5 * overlap
            if c["owner"] is not None: rel = max(rel, overlap)                             # LSA was fitted on the PEPs only, so user documents rely on key-word overlap
            if i in pinned: rel = max(rel, .5)                                             # a PEP the user named is in scope by definition
            out.append(dict(c, relevance=round(float(rel), 3)))
            if len(out) == k: break
        return out
