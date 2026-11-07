"""SQLite storage: users and API keys, conversation memory, uploaded documents, and the usage/cost ledger.
API keys are random 32-byte tokens shown once; only their SHA-256 hash is stored."""
import datetime, hashlib, json, os, secrets, sqlite3, threading, time
DB = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "assistant.db"))
_lock = threading.Lock()
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT UNIQUE, key_hash TEXT UNIQUE, role TEXT, daily_token_limit INTEGER, created TEXT);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, user_id INTEGER, session TEXT, role TEXT, content TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS summaries(user_id INTEGER, session TEXT, summary TEXT, PRIMARY KEY(user_id, session));
CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, kind TEXT, pages INTEGER, chunks INTEGER, method TEXT, ts TEXT, text TEXT);
CREATE TABLE IF NOT EXISTS usage(id INTEGER PRIMARY KEY, ts TEXT, user_id INTEGER, session TEXT, endpoint TEXT, provider TEXT, model TEXT, prompt_tokens INTEGER,
  completion_tokens INTEGER, exact INTEGER, cost_usd REAL, latency_ms REAL, ttft_ms REAL, status TEXT, guardrail TEXT, grounded REAL, flagged INTEGER, top_source TEXT);
"""
def conn():
    c = sqlite3.connect(DB, check_same_thread=False); c.row_factory = sqlite3.Row; return c
def init():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    with _lock, conn() as c: c.executescript(SCHEMA)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
def h(key): return hashlib.sha256(key.encode()).hexdigest()
def create_user(name, role="user", daily_token_limit=200_000):
    key = "sk-asst-" + secrets.token_urlsafe(32)
    with _lock, conn() as c: c.execute("INSERT INTO users(name,key_hash,role,daily_token_limit,created) VALUES(?,?,?,?,?)", (name, h(key), role, daily_token_limit, now()))
    return key
def user_by_key(key):
    with conn() as c: r = c.execute("SELECT * FROM users WHERE key_hash=?", (h(key),)).fetchone()
    return dict(r) if r else None
def add_message(uid, session, role, content):
    with _lock, conn() as c: c.execute("INSERT INTO messages(user_id,session,role,content,ts) VALUES(?,?,?,?,?)", (uid, session, role, content, now()))
def history(uid, session, n=None):
    with conn() as c: rows = [dict(r) for r in c.execute("SELECT role,content,ts FROM messages WHERE user_id=? AND session=? ORDER BY id", (uid, session))]
    return rows[-n:] if n else rows
def get_summary(uid, session):
    with conn() as c: r = c.execute("SELECT summary FROM summaries WHERE user_id=? AND session=?", (uid, session)).fetchone()
    return r["summary"] if r else ""
def set_summary(uid, session, s):
    with _lock, conn() as c: c.execute("INSERT OR REPLACE INTO summaries VALUES(?,?,?)", (uid, session, s))
def delete_session(uid, session):
    with _lock, conn() as c: n = c.execute("DELETE FROM messages WHERE user_id=? AND session=?", (uid, session)).rowcount; c.execute("DELETE FROM summaries WHERE user_id=? AND session=?", (uid, session))
    return n
def sessions(uid):
    with conn() as c: return [dict(r) for r in c.execute("SELECT session, COUNT(*) AS messages, MAX(ts) AS last FROM messages WHERE user_id=? GROUP BY session ORDER BY last DESC", (uid,))]
def add_document(uid, name, kind, pages, chunks, method, text):
    with _lock, conn() as c: c.execute("INSERT INTO documents(user_id,name,kind,pages,chunks,method,ts,text) VALUES(?,?,?,?,?,?,?,?)", (uid, name, kind, pages, chunks, method, now(), text))
def documents(uid=None):
    with conn() as c:
        q = "SELECT id,user_id,name,kind,pages,chunks,method,ts FROM documents" + (" WHERE user_id=?" if uid is not None else "")
        return [dict(r) for r in c.execute(q, (uid,) if uid is not None else ())]
def all_document_texts():
    with conn() as c: return [dict(r) for r in c.execute("SELECT user_id,name,text FROM documents")]
def delete_document(uid, name):
    with _lock, conn() as c: return c.execute("DELETE FROM documents WHERE user_id=? AND name=?", (uid, name)).rowcount
def log_usage(**r):
    r.setdefault("ts", now()); cols = ",".join(r); qs = ",".join("?" * len(r))
    with _lock, conn() as c: c.execute(f"INSERT INTO usage({cols}) VALUES({qs})", tuple(r.values()))
def tokens_today(uid):
    day = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    with conn() as c: r = c.execute("SELECT COALESCE(SUM(prompt_tokens+completion_tokens),0) t FROM usage WHERE user_id=? AND ts>=?", (uid, day)).fetchone()
    return r["t"]
def usage_rows(uid=None, since=None):
    q, a = "SELECT u.*, us.name AS user FROM usage u LEFT JOIN users us ON us.id=u.user_id WHERE 1=1", []
    if uid is not None: q += " AND u.user_id=?"; a.append(uid)
    if since: q += " AND u.ts>=?"; a.append(since)
    with conn() as c: return [dict(r) for r in c.execute(q + " ORDER BY u.id", a)]
