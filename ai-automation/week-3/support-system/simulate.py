"""SIMULATED traffic for a demo: 12 scripted conversations (written to cover every path: KB answers, FAQ, small talk,
fallback, a repeated fallback that escalates, a frustrated user, account requests, a human request) are sent through
the real API with FastAPI's test client, then the daily report runs. The users are scripted, not real.
    python simulate.py   (uses a fresh support.sqlite)"""
import os
os.environ["SUPPORT_DB"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "support.sqlite")
if os.path.exists(os.environ["SUPPORT_DB"]): os.remove(os.environ["SUPPORT_DB"])
import shutil; shutil.rmtree(os.path.join(os.path.dirname(os.path.abspath(__file__)), "outbox"), ignore_errors=True)
from fastapi.testclient import TestClient
import app as A
C = TestClient(A.app)
CONVS = {
 "s01": ["hi", "python is not recognized in cmd after installing", "thanks!"],
 "s02": ["how do I install python on my macbook", "it asks to install developer tools, is that ok?"],
 "s03": ["is the course free?", "do i get a certifcate at the end"],
 "s04": ["I get IndentationError on line 3", "what does TypeError can only concatenate str mean"],
 "s05": ["when is the next lesson coming out", "how long will the whole course take"],
 "s06": ["can i do this on my phone without installing"],
 "s07": ["please delete my account and all my data"],
 "s08": ["how do i stop getting your emails"],
 "s09": ["what's the weather in pune", "can you book me a train ticket"],
 "s10": ["the loops video keeps buffering", "still doesn't help, this is useless"],
 "s11": ["i want to talk to a real person about the mini project review"],
 "s12": ["where do i get feedback on my practice code", "bye"],
}
for s, msgs in CONVS.items():
    for m in msgs:
        r = C.post("/chat", json={"session": s, "message": m, **({"email": "learner@example.com"} if s == "s11" else {})}).json()
        print(f"{s} USER: {m}\n    BOT [{r['action']}{' ' + r['ticket'] if r['ticket'] else ''}]: {r['reply'][:150].replace(chr(10), ' ')}")
print(C.get("/health").json())
import daily_report
k, md, day = daily_report.build(24); os.makedirs("reports", exist_ok=True); open(f"reports/daily-{day}.md", "w").write(md); open(f"reports/daily-{day}.html", "w").write(daily_report.to_html(md))
print(md)
