"""Conversation memory per (user, session), persisted in SQLite: the last WINDOW exchanges verbatim plus a running
summary of older ones (written by the LLM when configured, extractive otherwise). Follow-ups are rewritten into
standalone search queries so retrieval works for 'what does it return?' or 'going back to the first topic'."""
import re
from . import store
from .text import STOP, content_words, words
WINDOW = 3
def topic(q): return [w for w in words(q) if w not in STOP and len(w) > 2][:5]           # unstemmed: these words go back into a query
def context(uid, session):
    turns = store.history(uid, session, 2 * WINDOW); s = store.get_summary(uid, session)
    lines = ([f"Summary of earlier conversation: {s}"] if s else []) + [f"{'User' if t['role'] == 'user' else 'Assistant'}: {re.sub(r'\s*\[\d+\]', '', t['content'])[:600]}" for t in turns]
    return "\n".join(lines)
def standalone(uid, session, q):
    hist = store.history(uid, session); users = [t["content"] for t in hist if t["role"] == "user"]
    if not users: return q
    ql = q.lower()
    if re.search(r"\b(first topic|going back|earlier question|at the start|originally)\b", ql): return q + " " + " ".join(topic(users[0]))
    if re.search(r"\b(it|its|that|this|they|them|those|these|one)\b", ql) and len(content_words(q)) <= 4: return q + " " + " ".join(topic(users[-1]))
    return q
def remember(uid, session, q, a):
    store.add_message(uid, session, "user", q); store.add_message(uid, session, "assistant", a)
    hist = store.history(uid, session)
    if len(hist) > 2 * WINDOW and len(hist) % 2 == 0:                                 # fold the exchange that just left the window
        old_q, old_a = hist[-2 * WINDOW - 2]["content"], hist[-2 * WINDOW - 1]["content"]
        first = re.split(r"(?<=[.!?])\s+", re.sub(r"\s*\[\d+\]", "", old_a).strip())[0][:200]
        s = store.get_summary(uid, session); store.set_summary(uid, session, (s + " " if s else "") + f"User asked about {', '.join(topic(old_q))}; answer: {first}")
