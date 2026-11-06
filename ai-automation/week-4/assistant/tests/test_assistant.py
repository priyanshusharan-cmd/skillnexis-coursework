import datetime as dt, os, shutil, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zoneinfo import ZoneInfo
TMP = tempfile.mkdtemp(); shutil.copy(os.path.join(os.path.dirname(__file__), "..", "data", "calendar.ics"), os.path.join(TMP, "cal.ics"))
os.environ.update(ASSISTANT_DB=os.path.join(TMP, "a.sqlite"), CALENDAR_ICS=os.path.join(TMP, "cal.ics"), POLL_MINUTES="0")
from app import calendar_svc as cal, understand
TZ = ZoneInfo("Asia/Kolkata")
def mail(body, subject="Hello", sender="Rahul Verma <rahul@example.com>", date="2026-11-02T09:00:00+05:30"):
    return dict(message_id="<t>", sender=sender, sender_email=sender.split("<")[1].strip(">"), subject=subject, date=date, body=body, list_unsubscribe=False)
def test_action_item_with_relative_deadline():
    u = understand.rules(mail("Hi Priya,\n\nCan you send me the final budget by Thursday? Thanks"))
    assert u["action_items"][0]["text"] == "Send Rahul the final budget by Thursday" and u["action_items"][0]["due"] == "2026-11-05"
def test_deadline_in_next_sentence_and_two_deadlines_in_one():
    u = understand.rules(mail("Could you review the contracts? Ideally by end of day Friday."));  assert u["action_items"][0]["due"] == "2026-11-06"
    u = understand.rules(mail("Please submit your slides by 25 November and your bio by 15 November.")); assert [i["due"] for i in u["action_items"]] == ["2026-11-25", "2026-11-15"]
def test_fyi_and_automated_have_no_tasks():
    assert understand.rules(mail("FYI, the policy is attached. Nothing to do for now."))["category"] == "fyi"
    assert understand.rules(mail("Top stories this week. Unsubscribe at any time.", sender="News <news@x.example.com>"))["category"] == "automated"
def test_meeting_next_week_weekdays_shift_to_next_week():
    u = understand.rules(mail("Could we schedule a 30-minute call next week? I'm free Tuesday or Wednesday afternoon."))
    assert u["meeting"]["minutes"] == 30 and [p["date"] for p in u["meeting"]["preferences"]] == ["2026-11-10", "2026-11-11"] and u["meeting"]["part_of_day"] == "afternoon"
def test_slot_avoids_busy_and_buffers():
    now = dt.datetime(2026, 11, 6, 18, 0, tzinfo=TZ)
    t, why = cal.find_slot(dict(minutes=60, preferences=[dict(date="2026-11-10", time=None, phrase="Tuesday")], part_of_day="morning"), now=now)
    assert t == dt.datetime(2026, 11, 10, 11, 15, tzinfo=TZ)                    # 10-11 is busy, +15 min buffer
def test_proposed_time_in_past_falls_back():
    now = dt.datetime(2026, 11, 6, 18, 0, tzinfo=TZ)
    t, why = cal.find_slot(dict(minutes=30, preferences=[dict(date="2026-11-05", time="15:00", phrase="Thursday 3pm")], next_week=True), now=now)
    assert t.date() >= dt.date(2026, 11, 9) and "past" in why
def test_api_smoke():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app); r = c.post("/api/run").json(); assert r["new"] == 14 and r["errors"] == 0
    s = c.get("/api/status").json(); assert s["emails"] == 14 and s["meetings"] == 3
    d = c.get("/api/drafts").json(); assert c.post(f"/api/drafts/{d[0]['id']}/approve").json()["status"].startswith("approved")
    assert "Weekly report" in c.get("/report/weekly").text
