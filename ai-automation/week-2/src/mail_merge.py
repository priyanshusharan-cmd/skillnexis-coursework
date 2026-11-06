"""Task 3: personalised emails to a contact list from a spreadsheet (.xlsx or .csv).
* Jinja2 template with conditional content (subject and body change with each contact's progress)
* data hygiene first: trims and lower-cases emails, validates them, drops duplicates and unsubscribed contacts
* DRY RUN by default: writes every message as an .eml file to review; --send delivers over SMTP with a pause between
  messages, and logs every result to outputs/mail_log.csv
SMTP settings come from the environment (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM). A Gmail account with a
free App Password works: host smtp.gmail.com, port 587.
    python src/mail_merge.py data/contacts.xlsx data/templates/progress.j2 [--send]"""
import argparse, csv, datetime, os, re, smtplib, ssl, sys, time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
import pandas as pd
from jinja2 import Environment, StrictUndefined
EMAIL = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}$")
def load(path):
    df = pd.read_excel(path) if path.endswith((".xlsx", ".xls")) else pd.read_csv(path)
    df["email"] = df["email"].astype(str).str.strip().str.lower(); report = {"rows": len(df)}
    bad = ~df["email"].str.match(EMAIL); report["invalid_email"] = df.loc[bad, "email"].tolist(); df = df[~bad]
    dup = df.duplicated("email"); report["duplicates"] = int(dup.sum()); df = df[~dup]
    if "subscribed" in df: uns = ~df["subscribed"].astype(bool); report["unsubscribed"] = df.loc[uns, "email"].tolist(); df = df[~uns]
    df = df.fillna(""); df["company"] = df["company"].replace({"—": "", "-": ""}) if "company" in df else ""
    report["to_send"] = len(df); return df.to_dict("records"), report
def render(tpl_text, row):
    env = Environment(undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True); head, body = tpl_text.split("\n---\n", 1)
    subject = env.from_string(head.replace("Subject:", "", 1).strip()).render(**row)
    return subject, re.sub(r"\n{3,}", "\n\n", env.from_string(body).render(**row)).strip() + "\n"
def message(sender, row, subject, body):
    m = EmailMessage(); m["From"] = sender; m["To"] = f"{row.get('first_name', '')} {row.get('last_name', '')} <{row['email']}>".strip()
    m["Subject"] = subject; m["Date"] = formatdate(localtime=True); m["Message-ID"] = make_msgid(domain=sender.split("@")[-1].strip(">"))
    m["List-Unsubscribe"] = f"<mailto:{sender.strip('<>').split('<')[-1]}?subject=unsubscribe>"; m.set_content(body); return m
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("contacts"); ap.add_argument("template"); ap.add_argument("--send", action="store_true"); ap.add_argument("--pause", type=float, default=2.0); o = ap.parse_args()
    rows, rep = load(o.contacts); tpl = open(o.template, encoding="utf-8").read(); sender = os.environ.get("SMTP_FROM", "Mina <hello@codeinsmallsteps.example>")
    print(f"contacts: {rep['rows']} rows · invalid {len(rep['invalid_email'])} {rep['invalid_email']} · duplicates {rep['duplicates']} · unsubscribed {len(rep.get('unsubscribed', []))} · to send {rep['to_send']}")
    os.makedirs("outputs/emails", exist_ok=True); log = []
    smtp = None
    if o.send:
        smtp = smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 587)), timeout=30)
        if os.environ.get("SMTP_TLS", "1") == "1": smtp.starttls(context=ssl.create_default_context())
        if os.environ.get("SMTP_USER"): smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
    for i, r in enumerate(rows):
        subject, body = render(tpl, r); m = message(sender, r, subject, body)
        path = f"outputs/emails/{i + 1:02d}-{r['email'].split('@')[0]}.eml"; open(path, "wb").write(bytes(m))
        status = "dry-run"
        if smtp:
            try: smtp.send_message(m); status = "sent"; time.sleep(o.pause)
            except smtplib.SMTPException as e: status = f"error: {e}"
        log.append(dict(time=datetime.datetime.now().isoformat(timespec="seconds"), email=r["email"], subject=subject, status=status)); print(f"{status:8} {r['email']:28} {subject}")
    if smtp: smtp.quit()
    with open("outputs/mail_log.csv", "w", newline="") as f: w = csv.DictWriter(f, fieldnames=list(log[0])); w.writeheader(); w.writerows(log)
