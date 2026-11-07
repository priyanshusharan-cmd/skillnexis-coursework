"""Multimodal document ingestion: PDF, images and plain text become searchable chunks for the uploading user.
  PDF   -> pypdf text per page; a PDF with no text layer at all (a scan) is rejected with a clear message
  image -> Gemini vision description when GEMINI_API_KEY is set, else Tesseract OCR (text, code, error screenshots);
           an image with no readable text is reported, not silently indexed
  text  -> .txt / .md / .rst as-is"""
import io
from PIL import Image
from .llm import describe_image
MAX_BYTES = 10 * 1024 * 1024
KINDS = {"application/pdf": "pdf", "image/png": "image", "image/jpeg": "image", "image/webp": "image", "text/plain": "text", "text/markdown": "text", "text/x-rst": "text"}
class IngestError(Exception):
    def __init__(s, status, code, msg): s.status, s.code, s.msg = status, code, msg
def ocr(img):
    import pytesseract
    d = pytesseract.image_to_data(img.convert("L"), output_type=pytesseract.Output.DICT)
    words = [w for w, c in zip(d["text"], d["conf"]) if w.strip() and float(c) > 50]; conf = [float(c) for w, c in zip(d["text"], d["conf"]) if w.strip() and float(c) > 50]
    text = pytesseract.image_to_string(img.convert("L")); return text.strip(), (sum(conf) / len(conf) if conf else 0.0), len(words)
def extract(name, mime, data):
    """-> (kind, [(text, page)], method)"""
    kind = KINDS.get(mime) or ("pdf" if name.lower().endswith(".pdf") else "text" if name.lower().endswith((".txt", ".md", ".rst")) else None)
    if kind is None: raise IngestError(415, "unsupported_media_type", f"'{mime}' is not supported; upload PDF, PNG, JPEG, WebP or plain text")
    if not data: raise IngestError(400, "empty_file", "The file is empty")
    if len(data) > MAX_BYTES: raise IngestError(413, "file_too_large", "Larger than 10 MB")
    if kind == "text":
        try: return kind, [(data.decode("utf-8"), None)], "text"
        except UnicodeDecodeError: raise IngestError(422, "unreadable_file", "Text files must be UTF-8")
    if kind == "pdf":
        from pypdf import PdfReader
        try: reader = PdfReader(io.BytesIO(data)); pages = [(p.extract_text() or "", i) for i, p in enumerate(reader.pages, 1)]
        except Exception: raise IngestError(422, "unreadable_file", "The PDF is corrupt or encrypted")
        good = [(t, i) for t, i in pages if len(t.strip()) > 20]
        if not good: raise IngestError(422, "no_text", f"None of the {len(pages)} pages has a text layer (a scanned PDF); upload page images instead to OCR them")
        return kind, good, f"pdf text ({len(good)}/{len(pages)} pages)"
    try: img = Image.open(io.BytesIO(data)); img.load()
    except Exception: raise IngestError(422, "unreadable_file", "The image is corrupt")
    desc = None
    try: desc = describe_image(data, mime)
    except Exception: desc = None
    if desc: return kind, [(desc, None)], "gemini vision"
    if max(img.size) < 1000: img = img.resize((img.width * 2, img.height * 2))       # small screenshots OCR better upscaled
    text, conf, n = ocr(img)
    if n < 3: raise IngestError(422, "no_text", "No readable text found in the image (OCR). With GEMINI_API_KEY set, images are described by a vision model instead")
    return kind, [(text, None)], f"tesseract ocr (mean confidence {conf:.0f})"
