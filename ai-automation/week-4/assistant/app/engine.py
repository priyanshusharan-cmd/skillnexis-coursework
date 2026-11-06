"""The automation loop: fetch new emails -> understand -> create tasks -> schedule meetings -> draft replies -> log.
Idempotent: an email already processed (same Message-ID) is skipped, so it is safe to run every few minutes."""
import datetime as dt, os, re, traceback
from . import calendar_svc as cal, mailbox, reply, store, understand
ME = os.environ.get("OWNER_NAME", "Priya")
def process(now=None):
    c = store.conn(); stats = dict(fetched=0, new=0, tasks=0, meetings=0, drafts=0, skipped_automated=0, errors=0)
    try: msgs = mailbox.source().fetch()
    except Exception as e: store.log(c, "fetch failed", f"{type(e).__name__}: {e}", "error"); return stats
    stats["fetched"] = len(msgs); done = {r["message_id"] for r in store.rows(c, "select message_id from emails")}
    for m in msgs:
        if m["message_id"] in done: continue
        try:
            u = understand.understand(m); stats["new"] += 1
            c.execute("insert into emails values (?,?,?,?,?,?,?,?)", (m["message_id"], m["date"], m["sender"], m["subject"], u["category"], int(u.get("urgent", False)), u.get("engine"), store.now()))
            for it in u["action_items"]:
                c.execute("insert into tasks (message_id, text, due, priority, created, source_subject, owner) values (?,?,?,?,?,?,?)", (m["message_id"], it["text"], it.get("due"), it.get("priority", "medium"), store.now(), m["subject"], ME)); stats["tasks"] += 1
            if re.search(r"\b(it'?s fixed|is fixed|resolved|no longer needed|ignore my (last|previous))\b", m["body"], re.I):     # a follow-up that closes earlier asks
                thread = re.sub(r"^(re|fwd?):\s*", "", m["subject"], flags=re.I)
                prev = [r["message_id"] for r in store.rows(c, "select message_id, subject from emails where message_id != ?", m["message_id"]) if re.sub(r"^(re|fwd?):\s*", "", r["subject"], flags=re.I) == thread]
                for mid in prev:
                    n = c.execute("update tasks set status='done' where message_id=? and status='open'", (mid,)).rowcount
                    if n: store.log(c, "tasks auto-closed", f"{n} task(s) from '{thread}': the follow-up says it's resolved")
            slot = None
            if u.get("meeting"):
                start, why = cal.find_slot(u["meeting"], now=now)
                if start:
                    mins = u["meeting"].get("minutes") or 30; title = f"{reply.first_name(m['sender'])} / {ME}: {m['subject'].removeprefix('Re: ')}"
                    eid, inv = cal.book(title, start, mins, m["sender_email"], f"Booked by the assistant from the email '{m['subject']}'. Reason: {why}")
                    c.execute("insert into meetings (message_id, title, start, minutes, attendee, reason, event_id, invite, created) values (?,?,?,?,?,?,?,?,?)", (m["message_id"], title, start.isoformat(), mins, m["sender_email"], why, eid, inv, store.now()))
                    slot = dict(start=start, minutes=mins); stats["meetings"] += 1; store.log(c, "meeting booked", f"{title} at {start:%a %d %b %H:%M} ({why})")
                else: store.log(c, "no free slot", m["subject"], "warning")
            if u.get("needs_reply") or slot:
                body, eng = reply.draft(m, u, slot, ME)
                subj = m["subject"] if m["subject"].lower().startswith("re:") else "Re: " + m["subject"]
                c.execute("insert into drafts (message_id, to_addr, subject, body, created, engine) values (?,?,?,?,?,?)", (m["message_id"], m["sender_email"], subj, body, store.now(), eng)); stats["drafts"] += 1
            if u["category"] in ("automated", "fyi"): stats["skipped_automated"] += 1
            c.commit(); store.log(c, "email processed", f"{m['subject']} -> {u['category']}, {len(u['action_items'])} task(s)" + (", meeting" if slot else ""))
        except Exception as e:
            stats["errors"] += 1; store.log(c, "processing error", f"{m.get('subject')}: {type(e).__name__}: {e}\n{traceback.format_exc()[-600:]}", "error")
    store.log(c, "run finished", stats); return stats
