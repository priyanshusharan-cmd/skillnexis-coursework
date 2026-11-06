"""Email sources and sending. IMAP works with Gmail/Outlook (an App Password, free); the folder source reads .eml
files (the demo inbox). Sending is SMTP and only ever happens for drafts a person approved on the dashboard."""
import email, glob, imaplib, os, smtplib, ssl
from email import policy
from email.message import EmailMessage
from email.utils import parsedate_to_datetime, parseaddr
def parse(raw):
    m = email.message_from_bytes(raw, policy=policy.default); body = m.get_body(preferencelist=("plain", "html"))
    text = body.get_content() if body else ""
    return dict(message_id=m.get("Message-ID", "").strip(), sender=m.get("From", ""), sender_email=parseaddr(m.get("From", ""))[1].lower(), subject=m.get("Subject", ""),
                date=parsedate_to_datetime(m["Date"]).isoformat() if m.get("Date") else None, body=text, list_unsubscribe=bool(m.get("List-Unsubscribe")))
class FolderSource:
    def __init__(self, folder): self.folder = folder
    def fetch(self): return [parse(open(p, "rb").read()) for p in sorted(glob.glob(os.path.join(self.folder, "*.eml")))]
class IMAPSource:
    """Unread messages from INBOX (read-only: nothing is marked or deleted)."""
    def __init__(self): self.h, self.u, self.p = os.environ["IMAP_HOST"], os.environ["IMAP_USER"], os.environ["IMAP_PASS"]
    def fetch(self, limit=50):
        with imaplib.IMAP4_SSL(self.h) as M:
            M.login(self.u, self.p); M.select("INBOX", readonly=True); _, ids = M.search(None, "UNSEEN"); out = []
            for i in ids[0].split()[-limit:]:
                _, d = M.fetch(i, "(BODY.PEEK[])"); out.append(parse(d[0][1]))
            return out
def source():
    return IMAPSource() if os.environ.get("IMAP_HOST") else FolderSource(os.environ.get("INBOX_DIR", os.path.join(os.path.dirname(__file__), "..", "data", "inbox")))
def send(to, subject, body, in_reply_to=None):
    if not os.environ.get("SMTP_HOST"): return "not sent: SMTP not configured"
    m = EmailMessage(); m["From"] = os.environ.get("SMTP_FROM", os.environ.get("SMTP_USER", "")); m["To"] = to; m["Subject"] = subject
    if in_reply_to: m["In-Reply-To"] = m["References"] = in_reply_to
    m.set_content(body)
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 587)), timeout=30) as s:
        if os.environ.get("SMTP_TLS", "1") == "1": s.starttls(context=ssl.create_default_context())
        if os.environ.get("SMTP_USER"): s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(m)
    return "sent"
