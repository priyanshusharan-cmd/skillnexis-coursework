"""Builds the demo PDF library: the 10 typing-related PEPs (public domain / CC0) typeset as PDFs, so the knowledge base
ingests real multi-page PDFs (headings, paragraphs, code blocks) the same way it would company documents."""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer
from common.loaders import load_peps
TYPING = [484, 526, 585, 593, 604, 612, 673, 675, 681, 695]; S = getSampleStyleSheet()
esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
for d in load_peps(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "peps")):
    if d.metadata["pep"] not in TYPING: continue
    path = os.path.join("pdfs", f"pep-{d.metadata['pep']:04d}.pdf"); flow = [Paragraph(esc(f"PEP {d.metadata['pep']}: {d.metadata['title']}"), S["Title"]), Paragraph(esc(f"Status: {d.metadata['status']} · Created: {d.metadata['created']} · Public domain / CC0"), S["Italic"]), Spacer(1, 8)]
    for block in re.split(r"\n\s*\n", d.page_content):
        if block.startswith("    ") or block.count("\n") and all(l.startswith((" ", "\t")) for l in block.splitlines() if l): flow.append(Preformatted(block, S["Code"]))
        elif len(block) < 60 and "\n" not in block and not block.endswith("."): flow.append(Paragraph(esc(block), S["Heading2"]))
        else: flow.append(Paragraph(esc(" ".join(block.split())), S["BodyText"]))
    SimpleDocTemplate(path, pagesize=A4, title=f"PEP {d.metadata['pep']}").build(flow); print(path)
