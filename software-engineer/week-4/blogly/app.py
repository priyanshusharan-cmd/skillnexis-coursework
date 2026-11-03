"""Blogly: blog SaaS backend. JWT auth, posts, comments, likes, pagination, search, rate limiting,
real-time updates over WebSocket, Prometheus metrics, JSON logs, and a web UI.

Run:   uvicorn blogly.app:app --reload   then open http://127.0.0.1:8000 (web app), /docs (Swagger), /status
Env:   BLOG_DB (default blog.db), JWT_SECRET (required outside tests), RATE_LIMIT_PER_MIN (default 60),
       LOGIN_LIMIT_PER_MIN (default 5), METRICS_TOKEN (optional: require it to read /metrics), LOG_LEVEL
"""
import math
import os
import re
import secrets
import sqlite3
from pathlib import Path
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import db as store
from . import observability
from .ratelimit import TokenBucket
from .realtime import Hub
from .security import create_token, decode_token, hash_password, verify_password


# ---------------------------------------------------------------- schemas
class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=30, examples=["priya_rao"])
    password: str = Field(min_length=8, max_length=72, examples=["correct-horse-battery"])

    @field_validator("username")
    @classmethod
    def username_chars(cls, v):
        if not re.fullmatch(r"[A-Za-z0-9_]+", v):
            raise ValueError("username may only contain letters, digits and underscores")
        return v

    @field_validator("password")
    @classmethod
    def password_bytes(cls, v):
        if len(v.encode()) > 72:
            raise ValueError("password must be at most 72 bytes")
        if v.strip() != v or not v.strip():
            raise ValueError("password must not start or end with spaces")
        return v


class UserOut(BaseModel):
    id: int
    username: str
    created_at: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth token type, not a secret
    expires_in: int


def _clean(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("must not be blank")
    return v


class PostIn(BaseModel):
    title: str = Field(min_length=1, max_length=200, examples=["Designing a URL shortener"])
    body: str = Field(min_length=1, max_length=10_000, examples=["Start with the read path..."])

    @field_validator("title", "body")
    @classmethod
    def not_blank(cls, v):
        return _clean(v)


class PostPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1, max_length=10_000)

    @field_validator("title", "body")
    @classmethod
    def not_blank(cls, v):
        return None if v is None else _clean(v)


class PostOut(BaseModel):
    id: int
    title: str
    body: str
    author: str
    created_at: str
    updated_at: str | None
    likes: int
    comments: int


class PostPage(BaseModel):
    items: list[PostOut]
    page: int
    page_size: int
    total: int
    pages: int


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000, examples=["Great write-up!"])

    @field_validator("body")
    @classmethod
    def not_blank(cls, v):
        return _clean(v)


class CommentOut(BaseModel):
    id: int
    post_id: int
    author: str
    body: str
    created_at: str


class CommentPage(BaseModel):
    items: list[CommentOut]
    page: int
    page_size: int
    total: int
    pages: int


# ---------------------------------------------------------------- app factory
STATIC = Path(__file__).with_name("static")


def create_app(db_path=None, secret=None, rate_per_min=None, login_per_min=None, token_ttl=3600, metrics_token=None):
    db_path = db_path or os.environ.get("BLOG_DB", "blog.db")
    secret = secret or os.environ.get("JWT_SECRET")
    if not secret:
        raise RuntimeError("set JWT_SECRET (a long random string) before starting the API")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters")
    rate_per_min = rate_per_min or int(os.environ.get("RATE_LIMIT_PER_MIN", 60))
    login_per_min = login_per_min or int(os.environ.get("LOGIN_LIMIT_PER_MIN", 5))
    metrics_token = metrics_token if metrics_token is not None else os.environ.get("METRICS_TOKEN", "")
    store.init(db_path)
    observability.setup_logging(os.environ.get("LOG_LEVEL", "INFO"))

    app = FastAPI(
        title="Blogly API",
        version="2.0.0",
        description="Blogly, SkillNexis Software Engineer week 4. Real-time events: connect to `/ws`. Log in with **POST /auth/login**, then click **Authorize** "
                    "and paste the `access_token` to call the protected endpoints.",
    )
    general = TokenBucket(rate_per_min, rate_per_min / 60)
    login_bucket = TokenBucket(login_per_min, login_per_min / 60)
    bearer = HTTPBearer(auto_error=False)

    def client_key(request: Request):
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            try:
                return "user:" + str(decode_token(auth[7:], secret))
            except jwt.InvalidTokenError:
                pass
        return "ip:" + (request.client.host if request.client else "unknown")

    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        path = request.url.path
        if path in ("/", "/status", "/health", "/metrics", "/docs", "/openapi.json", "/redoc") or path.startswith("/static/"):
            return await call_next(request)
        bucket = login_bucket if path in ("/auth/login", "/auth/register") else general
        key = ("ip:" + (request.client.host if request.client else "unknown")) if bucket is login_bucket else client_key(request)
        allowed, remaining, retry = bucket.take(key)
        if not allowed:
            return JSONResponse({"detail": "Too many requests, slow down"}, status_code=429,
                                headers={"Retry-After": str(retry), "X-RateLimit-Limit": str(bucket.capacity), "X-RateLimit-Remaining": "0"})
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(bucket.capacity)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    metrics = observability.Metrics()
    hub = Hub(metrics)
    app.state.metrics, app.state.hub = metrics, hub
    observability.install(app, metrics)  # outermost middleware: sees 429s too

    def get_db():
        conn = store.connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    DB = Annotated[sqlite3.Connection, Depends(get_db)]

    def current_user(conn: DB, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        if creds is None:
            raise HTTPException(401, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})
        try:
            uid = decode_token(creds.credentials, secret)
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token expired", headers={"WWW-Authenticate": "Bearer"}) from None
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid token", headers={"WWW-Authenticate": "Bearer"}) from None
        row = conn.execute("SELECT id, username, created_at FROM users WHERE id = ?", (uid,)).fetchone()
        if row is None:
            raise HTTPException(401, "User no longer exists")
        return row

    User = Annotated[sqlite3.Row, Depends(current_user)]

    def post_row(conn, post_id):
        row = conn.execute(
            """SELECT p.*, u.username AS author,
                      (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) AS likes,
                      (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comments
               FROM posts p JOIN users u ON u.id = p.author_id WHERE p.id = ?""", (post_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Post not found")
        return row

    def page_meta(total, page, size):
        return {"page": page, "page_size": size, "total": total, "pages": math.ceil(total / size) if total else 0}

    # ---------------------------------------------------------------- routes
    @app.get("/health", tags=["meta"])
    def health(conn: DB):
        conn.execute("SELECT 1")  # proves the database answers, not just the process
        return {"status": "ok"}

    @app.get("/metrics", include_in_schema=False)
    def prometheus(request: Request):
        if metrics_token and request.headers.get("authorization") != f"Bearer {metrics_token}":
            raise HTTPException(401, "metrics token required")
        body, ctype = metrics.render()
        return Response(body, media_type=ctype)

    @app.get("/api/status", tags=["meta"], description="Numbers behind the /status dashboard.")
    def status_summary():
        return metrics.summary()

    @app.websocket("/ws")
    async def ws(websocket: WebSocket):
        await hub.serve(websocket)

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/status", include_in_schema=False)
    def status_page():
        return FileResponse(STATIC / "status.html")

    @app.post("/auth/register", response_model=UserOut, status_code=201, tags=["auth"])
    def register(body: Credentials, conn: DB):
        try:
            with conn:
                cur = conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (body.username, hash_password(body.password)))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Username already taken") from None
        metrics.signups.inc()
        return dict(conn.execute("SELECT id, username, created_at FROM users WHERE id = ?", (cur.lastrowid,)).fetchone())

    @app.post("/auth/login", response_model=Token, tags=["auth"])
    def login(body: Credentials, conn: DB):
        row = conn.execute("SELECT id, password_hash FROM users WHERE username = ?", (body.username,)).fetchone()
        # same message and similar work either way, so the response does not reveal which usernames exist
        ok = verify_password(body.password, row["password_hash"] if row else hash_password(secrets.token_hex(8)))
        if row is None or not ok:
            raise HTTPException(401, "Incorrect username or password")
        return {"access_token": create_token(row["id"], secret, token_ttl), "expires_in": token_ttl}

    @app.get("/users/me", response_model=UserOut, tags=["auth"])
    def me(user: User):
        return dict(user)

    @app.get("/posts", response_model=PostPage, tags=["posts"])
    def list_posts(conn: DB,
                   page: Annotated[int, Query(ge=1)] = 1,
                   page_size: Annotated[int, Query(ge=1, le=50)] = 10,
                   q: Annotated[str | None, Query(max_length=100, description="search in title and body")] = None,
                   author: Annotated[str | None, Query(max_length=30)] = None):
        where, args = [], []
        if q:
            like = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            where.append("(p.title LIKE ? ESCAPE '\\' OR p.body LIKE ? ESCAPE '\\')")
            args += [like, like]
        if author:
            where.append("u.username = ?")
            args.append(author)
        clause = ("WHERE " + " AND ".join(where)) if where else ""
        total = conn.execute(f"SELECT COUNT(*) FROM posts p JOIN users u ON u.id = p.author_id {clause}", args).fetchone()[0]
        rows = conn.execute(
            f"""SELECT p.*, u.username AS author,
                       (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.id) AS likes,
                       (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comments
                FROM posts p JOIN users u ON u.id = p.author_id {clause}
                ORDER BY p.created_at DESC, p.id DESC LIMIT ? OFFSET ?""", args + [page_size, (page - 1) * page_size]).fetchall()
        return {"items": [dict(r) for r in rows], **page_meta(total, page, page_size)}

    @app.post("/posts", response_model=PostOut, status_code=201, tags=["posts"])
    def create_post(body: PostIn, conn: DB, user: User):
        with conn:
            cur = conn.execute("INSERT INTO posts (author_id, title, body) VALUES (?, ?, ?)", (user["id"], body.title, body.body))
        post = dict(post_row(conn, cur.lastrowid))
        hub.publish("post_created", post={k: post[k] for k in PostOut.model_fields})
        return post

    @app.get("/posts/{post_id}", response_model=PostOut, tags=["posts"])
    def get_post(post_id: int, conn: DB):
        return dict(post_row(conn, post_id))

    def own_post(conn, post_id, user):
        row = post_row(conn, post_id)
        if row["author_id"] != user["id"]:
            raise HTTPException(403, "You can only change your own posts")
        return row

    @app.patch("/posts/{post_id}", response_model=PostOut, tags=["posts"])
    def update_post(post_id: int, body: PostPatch, conn: DB, user: User):
        own_post(conn, post_id, user)
        changes = body.model_dump(exclude_none=True)
        if not changes:
            raise HTTPException(422, "Send at least one of title or body")
        sets = ", ".join(f"{k} = ?" for k in changes)
        with conn:
            conn.execute(f"UPDATE posts SET {sets}, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?", [*changes.values(), post_id])
        return dict(post_row(conn, post_id))

    @app.delete("/posts/{post_id}", status_code=204, tags=["posts"])
    def delete_post(post_id: int, conn: DB, user: User):
        own_post(conn, post_id, user)
        with conn:
            conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        hub.publish("post_deleted", post_id=post_id)
        return Response(status_code=204)

    @app.get("/posts/{post_id}/comments", response_model=CommentPage, tags=["comments"])
    def list_comments(post_id: int, conn: DB, page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=50)] = 20):
        post_row(conn, post_id)
        total = conn.execute("SELECT COUNT(*) FROM comments WHERE post_id = ?", (post_id,)).fetchone()[0]
        rows = conn.execute(
            "SELECT c.id, c.post_id, u.username AS author, c.body, c.created_at FROM comments c JOIN users u ON u.id = c.author_id "
            "WHERE c.post_id = ? ORDER BY c.id LIMIT ? OFFSET ?", (post_id, page_size, (page - 1) * page_size)).fetchall()
        return {"items": [dict(r) for r in rows], **page_meta(total, page, page_size)}

    @app.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=201, tags=["comments"])
    def add_comment(post_id: int, body: CommentIn, conn: DB, user: User):
        post_row(conn, post_id)
        with conn:
            cur = conn.execute("INSERT INTO comments (post_id, author_id, body) VALUES (?, ?, ?)", (post_id, user["id"], body.body))
        comment = dict(conn.execute("SELECT c.id, c.post_id, u.username AS author, c.body, c.created_at FROM comments c "
                                 "JOIN users u ON u.id = c.author_id WHERE c.id = ?", (cur.lastrowid,)).fetchone())
        hub.publish("comment_added", comment=comment)
        return comment

    @app.delete("/comments/{comment_id}", status_code=204, tags=["comments"])
    def delete_comment(comment_id: int, conn: DB, user: User):
        row = conn.execute("SELECT c.author_id, p.author_id AS post_author FROM comments c JOIN posts p ON p.id = c.post_id WHERE c.id = ?",
                           (comment_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Comment not found")
        if user["id"] not in (row["author_id"], row["post_author"]):
            raise HTTPException(403, "Only the comment author or the post author can delete this comment")
        with conn:
            conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        return Response(status_code=204)

    @app.put("/posts/{post_id}/like", status_code=204, tags=["likes"], description="Idempotent: liking twice is still one like.")
    def like(post_id: int, conn: DB, user: User):
        post_row(conn, post_id)
        with conn:
            conn.execute("INSERT OR IGNORE INTO likes (post_id, user_id) VALUES (?, ?)", (post_id, user["id"]))
        hub.publish("likes_changed", post_id=post_id, likes=post_row(conn, post_id)["likes"])
        return Response(status_code=204)

    @app.delete("/posts/{post_id}/like", status_code=204, tags=["likes"])
    def unlike(post_id: int, conn: DB, user: User):
        post_row(conn, post_id)
        with conn:
            conn.execute("DELETE FROM likes WHERE post_id = ? AND user_id = ?", (post_id, user["id"]))
        hub.publish("likes_changed", post_id=post_id, likes=post_row(conn, post_id)["likes"])
        return Response(status_code=204)

    return app


# The module-level app for uvicorn. Without JWT_SECRET (e.g. when tests import create_app) it is
# left unset; uvicorn then fails with a clear message instead of starting with a weak secret.
app = create_app() if os.environ.get("JWT_SECRET") else None
