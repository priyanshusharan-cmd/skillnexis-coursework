"""Calendar: free-slot search and booking. Local .ics calendar by default; Google Calendar when
GOOGLE_CALENDAR_ID + GOOGLE_SERVICE_ACCOUNT_JSON are set (share the calendar with the service account; free).
Rules: working hours 09:30-17:30 Asia/Kolkata, Mon-Fri, 15-minute grid, 15-minute buffer around existing events, a
requested date/time is tried first, then the requested part of the day, then the next working days."""
import datetime as dt, os, uuid
from zoneinfo import ZoneInfo
from icalendar import Calendar, Event
TZ = ZoneInfo(os.environ.get("TZ_NAME", "Asia/Kolkata")); START, END, BUF = dt.time(9, 30), dt.time(17, 30), dt.timedelta(minutes=15)
PARTS = {"morning": (dt.time(9, 30), dt.time(12, 30)), "afternoon": (dt.time(13, 30), dt.time(17, 30))}
ICS = os.environ.get("CALENDAR_ICS", os.path.join(os.path.dirname(__file__), "..", "data", "calendar.ics"))
def _load():
    return Calendar.from_ical(open(ICS, "rb").read()) if os.path.exists(ICS) else Calendar()
def busy():
    out = []
    if os.environ.get("GOOGLE_CALENDAR_ID"):
        svc = _google(); now = dt.datetime.now(TZ)
        for e in svc.events().list(calendarId=os.environ["GOOGLE_CALENDAR_ID"], timeMin=now.isoformat(), timeMax=(now + dt.timedelta(days=21)).isoformat(), singleEvents=True).execute().get("items", []):
            if "dateTime" in e["start"]: out.append((dt.datetime.fromisoformat(e["start"]["dateTime"]), dt.datetime.fromisoformat(e["end"]["dateTime"]), e.get("summary", "")))
        return out
    for c in _load().walk("VEVENT"):
        a, b = c.decoded("DTSTART"), c.decoded("DTEND"); a = a if a.tzinfo else a.replace(tzinfo=TZ); b = b if b.tzinfo else b.replace(tzinfo=TZ); out.append((a, b, str(c.get("SUMMARY"))))
    return out
def free(a, b, B):
    return all(b + BUF <= x or a >= y + BUF for x, y, _ in B)
def find_slot(meeting, now=None):
    now = now or dt.datetime.now(TZ); dur = dt.timedelta(minutes=meeting.get("minutes") or 30); B = busy(); tried = []
    def scan(day, lo=START, hi=END):
        t = dt.datetime.combine(day, lo, TZ)
        while t + dur <= dt.datetime.combine(day, hi, TZ):
            if t > now + dt.timedelta(hours=2) and free(t, t + dur, B): return t
            t += dt.timedelta(minutes=15)
    part = PARTS.get(meeting.get("part_of_day") or "", (START, END))
    for p in meeting.get("preferences", []):                                   # 1) exactly what they asked for
        d = dt.date.fromisoformat(p["date"])
        if d.weekday() > 4: continue
        if p.get("time"):
            t = dt.datetime.combine(d, dt.time.fromisoformat(p["time"]), TZ)
            if t > now and free(t, t + dur, B): return t, f"their proposed time ({p.get('phrase', p['date'])})"
            tried.append(f"{t:%a %d %b %H:%M} ({'past' if t <= now else 'busy'})")
        else:
            t = scan(d, *part)
            if t: return t, f"their proposed day ({p.get('phrase', p['date'])}" + (f", {meeting['part_of_day']}" if meeting.get("part_of_day") and meeting["part_of_day"] not in p.get("phrase", "").lower() else "") + ")"
            tried.append(f"{d:%a %d %b} (no free {meeting.get('part_of_day') or 'slot'})")
    d = now.date() + dt.timedelta(days=(7 - now.weekday()) if meeting.get("next_week") else 1)   # 2) next working days
    for _ in range(15):
        if d.weekday() < 5:
            t = scan(d, *part) or scan(d)
            if t: return t, "first free slot" + (" next week" if meeting.get("next_week") else "") + (f" (tried: {', '.join(tried)})" if tried else "")
        d += dt.timedelta(days=1)
    return None, "no free slot in 3 weeks"
def book(title, start, minutes, attendee, description=""):
    end = start + dt.timedelta(minutes=minutes); uid = f"{uuid.uuid4()}@assistant"
    if os.environ.get("GOOGLE_CALENDAR_ID"):
        ev = _google().events().insert(calendarId=os.environ["GOOGLE_CALENDAR_ID"], body=dict(summary=title, description=description, start={"dateTime": start.isoformat()},
                                       end={"dateTime": end.isoformat()}, attendees=[{"email": attendee}])).execute(); return ev["id"], None
    cal = _load(); e = Event(); e.add("uid", uid); e.add("summary", title); e.add("dtstart", start); e.add("dtend", end); e.add("description", description); e.add("attendee", f"mailto:{attendee}")
    cal.add_component(e); open(ICS, "wb").write(cal.to_ical())
    inv = Calendar(); inv.add("prodid", "-//AI business assistant//EN"); inv.add("version", "2.0"); inv.add("method", "REQUEST"); inv.add_component(e)
    os.makedirs(os.path.join(os.path.dirname(ICS), "invites"), exist_ok=True); path = os.path.join(os.path.dirname(ICS), "invites", uid.split("@")[0][:8] + ".ics"); open(path, "wb").write(inv.to_ical())
    return uid, path
def _google():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    cr = service_account.Credentials.from_service_account_file(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"], scopes=["https://www.googleapis.com/auth/calendar"])
    return build("calendar", "v3", credentials=cr, cache_discovery=False)
