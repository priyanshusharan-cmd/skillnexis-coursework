"""Builds sample PDFs to classify: 12 'news digest' PDFs (3 per topic, 6 test-set articles each, never seen in
training), one mixed-topic PDF (should go to review) and one image-only PDF with no text layer (should be rejected
with a clear reason).   python make_samples.py -> samples/*.pdf, samples/answer_key.csv"""
import csv, os, random
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from PIL import Image, ImageDraw
LABELS = ["World", "Sports", "Business", "Sci/Tech"]; os.makedirs("samples", exist_ok=True); rnd = random.Random(7); S = getSampleStyleSheet()
d = pd.read_csv("data/test.csv", header=None, names=["label", "title", "desc"]); d["desc"] = d["desc"].str.replace("\\", " ", regex=False).str.replace(r"#\d+;", " ", regex=True)
def pdf(path, heading, rows):
    doc = SimpleDocTemplate(path, pagesize=A4, title=heading); flow = [Paragraph(heading, S["Title"]), Spacer(1, 10)]
    for t, s in rows: flow += [Paragraph(t.replace("&", "&amp;"), S["Heading3"]), Paragraph(s.replace("&", "&amp;").replace("<", "&lt;"), S["BodyText"]), Spacer(1, 6)]
    doc.build(flow)
key = []; used = set()
for li, lab in enumerate(LABELS):
    pool = d[d["label"] == li + 1].index.tolist(); rnd.shuffle(pool)
    for k in range(3):
        idx = pool[k * 6:(k + 1) * 6]; used |= set(idx); name = f"digest-{chr(97 + li * 3 + k)}.pdf"      # neutral names: the file name gives nothing away
        pdf(f"samples/{name}", "News digest", [(d.title[i], d.desc[i]) for i in idx]); key.append((name, lab))
mixed = [i for li in range(4) for i in d[d["label"] == li + 1].index.tolist()[-2:]]
pdf("samples/digest-mixed.pdf", "News digest", [(d.title[i], d.desc[i]) for i in mixed]); key.append(("digest-mixed.pdf", "mixed (expect review)"))
img = Image.new("RGB", (1240, 1754), "white"); ImageDraw.Draw(img).text((100, 100), "Scanned page: no text layer", fill="black"); img.save("samples/scan-no-text.pdf"); key.append(("scan-no-text.pdf", "no text (expect rejection)"))
with open("samples/answer_key.csv", "w", newline="") as f: csv.writer(f).writerows([("file", "true_topic")] + key)
print(len(key), "sample PDFs")
