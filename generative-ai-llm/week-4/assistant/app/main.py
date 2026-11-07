"""PEP Assistant API: a domain assistant for Python language standards (PEPs) and the user's own documents.
RAG with citations, conversation memory, multimodal uploads, guardrails, hallucination checks, token streaming,
API-key auth, per-user budgets, and usage/cost analytics. Interactive docs at /docs (Swagger) and /redoc."""
import itertools, json, logging, os, re, time, uuid
from collections import defaultdict, deque
from typing import Literal, Optional
from fastapi import Depends, FastAPI, File, Header, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from . import grounding, guardrails, ingest, memory, store, usage
from .llm import provider, stream_answer
from .retrieval import KnowledgeBase
log = logging.getLogger("assistant"); logging.basicConfig(level=logging.INFO, format="%(message)s")
HERE = os.path.dirname(os.path.abspath(__file__)); RATE = int(os.environ.get("RATE_LIMIT_PER_MIN", 30))
TAGS = [dict(name="chat", description="Ask questions; answers are grounded in PEPs and your documents, with citations."),
        dict(name="documents", description="Upload PDFs, images (OCR / vision) or text to search them in chat."),
        dict(name="sessions", description="Conversation memory."), dict(name="usage", description="Your tokens and cost."),
        dict(name="admin", description="Analytics for admins."), dict(name="tools", description="Standalone checks.")]
app = FastAPI(title="PEP Assistant API", version="1.0.0", openapi_tags=TAGS,
              description="A domain assistant for **Python Enhancement Proposals** and your own documents.\n\n"
                          "**Auth:** send your API key as `Authorization: Bearer <key>` (or `X-API-Key`).\n\n"
                          "**Errors** are JSON: `{\"error\": {\"code\", \"message\", \"request_id\"}}`.\n\n"
                          "**Streaming:** `POST /v1/chat` with `\"stream\": true` returns Server-Sent Events: `meta`, many `token`, then `done`.")
store.init(); KB = KnowledgeBase()
for d in store.all_document_texts():
    try: KB.add(d["user_id"], d["name"], json.loads(d["text"]))
    except Exception as e: log.warning(json.dumps({"event": "reindex_failed", "doc": d["name"], "error": str(e)}))
if os.environ.get("ADMIN_KEY") and not store.user_by_key(os.environ["ADMIN_KEY"]):      # bootstrap an admin from a secret env var
    with store.conn() as c: c.execute("INSERT OR IGNORE INTO users(name,key_hash,role,daily_token_limit,created) VALUES('admin',?,'admin',10000000,?)", (store.h(os.environ["ADMIN_KEY"]), store.now()))
class APIError(Exception):
    def __init__(s, status, code, message, headers=None): s.status, s.code, s.message, s.headers = status, code, message, headers
def err(status, code, message, rid, headers=None): return JSONResponse({"error": {"code": code, "message": message, "request_id": rid}}, status_code=status, headers=headers)
@app.middleware("http")
async def mw(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]; request.state.rid = rid; t = time.perf_counter()
    try: resp = await call_next(request)
    except Exception as e: log.exception(json.dumps({"event": "unhandled", "request_id": rid, "error": repr(e)})); resp = err(500, "internal_error", "Something went wrong on our side", rid)
    resp.headers["X-Request-ID"] = rid; resp.headers["X-Process-Time-ms"] = f"{(time.perf_counter() - t) * 1000:.1f}"
    log.info(json.dumps({"event": "request", "request_id": rid, "method": request.method, "path": request.url.path, "status": resp.status_code})); return resp
@app.exception_handler(APIError)
async def _api(request, e): return err(e.status, e.code, e.message, request.state.rid, e.headers)
@app.exception_handler(RequestValidationError)
async def _val(request, e): return err(422, "invalid_request", "; ".join(f"{'.'.join(map(str, d['loc']))}: {d['msg']}" for d in e.errors()), request.state.rid)
@app.exception_handler(StarletteHTTPException)
async def _http(request, e): return err(e.status_code, "http_error", str(e.detail), getattr(request.state, "rid", "-"))
HITS = defaultdict(deque)
def user(authorization: Optional[str] = Header(None, description="Bearer <API key>"), x_api_key: Optional[str] = Header(None)):
    key = x_api_key or (authorization[7:] if authorization and authorization.lower().startswith("bearer ") else None)
    if not key: raise APIError(401, "unauthorized", "Missing API key: send 'Authorization: Bearer <key>'", {"WWW-Authenticate": "Bearer"})
    u = store.user_by_key(key)
    if not u: raise APIError(401, "unauthorized", "Invalid API key", {"WWW-Authenticate": "Bearer"})
    q, now = HITS[u["id"]], time.time()
    while q and now - q[0] > 60: q.popleft()
    if len(q) >= RATE: raise APIError(429, "rate_limited", f"More than {RATE} requests per minute", {"Retry-After": "60"})
    q.append(now); return u
def admin(u=Depends(user)):
    if u["role"] != "admin": raise APIError(403, "forbidden", "Admin only")
    return u
class ChatIn(BaseModel):
    message: str = Field(..., examples=["What does the walrus operator := do?"], description="The user's question (max 2,000 characters)")
    session_id: Optional[str] = Field(None, description="Reuse to keep conversation memory; omitted = a new session", examples=["demo-1"])
    stream: bool = Field(False, description="true = Server-Sent Events token stream")
    top_k: int = Field(5, ge=1, le=10, description="How many source chunks to retrieve")
class Source(BaseModel):
    n: int; source: str; title: Optional[str] = None; page: Optional[int] = None; url: Optional[str] = None; relevance: float
class ChatOut(BaseModel):
    session_id: str; answer: str; status: Literal["ok", "off_domain", "blocked"]; sources: list[Source]
    grounding: dict = Field(description="Hallucination check: share of supported sentences, per-sentence evidence, flagged")
    usage: dict = Field(description="prompt/completion tokens (exact or estimated), cost in USD, provider, model")
    redacted: list[str] = Field(description="Kinds of personal data removed from the question")
    warnings: list[str]
def _sources(hits): return [dict(n=i, source=h["source"], title=h["title"], page=h.get("page"), url=h.get("url"), relevance=h["relevance"]) for i, h in enumerate(hits, 1)]
def _chat(u, body):
    """Generator of (event, data) for one chat turn; shared by the JSON and the streaming endpoints."""
    t0 = time.perf_counter(); sid = body.session_id or uuid.uuid4().hex[:10]
    if store.tokens_today(u["id"]) >= u["daily_token_limit"]: raise APIError(429, "budget_exceeded", f"Daily token budget of {u['daily_token_limit']:,} reached; it resets at 00:00 UTC")
    g = guardrails.check_input(body.message)
    if not g["allowed"]:
        store.log_usage(user_id=u["id"], session=sid, endpoint="chat", provider="-", model="-", prompt_tokens=0, completion_tokens=0, exact=0, cost_usd=0, latency_ms=(time.perf_counter() - t0) * 1000,
                        ttft_ms=None, status="blocked", guardrail=";".join(g["reasons"] + [f"redacted:{r}" for r in g["redacted"]]), grounded=None, flagged=0, top_source=None)
        raise APIError(400, "guardrail_blocked", "Message blocked: " + ", ".join(g["reasons"]))
    q = g["text"]; hits = KB.search(re.sub(r"\[REDACTED \w+\]", " ", memory.standalone(u["id"], sid, q)), owner=u["id"], k=body.top_k); kind, model = provider()
    warnings = [f"Removed {', '.join(g['redacted'])} from your message before processing."] if g["redacted"] else []
    yield "meta", dict(session_id=sid, sources=_sources(hits), redacted=g["redacted"], provider=kind, model=model)
    if not hits or max(h["relevance"] for h in hits) < guardrails.DOMAIN_MIN:
        ans = "I can only answer questions about Python Enhancement Proposals (PEPs) and the documents you've uploaded, and I couldn't find anything relevant to that."
        for w in re.findall(r"\S+\s*", ans): yield "token", w
        memory.remember(u["id"], sid, q, ans); ms = (time.perf_counter() - t0) * 1000
        store.log_usage(user_id=u["id"], session=sid, endpoint="chat", provider=kind, model=model, prompt_tokens=0, completion_tokens=0, exact=0, cost_usd=0, latency_ms=ms, ttft_ms=ms,
                        status="off_domain", guardrail="off_domain" + "".join(f";redacted:{r}" for r in g["redacted"]), grounded=None, flagged=0, top_source=None)
        yield "done", dict(session_id=sid, answer=ans, status="off_domain", sources=[], grounding=dict(grounded=1.0, abstained=True, sentences=[], flagged=False),
                           usage=dict(prompt_tokens=0, completion_tokens=0, cost_usd=0.0, provider=kind, model=model, exact=False), redacted=g["redacted"], warnings=warnings); return
    parts, buf, ttft, use = [], "", None, {}
    for ev, val in stream_answer(q, hits, memory.context(u["id"], sid), KB):
        if ev == "usage": use = val; continue
        if ttft is None: ttft = (time.perf_counter() - t0) * 1000
        buf += val
        if re.search(r"\s$", buf): out, _ = guardrails.check_output(buf); parts.append(out); yield "token", out; buf = ""
    if buf: out, _ = guardrails.check_output(buf); parts.append(out); yield "token", out
    ans = "".join(parts).strip(); gr = grounding.check(ans, hits, KB)
    if gr["flagged"]: warnings.append(f"Only {gr['grounded']:.0%} of this answer is supported by the sources; check the cited passages.")
    c = usage.cost(use["provider"], use["model"], use["prompt_tokens"], use["completion_tokens"]); ms = (time.perf_counter() - t0) * 1000
    memory.remember(u["id"], sid, q, ans)
    store.log_usage(user_id=u["id"], session=sid, endpoint="chat", provider=use["provider"], model=use["model"], prompt_tokens=use["prompt_tokens"], completion_tokens=use["completion_tokens"],
                    exact=int(use["exact"]), cost_usd=c, latency_ms=ms, ttft_ms=ttft, status="ok", guardrail=";".join(f"redacted:{r}" for r in g["redacted"]) + (";ungrounded" if gr["flagged"] else ""),
                    grounded=gr["grounded"], flagged=int(gr["flagged"]), top_source=hits[0]["source"])
    yield "done", dict(session_id=sid, answer=ans, status="ok", sources=_sources(hits), grounding=gr, usage=dict(use, cost_usd=c), redacted=g["redacted"], warnings=warnings)
@app.post("/v1/chat", tags=["chat"], response_model=ChatOut, responses={200: {"content": {"text/event-stream": {}}, "description": "JSON, or an SSE stream when stream=true"},
          400: {"description": "guardrail_blocked"}, 401: {"description": "unauthorized"}, 429: {"description": "rate_limited / budget_exceeded"}})
def chat(body: ChatIn, u=Depends(user)):
    """Ask a question. Retrieval-augmented, cited, memory-aware, guarded and hallucination-checked."""
    gen = _chat(u, body)
    if not body.stream:
        done = None
        for ev, data in gen:
            if ev == "done": done = data
        return done
    first = next(gen)                                         # raise auth/budget/guardrail errors as JSON before streaming starts
    def sse():
        for ev, data in itertools.chain([first], gen): yield f"event: {ev}\ndata: {json.dumps(data if ev != 'token' else {'t': data})}\n\n"
    return StreamingResponse(sse(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
@app.post("/v1/documents", tags=["documents"], status_code=201)
async def upload(file: UploadFile = File(..., description="PDF, PNG/JPEG/WebP image, or UTF-8 text"), u=Depends(user)):
    """Add a document to your private knowledge base. Images are OCR'd (or described by Gemini vision when configured)."""
    data = await file.read(ingest.MAX_BYTES + 1)
    try: kind, pieces, method = ingest.extract(file.filename or "upload", file.content_type, data)
    except ingest.IngestError as e: raise APIError(e.status, e.code, e.msg)
    name = os.path.basename(file.filename or f"upload-{uuid.uuid4().hex[:6]}"); KB.remove(u["id"], name)
    n = KB.add(u["id"], name, pieces, title=name); store.delete_document(u["id"], name); store.add_document(u["id"], name, kind, len(pieces), n, method, json.dumps(pieces))
    return dict(name=name, kind=kind, pages=len(pieces), chunks=n, method=method, preview=pieces[0][0][:300])
@app.get("/v1/documents", tags=["documents"])
def list_documents(u=Depends(user)):
    """List your uploaded documents (name, kind, pages, chunks, extraction method)."""
    return store.documents(u["id"])
@app.delete("/v1/documents/{name}", tags=["documents"])
def delete_document(name: str, u=Depends(user)):
    """Delete one of your documents and its chunks."""
    n = KB.remove(u["id"], name)
    if not store.delete_document(u["id"], name): raise APIError(404, "not_found", f"No document called '{name}'")
    return dict(deleted=name, chunks=n)
@app.get("/v1/sessions", tags=["sessions"])
def list_sessions(u=Depends(user)):
    """Your conversations, newest first."""
    return store.sessions(u["id"])
@app.get("/v1/sessions/{session_id}", tags=["sessions"])
def get_session(session_id: str, u=Depends(user)):
    """A conversation's messages and its running summary (the memory the assistant uses)."""
    h = store.history(u["id"], session_id)
    if not h: raise APIError(404, "not_found", "No such session")
    return dict(session_id=session_id, summary=store.get_summary(u["id"], session_id), messages=h)
@app.delete("/v1/sessions/{session_id}", tags=["sessions"])
def forget_session(session_id: str, u=Depends(user)):
    """Delete a conversation and its memory."""
    return dict(deleted_messages=store.delete_session(u["id"], session_id))
@app.get("/v1/usage", tags=["usage"])
def my_usage(u=Depends(user)):
    """Your tokens (exact when the provider reports them, else estimated), cost, budget, latency and grounding stats."""
    s = usage.summary(store.usage_rows(u["id"])); s.pop("by_user", None)
    return dict(user=u["name"], tokens_today=store.tokens_today(u["id"]), daily_token_limit=u["daily_token_limit"], **s)
class CheckIn(BaseModel):
    answer: str = Field(..., examples=["The walrus operator := assigns a value inside an expression [1]."])
    question: Optional[str] = Field(None, description="If sources are omitted, they are retrieved for this question")
    sources: Optional[list[str]] = Field(None, description="Source passages; [1] refers to the first")
@app.post("/v1/check", tags=["tools"])
def check(body: CheckIn, u=Depends(user)):
    """Hallucination check for any answer: which sentences are supported by the sources, with evidence."""
    if body.sources: hits = [dict(source=f"source {i}", title="", text=t) for i, t in enumerate(body.sources, 1)]
    elif body.question: hits = KB.search(body.question, owner=u["id"])
    else: raise APIError(422, "invalid_request", "Give either sources or a question")
    return grounding.check(body.answer, hits, KB)
@app.get("/admin/analytics", tags=["admin"])
def analytics(days: int = Query(30, ge=1, le=365), u=Depends(admin)):
    """Service-wide usage, cost, latency, guardrail and grounding analytics (feeds /dashboard)."""
    import datetime
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).isoformat()
    return dict(usage.summary(store.usage_rows(since=since)), documents=len(store.documents()), provider="/".join(provider()))
@app.post("/admin/users", tags=["admin"], status_code=201)
def create_user(name: str = Query(..., min_length=2, max_length=40), role: Literal["user", "admin"] = "user", daily_token_limit: int = Query(200_000, ge=1000), u=Depends(admin)):
    """Create a user and return their API key (shown once)."""
    try: key = store.create_user(name, role, daily_token_limit)
    except Exception: raise APIError(409, "conflict", f"User '{name}' already exists")
    return dict(name=name, role=role, api_key=key, note="Store this key now; only its hash is kept.")
@app.get("/health", tags=["tools"])
def health():
    """Liveness, knowledge-base size and the active answer engine (no auth)."""
    kind, model = provider(); return dict(status="ok", chunks=len(KB.chunks), provider=kind, model=model)
@app.get("/", include_in_schema=False)
def home(): return FileResponse(os.path.join(HERE, "static", "chat.html"))
@app.get("/dashboard", include_in_schema=False)
def dashboard(): return FileResponse(os.path.join(HERE, "static", "dashboard.html"))
