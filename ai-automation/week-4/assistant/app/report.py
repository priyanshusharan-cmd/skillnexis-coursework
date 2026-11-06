"""Task summary (daily) and the weekly report: emails handled, time saved estimate, open/overdue tasks by priority,
meetings booked, drafts awaiting approval, and what's due next week."""
import collections, datetime as dt
from . import store
MIN_SAVED = dict(email=2, task=1, meeting=6, draft=4)                 # rough minutes a person would spend on each by hand
def weekly(today=None):
    today = today or dt.date.today(); start = today - dt.timedelta(days=7); c = store.conn()
    em = store.rows(c, "select * from emails"); ts = store.rows(c, "select * from tasks"); mt = store.rows(c, "select * from meetings"); dr = store.rows(c, "select * from drafts")
    cats = collections.Counter(e["category"] for e in em); open_t = [t for t in ts if t["status"] == "open"]
    overdue = [t for t in open_t if t["due"] and t["due"] < today.isoformat()]; nextw = sorted([t for t in open_t if t["due"] and today.isoformat() <= t["due"] <= (today + dt.timedelta(days=7)).isoformat()], key=lambda t: t["due"])
    saved = MIN_SAVED["email"] * len(em) + MIN_SAVED["task"] * len(ts) + MIN_SAVED["meeting"] * len(mt) + MIN_SAVED["draft"] * len(dr)
    L = [f"# Weekly report · week ending {today:%d %b %Y}", "", "| | |", "|---|---|", f"| Emails processed | {len(em)} ({', '.join(f'{k} {v}' for k, v in cats.most_common())}) |",
         f"| Tasks created | {len(ts)} ({sum(t['priority'] == 'high' for t in ts)} high priority) |", f"| Open / overdue tasks | {len(open_t)} / {len(overdue)} |",
         f"| Meetings booked | {len(mt)} |", f"| Reply drafts | {len(dr)} ({sum(d['status'] == 'awaiting approval' for d in dr)} awaiting approval, {sum(d['status'] == 'sent' for d in dr)} sent) |",
         f"| Estimated time saved | ~{saved} min (assumes {MIN_SAVED['email']} min per email triaged, {MIN_SAVED['draft']} per reply drafted, {MIN_SAVED['meeting']} per meeting scheduled) |", ""]
    L += ["## Overdue", ""] + ([f"- **{t['text']}** (due {t['due']}, from \"{t['source_subject']}\")" for t in overdue] or ["- none"])
    L += ["", "## Due in the next 7 days", ""] + ([f"- {t['due']} · {t['priority']} · {t['text']}" for t in nextw] or ["- none"])
    L += ["", "## Meetings booked", ""] + [f"- {dt.datetime.fromisoformat(x['start']):%a %d %b %H:%M} · {x['title']} ({x['minutes']} min) · {x['reason']}" for x in mt]
    L += ["", "## Open tasks without a deadline", ""] + [f"- {t['text']} (from \"{t['source_subject']}\")" for t in open_t if not t["due"]]
    return "\n".join(L) + "\n"
def daily(today=None):
    today = today or dt.date.today(); c = store.conn(); ts = store.rows(c, "select * from tasks where status='open' order by case priority when 'high' then 0 when 'medium' then 1 else 2 end, coalesce(due,'9999')")
    return "\n".join([f"# Task summary · {today:%a %d %b}", ""] + [f"- [{t['priority']}] {t['text']}" + (f" (due {t['due']})" if t["due"] else "") for t in ts]) + "\n"
