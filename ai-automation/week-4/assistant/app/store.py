"""SQLite store for emails, tasks, drafts, meetings and the activity log (one file; the dashboard reads it)."""
import datetime as dt, json, os, sqlite3, threading
DB = os.environ.get("ASSISTANT_DB", os.path.join(os.path.dirname(__file__), "..", "data", "assistant.sqlite")); _lock = threading.Lock()
SCHEMA = """
create table if not exists emails (message_id text primary key, received text, sender text, subject text, category text, urgent int, engine text, processed text);
create table if not exists tasks (id integer primary key, message_id text, text text, due text, priority text, status text default 'open', created text, source_subject text, owner text);
create table if not exists drafts (id integer primary key, message_id text, to_addr text, subject text, body text, status text default 'awaiting approval', created text, engine text);
create table if not exists meetings (id integer primary key, message_id text, title text, start text, minutes int, attendee text, reason text, event_id text, invite text, created text);
create table if not exists log (time text, level text, event text, detail text);
"""
def conn():
    c = sqlite3.connect(DB, check_same_thread=False); c.row_factory = sqlite3.Row; c.executescript(SCHEMA); return c
def now(): return dt.datetime.now().isoformat(timespec="seconds")
def log(c, event, detail="", level="info"):
    with _lock: c.execute("insert into log values (?,?,?,?)", (now(), level, event, detail if isinstance(detail, str) else json.dumps(detail))); c.commit()
def rows(c, sql, *a): return [dict(r) for r in c.execute(sql, a).fetchall()]
