"""Customer-support chatbot service (FastAPI).
  GET  /             chat page            POST /chat {session, message, email?} -> reply
  GET  /health       status, KB size and logging backend
Each turn: detect intent + search the knowledge base -> answer with a cited article, a FAQ answer, small talk, a
clarifying fallback, or an ESCALATION (a ticket, an email to support with the full transcript, and a reply telling the
user what happens next). Every turn is logged (Google Sheets or SQLite).
    uvicorn app:app --port 8000"""
import datetime, os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import support as S
app = FastAPI(title="Code in Small Steps support"); LOG = S.Log(); SESS = {}
SUPPORT_TO = os.environ.get("SUPPORT_EMAIL", "support@codeinsmallsteps.example")
class Msg(BaseModel):
    session: str = Field(min_length=1, max_length=64); message: str = Field(min_length=1, max_length=2000); email: str | None = None
@app.get("/health")
def health(): return dict(ok=True, kb_paragraphs=len(S.KB_.docs), log_backend=LOG.backend)
@app.post("/chat")
def chat(m: Msg):
    hist = SESS.setdefault(m.session, []); action, d = S.decide(m.message, hist); top = d["hits"][0]; ticket = ""; reason = d.get("reason", "")
    if action == "kb":
        reply = f"{top['text']}\n\n📄 Source: {top['title']}"
    elif action in ("faq", "smalltalk"):
        reply = d["intent"]["reply"]
    elif action == "fallback":
        reply = "I'm not sure I've got that right. Could you rephrase it, or tell me which lesson or error message it's about? You can also type 'human' to reach the team."
    else:
        transcript = "\n".join(f"[{h['time']}] USER: {h['user']}\n           BOT: {h['bot']}" for h in hist) + f"\n[now] USER: {m.message}"
        ticket = "pending"
        status = S.send_email(SUPPORT_TO, f"[Escalation] {reason}: session {m.session}",
                              f"A chat needs a human.\n\nReason: {reason}\nUser email: {m.email or 'not given'}\nSession: {m.session}\n\nTranscript:\n{transcript}\n")
        ticket = LOG.ticket(m.session, reason, status)
        reply = (f"I've passed this to our support team (ticket {ticket}). A person will reply " + (f"to {m.email} " if m.email else "") +
                 "within 24 hours." + ("" if m.email else " Please share your email address so they can reach you."))
    now = datetime.datetime.now().isoformat(timespec="seconds")
    LOG.add(dict(time=now, session=m.session, turn=len(hist) + 1, user_message=m.message, bot_reply=reply, action=action, intent=d["intent"]["intent"], confidence=d["intent"]["confidence"],
                 kb_article=top["article"] if action == "kb" else "", kb_score=top["score"], ticket=ticket, escalation_reason=reason))
    hist.append(dict(time=now, user=m.message, bot=reply, action=action))
    return dict(reply=reply, action=action, ticket=ticket or None, source=top["title"] if action == "kb" else None)
@app.get("/", response_class=HTMLResponse)
def page(): return open(os.path.join(S.HERE, "chat.html")).read()
