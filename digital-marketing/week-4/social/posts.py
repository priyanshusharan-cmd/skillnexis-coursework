"""Hisaab launch campaign "Hisaab Barabar" (settle up evenly): 21 social posts from one template.
    python social/posts.py && node social/render.js
"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
C = {"brand": "#0F766E", "dark": "#0B3B37", "tint": "#D5F5EF", "ink": "#101828", "owe": "#B42318", "owed": "#067647", "amber": "#FEF0C7", "cream": "#F7FBF9"}
# id, kind (f=feed 1080x1350, s=story/reel 1080x1920), bg, fg, eyebrow, title, body, extra
P = [
 ("01-launch", "f", C["dark"], "#fff", "Launching on Android", "Kaun kitna dega? Hisaab batayega.", "Split hostel, flat and trip expenses. Settle with any UPI app in one tap.", "cta:Join the waitlist"),
 ("02-problem", "f", C["cream"], C["ink"], "Sound familiar?", "“Bhai, ₹120 de dena.”\n“Kaunsa ₹120?”", "Every hostel group chat, every week. There's a better way.", ""),
 ("03-howto", "f", C["tint"], C["ink"], "How it works", "Add. Split. Settle.", "1 · Add an expense in 10 seconds\n2 · See one balance per friend\n3 · Pay with any UPI app", ""),
 ("04-upi", "f", C["cream"], C["ink"], "Your money, your UPI", "We never hold your money.", "Settle up opens your own UPI app with the amount filled in. Bank to bank. We never see your PIN.", "lock"),
 ("05-simplify", "f", C["dark"], "#fff", "Simplify debts", "5 payments → 3", "Same totals, fewer UPI transfers. Hisaab works out who pays whom.", ""),
 ("06-trip", "f", C["amber"], C["ink"], "Goa trip?", "Split by shares, not by guilt.", "Someone skipped the parasailing? They pay fewer shares. Fair, automatically.", ""),
 ("07-meme", "f", "#fff", C["ink"], "Hostel truths", "The friend who says “I'll pay you later”", "…and the app that remembers so you don't have to. 😌", "meme"),
 ("08-free", "f", C["brand"], "#fff", "No daily limits", "Free. Actually free.", "Add as many expenses as your room creates. No daily cap, no paywall on splitting.", ""),
 ("09a-carousel", "f", C["dark"], "#fff", "Swipe →", "5 fair ways to split hostel costs", "A 60-second guide", "dots:0"),
 ("09b-carousel", "f", C["cream"], C["ink"], "01 · Wi-Fi & supplies", "Equal split", "Everyone uses it, everyone pays the same.", "dots:1"),
 ("09c-carousel", "f", C["cream"], C["ink"], "02 · Food orders", "Only who ate", "Untick whoever wasn't there.", "dots:2"),
 ("09d-carousel", "f", C["cream"], C["ink"], "03 · Trips", "By shares", "Missed a day? Fewer shares.", "dots:3"),
 ("10a-carousel", "f", C["tint"], C["ink"], "Swipe →", "Hisaab vs the notes app", "Why your screenshot ledger keeps failing", "dots:0"),
 ("10b-carousel", "f", "#fff", C["ink"], "Notes app", "Nobody reads it.", "Hisaab: everyone sees the same balance, live.", "dots:1"),
 ("10c-carousel", "f", "#fff", C["ink"], "Notes app", "You do the maths.", "Hisaab: splits, rounding and simplifying done for you.", "dots:2"),
 ("10d-carousel", "f", C["brand"], "#fff", "Notes app", "Asking feels awkward.", "Hisaab: a friendly reminder, sent by you, in your tone.", "dots:3"),
 ("11-reel-demo", "s", C["dark"], "#fff", "Reel", "Settle a ₹386 debt in 9 seconds", "", "play"),
 ("12-reel-pov", "s", C["amber"], C["ink"], "Reel", "POV: you're the friend who always pays first", "", "play"),
 ("13-reel-creator", "s", C["brand"], "#fff", "Reel · creator collab", "We gave 4 roommates one month. Here's who owed whom.", "", "play"),
 ("14-story-poll", "s", C["tint"], C["ink"], "Poll", "Who pays first in your room?", "A · Me, always\nB · Whoever has UPI open\nC · We fight about it", "sticker"),
 ("16-tag", "f", C["amber"], C["ink"], "Tag them 👇", "Tag the roommate who owes you money", "No names, no shame. Just Hisaab.", ""),
 ("17-flat", "f", C["cream"], C["ink"], "Moving into a flat?", "Rent, maid, groceries: sorted.", "One group, recurring expenses, a monthly settle day. Flatmate drama: optional.", ""),
 ("18-founding", "f", C["dark"], "#fff", "Founding roommates", "First 1,000 sign-ups get a badge for life", "Join the waitlist, invite your room, be part of the first Hisaab groups.", "cta:Claim your spot"),
 ("19-tips", "f", C["tint"], C["ink"], "Trip money rule", "Settle before the trip ends.", "Debts are smallest and memories freshest on the last night. Hisaab makes it a 2-minute job.", ""),
 ("20-story-thisorthat", "s", C["amber"], C["ink"], "This or that", "Split equally or by what you ate?", "Equally: friendship first\nBy what you ate: justice first", "sticker"),
 ("21-story-countdown", "s", C["brand"], "#fff", "Countdown", "Hisaab lands on Android in 7 days", "Tap ‘remind me’ and we'll ping you at launch.", "cta:Remind me"),
 ("22-reel-settleday", "s", C["tint"], C["ink"], "Reel", "Room 214's monthly Settle Day (it takes 2 minutes)", "", "play"),
 ("15-story-waitlist", "s", C["dark"], "#fff", "Link sticker", "Be first to try Hisaab", "Waitlist members get early access + a ‘Founding roommate’ badge.", "cta:Join the waitlist →"),
]
CSS = "*{box-sizing:border-box;margin:0}body{background:#ccc;padding:30px;display:flex;flex-wrap:wrap;gap:30px;font-family:Inter,sans-serif}" + \
 ".a{position:relative;overflow:hidden;display:flex;flex-direction:column;padding:96px} .f{width:1080px;height:1350px} .s{width:1080px;height:1920px;padding:130px 100px}" + \
 ".logo{font:800 40px 'Inter Display',Inter;display:flex;gap:16px;align-items:center}.logo i{width:56px;height:56px;border-radius:16px;display:grid;place-items:center;font-style:normal;font:800 30px Inter}" + \
 ".k{font:700 30px Inter;letter-spacing:.12em;text-transform:uppercase;opacity:.85;margin-top:120px}h1{font:800 100px/1.04 'Inter Display',Inter;letter-spacing:-.02em;margin-top:28px;white-space:pre-line}" + \
 "p{font:500 42px/1.4 Inter;margin-top:36px;white-space:pre-line;max-width:860px}.foot{margin-top:auto;display:flex;justify-content:space-between;align-items:center;font:600 32px Inter;opacity:.85}" + \
 ".cta{display:inline-block;margin-top:56px;padding:26px 44px;border-radius:24px;font:800 42px Inter}.dots{display:flex;gap:14px}.dots b{width:18px;height:18px;border-radius:50%;background:currentColor;opacity:.3}.dots b.on{opacity:1}" + \
 ".play{width:200px;height:200px;border-radius:50%;background:rgba(255,255,255,.9);display:grid;place-items:center;margin-top:auto}.play::after{content:'';border-left:66px solid #0B3B37;border-top:42px solid transparent;border-bottom:42px solid transparent;margin-left:16px}" + \
 ".phone{position:absolute;right:-60px;bottom:-140px;width:460px;border-radius:56px;box-shadow:0 30px 60px rgba(0,0,0,.3);border:14px solid #111}.sticker{background:#fff;border-radius:40px;padding:44px;margin-top:60px;color:#101828;box-shadow:0 20px 50px rgba(0,0,0,.12)}"
SHOTS = {"01-launch": "05-home", "05-simplify": "11-balances-simplify", "08-free": "07-add-expense", "11-reel-demo": "13-payment-success", "04-upi": "12-settle-up"}

def post(id_, k, bg, fg, eb, t, body, ex):
    inner = f'<div class="logo"><i style="background:{fg};color:{bg}">h</i>Hisaab</div><div class="k">{eb}</div><h1 style="{"font-size:118px" if k == "s" else ""}">{t}</h1>'
    if ex == "sticker":
        inner += '<div class="sticker">' + "".join(f'<div style="background:#F2F4F7;border-radius:20px;padding:28px 32px;margin:14px 0;font:700 44px Inter">{x}</div>' for x in body.split("\n")) + "</div>"
    elif body: inner += f"<p>{body}</p>"
    if ex.startswith("cta:"): inner += f'<div><span class="cta" style="background:{fg};color:{bg}">{ex[4:]}</span></div>'
    if ex == "play": inner += '<div class="play"></div>'
    if ex == "meme": inner += '<div style="margin-top:50px;display:flex;gap:24px"><div style="flex:1;background:#FDECEA;border-radius:30px;padding:36px;font:700 40px Inter;color:#B42318">Before: “I’ll pay you later” 🙃</div><div style="flex:1;background:#DCFAE6;border-radius:30px;padding:36px;font:700 40px Inter;color:#067647">After: “Paid ₹120 via UPI ✓”</div></div>'
    if id_ in SHOTS: inner = inner.replace("<p>", '<p style="max-width:540px">').replace("<h1 style=\"\">", '<h1 style="max-width:700px">'); inner += f'<img class="phone" src="../../../ui-ux/week-4/exports/screens/{SHOTS[id_]}.png" alt="">'
    dots = ex.startswith("dots:")
    inner += f'<div class="foot"><span>@hisaab.app</span>{"<div class=dots>" + "".join(f"<b class={chr(34)}{"on" if i == int(ex[5:]) else ""}{chr(34)}></b>" for i in range(4)) + "</div>" if dots else ""}</div>'
    return f'<div class="a {k}" id="{id_}" style="background:{bg};color:{fg}">{inner}</div>'

open(os.path.join(HERE, "posts.html"), "w").write(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(post(*p) for p in P)}</body></html>")
ids = sorted({p[0][:2] for p in P}); print(len(P), "images,", len(ids), "posts")
