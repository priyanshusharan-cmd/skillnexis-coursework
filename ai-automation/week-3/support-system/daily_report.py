"""Daily summary report: reads the last 24 h of logged turns (SQLite, the mirror of the Sheets log), computes
volumes, the automatic-resolution rate, escalations with reasons, top intents and KB articles, and the questions the
bot could not answer (the to-do list for new KB articles). Sends it as an HTML email to SUPPORT_EMAIL (or saves it to
outbox/ without SMTP) and writes reports/daily-<date>.md.
Schedule it daily: cron `0 9 * * * cd /path && python daily_report.py`, or the GitHub Actions workflow in this folder.
    python daily_report.py [--hours 24]"""
import argparse, collections, datetime, html, os, sqlite3
import support as S
def build(hours=24):
    since = (datetime.datetime.now() - datetime.timedelta(hours=hours)).isoformat(timespec="seconds"); log = S.Log(); rows = log.rows(since)
    tickets = log.db.execute("select id, time, reason, email_status from tickets where time >= ?", (since,)).fetchall()
    sess = collections.defaultdict(list)
    for r in rows: sess[r["session"]].append(r)
    esc_s = {s for s, t in sess.items() if any(x["action"] == "escalate" for x in t)}
    answered = sum(r["action"] in ("kb", "faq") for r in rows); questions = sum(r["action"] not in ("smalltalk",) for r in rows)
    intents = collections.Counter(r["intent"] for r in rows if r["action"] != "smalltalk"); arts = collections.Counter(r["kb_article"] for r in rows if r["kb_article"])
    unanswered = [r["user_message"] for r in rows if r["action"] == "fallback"]; reasons = collections.Counter(r["escalation_reason"] for r in rows if r["action"] == "escalate")
    k = dict(conversations=len(sess), messages=len(rows), questions=questions, answered_automatically=answered, auto_answer_rate=round(answered / max(questions, 1), 3),
             conversations_resolved_without_human=len(sess) - len(esc_s), escalations=len(tickets))
    day = datetime.date.today().isoformat()
    md = [f"# Support daily summary · {day}", "", f"Window: last {hours} h · log backend: {log.backend}", "", "| Metric | Value |", "|---|---|"] + [f"| {a.replace('_', ' ')} | {b if not isinstance(b, float) else f'{b:.0%}'} |" for a, b in k.items()]
    md += ["", "## Escalations", ""] + ([f"* **{t[0]}** {t[1][11:16]}: {t[2]} ({t[3]})" for t in tickets] or ["* none"])
    md += ["", "## Top intents", ""] + [f"* {i}: {n}" for i, n in intents.most_common(6)]
    md += ["", "## Knowledge-base articles used", ""] + [f"* {a}: {n}" for a, n in arts.most_common()]
    md += ["", "## Not answered (candidates for new KB articles)", ""] + ([f"* \"{u}\"" for u in unanswered] or ["* none"])
    return k, "\n".join(md) + "\n", day
def to_html(md):
    out = []
    for line in md.splitlines():
        if line.startswith("# "): out.append(f"<h2 style='color:#14213D'>{html.escape(line[2:])}</h2>")
        elif line.startswith("## "): out.append(f"<h3 style='color:#E8590C;margin-bottom:4px'>{html.escape(line[3:])}</h3>")
        elif line.startswith("| ") and "---" not in line: c = [html.escape(x.strip()) for x in line.strip("|").split("|")]; out.append(f"<tr><td style='padding:4px 12px 4px 0'>{c[0]}</td><td><b>{c[1]}</b></td></tr>")
        elif line.startswith("* "): out.append(f"<li>{html.escape(line[2:]).replace('**', '')}</li>")
        elif line.strip() and "---" not in line: out.append(f"<p>{html.escape(line)}</p>")
    return "<div style='font-family:system-ui;max-width:600px'>" + "\n".join(out).replace("<tr>", "<table><tr>", 1).replace("</tr>\n<h3", "</tr></table>\n<h3", 1) + "</div>"
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--hours", type=int, default=24); o = ap.parse_args()
    k, md, day = build(o.hours); os.makedirs(os.path.join(S.HERE, "reports"), exist_ok=True)
    open(os.path.join(S.HERE, "reports", f"daily-{day}.md"), "w").write(md); open(os.path.join(S.HERE, "reports", f"daily-{day}.html"), "w").write(to_html(md))
    status = S.send_email(os.environ.get("SUPPORT_EMAIL", "support@codeinsmallsteps.example"), f"Support daily summary {day}: {k['conversations']} chats, {k['escalations']} escalations", md)
    print(md); print("email:", status)
