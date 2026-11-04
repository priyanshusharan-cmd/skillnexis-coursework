"""Generates the screen pages from shared components and the tokens:
  wireframes.html   8 low-fidelity screens of "Circle", a social app (greyscale boxes + annotations)
  circle-hifi.html  3 of those wireframes taken to high fidelity
  haat.html         10-screen e-commerce app "Haat" (mini project)
    python design/screens.py && node design/render.js
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

ICONS = {
    "home": "M3 11 12 3l9 8v10h-6v-6H9v6H3z", "search": "M10.5 4a6.5 6.5 0 1 1 0 13 6.5 6.5 0 0 1 0-13zm5 11.5L21 21",
    "heart": "M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z", "cart": "M3 4h2l2.4 11h10.2L20 7H6.2M9 20h.01M17 20h.01",
    "user": "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-7 9a7 7 0 0 1 14 0", "bell": "M6 16V11a6 6 0 1 1 12 0v5l2 2H4zm4 4h4",
    "chat": "M4 5h16v11H8l-4 4z", "plus": "M12 5v14M5 12h14", "back": "M15 5l-7 7 7 7", "filter": "M4 6h16M7 12h10M10 18h4",
    "grid": "M4 4h7v7H4zm9 0h7v7h-7zM4 13h7v7H4zm9 0h7v7h-7z", "box": "M4 8l8-4 8 4v8l-8 4-8-4zm0 0 8 4 8-4M12 12v8",
    "gear": "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm8 3-2-1 .6-2.2-1.6-1.6L14.8 7 13.8 5h-3.6l-1 2-2.2-.6L5.4 8 6 10.2 4 11.4v1.2l2 1.2-.6 2.2L7 17.6l2.2-.6 1 2h3.6l1-2 2.2.6 1.6-1.6-.6-2.2 2-1.2z",
    "send": "M4 12 20 4l-6 16-3-7z", "image": "M4 5h16v14H4zm0 11 5-5 4 4 2-2 5 5", "dots": "M6 12h.01M12 12h.01M18 12h.01",
    "check": "M5 12l4 4 10-10", "pin": "M12 21s-6-6-6-11a6 6 0 1 1 12 0c0 5-6 11-6 11zm0-9a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
    "star": "M12 4l2.4 5 5.6.8-4 3.9.9 5.5-4.9-2.6-4.9 2.6.9-5.5-4-3.9 5.6-.8z", "card": "M3 6h18v12H3zm0 4h18",
    "truck": "M3 6h11v9H3zm11 3h4l3 3v3h-7M7 18h.01M17 18h.01", "chevron": "M9 6l6 6-6 6", "mic": "M12 4a3 3 0 0 1 3 3v5a3 3 0 0 1-6 0V7a3 3 0 0 1 3-3zm-6 8a6 6 0 0 0 12 0M12 18v3",
}


def icon(name, size=24, cls=""):
    return (f'<svg class="ic {cls}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="{ICONS[name]}"/></svg>')


BASE_CSS = """
*{box-sizing:border-box} body{margin:0;padding:40px;background:#e9e7e3;display:flex;flex-wrap:wrap;gap:40px;font:var(--body)}
.frame{width:390px;height:844px;border-radius:44px;overflow:hidden;position:relative;background:var(--surface);color:var(--ink-900);
  box-shadow:0 0 0 10px #1b1b1b,0 24px 60px rgba(0,0,0,.25);display:flex;flex-direction:column}
.status{height:47px;flex:none;display:flex;justify-content:space-between;align-items:flex-end;padding:0 28px 6px;font:600 15px/20px var(--font-body)}
.screen{flex:1;overflow:hidden;display:flex;flex-direction:column;min-height:0}
.label-out{position:absolute;top:-30px;left:4px;font:600 13px var(--font-body);color:#555}
.wrap{position:relative;margin-top:24px}
.tabbar{flex:none;height:84px;display:flex;justify-content:space-around;align-items:flex-start;padding-top:10px;border-top:1px solid var(--line);background:var(--surface)}
.tab{display:flex;flex-direction:column;align-items:center;gap:2px;font:var(--caption);color:var(--ink-500);width:64px}
.tab.on{color:var(--brand-600)} .ic{flex:none;display:block}
.row{display:flex;align-items:center;gap:var(--s3)} .pad{padding:0 var(--s4)} .grow{flex:1}
.top{display:flex;align-items:center;gap:var(--s3);padding:var(--s2) var(--s4) var(--s3)}
.iconbtn{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;color:var(--ink-900)}
.muted{color:var(--ink-500)} .btn{font:var(--label);border:0;border-radius:var(--r-md);height:52px;display:flex;align-items:center;justify-content:center;gap:8px}
.btn.p{background:var(--brand-600);color:#fff} .btn.s{background:var(--brand-100);color:var(--brand-600)}
.chip{font:var(--label);padding:8px 14px;border-radius:999px;border:1px solid var(--line);white-space:nowrap;color:var(--ink-700)}
.chip.on{background:var(--ink-900);color:#fff;border-color:var(--ink-900)}
.badge{position:absolute;top:2px;right:2px;min-width:18px;height:18px;border-radius:9px;background:var(--brand-600);color:#fff;font:700 11px/18px var(--font-body);text-align:center;padding:0 5px}
"""

WIRE_CSS = """
.wf{--surface:#fff;--ink-900:#222;--ink-700:#555;--ink-500:#777;--line:#ccc;--brand-600:#222;--brand-100:#ddd}
.wf .frame{font-family:var(--font-body)} .b{background:#d9d9d9;border-radius:6px} .b2{background:#ececec;border-radius:6px}
.ln{height:10px;background:#cfcfcf;border-radius:5px;margin:6px 0} .note{position:absolute;background:#fff6a8;color:#3b3200;font:500 12px/16px var(--font-body);
  padding:6px 8px;border-radius:4px;box-shadow:0 2px 6px rgba(0,0,0,.15);width:150px;z-index:2} .x{background:repeating-linear-gradient(45deg,#e4e4e4 0 8px,#d4d4d4 8px 16px);border-radius:6px}
.av{border-radius:50%;background:#cfcfcf;flex:none}
"""


def frame(label, body, tabbar=None, theme=""):
    return (f'<div class="wrap {theme}"><div class="label-out">{label}</div><div class="frame" data-name="{label}">'
            f'<div class="status"><span>9:41</span><span>●●● ▮</span></div><div class="screen">{body}</div>{tabbar or ""}</div></div>')


def tabbar(items, on):
    return '<nav class="tabbar">' + "".join(
        f'<div class="tab {"on" if i == on else ""}" style="position:relative">{icon(ic)}{name}{badge}</div>'
        for i, (ic, name, badge) in enumerate(items)) + "</nav>"


def page(title, theme, css, frames):
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{title}</title><link rel="stylesheet" href="tokens.css">'
            f'<style>{BASE_CSS}{css}</style></head><body class="theme-{theme}">{"".join(frames)}</body></html>')


# ------------------------------------------------------------------ Circle wireframes (low fidelity)
def note(text, top, left):
    return f'<div class="note" style="top:{top}px;left:{left}px">{text}</div>'


CTABS = [("home", "Home", ""), ("search", "Explore", ""), ("plus", "Post", ""), ("chat", "Chats", ""), ("user", "Me", "")]


def wf_post(img=180):
    return ('<div class="pad" style="margin-top:12px"><div class="row"><div class="av" style="width:36px;height:36px"></div><div class="grow"><div class="ln" style="width:40%"></div>'
            f'<div class="ln" style="width:25%;height:8px"></div></div></div><div class="x" style="height:{img}px;margin-top:10px"></div>'
            '<div class="row" style="margin-top:10px;gap:18px"><div class="b" style="width:22px;height:22px"></div><div class="b" style="width:22px;height:22px"></div>'
            '<div class="b" style="width:22px;height:22px"></div></div><div class="ln" style="width:85%"></div></div>')


def wireframes():
    tb = lambda on: tabbar(CTABS, on)  # noqa: E731
    stories = '<div class="row pad" style="gap:12px;margin:8px 0">' + "".join('<div class="av" style="width:58px;height:58px;border:3px solid #999"></div>' for _ in range(5)) + "</div>"
    f = []
    f.append(frame("1 · Feed", '<div class="top"><div class="b" style="width:90px;height:22px"></div><div class="grow"></div><div class="b" style="width:26px;height:26px"></div></div>'
                   + stories + wf_post() + wf_post(120) + note("Stories row: tap to view, long-press to mute", 92, 220)
                   + note("Like / comment / share: 44 px targets", 410, 220), tb(0)))
    f.append(frame("2 · Story viewer", '<div class="x" style="position:absolute;inset:0"></div><div style="position:relative;padding:8px 12px"><div class="row" style="gap:4px">'
                   + "".join('<div class="b" style="height:3px;flex:1;background:#888"></div>' for _ in range(4)) + '</div><div class="row" style="margin-top:12px">'
                   '<div class="av" style="width:34px;height:34px"></div><div class="ln" style="width:30%;background:#aaa"></div></div></div>'
                   '<div style="position:absolute;bottom:40px;left:16px;right:16px" class="row"><div class="b2 grow" style="height:46px;border-radius:23px"></div><div class="b" style="width:46px;height:46px;border-radius:50%"></div></div>'
                   + note("Progress bars = number of stories; tap left/right to skip", 70, 200) + note("Reply goes to DMs", 700, 16)))
    f.append(frame("3 · Post + comments", '<div class="top"><div class="b" style="width:24px;height:24px"></div><div class="ln" style="width:30%"></div></div>' + wf_post(220)
                   + "".join('<div class="row pad" style="margin-top:14px;align-items:flex-start"><div class="av" style="width:30px;height:30px"></div><div class="grow"><div class="ln" style="width:35%"></div><div class="ln" style="width:80%"></div></div></div>' for _ in range(3))
                   + '<div style="margin-top:auto;padding:12px 16px 30px;border-top:1px solid #ccc" class="row"><div class="av" style="width:32px;height:32px"></div><div class="b2 grow" style="height:40px;border-radius:20px"></div></div>'
                   + note("Composer stays above the keyboard", 760, 210)))
    f.append(frame("4 · Create post", '<div class="top"><div class="ln" style="width:18%"></div><div class="grow"></div><div class="b" style="width:70px;height:34px;border-radius:17px"></div></div>'
                   '<div class="x" style="height:330px;margin:0 16px"></div><div class="row pad" style="margin-top:10px">' + "".join('<div class="b" style="width:68px;height:68px"></div>' for _ in range(4)) + '</div>'
                   '<div class="pad" style="margin-top:16px"><div class="b2" style="height:90px"></div><div class="row" style="margin-top:12px;gap:8px">' + "".join('<div class="b2" style="width:80px;height:32px;border-radius:16px"></div>' for _ in range(3)) + "</div></div>"
                   + note("Caption, tag people, location chips", 590, 220) + note("Post disabled until media or text exists", 62, 160), tb(2)))
    grid = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2px;margin-top:12px">' + "".join('<div class="x" style="aspect-ratio:1"></div>' for _ in range(9)) + "</div>"
    f.append(frame("5 · Profile", '<div class="top"><div class="ln" style="width:30%"></div><div class="grow"></div><div class="b" style="width:24px;height:24px"></div></div>'
                   '<div class="row pad"><div class="av" style="width:84px;height:84px"></div><div class="row grow" style="justify-content:space-around">' + "".join('<div><div class="b" style="width:36px;height:18px;margin:auto"></div><div class="ln" style="width:48px"></div></div>' for _ in range(3)) + "</div></div>"
                   '<div class="pad"><div class="ln" style="width:40%"></div><div class="ln" style="width:75%"></div><div class="row" style="margin-top:10px"><div class="b grow" style="height:38px"></div><div class="b2 grow" style="height:38px"></div></div></div>'
                   + grid + note("Posts / Followers / Following", 120, 230), tb(4)))
    f.append(frame("6 · Explore / search", '<div class="pad" style="margin-top:8px"><div class="b2" style="height:44px;border-radius:22px"></div><div class="row" style="margin-top:12px;gap:8px">' + "".join('<div class="b2" style="width:76px;height:32px;border-radius:16px"></div>' for _ in range(4)) + "</div></div>"
                   '<div style="display:grid;grid-template-columns:repeat(3,1fr);grid-auto-rows:124px;gap:2px;margin-top:12px"><div class="x" style="grid-row:span 2;grid-column:span 2"></div>' + "".join('<div class="x"></div>' for _ in range(7)) + "</div>"
                   + note("Topic chips filter the grid", 120, 220), tb(1)))
    notif = "".join(f'<div class="row pad" style="margin-top:14px"><div class="av" style="width:44px;height:44px"></div><div class="grow"><div class="ln" style="width:{w}%"></div><div class="ln" style="width:30%;height:8px"></div></div><div class="x" style="width:44px;height:44px"></div></div>' for w in (80, 65, 90, 70, 55, 85))
    f.append(frame("7 · Notifications", '<div class="top"><div class="ln" style="width:40%;height:14px"></div></div><div class="pad"><div class="ln" style="width:20%;height:8px"></div></div>' + notif
                   + note("Grouped: Today / This week", 70, 220), tb(0)))
    chat = "".join(f'<div class="row" style="justify-content:{"flex-end" if i % 2 else "flex-start"};padding:0 16px;margin-top:10px"><div class="{"b" if i % 2 else "b2"}" style="width:{w}px;height:{h}px;border-radius:16px"></div></div>'
                   for i, (w, h) in enumerate([(190, 40), (150, 40), (230, 60), (120, 40), (200, 40)]))
    f.append(frame("8 · Chat", '<div class="top"><div class="b" style="width:24px;height:24px"></div><div class="av" style="width:36px;height:36px"></div><div class="grow"><div class="ln" style="width:45%"></div><div class="ln" style="width:25%;height:8px"></div></div></div>'
                   + chat + '<div style="margin-top:auto;padding:12px 16px 30px" class="row"><div class="b" style="width:32px;height:32px;border-radius:50%"></div><div class="b2 grow" style="height:44px;border-radius:22px"></div><div class="b" style="width:44px;height:44px;border-radius:50%"></div></div>'
                   + note("Sent = right, received = left; read receipts under the last sent", 300, 16)))
    return page("Circle: low-fidelity wireframes", "circle wf", WIRE_CSS, f)


# ------------------------------------------------------------------ Circle high fidelity
CIRCLE_CSS = """
.av{border-radius:50%;flex:none;display:grid;place-items:center;color:#fff;font:700 15px var(--font-body)}
.ring{padding:3px;border-radius:50%;background:conic-gradient(var(--accent-600),var(--brand-500),var(--accent-600))}
.ring>.av{border:3px solid #fff}
.ph{border-radius:var(--r-lg);position:relative;overflow:hidden}
.bubble{max-width:250px;padding:10px 14px;border-radius:20px;font:var(--body)}
.me{background:var(--brand-600);color:#fff;border-bottom-right-radius:6px;margin-left:auto}
.them{background:var(--canvas);color:var(--ink-900);border-bottom-left-radius:6px}
"""
PEOPLE = [("Aarav", "#6457F0"), ("Diya", "#B0127A"), ("Kabir", "#0E7C3A"), ("Meera", "#C2410C"), ("Ishan", "#0369A1"), ("Zoya", "#7C3AED")]


def av(name, color, size=40):
    return f'<div class="av" style="width:{size}px;height:{size}px;background:{color};font-size:{size // 2.6:.0f}px">{name[0]}</div>'


def circle_hifi():
    tb = lambda on: tabbar([("home", "Home", ""), ("search", "Explore", ""), ("plus", "Post", ""), ("chat", "Chats", '<span class="badge">3</span>'), ("user", "Me", "")], on)  # noqa: E731
    stories = '<div class="row pad" style="gap:14px;margin:4px 0 12px;overflow:hidden">' + "".join(
        f'<div style="text-align:center;width:64px"><div class="ring">{av(n, c, 54)}</div><div class="t-caption" style="margin-top:4px;color:var(--ink-700)">{n}</div></div>' for n, c in PEOPLE[:5]) + "</div>"
    post = (f'<div style="border-top:1px solid var(--line);padding-top:12px"><div class="row pad">{av("Diya", "#B0127A", 38)}<div class="grow"><div class="t-label">Diya Rao</div>'
            '<div class="t-caption muted">Nandi Hills · 2 h</div></div>' + icon("dots") + '</div>'
            '<div class="ph" style="height:300px;margin:12px 16px 0;background:linear-gradient(160deg,#FDBA74 0%,#F472B6 45%,#6457F0 100%)">'
            '<svg viewBox="0 0 358 300" style="position:absolute;inset:0"><path d="M0 220 L70 160 L130 200 L210 120 L290 190 L358 150 L358 300 L0 300Z" fill="rgba(22,21,29,.55)"/>'
            '<circle cx="270" cy="80" r="34" fill="rgba(255,255,255,.85)"/></svg></div>'
            f'<div class="row pad" style="margin-top:10px;gap:18px"><span class="row" style="gap:6px;color:var(--accent-600)">{icon("heart")}<b class="t-label">248</b></span>'
            f'<span class="row" style="gap:6px">{icon("chat")}<span class="t-label">32</span></span>{icon("send")}</div>'
            '<p class="t-body pad" style="margin:8px 0 0"><b>Diya Rao</b> Sunrise was worth the 4 am alarm 🌄</p></div>')
    feed = (f'<div class="top"><span class="t-headline" style="color:var(--brand-600)">circle</span><div class="grow"></div>'
            f'<div class="iconbtn" style="position:relative">{icon("bell")}<span class="badge">5</span></div></div>' + stories + post)
    grid = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2px;margin-top:16px">' + "".join(
        f'<div style="aspect-ratio:1;background:linear-gradient({a}deg,{c1},{c2})"></div>' for a, c1, c2 in
        [(135, "#6457F0", "#B0127A"), (200, "#FDBA74", "#F472B6"), (90, "#0E7C3A", "#86EFAC"), (160, "#0369A1", "#7DD3FC"), (45, "#16151D", "#6457F0"),
         (120, "#F59E0B", "#B0127A"), (180, "#A78BFA", "#ECEAFE"), (60, "#B4381F", "#FDBA74"), (300, "#14B8A6", "#6457F0")]) + "</div>"
    stat = lambda n, l: f'<div style="text-align:center"><div class="t-title">{n}</div><div class="t-caption muted">{l}</div></div>'  # noqa: E731
    profile = (f'<div class="top"><span class="t-title">kabir.codes</span><div class="grow"></div>{icon("gear")}</div>'
               f'<div class="row pad" style="gap:20px"><div class="ring">{av("Kabir", "#0E7C3A", 84)}</div><div class="row grow" style="justify-content:space-around">'
               + stat("128", "Posts") + stat("2.4k", "Followers") + stat("310", "Following") + '</div></div>'
               '<div class="pad" style="margin-top:12px"><div class="t-label">Kabir Shah</div><p class="t-body" style="margin:2px 0;color:var(--ink-700)">CSE @ BMSCE · building tiny robots 🤖 · Bengaluru</p>'
               '<div class="row" style="margin-top:12px;gap:8px"><div class="btn p grow" style="height:44px">Follow</div><div class="btn s grow" style="height:44px">Message</div></div></div>'
               f'<div class="row" style="margin-top:16px;border-bottom:1px solid var(--line)"><div class="grow" style="display:flex;justify-content:center;padding:10px;border-bottom:2px solid var(--ink-900)">{icon("grid")}</div>'
               f'<div class="grow muted" style="display:flex;justify-content:center;padding:10px">{icon("heart")}</div></div>' + grid)
    msgs = [("them", "Are you coming to the robotics meetup on Saturday?"), ("me", "Yes! Bringing the line-follower 🤖"), ("them", "Nice. Can you demo the PID tuning?"),
            ("me", "Sure, I'll bring the laptop too"), ("them", "See you at 4 then 👋")]
    chat = (f'<div class="top" style="border-bottom:1px solid var(--line)">{icon("back")}{av("Meera", "#C2410C", 40)}<div class="grow"><div class="t-label">Meera Iyer</div>'
            '<div class="t-caption" style="color:var(--online)">● Active now</div></div>' + icon("dots") + '</div>'
            '<div style="padding:16px;display:flex;flex-direction:column;gap:10px;flex:1"><div class="t-caption muted" style="text-align:center">Today 6:12 pm</div>'
            + "".join(f'<div class="bubble {k}">{t}</div>' for k, t in msgs) + '<div class="t-caption muted" style="text-align:right">Seen</div></div>'
            f'<div class="row" style="padding:10px 16px 30px;gap:10px"><div class="iconbtn" style="background:var(--brand-100);color:var(--brand-600)">{icon("image")}</div>'
            f'<div class="grow" style="height:44px;border:1px solid var(--ink-500);border-radius:22px;display:flex;align-items:center;padding:0 16px;color:var(--ink-500)">Message…</div>'
            f'<div class="iconbtn" style="background:var(--brand-600);color:#fff">{icon("send")}</div></div>')
    f = [frame("1 · Feed (hi-fi)", feed, tb(0)), frame("5 · Profile (hi-fi)", profile, tb(4)), frame("8 · Chat (hi-fi)", chat)]
    return page("Circle: high-fidelity mockups", "circle", CIRCLE_CSS, f)


# ------------------------------------------------------------------ Haat e-commerce (10 screens)
HAAT_CSS = """
.prod{border-radius:var(--r-md);display:grid;place-items:center;position:relative;overflow:hidden}
.price{font:700 16px/24px var(--font-body)} .mrp{font:var(--caption);color:var(--ink-500);text-decoration:line-through}
.off{font:var(--caption);color:var(--leaf-700);font-weight:700} .card{background:var(--surface);border-radius:var(--r-lg);padding:var(--s3)}
.search{height:48px;border:1px solid var(--ink-500);border-radius:var(--r-md);display:flex;align-items:center;gap:10px;padding:0 14px;color:var(--ink-500);background:#fff}
.add{height:36px;border-radius:10px;border:1.5px solid var(--brand-600);color:var(--brand-600);font:var(--label);display:grid;place-items:center;background:#fff}
.stepper{display:flex;align-items:center;justify-content:space-between;height:36px;border-radius:10px;background:var(--brand-600);color:#fff;font:var(--label);padding:0 12px;width:96px}
.sec{display:flex;justify-content:space-between;align-items:baseline;padding:0 var(--s4);margin:var(--s5) 0 var(--s3)}
.list-row{display:flex;align-items:center;gap:14px;padding:14px 16px;border-bottom:1px solid var(--line)}
.sum{display:flex;justify-content:space-between;margin:6px 0}
.bar{flex:none;padding:12px 16px 30px;background:var(--surface);border-top:1px solid var(--line)}
.radio{width:22px;height:22px;border-radius:50%;border:2px solid var(--ink-500);flex:none} .radio.on{border:7px solid var(--brand-600)}
.step{display:flex;flex-direction:column;align-items:center;gap:4px;font:var(--caption);color:var(--ink-500);flex:1}
.dot{width:26px;height:26px;border-radius:50%;display:grid;place-items:center;background:var(--line);color:var(--ink-700);font:700 12px var(--font-body)}
.step.done .dot{background:var(--leaf-700);color:#fff} .step.now .dot{background:var(--brand-600);color:#fff} .step.now{color:var(--ink-900)}
.toggle{width:46px;height:28px;border-radius:14px;background:var(--ink-500);position:relative;flex:none}
.toggle::after{content:"";position:absolute;top:3px;left:3px;width:22px;height:22px;border-radius:50%;background:#fff}
.toggle.on{background:var(--leaf-700)} .toggle.on::after{left:21px}
"""
P = {"mango": ("Alphonso mangoes", "1 kg", 349, 420, "#FDBA74", "#F59E0B"), "atta": ("Whole wheat atta", "5 kg", 289, 330, "#FDE68A", "#D6A75A"),
     "tea": ("Assam CTC tea", "500 g", 215, 260, "#B45309", "#7C2D12"), "ghee": ("Desi cow ghee", "1 L", 649, 720, "#FEF3C7", "#FCD34D"),
     "rice": ("Sona masoori rice", "5 kg", 399, 470, "#F5F5F4", "#D6D3D1"), "paneer": ("Fresh paneer", "200 g", 95, 110, "#FFFBEB", "#FDE68A"),
     "banana": ("Robusta bananas", "1 dozen", 59, 70, "#FEF08A", "#EAB308"), "dal": ("Toor dal", "1 kg", 165, 190, "#FDE047", "#CA8A04")}


def prod_img(key, h=120, r=None):
    _, _, _, _, c1, c2 = P[key]
    shape = {"mango": '<ellipse cx="50" cy="55" rx="28" ry="34" fill="{c}"/><path d="M50 22c6-8 16-8 20-4" stroke="#3f6212" stroke-width="5" fill="none"/>',
             "banana": '<path d="M20 30c10 40 50 50 64 36" stroke="{c}" stroke-width="16" fill="none" stroke-linecap="round"/>',
             "tea": '<rect x="28" y="22" width="44" height="60" rx="6" fill="{c}"/><rect x="34" y="40" width="32" height="14" fill="#fff8"/>'}.get(
        key, '<rect x="26" y="20" width="48" height="64" rx="10" fill="{c}"/><rect x="32" y="44" width="36" height="16" rx="3" fill="#fff9"/>').format(c=c2)
    return (f'<div class="prod" style="height:{h}px;background:radial-gradient(circle at 30% 25%,#fff 0%,{c1} 90%);{f"border-radius:{r}px;" if r is not None else ""}">'
            f'<svg viewBox="0 0 100 100" width="{h * .8:.0f}" height="{h * .8:.0f}">{shape}</svg></div>')


def pcard(key, qty=0, img=110):
    name, unit, price, mrp, *_ = P[key]
    btn = f'<div class="stepper"><span>−</span><span>{qty}</span><span>+</span></div>' if qty else '<div class="add">Add</div>'
    return (f'<div class="card" style="border:1px solid var(--line)">{prod_img(key, img)}<div class="t-caption muted" style="margin-top:8px">{unit}</div>'
            f'<div class="t-label" style="height:40px;color:var(--ink-900)">{name}</div><div class="row" style="justify-content:space-between;margin-top:6px">'
            f'<div><div class="price">₹{price}</div><span class="mrp">₹{mrp}</span> <span class="off">{round(100 * (mrp - price) / mrp)}% off</span></div></div>'
            f'<div style="margin-top:10px">{btn}</div></div>')


def haat():
    tabs = lambda on, n=3: tabbar([("home", "Home", ""), ("grid", "Categories", ""), ("heart", "Wishlist", ""),  # noqa: E731
                                   ("cart", "Cart", f'<span class="badge">{n}</span>' if n else ""), ("user", "Account", "")], on)
    hdr = lambda t, right="": f'<div class="top">{icon("back")}<span class="t-title grow">{t}</span>{right}</div>'  # noqa: E731
    cats = [("Fruits", "#FDBA74", "mango"), ("Staples", "#FDE68A", "atta"), ("Dairy", "#FEF3C7", "paneer"), ("Tea & coffee", "#FBBF24", "tea"),
            ("Rice & dal", "#E7E5E4", "rice"), ("Oils & ghee", "#FDE68A", "ghee"), ("Bananas", "#FEF08A", "banana"), ("Pulses", "#FDE047", "dal")]
    s = []
    home = (f'<div class="pad" style="padding-top:4px"><div class="row"><div class="grow"><div class="t-caption muted">Deliver to</div>'
            f'<div class="row t-label" style="gap:4px">{icon("pin", 18)}Hostel B, BMSCE {icon("chevron", 16)}</div></div><div class="av" style="width:40px;height:40px;border-radius:50%;background:var(--brand-100);color:var(--brand-600);display:grid;place-items:center;font:700 16px var(--font-body)">P</div></div>'
            f'<div class="search" style="margin-top:12px">{icon("search", 20)}<span class="grow">Search “mango”, “atta”…</span>{icon("mic", 20)}</div>'
            '<div style="margin-top:16px;border-radius:var(--r-lg);padding:18px;background:linear-gradient(120deg,var(--brand-600),#E2743C);color:#fff;position:relative;overflow:hidden">'
            '<div class="t-caption" style="opacity:.9;letter-spacing:.06em">MANGO SEASON</div><div class="t-title" style="margin:4px 0 2px;width:210px">Alphonso, straight from Ratnagiri</div>'
            '<div class="t-label">Up to 20% off · 30-min delivery</div><svg viewBox="0 0 100 100" width="120" style="position:absolute;right:-6px;bottom:-14px"><ellipse cx="50" cy="55" rx="30" ry="36" fill="#FDBA74"/></svg></div></div>'
            '<div class="sec"><span class="t-title">Shop by category</span><span class="t-label" style="color:var(--brand-600)">See all</span></div>'
            '<div class="row pad" style="gap:14px">' + "".join(f'<div style="width:72px;text-align:center">{prod_img(k, 64, 18)}<div class="t-caption" style="margin-top:4px">{n}</div></div>' for n, _, k in cats[:4]) + '</div>'
            '<div class="sec"><span class="t-title">Best sellers</span><span class="t-label" style="color:var(--brand-600)">See all</span></div>'
            '<div class="row pad" style="gap:12px;align-items:stretch"><div style="width:170px">' + pcard("mango", 1, 72) + '</div><div style="width:170px">' + pcard("atta", 0, 72) + "</div></div>")
    s.append(frame("01 · Home", home, tabs(0)))
    catgrid = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;padding:0 16px">' + "".join(
        f'<div style="text-align:center">{prod_img(k, 96, 20)}<div class="t-label" style="margin-top:6px;color:var(--ink-900)">{n}</div></div>' for n, _, k in cats + cats[:1]) + "</div>"
    s.append(frame("02 · Categories", '<div class="top"><span class="t-headline grow">Categories</span>' + icon("search") + '</div>'
                   '<div class="row pad" style="gap:8px;margin-bottom:16px"><span class="chip on">All</span><span class="chip">Fresh</span><span class="chip">Pantry</span><span class="chip">Organic</span></div>' + catgrid, tabs(1)))
    name, unit, price, mrp, *_ = P["mango"]
    detail = (prod_img("mango", 330, 0) + f'<div style="position:absolute;top:56px;left:16px;right:16px" class="row"><div class="iconbtn" style="background:#fff">{icon("back")}</div>'
              f'<div class="grow"></div><div class="iconbtn" style="background:#fff;color:var(--brand-600)">{icon("heart")}</div></div>'
              f'<div class="pad" style="margin-top:16px"><span class="t-caption" style="background:var(--leaf-100);color:var(--leaf-700);padding:4px 10px;border-radius:999px;font-weight:600">In stock · 30 min</span>'
              f'<h1 class="t-headline" style="margin:10px 0 2px">{name}</h1><div class="row t-caption muted" style="gap:4px">{icon("star", 16, "")}<b style="color:var(--ink-900)">4.7</b> (2,148 ratings) · Ratnagiri, MH</div>'
              f'<div class="row" style="margin-top:12px;gap:10px;align-items:baseline"><span class="t-display">₹{price}</span><span class="mrp" style="font-size:16px">₹{mrp}</span><span class="off" style="font-size:14px">17% off</span></div>'
              '<div class="t-label" style="margin-top:16px">Pack size</div><div class="row" style="gap:8px;margin-top:8px"><span class="chip">500 g</span><span class="chip on">1 kg</span><span class="chip">2 kg</span></div>'
              '<p class="t-body" style="color:var(--ink-700);margin:14px 0 0">Hand-picked, naturally ripened with no carbide. Sweet, fibre-free pulp; ripe in 1–2 days at room temperature.</p></div>')
    s.append(frame("03 · Product detail", detail + '<div class="bar row" style="margin-top:auto;gap:12px"><div class="stepper" style="width:110px;height:52px;background:var(--brand-100);color:var(--brand-600)"><span>−</span><span>1</span><span>+</span></div>'
                   '<div class="btn p grow">Add to cart · ₹349</div></div>'))
    lines = [("mango", 1), ("atta", 1), ("paneer", 2)]
    sub = sum(P[k][2] * q for k, q in lines)
    mrp_t = sum(P[k][3] * q for k, q in lines)
    cart = (hdr("My cart (4 items)") + '<div style="background:var(--leaf-100);color:var(--leaf-700);margin:0 16px 8px;padding:10px 14px;border-radius:var(--r-md)" class="row t-label">'
            + icon("truck", 20) + 'Free delivery unlocked on orders over ₹499</div>'
            + "".join(f'<div class="list-row">{prod_img(k, 64, 14).replace("prod", "prod", 1)}<div class="grow"><div class="t-label">{P[k][0]}</div><div class="t-caption muted">{P[k][1]}</div>'
                      f'<div class="price" style="margin-top:4px">₹{P[k][2] * q}</div></div><div class="stepper"><span>−</span><span>{q}</span><span>+</span></div></div>' for k, q in lines)
            + f'<div class="pad" style="margin-top:16px"><div class="t-title" style="margin-bottom:8px">Bill details</div><div class="sum t-body"><span class="muted">Item total (MRP ₹{mrp_t})</span><span>₹{sub}</span></div>'
            f'<div class="sum t-body"><span class="muted">Delivery</span><span style="color:var(--leaf-700);font-weight:600">FREE</span></div><div class="sum t-body"><span class="muted">Handling</span><span>₹5</span></div>'
            f'<div class="sum t-title" style="border-top:1px solid var(--line);padding-top:10px;margin-top:10px"><span>To pay</span><span>₹{sub + 5}</span></div>'
            f'<div class="t-caption" style="color:var(--leaf-700);font-weight:600">You save ₹{mrp_t - sub} on this order</div></div>'
            f'<div class="bar" style="margin-top:auto"><div class="btn p">Proceed to checkout · ₹{sub + 5}</div></div>')
    s.append(frame("04 · Cart", cart))
    steps = '<div class="row pad" style="margin:4px 0 16px">' + "".join(f'<div class="step {c}"><div class="dot">{"✓" if c == "done" else i}</div>{n}</div>' for i, (n, c) in enumerate([("Address", "done"), ("Payment", "now"), ("Review", "")], 1)) + "</div>"
    pay = [("UPI · GPay / PhonePe / Paytm", "card", True), ("Credit / debit card", "card", False), ("Cash on delivery", "box", False)]
    checkout = (hdr("Checkout") + steps + f'<div class="pad"><div class="card" style="border:1px solid var(--line)"><div class="row">{icon("pin", 22)}<div class="grow"><div class="t-label">Hostel B, Room 214</div>'
                '<div class="t-caption muted">BMS College of Engineering, Basavanagudi, Bengaluru 560019</div></div><span class="t-label" style="color:var(--brand-600)">Change</span></div></div>'
                '<div class="t-title" style="margin:20px 0 8px">Pay with</div>' + "".join(f'<div class="card row" style="border:1.5px solid {"var(--brand-600)" if on else "var(--line)"};margin-bottom:10px;min-height:56px"><div class="radio {"on" if on else ""}"></div><span class="t-label grow" style="color:var(--ink-900)">{n}</span>{icon(ic, 22)}</div>' for n, ic, on in pay)
                + '<div class="row t-caption muted" style="margin-top:8px;gap:6px">' + icon("check", 16) + 'Payments are encrypted. We never store your UPI PIN.</div></div>'
                f'<div class="bar" style="margin-top:auto"><div class="row" style="justify-content:space-between;margin-bottom:10px"><span class="t-label muted">Total</span><span class="t-title">₹{sub + 5}</span></div><div class="btn p">Pay ₹{sub + 5}</div></div>')
    s.append(frame("05 · Checkout", checkout))
    menu = [("box", "Your orders"), ("heart", "Wishlist"), ("pin", "Saved addresses"), ("card", "Payment methods"), ("bell", "Notifications"), ("gear", "Settings")]
    profile = ('<div class="pad" style="padding-top:8px"><div class="row" style="gap:14px"><div class="av" style="width:64px;height:64px;border-radius:50%;background:var(--brand-100);color:var(--brand-600);display:grid;place-items:center;font:700 26px var(--font-display)">P</div>'
               '<div class="grow"><div class="t-title">Priya Nair</div><div class="t-caption muted">+91 98450 •••21 · priya@example.com</div></div></div>'
               '<div class="row" style="gap:10px;margin-top:16px">' + "".join(f'<div class="card grow" style="background:var(--canvas);text-align:center"><div class="t-title">{v}</div><div class="t-caption muted">{k}</div></div>' for k, v in (("Orders", "23"), ("Saved", "₹1,860"), ("Haat coins", "340"))) + "</div></div>"
               '<div style="margin-top:12px">' + "".join(f'<div class="list-row">{icon(ic)}<span class="t-body grow">{t}</span>{icon("chevron", 20, "")}</div>' for ic, t in menu) + "</div>")
    s.append(frame("06 · Profile", profile, tabs(4)))
    orders = [("Arriving in 12 min", "now", "Alphonso mangoes, atta +1", "₹738"), ("Delivered · 2 Nov", "done", "Assam tea, paneer", "₹405"), ("Delivered · 28 Oct", "done", "Rice, toor dal, ghee", "₹1,213")]
    track = '<div class="row" style="margin:14px 0 4px">' + "".join(f'<div class="step {c}"><div class="dot">{"✓" if c == "done" else "•"}</div>{n}</div>' for n, c in (("Packed", "done"), ("On the way", "now"), ("Delivered", ""))) + "</div>"
    ol = '<div class="pad">' + "".join(f'<div class="card" style="border:1px solid var(--line);margin-bottom:12px"><div class="row"><span class="t-label grow" style="color:{"var(--brand-600)" if st == "now" else "var(--leaf-700)"}">{t}</span><span class="t-label">{amt}</span></div>'
                                       f'<div class="t-body" style="color:var(--ink-700);margin-top:4px">{items}</div>{track if st == "now" else ""}'
                                       f'<div class="row" style="margin-top:10px;gap:8px"><div class="btn s grow" style="height:40px">{"Track order" if st == "now" else "Reorder"}</div><div class="btn grow" style="height:40px;background:#fff;border:1px solid var(--ink-500);color:var(--ink-900)">{"Help" if st == "now" else "Rate"}</div></div></div>' for t, st, items, amt in orders) + "</div>"
    s.append(frame("07 · Orders", hdr("Your orders") + ol, tabs(4)))
    srch = (f'<div class="top">{icon("back")}<div class="search grow" style="border-color:var(--brand-600);border-width:2px;color:var(--ink-900)">{icon("search", 20)}<span class="grow">mang</span>✕</div></div>'
            '<div class="pad"><div class="t-caption muted" style="margin:4px 0 8px">SUGGESTIONS</div>' + "".join(f'<div class="row" style="padding:10px 0;gap:12px">{icon("search", 18)}<span class="t-body"><b>mang</b>{x}</span></div>' for x in ("o", "o pulp", "o pickle")) +
            '<div class="row" style="justify-content:space-between;margin-top:12px"><span class="t-title">Results for “mango”</span><span class="row t-label" style="gap:4px">' + icon("filter", 18) + 'Filter</span></div></div>'
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px 16px">' + pcard("mango") + pcard("banana") + "</div>")
    s.append(frame("08 · Search", srch))
    wish = (hdr("Wishlist (4)") + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:0 16px">' + "".join(pcard(k) for k in ("ghee", "tea", "rice", "dal")) + "</div>")
    s.append(frame("09 · Wishlist", wish, tabs(2)))
    sets = [("Order updates", "Delivery and payment alerts", True), ("Offers & deals", "Max one a day", False), ("Dark mode", "Follow the system setting", False),
            ("Large text", "Uses your phone's font size", True)]
    settings = (hdr("Settings") + '<div class="pad t-caption muted" style="margin:4px 0">PREFERENCES</div>' + "".join(
        f'<div class="list-row"><div class="grow"><div class="t-body">{t}</div><div class="t-caption muted">{d}</div></div><div class="toggle {"on" if on else ""}" role="switch" aria-checked="{str(on).lower()}"></div></div>' for t, d, on in sets)
        + '<div class="pad t-caption muted" style="margin:16px 0 4px">ACCOUNT</div>' + "".join(f'<div class="list-row"><span class="t-body grow">{t}</span>{icon("chevron", 20)}</div>' for t in ("Language · English", "Privacy & data", "Help centre"))
        + '<div class="list-row"><span class="t-body grow" style="color:var(--danger-700);font-weight:600">Log out</span></div>')
    s.append(frame("10 · Settings", settings))
    return page("Haat: e-commerce app (10 screens)", "haat", HAAT_CSS, s)


if __name__ == "__main__":
    for name, html in (("wireframes.html", wireframes()), ("circle-hifi.html", circle_hifi()), ("haat.html", haat())):
        open(os.path.join(HERE, name), "w").write(html)
    print("pages written")
