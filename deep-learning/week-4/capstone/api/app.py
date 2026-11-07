"""Blood smear analyser API (FastAPI).
  GET  /health                 liveness, model loaded
  POST /analyze                field "file": a smear photo -> WBC boxes, platelet count, every accepted cell
                               (?annotated=true adds a PNG with the boxes drawn, base64; ?threshold= sets the WBC acceptance
                               probability, default 0.5; platelets use a fixed 0.97 tuned on the training images)
  POST /classify               field "file": one cell crop -> RBC / WBC / Platelets probabilities
Errors are JSON {"error": {"code", "message", "request_id"}}: 400 missing/empty, 413 > 8 MB, 415 not an image type,
422 corrupt image or bad parameter, 500 unexpected (logged, not leaked), 503 model missing.
Research/teaching demo, NOT a medical device: it was trained on 205 images from one public dataset."""
import base64, io, json, logging, os, sys, time, uuid
import numpy as np
from fastapi import FastAPI, File, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError
from starlette.exceptions import HTTPException as StarletteHTTPException
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from analyze import CLASSES, S, CellClassifier, analyze, draw
MAX_BYTES = 8 * 1024 * 1024; ACCEPT = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}
log = logging.getLogger("bccd-api"); logging.basicConfig(level=logging.INFO, format="%(message)s")
try: CLF, LOAD_ERR = CellClassifier(os.environ.get("MODEL_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "cells.tflite"))), None
except Exception as e: CLF, LOAD_ERR = None, str(e)
app = FastAPI(title="Blood smear analyser", version="1.0", description="WBC localisation + platelet count + cell-type classification. Not a medical device.")
STATS = dict(requests=0, analyses=0, errors=0, started=time.time())
class APIError(Exception):
    def __init__(s, status, code, message): s.status, s.code, s.message = status, code, message
def err(status, code, message, rid): return JSONResponse({"error": {"code": code, "message": message, "request_id": rid}}, status_code=status)
@app.middleware("http")
async def wrap(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]; request.state.rid = rid; t = time.perf_counter(); STATS["requests"] += 1
    try: resp = await call_next(request)
    except Exception as e: log.exception(json.dumps({"event": "unhandled", "request_id": rid, "error": repr(e)})); resp = err(500, "internal_error", "Something went wrong on our side", rid)
    if resp.status_code >= 400: STATS["errors"] += 1
    ms = (time.perf_counter() - t) * 1000; resp.headers["X-Request-ID"] = rid; resp.headers["X-Process-Time-ms"] = f"{ms:.1f}"
    log.info(json.dumps({"event": "request", "request_id": rid, "path": request.url.path, "status": resp.status_code, "ms": round(ms, 1)})); return resp
@app.exception_handler(APIError)
async def _api(request, e): return err(e.status, e.code, e.message, request.state.rid)
@app.exception_handler(RequestValidationError)
async def _val(request, e):
    missing = any(d["type"] == "missing" and d["loc"][-1] == "file" for d in e.errors())
    return err(400 if missing else 422, "missing_file" if missing else "invalid_request", "; ".join(f"{'.'.join(map(str, d['loc']))}: {d['msg']}" for d in e.errors()), request.state.rid)
@app.exception_handler(StarletteHTTPException)
async def _http(request, e): return err(e.status_code, "http_error", str(e.detail), getattr(request.state, "rid", "-"))
async def read_rgb(f: UploadFile):
    if f.content_type not in ACCEPT: raise APIError(415, "unsupported_media_type", f"'{f.content_type}' is not accepted; send JPEG, PNG, WebP, BMP or TIFF")
    data = await f.read(MAX_BYTES + 1)
    if not data: raise APIError(400, "empty_file", "The file is empty")
    if len(data) > MAX_BYTES: raise APIError(413, "file_too_large", "Larger than 8 MB")
    try: Image.open(io.BytesIO(data)).verify(); img = Image.open(io.BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError): raise APIError(422, "unreadable_image", "The image is corrupt or not really an image")
    if CLF is None: raise APIError(503, "model_unavailable", f"Model not loaded: {LOAD_ERR}")
    return img
@app.get("/health")
def health(): return dict(status="ok" if CLF else "degraded", model_loaded=CLF is not None, uptime_s=round(time.time() - STATS["started"]), requests=STATS["requests"], analyses=STATS["analyses"], errors=STATS["errors"])
@app.post("/analyze")
async def analyze_smear(file: UploadFile = File(...), annotated: bool = Query(False), threshold: float = Query(.5, ge=.05, le=.99)):
    img = await read_rgb(file)
    if max(img.size) > 2000: img.thumbnail((2000, 2000))
    if min(img.size) < 200: raise APIError(422, "image_too_small", f"{img.size[0]}x{img.size[1]} is too small for a smear photo (need >= 200 px)")
    if img.size != (640, 480): log.info(json.dumps({"event": "warning", "msg": f"image {img.size}; the model was built on 640x480 smears at one magnification"}))
    rgb = np.asarray(img); r = analyze(rgb, CLF, threshold); STATS["analyses"] += 1
    r["warnings"] = [] if img.size == (640, 480) else ["The pipeline was tuned on 640x480 BCCD smears; other magnifications may give wrong counts."]
    if r["wbc_count"] == 0: r["warnings"].append("No WBC found. Check the stain and focus, or this field may simply contain none.")
    if annotated: b = io.BytesIO(); draw(rgb, r).save(b, "PNG"); r["annotated_png"] = base64.b64encode(b.getvalue()).decode()
    r["disclaimer"] = "Research/teaching demo, not a medical device."; return r
@app.post("/classify")
async def classify_cell(file: UploadFile = File(...)):
    img = await read_rgb(file); p = CLF(np.asarray(img.resize((S, S), Image.BILINEAR)))
    return dict(label=CLASSES[int(p.argmax())], probabilities=dict(zip(CLASSES, [round(float(v), 4) for v in p])))
