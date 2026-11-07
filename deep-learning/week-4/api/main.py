"""Task 4: deploy the optimised model as a REST API (FastAPI) with proper error handling.
Serves the int8 TFLite CIFAR-10 classifier from task 3 (falls back to the float32 .tflite if that is what's present).

  GET  /health            liveness + model loaded + uptime
  GET  /model             model metadata (classes, input size, file, size)
  POST /predict           multipart field "file": one image -> top-k classes with probabilities
  POST /predict/batch     multipart field "files": up to 16 images -> one result (or one error) per file

Error handling (every error is JSON: {"error": {"code", "message", "request_id"}}):
  400 no file / empty file · 413 file over 5 MB · 415 not an image type we accept · 422 unreadable or corrupt image,
  bad query parameter · 429 rate limit (60 requests/minute per client) · 500 unexpected (logged with the request id,
  no stack trace leaked to the client) · 503 model not loaded.
Every response carries X-Request-ID and X-Process-Time-ms; every request is logged as one JSON line.
    uvicorn api.main:app --port 8000      (docs at /docs)"""
import io, json, logging, os, time, uuid
from collections import defaultdict, deque
import numpy as np
from fastapi import FastAPI, File, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError
from starlette.exceptions import HTTPException as StarletteHTTPException
HERE = os.path.dirname(os.path.abspath(__file__)); MODELS = os.path.join(HERE, "..", "models")
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
MAX_BYTES, MAX_BATCH, RATE = 5 * 1024 * 1024, 16, int(os.environ.get("RATE_LIMIT_PER_MIN", 60))
ACCEPT = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/gif"}
log = logging.getLogger("api"); logging.basicConfig(level=logging.INFO, format="%(message)s")
class APIError(Exception):
    def __init__(s, status, code, message): s.status, s.code, s.message = status, code, message
class Model:
    def __init__(s):
        from ai_edge_litert.interpreter import Interpreter
        for name in (os.environ.get("MODEL_FILE", ""), "cifar_int8_full.tflite", "cifar_float32.tflite"):
            p = os.path.join(MODELS, name) if name else ""
            if p and os.path.exists(p): break
        else: raise FileNotFoundError("no .tflite model in models/ - run src/tflite_benchmark.py first")
        s.path = p; s.it = Interpreter(model_path=p, num_threads=1); s.it.allocate_tensors()
        s.i, s.o = s.it.get_input_details()[0], s.it.get_output_details()[0]
    def __call__(s, x):                                    # x: float32 (32, 32, 3) in 0..255
        i, o = s.i, s.o; x = x[None]
        if i["dtype"] == np.int8: sc, z = i["quantization"]; x = np.clip(np.round(x / sc + z), -128, 127).astype(np.int8)
        s.it.set_tensor(i["index"], x); s.it.invoke(); y = s.it.get_tensor(o["index"])[0]
        if o["dtype"] == np.int8: sc, z = o["quantization"]; y = (y.astype(np.float32) - z) * sc
        e = np.exp(y - y.max()); return e / e.sum()       # the network outputs logits
STATE = dict(model=None, started=time.time(), load_error=None)
try: STATE["model"] = Model()
except Exception as e: STATE["load_error"] = str(e); log.error(json.dumps({"event": "model_load_failed", "error": str(e)}))
app = FastAPI(title="CIFAR-10 image classifier", version="1.0", description="TFLite int8 model, week-4 deployment task. Every error is JSON with a request id.")
HITS = defaultdict(deque)
@app.middleware("http")
async def wrap(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]; request.state.rid = rid; t = time.perf_counter()
    client = request.client.host if request.client else "?"
    if request.url.path.startswith("/predict"):
        q = HITS[client]; now = time.time()
        while q and now - q[0] > 60: q.popleft()
        if len(q) >= RATE: resp = err(429, "rate_limited", f"More than {RATE} requests per minute; retry shortly", rid); resp.headers["Retry-After"] = "60"; return resp
        q.append(now)
    try: resp = await call_next(request)
    except Exception as e:                                # anything unexpected: log it, don't leak internals
        log.exception(json.dumps({"event": "unhandled", "request_id": rid, "error": repr(e)})); resp = err(500, "internal_error", "Something went wrong on our side", rid)
    ms = (time.perf_counter() - t) * 1000; resp.headers["X-Request-ID"] = rid; resp.headers["X-Process-Time-ms"] = f"{ms:.1f}"
    log.info(json.dumps({"event": "request", "request_id": rid, "method": request.method, "path": request.url.path, "status": resp.status_code, "ms": round(ms, 1), "client": client}))
    return resp
def err(status, code, message, rid): return JSONResponse({"error": {"code": code, "message": message, "request_id": rid}}, status_code=status)
@app.exception_handler(APIError)
async def api_error(request: Request, e: APIError): return err(e.status, e.code, e.message, request.state.rid)
@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, e: RequestValidationError):
    msg = "; ".join(f"{'.'.join(str(x) for x in d['loc'])}: {d['msg']}" for d in e.errors())
    code = "missing_file" if any(d["type"] == "missing" and d["loc"][-1] in ("file", "files") for d in e.errors()) else "invalid_request"
    return err(400 if code == "missing_file" else 422, code, msg, request.state.rid)
@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, e: StarletteHTTPException): return err(e.status_code, "http_error", str(e.detail), getattr(request.state, "rid", "-"))
async def read_image(f: UploadFile):
    if f.content_type not in ACCEPT: raise APIError(415, "unsupported_media_type", f"{f.filename}: type '{f.content_type}' is not accepted; send JPEG, PNG, WebP, BMP or GIF")
    data = await f.read(MAX_BYTES + 1)
    if not data: raise APIError(400, "empty_file", f"{f.filename}: the file is empty")
    if len(data) > MAX_BYTES: raise APIError(413, "file_too_large", f"{f.filename}: larger than {MAX_BYTES // (1024 * 1024)} MB")
    try:
        img = Image.open(io.BytesIO(data)); img.verify(); img = Image.open(io.BytesIO(data)).convert("RGB")   # verify() catches truncated files
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError): raise APIError(422, "unreadable_image", f"{f.filename}: the image is corrupt or not really a {f.content_type}")
    if min(img.size) < 8: raise APIError(422, "image_too_small", f"{f.filename}: image is {img.size[0]}x{img.size[1]}; need at least 8x8")
    return img
def classify(img, k):
    m = STATE["model"]
    if m is None: raise APIError(503, "model_unavailable", "The model is not loaded: " + str(STATE["load_error"]))
    w, h = img.size; s = min(w, h); img = img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((32, 32), Image.BILINEAR)   # centre crop, keep aspect
    p = m(np.asarray(img, dtype=np.float32)); top = p.argsort()[::-1][:k]
    return dict(label=CLASSES[top[0]], confidence=round(float(p[top[0]]), 4), top_k=[dict(label=CLASSES[i], probability=round(float(p[i]), 4)) for i in top])
@app.get("/health")
def health(): return dict(status="ok" if STATE["model"] else "degraded", model_loaded=STATE["model"] is not None, uptime_s=round(time.time() - STATE["started"]))
@app.get("/model")
def model_info():
    m = STATE["model"]
    if m is None: raise APIError(503, "model_unavailable", "The model is not loaded: " + str(STATE["load_error"]))
    return dict(file=os.path.basename(m.path), size_kb=round(os.path.getsize(m.path) / 1024), input=[32, 32, 3], input_dtype=str(m.i["dtype"].__name__), classes=CLASSES,
                note="Trained on CIFAR-10 (32x32 photos of 10 object classes). Other kinds of image get a confident-looking but meaningless answer.")
@app.post("/predict")
async def predict(file: UploadFile = File(...), top_k: int = Query(3, ge=1, le=10)):
    img = await read_image(file); return dict(filename=file.filename, **classify(img, top_k))
@app.post("/predict/batch")
async def predict_batch(files: list[UploadFile] = File(...), top_k: int = Query(1, ge=1, le=10)):
    if len(files) > MAX_BATCH: raise APIError(413, "batch_too_large", f"{len(files)} files sent; at most {MAX_BATCH} per request")
    out = []
    for f in files:                                       # one bad file doesn't fail the whole batch
        try: out.append(dict(filename=f.filename, ok=True, **classify(await read_image(f), top_k)))
        except APIError as e: out.append(dict(filename=f.filename, ok=False, error={"code": e.code, "message": e.message}))
    return dict(count=len(out), succeeded=sum(r["ok"] for r in out), results=out)
