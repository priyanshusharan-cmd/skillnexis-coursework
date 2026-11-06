"""Reads an email: is it automated/FYI, what is being asked (action items with deadlines and priority), and is a
meeting being requested (with any proposed times). LLM when configured; otherwise rules + dateparser, which is
what the committed demo used. Both return the same structure."""
import datetime as dt, json, re
import dateparser
from dateparser.search import search_dates
from . import llm
AUTOMATED = re.compile(r"^(newsletter|no-?reply|noreply|notifications?|it|alerts?|events)\b|automated message|unsubscribe", re.I)
FYI = re.compile(r"\b(fyi|no need to reply|nothing to do|for your information|no action needed)\b", re.I)
REQUEST = re.compile(r"\b(can you|could you|would you|please|pls|need you to|make sure|let me know|send (me|over)|review|confirm|upload|submit|bring|look at)\b", re.I)
MEETING = re.compile(r"\b(meet(ing)?|call|catch up|sync|schedule|set up our|find an hour|discuss)\b", re.I)
URGENT = re.compile(r"\b(urgent|asap|immediately|today|right away|critical)\b", re.I)
DUR = re.compile(r"(\d+)\s*-?\s*(minute|min|hour|hr)s?", re.I)
def sentences(t): return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", t) if len(s.strip()) > 3]
def deadline_in(s, sent):
    """First future date phrase in a sentence, relative to when the email was sent ('by Thursday' -> that Thursday)."""
    phrases = re.findall(r"\b(?:by|before|until|due)\s+((?:end of day |the end of )?(?:next\s+)?(?:mon|tues|wednes|thurs|fri|satur|sun)day(?:\s+\d{1,2}(?::\d2)?\s*(?:am|pm))?|tomorrow|today|end of (?:day|week)|next week|\d{1,2}\s+\w+|\w+\s+\d{1,2}(?:st|nd|rd|th)?)", s, re.I)
    for p in phrases:
        p2 = re.sub(r"^(end of day|the end of)\s+", "", p, flags=re.I).replace("end of week", "friday")
        d = dateparser.parse(p2, settings={"RELATIVE_BASE": sent.replace(tzinfo=None), "PREFER_DATES_FROM": "future"})
        if d: return d.date().isoformat(), p
    return None, None
def tidy(t, sender):
    """'Can you send me the budget by Thursday?' -> 'Send Rahul the budget by Thursday' (a to-do, from my side)."""
    name = (re.sub(r"<.*?>", "", sender).strip().strip('"').split() or ["them"])[0]
    t = re.sub(r"^(?:(?:can|could|would) you|please|pls|i need you to|need you to)\s+", "", t.strip(), flags=re.I).rstrip("?. ")
    t = re.sub(r",\s*(?:otherwise|or else)\b.*$", "", t); t = re.sub(r"\b(me|us)\b", name, t); t = re.sub(r"\bI\b", name, t); t = re.sub(r"\byour\b", "my", t)
    return t[0].upper() + t[1:] if t else t
def rules(m):
    sent = dt.datetime.fromisoformat(m["date"]) if m["date"] else dt.datetime.now()
    sender_local = m["sender_email"].split("@")[0]
    automated = bool(AUTOMATED.search(sender_local) or m["list_unsubscribe"] or AUTOMATED.search(m["body"][-200:]))
    fyi = bool(FYI.search(m["body"]))
    items = []; S = sentences(m["body"])
    for k, s in enumerate(S):
        if MEETING.search(s) and re.search(r"\?|\bneed to set up\b|\bcan we\b|\bcould we\b", s, re.I): continue      # the meeting request itself is handled by scheduling
        if REQUEST.search(s) and not FYI.search(s) and not re.match(r"^(thanks|best|kind regards|regards)\b", s, re.I):
            parts = re.split(r"\s+and\s+(?=(?:your|the|my)\b)", s) if len(re.findall(r"\bby\b", s, re.I)) > 1 else [s]
            verb = re.search(r"\b(submit|send|upload|review|confirm|bring)\b", parts[0], re.I)
            for j, part in enumerate(parts):
                if j and verb: part = verb.group(1) + " " + part              # "... and your bio by 15 November" -> "submit your bio by 15 November"
                due, phrase = deadline_in(part, sent)
                if not due and k + 1 < len(S) and not REQUEST.search(S[k + 1]): due, phrase = deadline_in(S[k + 1], sent)   # "Ideally by end of day Friday."
                if not due and re.search(r"\bASAP|today\b", part, re.I): due = sent.date().isoformat()
                text = re.sub(r"^(hi|hello|hey)\b[^,]*,\s*", "", part, flags=re.I); text = re.sub(r"^(also|one more thing|just|so|update)[,:]?\s*", "", text, flags=re.I).lstrip(":;,- ")
                raw = text[0].upper() + text[1:]
                items.append(dict(text=tidy(raw, m["sender"]), raw=raw, due=due, due_phrase=phrase))
    if automated and not re.search(r"\bsubmit|confirm\b", m["body"], re.I): items = []
    if automated and items:                                      # automated mails with real deadlines (e.g. a speaker slot) still count
        pass
    meeting = None
    if MEETING.search(m["body"]) and not automated and not fyi and re.search(r"\?|\bcan we\b|\bcould we\b|\bwould you be open\b", m["body"], re.I):
        dm = DUR.search(m["body"]); minutes = int(dm.group(1)) * (60 if dm and dm.group(2).lower().startswith("h") else 1) if dm else (60 if re.search(r"\ban hour\b", m["body"]) else 30)
        prefs = []; nw = bool(re.search(r"next week", m["body"], re.I))
        for txt, d in (search_dates(m["body"], settings={"RELATIVE_BASE": sent.replace(tzinfo=None), "PREFER_DATES_FROM": "future"}) or []):
            if re.search(r"(mon|tues|wednes|thurs|fri)day|\d(am|pm)|tomorrow", txt, re.I):
                d = d.date()
                if nw and re.search(r"(mon|tues|wednes|thurs|fri)day", txt, re.I) and not re.search(r"next", txt, re.I):     # "next week ... Tuesday" = next week's Tuesday
                    nxt = sent.date() + dt.timedelta(days=7 - sent.weekday()); d = nxt + dt.timedelta(days=d.weekday())
                if d > sent.date(): prefs.append(dict(phrase=txt.strip(), date=d.isoformat(), time=dt.datetime.combine(d, dt.time()).strftime("%H:%M") if False else (re.search(r"(\d{1,2})\s*(am|pm)", txt, re.I) and dt.datetime.strptime(re.search(r"(\d{1,2})\s*(am|pm)", txt, re.I).group(0).replace(" ", "").upper(), "%I%p").strftime("%H:%M")) or None))
        part = "afternoon" if re.search(r"afternoon", m["body"], re.I) else "morning" if re.search(r"morning", m["body"], re.I) else None
        meeting = dict(minutes=minutes, preferences=prefs, part_of_day=part, next_week=bool(re.search(r"next week", m["body"], re.I)))
    urgent = bool(URGENT.search(m["body"]) or (URGENT.search(m["subject"]) and not re.match(r"^re:", m["subject"], re.I)))
    if re.search(r"\b(it'?s fixed|resolved|all good now)\b", m["body"], re.I): urgent = False
    for it in items:
        days = (dt.date.fromisoformat(it["due"]) - sent.date()).days if it["due"] else None
        it["priority"] = "high" if urgent or (days is not None and days <= 1) else "medium" if days is not None and days <= 4 else "low"
    category = "automated" if automated and not items else "fyi" if fyi and not items else "action" if items or meeting else "conversation"
    return dict(category=category, urgent=urgent, action_items=items, meeting=meeting, needs_reply=category in ("action",) and not automated, engine="rules")
PROMPT = """Today is {date}. Analyse this email for the recipient. Return JSON:
{{"category": "action|fyi|automated|conversation", "urgent": bool, "needs_reply": bool,
 "action_items": [{{"text": "imperative task", "due": "YYYY-MM-DD or null", "priority": "high|medium|low"}}],
 "meeting": null or {{"minutes": int, "preferences": [{{"date": "YYYY-MM-DD", "time": "HH:MM or null"}}], "part_of_day": "morning|afternoon|null"}}}}
FROM: {sender}\nSUBJECT: {subject}\n\n{body}"""
def understand(m):
    try:
        out, eng = llm.chat(PROMPT.format(date=m["date"], sender=m["sender"], subject=m["subject"], body=m["body"][:6000]), json_mode=True, temperature=0)
        d = llm.parse_json(out); d["engine"] = eng; return d
    except RuntimeError:
        return rules(m)
