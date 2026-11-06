"""Demo run on the fictional sample inbox (data/inbox, 14 emails for the made-up company "Northwind Learning"):
fresh database, a copy of the seed calendar, one processing run, then the daily summary and weekly report.
    python demo.py -> data/demo/*.md, data/demo/assistant.sqlite, data/demo/calendar.ics, data/demo/invites/"""
import json, os, shutil
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "demo"); shutil.rmtree(D, ignore_errors=True); os.makedirs(D)
shutil.copy(os.path.join(os.path.dirname(D), "calendar.ics"), os.path.join(D, "calendar.ics"))
os.environ.update(ASSISTANT_DB=os.path.join(D, "assistant.sqlite"), CALENDAR_ICS=os.path.join(D, "calendar.ics"))
from app import engine, report, store
stats = engine.process(); print(json.dumps(stats))
c = store.conn()
open(os.path.join(D, "daily-summary.md"), "w").write(report.daily()); open(os.path.join(D, "weekly-report.md"), "w").write(report.weekly())
L = ["# Demo run: what the assistant did", "", f"Run stats: `{json.dumps(stats)}`", "", "## Emails", "", "| Subject | Category | Urgent |", "|---|---|---|"]
L += [f"| {e['subject']} | {e['category']} | {'yes' if e['urgent'] else ''} |" for e in store.rows(c, "select * from emails order by received")]
L += ["", "## Tasks", "", "| Priority | Task | Due | From |", "|---|---|---|---|"] + [f"| {t['priority']} | {t['text']} | {t['due'] or '—'} | {t['source_subject']} |" for t in store.rows(c, "select * from tasks")]
L += ["", "## Meetings booked", ""] + [f"- **{m['start'][:16].replace('T', ' ')}** {m['title']} ({m['minutes']} min): {m['reason']}" for m in store.rows(c, "select * from meetings")]
L += ["", "## Reply drafts (awaiting approval)", ""] + [f"### {d['subject']} → {d['to_addr']}\n\n```\n{d['body']}\n```\n" for d in store.rows(c, "select * from drafts")]
open(os.path.join(D, "run.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
