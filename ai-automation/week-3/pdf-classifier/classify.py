"""Classify PDFs by topic: extract text (pypdf) -> model -> topic + confidence; low confidence goes to review, no
text layer is rejected with a reason (it would need OCR). Copies each file into sorted/<topic>/ and writes a CSV report.
    python classify.py samples/ [--threshold 0.6]   ->  sorted/, results/classified.csv"""
import argparse, csv, os, shutil, sys
import joblib
from pypdf import PdfReader
HERE = os.path.dirname(os.path.abspath(__file__)); _m = None
def model():
    global _m
    if _m is None: _m = joblib.load(os.path.join(HERE, "model.joblib"))
    return _m
def pdf_text(path_or_file, max_pages=20):
    r = PdfReader(path_or_file); return " ".join((p.extract_text() or "") for p in r.pages[:max_pages]), len(r.pages)
def classify_text(text, threshold=0.6):
    words = len(text.split())
    if words < 20: return dict(topic="rejected", confidence=0.0, reason=f"only {words} words of text; scanned image? run OCR first", words=words)
    m = model(); p = m.predict_proba([text])[0]; order = p.argsort()[::-1]
    top, conf = m.classes_[order[0]], float(p[order[0]]); second = f"{m.classes_[order[1]]} {p[order[1]]:.2f}"
    # whole-document probabilities get overconfident on long text, so also vote over ~60-word chunks: a document
    # whose chunks disagree is mixed-topic and goes to review even if the overall score looks confident
    ws = text.split(); chunks = [" ".join(ws[i:i + 60]) for i in range(0, len(ws), 60) if len(ws[i:i + 60]) >= 20] or [text]
    votes = m.predict(chunks); share = float((votes == top).mean())
    mix = ", ".join(f"{c} {float((votes == c).mean()):.0%}" for c in m.classes_ if (votes == c).any())
    reason = "" if conf >= threshold and share >= .6 else (f"confidence {conf:.2f} < {threshold}" if conf < threshold else f"mixed topics across the document ({mix})")
    return dict(topic=top if not reason else "needs-review", predicted=top, confidence=round(conf, 3), chunk_agreement=round(share, 2), runner_up=second, words=words, reason=reason)
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("folder"); ap.add_argument("--threshold", type=float, default=0.6); ap.add_argument("--out", default="sorted"); o = ap.parse_args()
    rows = []
    for f in sorted(x for x in os.listdir(o.folder) if x.lower().endswith(".pdf")):
        try: text, pages = pdf_text(os.path.join(o.folder, f)); r = classify_text(text, o.threshold)
        except Exception as e: r, pages = dict(topic="rejected", confidence=0.0, reason=f"unreadable PDF: {e}"), 0
        dest = os.path.join(o.out, r["topic"].replace("/", "-")); os.makedirs(dest, exist_ok=True); shutil.copy2(os.path.join(o.folder, f), dest)
        rows.append(dict(file=f, pages=pages, **r)); print(f"{f:22} -> {r['topic']:13} {r['confidence']:.2f}  {r.get('runner_up', '')}  {r['reason']}")
    os.makedirs("results", exist_ok=True); keys = sorted({k for r in rows for k in r}, key=lambda k: ["file", "topic", "predicted", "confidence", "chunk_agreement", "runner_up", "pages", "words", "reason"].index(k))
    with open("results/classified.csv", "w", newline="") as fh: w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
