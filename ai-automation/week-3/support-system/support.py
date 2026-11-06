"""Core of the support system: knowledge-base retrieval, intent detection (the FAQ bot's model), escalation rules,
email, and conversation logging (Google Sheets, or SQLite when no Google credentials are configured)."""
import datetime, glob, json, os, re, smtplib, sqlite3, sys, uuid
from email.message import EmailMessage
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "faq-bot"))
import bot as faq                                              # trained intent model + threshold from faq-bot/
# ---------------- knowledge base ----------------
SYN = {"macbook": "mac macos", "imac": "mac macos", "laptop": "computer", "phone": "phone mobile tablet", "mobile": "phone mobile", "buffering": "buffering not playing", "lagging": "buffering", "certifcate": "certificate", "emails": "emails unsubscribe", "free": "free price"}
def expand(q): return q + " " + " ".join(v for k, v in SYN.items() if re.search(rf"\b{k}\b", q, re.I))
class KB:
    """Two-stage retrieval. Stage 1 picks the ARTICLE (TF-IDF over title + full text, word 1-2 grams + char n-grams
    for typos); stage 2 picks the PARAGRAPH inside it that best matches the question, defaulting to the article's
    opening paragraph when nothing matches better. A small synonym map bridges everyday words (macbook -> macOS)."""
    def __init__(self, folder=os.path.join(HERE, "kb")):
        self.arts, self.docs = [], []
        for p in sorted(glob.glob(os.path.join(folder, "*.md"))):
            txt = open(p).read(); title = txt.splitlines()[0].lstrip("# ").strip()
            paras = [x.strip() for x in re.split(r"\n\s*\n", txt.split("\n", 1)[1]) if len(x.split()) >= 8]
            self.arts.append(dict(article=os.path.basename(p), title=title, paras=paras, text=title + ". " + title + ". " + " ".join(paras)))
            self.docs += [dict(article=os.path.basename(p), title=title, text=x) for x in paras]
        corpus = [a["text"] for a in self.arts]
        self.w = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english").fit(corpus + [d["text"] for d in self.docs])
        self.c = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True).fit(corpus)
        self.Aw, self.Ac = self.w.transform(corpus), self.c.transform(corpus)
    STOPW = set("the a an is are to of in on for and or i my me you your it this that do does how what can with at be not get".split())
    def terms(self, t): return {w[:5] for w in re.findall(r"[a-z0-9]+", t.lower()) if w not in self.STOPW and len(w) > 1}
    def bm25(self, q, para):
        """Paragraph score inside the chosen article: shared (5-letter-stemmed) terms weighted by rarity, length-normalised."""
        if not hasattr(self, "_idf"):
            import math; P = [self.terms(d["text"]) for d in self.docs]; self._avg = np.mean([len(d["text"].split()) for d in self.docs])
            self._idf = {t: math.log(1 + len(P) / (1 + sum(t in x for x in P))) for x in P for t in x}
        hit = self.terms(q) & self.terms(para); return sum(self._idf.get(t, 1) for t in hit) / (.5 + .5 * len(para.split()) / self._avg)
    def search(self, q, k=3):
        q2 = expand(q); s = .7 * (self.Aw @ self.w.transform([q2]).T).toarray().ravel() + .3 * (self.Ac @ self.c.transform([q2]).T).toarray().ravel()
        out = []
        for i in np.argsort(-s)[:k]:
            a = self.arts[i]; ps = np.array([self.bm25(q2, p) for p in a["paras"]])
            j = int(ps.argmax()) if ps.max() > ps[0] * 1.15 else 0
            out.append(dict(score=round(float(s[i]), 3), article=a["article"], title=a["title"], text=a["paras"][j]))
        return out
# ---------------- escalation ----------------
FRUSTRATED = re.compile(r"\b(useless|angry|terrible|worst|not helpful|doesn'?t help|still (not|doesn'?t)|ridiculous|waste|frustrat\w*|annoy\w*|again and again)\b", re.I)
SENSITIVE = re.compile(r"\b(delete|remove|erase)\b.*\b(account|data|details)\b|\bchange (my )?(email|name)\b|\b(locked|hacked|refund|charged|legal|complaint)\b", re.I)
def decide(msg, history):
    """Returns (action, details). Order matters: safety/explicit requests first, then confident answers, then fallback."""
    intent = faq.respond(msg); hits = KB_.search(msg); top = hits[0]
    if FRUSTRATED.search(msg): return "escalate", dict(reason="user frustrated", intent=intent, hits=hits)
    if intent["intent"] == "human_agent": return "escalate", dict(reason="asked for a human", intent=intent, hits=hits)
    if SENSITIVE.search(msg): return "escalate", dict(reason="account/data request needs a person", intent=intent, hits=hits)
    fallbacks = sum(1 for h in history[-4:] if h.get("action") == "fallback")
    if intent["intent"] in {"greeting", "goodbye", "thanks"} and intent["confidence"] >= .35: return "smalltalk", dict(intent=intent, hits=hits)
    if top["score"] >= .22: return "kb", dict(intent=intent, hits=hits)
    if intent["intent"] != "fallback": return "faq", dict(intent=intent, hits=hits)
    if fallbacks >= 1: return "escalate", dict(reason="two unanswered messages in a row", intent=intent, hits=hits)
    return "fallback", dict(intent=intent, hits=hits)
# ---------------- email ----------------
def send_email(to, subject, body):
    m = EmailMessage(); m["From"] = os.environ.get("SMTP_FROM", "support-bot@codeinsmallsteps.example"); m["To"] = to; m["Subject"] = subject; m.set_content(body)
    if os.environ.get("SMTP_HOST"):
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 587)), timeout=30) as s:
            if os.environ.get("SMTP_USER"): s.starttls(); s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(m)
        return "sent"
    os.makedirs(os.path.join(HERE, "outbox"), exist_ok=True); path = os.path.join(HERE, "outbox", f"{datetime.datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}.eml")
    open(path, "wb").write(bytes(m)); return f"saved {os.path.relpath(path, HERE)} (no SMTP configured)"
# ---------------- logging ----------------
COLS = ["time", "session", "turn", "user_message", "bot_reply", "action", "intent", "confidence", "kb_article", "kb_score", "ticket", "escalation_reason"]
class Log:
    """Google Sheets when GOOGLE_SERVICE_ACCOUNT_JSON (path to a service-account key) and SHEET_ID are set; otherwise
    SQLite. Same columns either way, so the daily report reads both."""
    def __init__(self):
        self.ws = None
        if os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON") and os.environ.get("SHEET_ID"):
            import gspread
            gc = gspread.service_account(filename=os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]); sh = gc.open_by_key(os.environ["SHEET_ID"])
            try: self.ws = sh.worksheet("conversations")
            except gspread.WorksheetNotFound: self.ws = sh.add_worksheet("conversations", rows=1000, cols=len(COLS)); self.ws.append_row(COLS)
        self.db = sqlite3.connect(os.environ.get("SUPPORT_DB", os.path.join(HERE, "support.sqlite")), check_same_thread=False)
        self.db.execute(f"create table if not exists conv ({', '.join(c + ' text' for c in COLS)})"); self.db.execute("create table if not exists tickets (id text, time text, session text, reason text, email_status text, status text)")
    @property
    def backend(self): return "google-sheets" if self.ws else "sqlite"
    def add(self, row):
        vals = [str(row.get(c, "")) for c in COLS]
        if self.ws: self.ws.append_row(vals, value_input_option="RAW")
        self.db.execute(f"insert into conv values ({','.join('?' * len(COLS))})", vals); self.db.commit()
    def ticket(self, session, reason, email_status):
        tid = "T-" + uuid.uuid4().hex[:6].upper(); self.db.execute("insert into tickets values (?,?,?,?,?,?)", (tid, datetime.datetime.now().isoformat(timespec="seconds"), session, reason, email_status, "open")); self.db.commit(); return tid
    def rows(self, since):
        cur = self.db.execute("select * from conv where time >= ?", (since,)); return [dict(zip(COLS, r)) for r in cur.fetchall()]
KB_ = KB()
