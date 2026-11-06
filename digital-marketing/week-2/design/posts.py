"""Bean & Bloom "Study Fuel" campaign: 15 Instagram assets generated from one brand kit.

Feed posts are 4:5 (1080 x 1350), carousels 4:5 per slide, reel covers and stories 9:16 (1080 x 1920).
    python design/posts.py && node design/render.js   -> exports/posts/*.png
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = {"cream": "#FFF7EC", "espresso": "#3B2416", "sage": "#4E6B4A", "sage-tint": "#E3EBDD", "bloom": "#E8A0A6",
         "bloom-tint": "#FBE3E5", "caramel": "#B9692B", "ink": "#2A1A10"}

CSS = """
*{box-sizing:border-box;margin:0} body{background:#ddd;display:flex;flex-wrap:wrap;gap:40px;padding:40px;font-family:Inter,sans-serif}
.a{position:relative;overflow:hidden;background:var(--cream);color:var(--espresso);display:flex;flex-direction:column;padding:88px}
.f{width:1080px;height:1350px} .s{width:1080px;height:1920px;padding:120px 96px}
h1{font:800 104px/1.02 'Inter Display',Inter;letter-spacing:-.02em} h2{font:800 76px/1.05 'Inter Display',Inter;letter-spacing:-.01em}
p{font:500 40px/1.35 Inter} .k{font:700 30px Inter;letter-spacing:.14em;text-transform:uppercase}
.logo{display:flex;align-items:center;gap:18px;font:800 36px 'Inter Display',Inter} .logo i{width:56px;height:56px;border-radius:50%;background:var(--espresso);position:relative;display:block}
.logo i::after{content:"";position:absolute;inset:14px 16px;border-radius:50% 50% 50% 0;background:var(--bloom);transform:rotate(-45deg)}
.foot{margin-top:auto;display:flex;justify-content:space-between;align-items:center} .handle{font:600 32px Inter;opacity:.8}
.pill{display:inline-block;padding:18px 34px;border-radius:999px;font:800 40px Inter}
.blob{position:absolute;border-radius:50%;z-index:0} .z{position:relative;z-index:1}
.cup{position:absolute;z-index:0}
.num{font:800 220px/1 'Inter Display',Inter;letter-spacing:-.04em}
.dots{display:flex;gap:14px} .dots b{width:18px;height:18px;border-radius:50%;background:currentColor;opacity:.3} .dots b.on{opacity:1}
.list li{font:600 44px/1.3 Inter;margin:22px 0;list-style:none;display:flex;gap:24px;align-items:flex-start} .list li::before{content:"";flex:none;width:28px;height:28px;margin-top:12px;border-radius:50%;background:var(--sage)}
.sticker{background:#fff;border-radius:40px;padding:48px;box-shadow:0 20px 50px rgba(59,36,22,.18);color:var(--espresso)}
.bar{height:96px;border-radius:24px;background:var(--sage-tint);display:flex;align-items:center;padding:0 36px;font:700 42px Inter;margin-top:24px}
.play{width:180px;height:180px;border-radius:50%;background:rgba(255,247,236,.92);display:grid;place-items:center}
.play::after{content:"";border-left:60px solid var(--espresso);border-top:38px solid transparent;border-bottom:38px solid transparent;margin-left:14px}
"""
VARS = ":root{" + ";".join(f"--{k}:{v}" for k, v in BRAND.items()) + "}"


def cup(x, y, s=1.0, fill="#3B2416", foam="#FFF7EC", rot=0):
    return (f'<svg class="cup" style="left:{x}px;top:{y}px;transform:rotate({rot}deg)" width="{420 * s}" height="{460 * s}" viewBox="0 0 420 460">'
            f'<path d="M60 120h260l-28 300a30 30 0 0 1-30 28H118a30 30 0 0 1-30-28z" fill="{fill}"/><path d="M320 170h30a50 50 0 0 1 0 100h-40" stroke="{fill}" stroke-width="26" fill="none"/>'
            f'<ellipse cx="190" cy="122" rx="132" ry="26" fill="{foam}"/><path d="M150 70c0-30 30-30 30-60M210 80c0-30 30-30 30-60" stroke="{fill}" stroke-width="14" stroke-linecap="round" fill="none" opacity=".5"/></svg>')


def logo(color="var(--espresso)"):
    return f'<div class="logo z" style="color:{color}"><i style="background:{color}"></i>Bean &amp; Bloom</div>'


def foot(color="var(--espresso)", extra=""):
    return f'<div class="foot z" style="color:{color}"><span class="handle">@beanandbloom.blr</span>{extra}</div>'


def asset(id_, label, cls, inner, bg="var(--cream)", color="var(--espresso)"):
    return f'<div><div style="font:600 18px Inter;color:#555;margin-bottom:8px">{label}</div><div class="a {cls}" id="{id_}" style="background:{bg};color:{color}">{inner}</div></div>'


def posts():
    A = []
    # ---------- feed posts (also the 5 graphics for the weekly task)
    A.append(asset("01-launch", "01 · Feed: campaign launch", "f",
        '<div class="blob" style="width:900px;height:900px;background:var(--bloom-tint);right:-300px;top:-220px"></div>' + cup(600, 800, 1.05) + logo()
        + '<div class="z" style="margin-top:120px"><div class="k" style="color:var(--sage)">Study Fuel · 10–23 Nov</div><h1 style="margin-top:28px;max-width:640px">Exam season? We saved you a corner.</h1>'
        '<p style="margin-top:36px;max-width:520px">Quiet tables, fast Wi-Fi and refills that keep up with your syllabus.</p></div>' + foot()))
    A.append(asset("02-offer", "02 · Feed: the offer", "f",
        logo("var(--cream)") + '<div class="z" style="margin-top:110px"><div class="k" style="color:var(--bloom)">Weekdays · 3–7 pm · show your college ID</div>'
        '<h1 style="margin-top:28px">Study Fuel combo</h1><div style="display:flex;align-items:flex-end;gap:28px;margin-top:40px"><span class="num" style="color:var(--bloom)">₹149</span><span style="font:600 44px Inter;margin-bottom:30px;text-decoration:line-through;opacity:.6">₹210</span></div>'
        '<p style="margin-top:24px;max-width:600px">Filter coffee or masala chai + banana-walnut bread.</p></div>' + cup(640, 760, .95, "#FFF7EC", "#E8A0A6", 8) + foot("var(--cream)"), "var(--espresso)", "var(--cream)"))
    A.append(asset("03-tip", "03 · Feed: study tip", "f",
        logo() + '<div class="z" style="margin-top:110px"><div class="k" style="color:var(--caramel)">Study tip #1</div><h2 style="margin-top:28px">The Bean &amp; Bloom Pomodoro</h2>'
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:56px">'
        '<div class="sticker"><div class="num" style="font-size:160px;color:var(--sage)">25</div><p style="font-weight:700">minutes of focus</p></div>'
        '<div class="sticker" style="background:var(--bloom-tint)"><div class="num" style="font-size:160px">5</div><p style="font-weight:700">minutes to refill</p></div></div>'
        '<p style="margin-top:48px">Four rounds, then a proper break. Your phone stays in the bag.</p></div>' + foot(extra='<span class="pill" style="background:var(--sage);color:#fff;font-size:30px">Save this</span>'),
        "var(--sage-tint)"))
    A.append(asset("04-amenities", "04 · Feed: why study here", "f",
        logo() + '<div class="z" style="margin-top:100px"><h2>Built for long study days</h2><ul class="list" style="padding:0;margin-top:48px">'
        '<li>Wi-Fi tested at 100 Mbps, every table</li><li>A plug point at every seat</li><li>Quiet zone upstairs: no calls, no music</li><li>Free water refills, always</li><li>Open 8 am–11 pm through exams</li></ul></div>'
        + cup(700, 930, .7, "#4E6B4A") + foot()))
    A.append(asset("05-ugc", "05 · Feed: share your setup (UGC call)", "f",
        '<div class="blob" style="width:760px;height:760px;background:var(--bloom);left:-260px;bottom:-260px;opacity:.5"></div>' + logo()
        + '<div class="z" style="margin-top:110px"><div class="k" style="color:var(--sage)">#StudyFuelCorner</div><h1 style="margin-top:28px">Show us your study corner.</h1>'
        '<p style="margin-top:36px;max-width:760px">Post your table setup, tag @beanandbloom.blr and use #StudyFuelCorner. Every Friday we pick 3 setups for a free Study Fuel combo.</p>'
        '<p style="margin-top:28px;font-size:30px;opacity:.75">We only repost with your permission. Faces optional.</p></div>' + foot(), "var(--bloom-tint)"))
    # ---------- carousels (3 carousels, 11 slides)
    spots = [("The window bar", "Morning light, 8 seats, plugs under the counter. Best before noon."), ("The quiet loft", "Upstairs, phones on silent, no music. Pin-drop until 9 pm."),
             ("The big table", "Seats 8, whiteboard on the wall. Bring your study group."), ("The garden nook", "Plants, breeze, chai. For revision that needs fresh air.")]
    A.append(asset("06a-carousel-spots", "06 · Carousel slide 1/5: 4 study spots", "f", logo() + '<div class="z" style="margin-top:160px"><div class="k" style="color:var(--sage)">Swipe →</div><h1 style="margin-top:28px">4 study spots inside Bean &amp; Bloom</h1><p style="margin-top:36px">Pick the one that fits your subject.</p></div>' + cup(620, 760, 1) + foot(extra='<div class="dots"><b class="on"></b><b></b><b></b><b></b><b></b></div>')))
    for i, (t, d) in enumerate(spots):
        A.append(asset(f"06{chr(98 + i)}-carousel-spots", f"06 · Carousel slide {i + 2}/5", "f",
            logo() + f'<div class="z" style="margin-top:120px"><span class="num" style="color:var(--bloom)">0{i + 1}</span><h2 style="margin-top:20px">{t}</h2><p style="margin-top:28px;max-width:780px">{d}</p></div>'
            + f'<div class="blob" style="width:640px;height:640px;background:{["var(--sage-tint)", "var(--bloom-tint)", "#F4E3CF", "var(--sage-tint)"][i]};right:-160px;bottom:-120px"></div>'
            + foot(extra='<div class="dots">' + "".join(f'<b class="{"on" if k == i + 1 else ""}"></b>' for k in range(5)) + "</div>")))
    menu = [("Filter coffee", 60), ("Masala chai", 50), ("Cold coffee", 120), ("Banana-walnut bread", 90), ("Veg grilled sandwich", 140), ("Brownie", 80)]
    A.append(asset("07a-carousel-menu", "07 · Carousel slide 1/3: menu under ₹150", "f", logo("var(--cream)") + '<div class="z" style="margin-top:160px"><h1>Everything under ₹150</h1><p style="margin-top:36px;opacity:.85">Student budget, proper food. Swipe for the list →</p></div>' + cup(600, 780, 1, "#FFF7EC", "#B9692B") + foot("var(--cream)"), "var(--espresso)", "var(--cream)"))
    A.append(asset("07b-carousel-menu", "07 · Carousel slide 2/3", "f", logo() + '<div class="z" style="margin-top:90px"><h2>Under ₹150</h2>' + "".join(f'<div class="bar" style="justify-content:space-between"><span>{n}</span><span>₹{p}</span></div>' for n, p in menu) + '</div>' + foot()))
    A.append(asset("07c-carousel-menu", "07 · Carousel slide 3/3", "f", logo() + '<div class="z" style="margin-top:180px"><h1>Or get both for ₹149.</h1><p style="margin-top:36px">Study Fuel combo: coffee or chai + banana bread. Weekdays 3–7 pm with your college ID.</p><div class="pill" style="background:var(--espresso);color:var(--cream);margin-top:56px">Save for later</div></div>' + foot(), "var(--bloom-tint)"))
    A.append(asset("08a-carousel-streak", "08 · Carousel slide 1/3: Study Streak card", "f", logo() + '<div class="z" style="margin-top:160px"><div class="k" style="color:var(--caramel)">New loyalty card</div><h1 style="margin-top:28px">Study 5 days, the 6th coffee is on us.</h1></div>' + foot(), "var(--sage-tint)"))
    A.append(asset("08b-carousel-streak", "08 · Carousel slide 2/3", "f", logo() + '<div class="z" style="margin-top:100px"><h2>How it works</h2><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:56px">'
        + "".join(f'<div class="sticker" style="padding:36px;height:220px;display:grid;place-items:center;background:{"var(--sage)" if k < 5 else "var(--bloom)"};color:#fff;font:800 64px Inter Display">{"☕" if k < 5 else "FREE"}</div>' for k in range(6))
        + '</div><p style="margin-top:48px">Ask for a card at the counter. One stamp per day you study with us, any order over ₹50.</p></div>' + foot()))
    A.append(asset("08c-carousel-streak", "08 · Carousel slide 3/3", "f", logo("var(--cream)") + '<div class="z" style="margin-top:180px"><h1>Valid till 23 Nov.</h1><p style="margin-top:36px">Cards are per person, not per table. Free drink: any coffee or chai up to ₹120.</p></div>' + cup(600, 780, 1, "#FFF7EC", "#4E6B4A") + foot("var(--cream)"), "var(--sage)", "var(--cream)"))
    # ---------- reel covers (3)
    reels = [("09-reel-latte", "60-second latte art", "var(--espresso)", "var(--cream)", "#E8A0A6"), ("10-reel-order", "What our barista orders in exam week", "var(--sage)", "var(--cream)", "#FFF7EC"),
             ("11-reel-dayin", "A day in the quiet loft", "var(--bloom-tint)", "var(--espresso)", "#3B2416")]
    for id_, t, bg, fg, c in reels:
        A.append(asset(id_, f"{id_[:2]} · Reel cover: {t}", "s", logo(fg) + f'<div class="z" style="margin-top:auto;margin-bottom:auto"><div class="play" style="margin-bottom:64px"></div><h1 style="font-size:120px">{t}</h1></div>'
                       + cup(520, 1180, 1.2, c, bg.replace("var(--bloom-tint)", "#FBE3E5") if "var" not in c else "#fff") + foot(fg), bg, fg))
    # ---------- stories (4)
    A.append(asset("12-story-poll", "12 · Story: poll", "s", logo() + '<div class="z" style="margin-top:220px"><h1 style="font-size:116px">Late-night revision needs…</h1><div class="sticker" style="margin-top:80px">'
        '<div class="bar" style="background:var(--sage);color:#fff;justify-content:space-between;height:130px;font-size:52px"><span>☕ Coffee</span><span>58%</span></div><div class="bar" style="justify-content:space-between;height:130px;font-size:52px"><span>🍵 Chai</span><span>42%</span></div>'
        '<p style="font-size:30px;margin-top:20px;opacity:.6">Poll sticker preview: percentages shown are placeholders</p></div></div>' + foot(), "var(--bloom-tint)"))
    A.append(asset("13-story-countdown", "13 · Story: countdown", "s", logo("var(--cream)") + '<div class="z" style="margin-top:300px"><div class="k" style="color:var(--bloom)">Countdown</div><h1 style="font-size:130px;margin-top:30px">Study Fuel starts Monday</h1>'
        '<div class="sticker" style="margin-top:80px;text-align:center"><p style="font-weight:700">10 Nov · 3 pm</p><div style="display:flex;justify-content:center;gap:24px;margin-top:20px;font:800 120px Inter Display">' + "".join(f'<span style="background:var(--espresso);color:var(--cream);border-radius:20px;padding:10px 26px">{d}</span>' for d in "03") + '<span>:</span>' + "".join(f'<span style="background:var(--espresso);color:var(--cream);border-radius:20px;padding:10px 26px">{d}</span>' for d in "12") + '</div><p style="margin-top:16px;font-size:30px;opacity:.6">days : hours · tap “remind me”</p></div></div>' + foot("var(--cream)"), "var(--espresso)", "var(--cream)"))
    A.append(asset("14-story-quiz", "14 · Story: quiz", "s", logo() + '<div class="z" style="margin-top:220px"><div class="k" style="color:var(--sage)">Quiz</div><h1 style="font-size:110px;margin-top:30px">Pull an all-nighter or sleep by 12?</h1><div class="sticker" style="margin-top:70px">'
        + "".join(f'<div class="bar" style="height:120px;font-size:46px">{x}</div>' for x in ("A · Coffee at midnight", "B · Chai at 6 pm, sleep by 12", "C · What's sleep?")) + '<p style="font-size:30px;margin-top:20px">Science says B: sleep consolidates memory.</p></div></div>' + foot(), "var(--sage-tint)"))
    A.append(asset("15-story-visit", "15 · Story: hours & location", "s", logo() + '<div class="z" style="margin-top:220px"><h1 style="font-size:130px">Find your corner</h1><div class="sticker" style="margin-top:80px">'
        '<p style="font-weight:800;font-size:52px">Open 8 am – 11 pm</p><p style="margin-top:12px">Through exams, 10–23 Nov</p><div class="bar" style="margin-top:40px">📍 2 min from the college main gate</div>'
        '<div class="bar" style="background:var(--espresso);color:var(--cream)">Tap the location sticker →</div></div></div>' + cup(560, 1300, 1, "#B9692B") + foot(), "var(--cream)"))
    return A


if __name__ == "__main__":
    html = f'<!doctype html><html><head><meta charset="utf-8"><style>{VARS}{CSS}</style></head><body>{"".join(posts())}</body></html>'
    open(os.path.join(HERE, "posts.html"), "w").write(html)
    print("written")
