"""AI business assistant service: background polling + REST API + web dashboard.
    uvicorn app.main:app --port 8000      (POLL_MINUTES, default 10; 0 disables background polling)"""
import datetime as dt, html, os, threading, time
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from . import engine, mailbox, report, store
app = FastAPI(title="AI business assistant"); STATE = dict(started=store.now(), last_run=None, last_stats=None, runs=0)
def run_once():
    STATE["last_stats"] = engine.process(); STATE["last_run"] = store.now(); STATE["runs"] += 1; return STATE["last_stats"]
def loop():
    mins = float(os.environ.get("POLL_MINUTES", 10))
    while mins > 0:
        try: run_once()
        except Exception as e: store.log(store.conn(), "loop error", str(e), "error")
        time.sleep(mins * 60)
@app.on_event("startup")
def start():
    if float(os.environ.get("POLL_MINUTES", 10)) > 0: threading.Thread(target=loop, daemon=True).start()
@app.get("/api/status")
def status():
    c = store.conn(); n = lambda q: c.execute(q).fetchone()[0]
    return dict(**STATE, source="imap" if os.environ.get("IMAP_HOST") else "demo folder", calendar="google" if os.environ.get("GOOGLE_CALENDAR_ID") else "local ics",
                smtp=bool(os.environ.get("SMTP_HOST")), emails=n("select count(*) from emails"), open_tasks=n("select count(*) from tasks where status='open'"),
                drafts_waiting=n("select count(*) from drafts where status='awaiting approval'"), meetings=n("select count(*) from meetings"), errors=n("select count(*) from log where level='error'"))
@app.post("/api/run")
def run(): return run_once()
@app.get("/api/tasks")
def tasks(): return store.rows(store.conn(), "select * from tasks order by status, coalesce(due,'9999')")
@app.post("/api/tasks/{tid}/done")
def done(tid: int):
    c = store.conn(); c.execute("update tasks set status='done' where id=?", (tid,)); c.commit(); store.log(c, "task done", str(tid)); return {"ok": True}
@app.get("/api/drafts")
def drafts(): return store.rows(store.conn(), "select * from drafts order by id")
@app.post("/api/drafts/{did}/approve")
def approve(did: int):
    c = store.conn(); d = store.rows(c, "select * from drafts where id=?", did)
    if not d: raise HTTPException(404)
    res = mailbox.send(d[0]["to_addr"], d[0]["subject"], d[0]["body"], d[0]["message_id"]); st = "sent" if res == "sent" else "approved (not sent: SMTP not configured)"
    c.execute("update drafts set status=? where id=?", (st, did)); c.commit(); store.log(c, "draft approved", f"{did}: {res}"); return {"status": st}
@app.get("/api/meetings")
def meetings(): return store.rows(store.conn(), "select * from meetings order by start")
@app.get("/api/logs")
def logs(limit: int = 100): return store.rows(store.conn(), "select * from log order by time desc limit ?", limit)
@app.get("/report/weekly", response_class=PlainTextResponse)
def weekly(): return report.weekly()
@app.get("/report/daily", response_class=PlainTextResponse)
def daily(): return report.daily()
@app.get("/", response_class=HTMLResponse)
def dashboard(): return open(os.path.join(os.path.dirname(__file__), "dashboard.html")).read()
