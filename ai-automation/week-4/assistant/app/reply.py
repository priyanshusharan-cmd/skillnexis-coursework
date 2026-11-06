"""Reply drafts. An LLM writes them when configured; otherwise templates built from what was understood (the action
items, a proposed meeting time with its .ics invite). Drafts are never sent automatically: a person approves each one
on the dashboard."""
import re
from . import llm
def first_name(sender):
    n = re.sub(r"<.*?>", "", sender).strip().strip('"'); return (n.split()[0] if n else "there")
def draft(m, u, slot=None, me="Priya"):
    try:
        prompt = (f"Write a short, warm, professional reply from {me}. Acknowledge each action item with a realistic commitment (do not invent facts). "
                  + (f"Propose the meeting at {slot['start']:%A %d %B, %I:%M %p} ({slot['minutes']} min) and say an invite is attached. " if slot else "") +
                  f"\n\nEMAIL FROM {m['sender']}\nSUBJECT {m['subject']}\n\n{m['body'][:4000]}\n\nACTION ITEMS: {u['action_items']}")
        body, eng = llm.chat(prompt, temperature=.5); return body.strip(), eng
    except RuntimeError:
        L = [f"Hi {first_name(m['sender'])},", ""]
        if u.get("urgent"): L.append("Thanks for flagging this; I'm looking at it now and will update you shortly.")
        items = u["action_items"]
        if items:
            if not u.get("urgent"): L.append("Thanks for your email. Noted:" if len(items) > 1 else "Thanks for your email.")
            for it in items:
                task = re.sub(r"^(can|could|would) you\s+|^please\s+|\?$", "", it.get("raw", it["text"]), flags=re.I).rstrip(".?")
                task = re.sub(r"\b(I|me)\b", "you", task); task = re.sub(r"\byour\b", "my", task)
                task = re.split(r",\s*(?:otherwise|or else|because|since)\b", task)[0]
                when = f" by {it['due_phrase'] or it['due']}" if it.get("due") and not re.search(r"\b(by|before|until|asap|today)\b", task, re.I) else ""
                L.append(f"- I'll {task[0].lower() + task[1:]}{when}." if len(items) > 1 else f"I'll {task[0].lower() + task[1:]}{when}.")
        if slot:
            L += ["", f"For the meeting, how about {slot['start']:%A %d %B at %I:%M %p} ({slot['minutes']} minutes)? I've attached a calendar invite; if that doesn't suit, send me a couple of times that work for you."]
        L += ["", "Best regards,", me]
        return "\n".join(L).replace("\n\n\n", "\n\n"), "template"
