"""Runs the same 5-step automation end to end on this machine, with stand-ins for the three apps, to prove the logic
before connecting real accounts:
  Google Sheets -> a CSV file (rows read, status column written back)
  Gmail         -> a real SMTP send to a local mail server
  Slack         -> a real HTTP POST of Slack's incoming-webhook JSON ({"text": ...}) to a local webhook receiver
Swap in real ones with env vars: SMTP_HOST/PORT/USER/PASS (e.g. a Gmail App Password) and SLACK_WEBHOOK_URL.
    python run_local.py"""
import csv, json, os, re, smtplib, threading, time
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
SHEET = "sheet.csv"
ROWS = [["Timestamp", "Full name", "Email address", "Coding experience", "Status"],
        ["2026-11-06 09:00", "aarav mehta", "Aarav.Mehta@Example.com", "Never coded", ""], ["2026-11-06 09:05", "Rohan Das", "rohan@example", "a little", ""],
        ["2026-11-06 09:10", "meera iyer", "meera@example.org", "some school python", ""], ["2026-11-06 09:12", "", "x@example.com", "none", ""]]
received = []
class Hook(BaseHTTPRequestHandler):
    def do_POST(self):
        received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"])))); self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass
def step2(r):
    email = r["Email address"].strip().lower(); name = re.sub(r"\s+", " ", r["Full name"].strip()).title(); exp = r["Coding experience"].lower()
    valid = bool(name) and bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[a-z]{2,}", email))
    track = "Python from zero" if re.search(r"never|none|beginner", exp) else "Python from zero (fast)" if re.search(r"some|little|school", exp) else "Debugging basics"
    return dict(email=email, name=name, first=name.split(" ")[0] if name else "", track=track, valid=valid, problem="" if valid else ("name missing" if not name else "invalid email"))
if __name__ == "__main__":
    with open(SHEET, "w", newline="") as f: csv.writer(f).writerows(ROWS)                     # the "spreadsheet" with 4 new responses
    from aiosmtpd.controller import Controller
    from aiosmtpd.handlers import Message
    inbox = []
    class Box(Message):
        def handle_message(self, m): inbox.append(m)
    smtp_host, smtp_port = os.environ.get("SMTP_HOST", "127.0.0.1"), int(os.environ.get("SMTP_PORT", 8026))
    ctl = None
    if smtp_host == "127.0.0.1": ctl = Controller(Box(), hostname="127.0.0.1", port=smtp_port); ctl.start()
    hook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not hook_url:
        srv = HTTPServer(("127.0.0.1", 8765), Hook); threading.Thread(target=srv.serve_forever, daemon=True).start(); hook_url = "http://127.0.0.1:8765/hook"
    rows = list(csv.DictReader(open(SHEET))); log = []
    for i, r in enumerate(rows):                                                                # step 1: new rows (no status yet)
        if r["Status"]: continue
        d = step2(r)                                                                            # step 2: validate & normalise
        if d["valid"]:                                                                          # step 3: branch
            m = EmailMessage(); m["From"] = "hello@codeinsmallsteps.example"; m["To"] = d["email"]; m["Subject"] = f"Welcome, {d['first']}! Your first small step"
            m.set_content(f"Hi {d['first']},\n\nYou're in the {d['track']} track. Start with lesson 1 (about 5 minutes).\n\nMina")
            with smtplib.SMTP(smtp_host, smtp_port) as s:                                     # step 4: email (Gmail stand-in)
                if os.environ.get("SMTP_USER"): s.starttls(); s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
                s.send_message(m)
            requests.post(hook_url, json={"text": f"New sign-up: {d['name']} ({d['track']})"}, timeout=10).raise_for_status()   # step 5: Slack
            r["Status"] = "OK"
        else:
            r["Status"] = f"INVALID: {d['problem']}"                                            # step 5b: write status back
        log.append(dict(row=i + 2, **{k: d[k] for k in ("email", "name", "track")}, status=r["Status"]))
    with open(SHEET, "w", newline="") as f: w = csv.DictWriter(f, fieldnames=ROWS[0]); w.writeheader(); w.writerows(rows)
    time.sleep(.5)
    if ctl: ctl.stop()
    out = dict(steps=log, emails_received=[dict(to=m["To"], subject=m["Subject"]) for m in inbox], slack_messages=received)
    json.dump(out, open("run-log.json", "w"), indent=1); print(json.dumps(out, indent=1))
    assert len(inbox) == 2 and len(received) == 2 and sum(s["status"].startswith("INVALID") for s in log) == 2
