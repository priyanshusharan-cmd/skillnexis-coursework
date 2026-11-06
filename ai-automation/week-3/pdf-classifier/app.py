"""Upload service: POST PDFs, get topics back, and the files are filed into sorted/<topic>/.
    uvicorn app:app --port 8000   then open http://localhost:8000"""
import io, os, shutil
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from classify import classify_text, pdf_text
app = FastAPI(title="PDF topic classifier"); MAX = 15 * 1024 * 1024
PAGE = """<!doctype html><meta name=viewport content="width=device-width,initial-scale=1"><title>PDF classifier</title>
<style>body{font:16px system-ui;max-width:640px;margin:40px auto;padding:0 16px}pre{background:#f4f4f4;padding:12px;border-radius:8px;white-space:pre-wrap}</style>
<h1>Classify PDFs by topic</h1><form id=f><input type=file name=files accept=application/pdf multiple required> <button>Classify</button></form><pre id=o></pre>
<script>f.onsubmit=async e=>{e.preventDefault();o.textContent='…';const r=await fetch('/classify',{method:'POST',body:new FormData(f)});o.textContent=JSON.stringify(await r.json(),null,1)}</script>"""
@app.get("/", response_class=HTMLResponse)
def home(): return PAGE
@app.get("/health")
def health(): return {"ok": True}
@app.post("/classify")
async def classify(files: list[UploadFile] = File(...)):
    out = []
    for f in files:
        data = await f.read()
        if len(data) > MAX: raise HTTPException(413, f"{f.filename} is larger than 15 MB")
        if not data.startswith(b"%PDF"): out.append(dict(file=f.filename, topic="rejected", reason="not a PDF")); continue
        try: text, pages = pdf_text(io.BytesIO(data)); r = classify_text(text)
        except Exception as e: r, pages = dict(topic="rejected", reason=f"unreadable PDF: {e}"), 0
        name = os.path.basename(f.filename or "upload.pdf"); dest = os.path.join("sorted", r["topic"].replace("/", "-")); os.makedirs(dest, exist_ok=True)
        open(os.path.join(dest, name), "wb").write(data); out.append(dict(file=name, pages=pages, **r))
    return {"results": out}
