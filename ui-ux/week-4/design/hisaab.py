"""Hisaab: split shared expenses with hostel-mates and trip friends, settle in one tap over UPI.

Generates from one source:
  screens.html     16 high-fidelity screens (static board)
  wireframes.html  the key flow as low-fidelity wireframes
  prototype.html   clickable prototype of the key flows (one phone, animated transitions)
  spec.html        3 screens in "spec mode" for developer handoff (sizes, type and colour tokens annotated)
    python design/hisaab.py && node design/render.js
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "week-2", "design"))
from screens import BASE_CSS, ICONS, icon  # noqa: E402  (shared icon set and phone frame styles from week 2)

ICONS.update({
    "split": "M6 4v6a6 6 0 0 0 6 6h0a6 6 0 0 0 6-6V4M12 16v4", "upi": "M7 4l4 16M13 4l4 16M5 9h14M4 15h14",
    "receipt": "M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6", "users": "M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-7 10a7 7 0 0 1 14 0M17 3a4 4 0 0 1 0 8m5 10a7 7 0 0 0-4-6.3",
    "bolt": "M13 3 5 14h6l-1 7 8-11h-6z", "share": "M4 12v8h16v-8M12 3v13M7 8l5-5 5 5", "food": "M7 3v18M4 3v5a3 3 0 0 0 6 0V3M17 3c-2 2-3 5-3 8h4v10",
    "cab": "M5 16V11l2-5h10l2 5v5M5 16h14M5 16v2m14-2v2M8 13h.01M16 13h.01", "home2": "M3 11 12 3l9 8M5 9v12h14V9", "pie": "M12 3v9h9A9 9 0 1 1 12 3zm3 0a6 6 0 0 1 6 6h-6z",
    "lock": "M6 11h12v10H6zM8 11V7a4 4 0 0 1 8 0v4", "clock": "M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18zm0 4v5l3 2",
})

CSS = """
.av{border-radius:50%;flex:none;display:grid;place-items:center;color:#fff;font:700 14px var(--font-body)}
.hero{background:var(--brand-900);color:#fff;border-radius:var(--r-lg);padding:var(--s4)}
.amt{font:700 31px/38px var(--font-display);letter-spacing:-.01em}
.owe{color:var(--owe-700)} .owed{color:var(--owed-700)}
.pill{font:var(--caption);font-weight:600;padding:3px 10px;border-radius:999px;white-space:nowrap}
.p-owe{background:var(--owe-100);color:var(--owe-700)} .p-owed{background:var(--owed-100);color:var(--owed-700)} .p-amber{background:var(--amber-100);color:var(--amber-700)}
.list-row{display:flex;align-items:center;gap:14px;padding:12px 16px;border-bottom:1px solid var(--line)}
.cat{width:44px;height:44px;border-radius:14px;display:grid;place-items:center;flex:none}
.bar{flex:none;padding:12px 16px 30px;background:var(--surface);border-top:1px solid var(--line)}
.key{height:56px;display:grid;place-items:center;font:600 24px var(--font-display);border-radius:12px}
.seg{display:flex;background:var(--canvas);border-radius:12px;padding:4px;gap:4px} .seg span{flex:1;text-align:center;padding:8px 0;border-radius:9px;font:var(--label);color:var(--ink-700)}
.seg span.on{background:var(--surface);color:var(--ink-900);box-shadow:0 1px 3px rgba(0,0,0,.12)}
.inp{height:52px;border:1.5px solid var(--ink-500);border-radius:var(--r-md);display:flex;align-items:center;padding:0 14px;gap:10px;font:var(--body)}
.dots{display:flex;gap:6px;justify-content:center} .dots i{width:8px;height:8px;border-radius:4px;background:var(--line)} .dots i.on{width:24px;background:var(--brand-600)}
.illus{height:300px;border-radius:28px;margin:8px 16px 0;position:relative;overflow:hidden;background:var(--brand-100)}
.check{width:96px;height:96px;border-radius:50%;background:var(--owed-700);display:grid;place-items:center;color:#fff;margin:0 auto}
[data-goto]{cursor:pointer} [data-goto]:focus-visible{outline:3px solid var(--brand-500);outline-offset:2px;border-radius:12px}
"""

PEOPLE = {"You": "#0F766E", "Aarav": "#6457F0", "Diya": "#B0127A", "Kabir": "#B54708", "Meera": "#0369A1", "Ishan": "#7C3AED"}


def av(n, s=40):
    return f'<div class="av" style="width:{s}px;height:{s}px;background:{PEOPLE[n]};font-size:{s // 2.7:.0f}px">{n[0]}</div>'


def frame(id_, label, body, tab=None):
    return (f'<div class="wrap" id="w-{id_}"><div class="label-out">{label}</div><div class="frame" data-name="{label}" data-id="{id_}">'
            f'<div class="status"><span>9:41</span><span>●●● ▮</span></div><div class="screen">{body}</div>{tab or ""}</div></div>')


def tabs(on):
    items = [("home2", "Home", "home"), ("users", "Groups", "group"), ("plus", "Add", "add"), ("clock", "Activity", "activity"), ("user", "You", "profile")]
    return '<nav class="tabbar">' + "".join(f'<div class="tab {"on" if k == on else ""}" data-goto="{g}">{icon(ic)}{n}</div>' for k, (ic, n, g) in enumerate(items)) + "</nav>"


def top(title, back="home", right=""):
    return f'<div class="top"><div class="iconbtn" data-goto="{back}" aria-label="Back">{icon("back")}</div><span class="t-title grow">{title}</span>{right}</div>'


def btn(text, goto, kind="p", extra=""):
    return f'<div class="btn {kind}" data-goto="{goto}" {extra}>{text}</div>'


def onboarding(n, title, body, art, cta, goto, skip=True):
    return (f'<div class="row pad" style="justify-content:flex-end;height:44px">{"<span class=\"t-label muted\" data-goto=\"signin\">Skip</span>" if skip else ""}</div>'
            f'<div class="illus">{art}</div><div class="pad" style="margin-top:28px"><div class="dots">{"".join(f"<i class={chr(34)}on{chr(34)}></i>" if i == n else "<i></i>" for i in range(3))}</div>'
            f'<h1 class="t-display" style="margin-top:24px" data-spec="display 31/38 · ink-900">{title}</h1><p class="t-body" style="color:var(--ink-700);margin-top:12px">{body}</p></div>'
            f'<div class="bar" style="margin-top:auto;border:0">{btn(cta, goto)}</div>')


ART1 = ('<svg viewBox="0 0 358 300" width="100%" height="100%"><circle cx="179" cy="150" r="96" fill="#fff"/>'
        '<rect x="110" y="96" width="138" height="108" rx="18" fill="#0F766E"/><path d="M130 132h98M130 158h60" stroke="#D5F5EF" stroke-width="10" stroke-linecap="round"/>'
        '<circle cx="92" cy="96" r="26" fill="#6457F0"/><circle cx="268" cy="96" r="26" fill="#B0127A"/><circle cx="92" cy="214" r="26" fill="#B54708"/><circle cx="268" cy="214" r="26" fill="#0369A1"/>'
        '<path d="M115 106l20 10M243 106l-20 10M115 204l20-10M243 204l-20-10" stroke="#0B3B37" stroke-width="4" stroke-dasharray="6 6"/></svg>')
ART2 = ('<svg viewBox="0 0 358 300" width="100%" height="100%"><rect x="60" y="60" width="238" height="70" rx="16" fill="#fff"/><text x="84" y="104" font-size="22" font-weight="700" fill="#101828">Maggi run ₹360</text>'
        '<path d="M179 140v28" stroke="#0B3B37" stroke-width="4"/><g font-size="18" font-weight="700">' + "".join(
            f'<rect x="{40 + i * 98}" y="176" width="82" height="64" rx="14" fill="#fff"/><text x="{58 + i * 98}" y="216" fill="#0F766E">₹120</text>' for i in range(3)) + "</g></svg>")
ART3 = ('<svg viewBox="0 0 358 300" width="100%" height="100%"><rect x="104" y="40" width="150" height="230" rx="26" fill="#fff"/><rect x="124" y="70" width="110" height="110" rx="18" fill="#0F766E"/>'
        '<path d="M150 118l20 20 36-38" stroke="#fff" stroke-width="12" fill="none" stroke-linecap="round" stroke-linejoin="round"/><text x="179" y="222" text-anchor="middle" font-size="22" font-weight="800" fill="#101828">₹240 paid</text>'
        '<text x="179" y="248" text-anchor="middle" font-size="14" fill="#5D6B82">via UPI · 2 sec</text></svg>')

EXP = [("food", "#FEF0C7", "Maggi & chai run", "Diya paid", 360, "Today, 11:40 pm", "you owe ₹120", "owe"),
       ("cab", "#E0EAFF", "Cab to Majestic", "You paid", 480, "Yesterday", "you lent ₹320", "owed"),
       ("home2", "#D5F5EF", "Wi-Fi recharge (Nov)", "Aarav paid", 799, "1 Nov", "you owe ₹266", "owe"),
       ("receipt", "#FDECEA", "Laundry tokens", "You paid", 150, "30 Oct", "you lent ₹100", "owed")]


def screens():
    s = {}
    s["ob1"] = ("01 · Onboarding: value", onboarding(0, "No more “who paid for what?”", "Add a shared expense in seconds. Hisaab keeps a running balance with every friend, so nobody has to remember.", ART1, "Next", "ob2"))
    s["ob2"] = ("02 · Onboarding: how it works", onboarding(1, "Split it any way that's fair", "Equally, by exact amounts, or by shares when someone skipped dinner. Everyone sees the same numbers.", ART2, "Next", "ob3"))
    s["ob3"] = ("03 · Onboarding: settle", onboarding(2, "Settle up in one tap", "Pay what you owe with any UPI app. Hisaab never holds your money and never sees your UPI PIN.", ART3, "Get started", "signin", skip=False))
    s["signin"] = ("04 · Sign in", top("", "ob3") + '<div class="pad"><h1 class="t-headline">What’s your phone number?</h1><p class="t-body" style="color:var(--ink-700);margin-top:8px">We’ll text a 6-digit code. Friends find you by this number, so splits reach the right person.</p>'
                   '<label class="t-label" style="display:block;margin-top:24px">Mobile number</label><div class="inp" style="margin-top:8px;border-color:var(--brand-600);border-width:2px" data-spec="input 52 · border 2 brand-600 · r 12"><b>+91</b><span style="width:1px;height:24px;background:var(--line)"></span>98450 12345</div>'
                   '<p class="t-caption muted" style="margin-top:8px">Standard SMS rates may apply.</p></div><div class="bar" style="margin-top:auto;border:0">' + btn("Send code", "home") + "</div>")
    groups = [("Room 214 · Hostel B", "4 people", "you owe ₹386", "owe", "group"), ("Coorg trip", "6 people", "owes you ₹1,240", "owed", "group"), ("Project team", "3 people", "settled up", "", "group")]
    s["home"] = ("05 · Home", '<div class="top"><div class="grow"><div class="t-caption muted">Namaste,</div><div class="t-title">Priyanshu</div></div><div class="iconbtn" style="position:relative">' + icon("bell") + '<span class="badge" style="background:var(--owe-700)">2</span></div></div>'
                 '<div class="pad"><div class="hero" data-spec="card r 20 · p 16 · brand-900"><div class="t-caption" style="color:var(--brand-100)">OVERALL BALANCE</div><div class="amt" style="margin:4px 0 2px">+ ₹854</div>'
                 '<div class="t-label" style="color:var(--brand-100)">You are owed ₹1,240 · you owe ₹386</div><div class="row" style="gap:8px;margin-top:14px"><div class="btn" style="background:#fff;color:var(--brand-900);flex:1;height:44px" data-goto="settle">Settle up</div>'
                 '<div class="btn" style="background:rgba(255,255,255,.14);color:#fff;flex:1;height:44px" data-goto="remind">Remind</div></div></div></div>'
                 '<div class="row pad" style="justify-content:space-between;margin:20px 0 4px"><span class="t-title">Groups</span><span class="t-label" style="color:var(--brand-600)" data-goto="newgroup">+ New</span></div>'
                 + "".join(f'<div class="list-row" data-goto="{g}"><div class="cat" style="background:var(--brand-100);color:var(--brand-600)">{icon("users")}</div><div class="grow"><div class="t-label">{n}</div><div class="t-caption muted">{m}</div></div>'
                           f'<span class="pill {"p-" + k if k else "p-amber"}" style="{"" if k else "background:var(--canvas);color:var(--ink-700)"}">{b}</span></div>' for n, m, b, k, g in groups), tabs(0))
    s["group"] = ("06 · Group: Room 214", top("Room 214 · Hostel B", "home", f'<div class="iconbtn" data-goto="newgroup" aria-label="Invite people">{icon("share")}</div>')
                  + '<div class="row pad" style="gap:-8px;margin-bottom:12px">' + "".join(f'<div style="margin-right:-8px;border:2px solid #fff;border-radius:50%">{av(n, 34)}</div>' for n in ("You", "Aarav", "Diya", "Kabir")) + '<span class="t-caption muted" style="margin-left:18px">You, Aarav, Diya, Kabir</span></div>'
                  '<div class="pad"><div class="card" style="background:var(--owe-100);border-radius:var(--r-lg);padding:14px 16px" data-goto="balances"><div class="row"><div class="grow"><div class="t-label owe">You owe ₹386 in this group</div>'
                  '<div class="t-caption" style="color:var(--ink-700)">Diya ₹120 · Aarav ₹266</div></div><span class="t-label owe">Details ›</span></div></div></div>'
                  '<div class="pad t-caption muted" style="margin:18px 0 4px;letter-spacing:.06em">NOVEMBER</div>'
                  + "".join(f'<div class="list-row" data-goto="expense"><div class="cat" style="background:{bg}">{icon(ic)}</div><div class="grow"><div class="t-label">{t}</div><div class="t-caption muted">{who} ₹{a} · {d}</div></div>'
                            f'<span class="t-label {k}">{r}</span></div>' for ic, bg, t, who, a, d, r, k in EXP)
                  + '<div style="position:absolute;right:20px;bottom:110px;width:60px;height:60px;border-radius:20px;background:var(--brand-600);color:#fff;display:grid;place-items:center;box-shadow:0 8px 20px rgba(15,118,110,.4)" data-goto="add" aria-label="Add expense" data-spec="FAB 60 · r20">' + icon("plus", 28) + "</div>", tabs(1))
    keypad = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;padding:0 16px">' + "".join(f'<div class="key">{k}</div>' for k in "123456789") + '<div class="key">.</div><div class="key">0</div><div class="key">⌫</div></div>'
    s["add"] = ("07 · Add expense", top("Add expense", "group", '<span class="t-label" style="color:var(--brand-600)">Room 214</span>')
                + '<div class="pad" style="text-align:center;margin-top:8px"><div class="t-caption muted">Amount</div><div style="font:800 52px/60px var(--font-display);margin:4px 0" data-spec="amount 52/60 · 800 · ink-900">₹360</div>'
                '<div class="inp" style="margin-top:8px;justify-content:center;border-color:var(--line)">' + icon("food", 20) + ' Maggi &amp; chai run</div>'
                '<div class="row" style="gap:8px;margin-top:12px"><div class="chip" style="flex:1;text-align:center">Paid by <b>Diya</b></div><div class="chip" style="flex:1;text-align:center" data-goto="split">Split <b>equally</b> ›</div></div></div>'
                '<div style="margin-top:12px">' + keypad + '</div><div class="bar" style="margin-top:auto;border:0">' + btn("Save expense", "saved") + "</div>")
    shares = [("You", 120, True), ("Aarav", 0, False), ("Diya", 120, True), ("Kabir", 120, True)]
    s["split"] = ("08 · Split options", top("Split ₹360", "add") + '<div class="pad"><div class="seg" data-spec="segmented · r 12 · p 4"><span class="on">Equally</span><span>Exact</span><span>Shares</span><span>%</span></div>'
                  '<p class="t-caption muted" style="margin:12px 0 4px">Untick anyone who wasn’t there.</p></div>'
                  + "".join(f'<div class="list-row">{av(n, 36)}<span class="t-body grow">{n}{" (skipped)" if not on else ""}</span><span class="t-label" style="color:{"var(--ink-900)" if on else "var(--ink-500)"}">₹{v}</span>'
                            f'<div style="width:24px;height:24px;border-radius:7px;display:grid;place-items:center;{"background:var(--brand-600);color:#fff" if on else "border:2px solid var(--ink-500)"}">{icon("check", 16) if on else ""}</div></div>' for n, v, on in shares)
                  + '<div class="pad" style="margin-top:12px"><div class="card" style="background:var(--canvas);border-radius:12px;padding:12px 14px" class="row"><span class="t-label">₹120 each · 3 people</span> <span class="t-caption muted">Totals ₹360 ✓</span></div></div>'
                  '<div class="bar" style="margin-top:auto;border:0">' + btn("Done", "add") + "</div>")
    s["saved"] = ("09 · Expense saved", top("Room 214 · Hostel B", "home")
                  + '<div class="pad"><div class="card" style="background:var(--owed-100);border-radius:16px;padding:14px 16px" class="row"><div class="row">' + icon("check", 22) + '<span class="t-label owed">Saved. Diya, Kabir and you were notified.</span></div></div></div>'
                  '<div class="pad t-caption muted" style="margin:18px 0 4px;letter-spacing:.06em">NOVEMBER</div>'
                  '<div class="list-row" style="background:var(--brand-100)"><div class="cat" style="background:#FEF0C7">' + icon("food") + '</div><div class="grow"><div class="t-label">Maggi &amp; chai run</div><div class="t-caption muted">Diya paid ₹360 · just now</div></div><span class="t-label owe">you owe ₹120</span></div>'
                  + "".join(f'<div class="list-row"><div class="cat" style="background:{bg}">{icon(ic)}</div><div class="grow"><div class="t-label">{t}</div><div class="t-caption muted">{who} ₹{a} · {d}</div></div><span class="t-label {k}">{r}</span></div>' for ic, bg, t, who, a, d, r, k in EXP[1:])
                  + '<div class="pad" style="margin-top:16px"><div class="t-caption muted" style="text-align:center">Undo is available for 10 seconds</div></div>', tabs(1))
    s["expense"] = ("10 · Expense detail", top("Expense", "group", f'<span class="t-label" style="color:var(--brand-600)">Edit</span>')
                    + '<div class="pad" style="text-align:center"><div class="cat" style="background:#FEF0C7;margin:0 auto;width:64px;height:64px;border-radius:20px">' + icon("food", 30) + '</div><h1 class="t-headline" style="margin-top:12px">Maggi &amp; chai run</h1>'
                    '<div class="amt" style="margin-top:4px">₹360</div><div class="t-caption muted">Added by Diya · Today, 11:40 pm</div></div>'
                    '<div class="pad t-caption muted" style="margin:20px 0 4px;letter-spacing:.06em">WHO OWES WHAT</div>'
                    + "".join(f'<div class="list-row">{av(n, 36)}<span class="t-body grow">{n}</span><span class="t-label {k}">{t}</span></div>' for n, t, k in (("Diya", "paid ₹360, owed ₹240", "owed"), ("You", "owe ₹120", "owe"), ("Kabir", "owes ₹120", "owe"), ("Aarav", "not included", "muted")))
                    + '<div class="pad" style="margin-top:16px"><div class="row t-caption muted" style="gap:8px">' + icon("receipt", 18) + 'Bill photo attached · 1 comment</div></div>')
    s["balances"] = ("11 · Balances & simplify", top("Balances", "group") + '<div class="pad"><div class="card" style="background:var(--brand-100);border-radius:16px;padding:14px 16px"><div class="row" style="gap:10px">'
                     + icon("bolt", 22) + '<div><div class="t-label" style="color:var(--brand-600)">Simplified: 5 payments → 3</div><div class="t-caption" style="color:var(--ink-700)">Same totals, fewer UPI transfers.</div></div></div></div></div>'
                     '<div class="pad t-caption muted" style="margin:18px 0 4px;letter-spacing:.06em">SUGGESTED PAYMENTS</div>'
                     + "".join(f'<div class="list-row">{av(a, 34)}<span class="t-caption muted">→</span>{av(b, 34)}<span class="t-body grow">{a} {"pay" if a == "You" else "pays"} {b}</span><b class="t-label">₹{x}</b>{"<span class=" + chr(34) + "chip" + chr(34) + " style=" + chr(34) + "border-color:var(--brand-600);color:var(--brand-600)" + chr(34) + " data-goto=" + chr(34) + "settle" + chr(34) + ">Pay</span>" if a == "You" else ""}</div>'
                               for a, b, x in (("You", "Diya", 120), ("You", "Aarav", 266), ("Kabir", "Diya", 120))))
    s["settle"] = ("12 · Settle up", top("Settle up", "balances") + f'<div class="pad" style="text-align:center;margin-top:8px"><div style="display:flex;justify-content:center">{av("Aarav", 72)}</div><div class="t-title" style="margin-top:10px">Pay Aarav</div>'
                   '<div class="t-caption muted">aarav@okicici</div><div style="font:800 52px/60px var(--font-display);margin:16px 0 4px">₹266</div><div class="t-caption muted">For: Wi-Fi recharge (Nov)</div></div>'
                   '<div class="pad t-caption muted" style="margin:24px 0 6px;letter-spacing:.06em">PAY WITH</div><div class="pad">'
                   + "".join(f'<div class="card row" style="border:1.5px solid {"var(--brand-600)" if on else "var(--line)"};border-radius:14px;padding:12px 14px;margin-bottom:8px"><div class="cat" style="background:var(--canvas);width:36px;height:36px">{icon("upi", 20)}</div><span class="t-label grow">{n}</span><div style="width:22px;height:22px;border-radius:50%;border:{"7px solid var(--brand-600)" if on else "2px solid var(--ink-500)"}"></div></div>' for n, on in (("Any UPI app", True), ("Record a cash payment", False)))
                   + '</div><div class="bar" style="margin-top:auto;border:0"><div class="row t-caption muted" style="gap:6px;justify-content:center;margin-bottom:10px">' + icon("lock", 16) + 'Paid directly bank to bank. Hisaab never holds money.</div>' + btn("Pay ₹266 with UPI", "paid") + "</div>")
    s["paid"] = ("13 · Payment success", '<div style="flex:1;display:flex;flex-direction:column;justify-content:center;text-align:center;padding:0 24px"><div class="check" data-spec="success 96 · owed-700">' + icon("check", 48) + '</div>'
                 '<h1 class="t-headline" style="margin-top:24px">₹266 sent to Aarav</h1><p class="t-body" style="color:var(--ink-700);margin-top:8px">UPI ref 4321 8765 0912. Aarav has been notified and your balance is updated.</p>'
                 '<div class="card" style="background:var(--canvas);border-radius:16px;padding:14px;margin-top:24px"><div class="t-caption muted">Room 214 balance</div><div class="t-title owe">You owe ₹120 <span class="t-caption muted">(was ₹386)</span></div></div></div>'
                 '<div class="bar" style="border:0">' + btn("Done", "home") + '<div class="btn" style="margin-top:8px;background:transparent;color:var(--brand-600)" data-goto="settle">Pay Diya ₹120 too</div></div>')
    s["newgroup"] = ("14 · Create group & invite", top("New group", "home") + '<div class="pad"><label class="t-label">Group name</label><div class="inp" style="margin-top:8px">Coorg trip</div>'
                     '<div class="t-label" style="margin-top:20px">Type</div><div class="row" style="gap:8px;margin-top:8px;flex-wrap:wrap"><span class="chip">Room</span><span class="chip on">Trip</span><span class="chip">Project</span><span class="chip">Other</span></div>'
                     '<div class="t-label" style="margin-top:20px">Add people</div></div>'
                     + "".join(f'<div class="list-row">{av(n, 36)}<span class="t-body grow">{n}</span><span class="t-caption muted">{p}</span></div>' for n, p in (("Meera", "on Hisaab"), ("Ishan", "on Hisaab")))
                     + '<div class="pad" style="margin-top:12px"><div class="card row" style="border:1.5px dashed var(--brand-600);border-radius:14px;padding:12px 14px;color:var(--brand-600)">' + icon("share", 20) + '<span class="t-label">Invite with a WhatsApp link</span></div>'
                     '<p class="t-caption muted" style="margin-top:8px">Friends can join without installing. They see the group in the browser.</p></div><div class="bar" style="margin-top:auto;border:0">' + btn("Create group", "group") + "</div>")
    acts = [("Diya", "added “Maggi &amp; chai run”", "you owe ₹120", "owe", "11:40 pm"), ("You", "paid Aarav ₹266 via UPI", "settled", "owed", "10:05 pm"),
            ("Kabir", "commented on “Cab to Majestic”: “I’ll pay Friday”", "", "", "6:12 pm"), ("Meera", "joined Coorg trip", "", "", "Yesterday"), ("Aarav", "added “Wi-Fi recharge (Nov)”", "you owe ₹266", "owe", "1 Nov")]
    s["activity"] = ("15 · Activity", '<div class="top"><span class="t-headline grow">Activity</span></div>' + "".join(
        f'<div class="list-row" style="align-items:flex-start">{av(n, 36)}<div class="grow"><div class="t-body"><b>{n}</b> {t}</div><div class="t-caption muted">{w}</div></div>{f"<span class=" + chr(34) + "pill p-" + k + chr(34) + ">" + b + "</span>" if b else ""}</div>' for n, t, b, k, w in acts), tabs(3))
    cats = [("Food & chai", 2340, "#B54708", 46), ("Travel", 1480, "#0369A1", 29), ("Room & bills", 920, "#0F766E", 18), ("Other", 360, "#7C3AED", 7)]
    s["insights"] = ("16 · Monthly insights", top("October spending", "profile") + '<div class="pad"><div class="t-caption muted">Your share of group spending</div><div class="amt">₹5,100</div><div class="t-caption owed" style="font-weight:600">₹640 less than September</div>'
                     '<div style="display:flex;height:14px;border-radius:7px;overflow:hidden;margin:16px 0 8px">' + "".join(f'<div style="width:{p}%;background:{c}"></div>' for _, _, c, p in cats) + '</div></div>'
                     + "".join(f'<div class="list-row"><div style="width:12px;height:12px;border-radius:4px;background:{c}"></div><span class="t-body grow">{n}</span><span class="t-caption muted">{p}%</span><b class="t-label" style="width:64px;text-align:right">₹{v:,}</b></div>' for n, v, c, p in cats)
                     + '<div class="pad" style="margin-top:16px"><div class="card" style="background:var(--amber-100);border-radius:16px;padding:14px"><div class="t-label" style="color:var(--amber-700)">Late-night food is your biggest category</div><div class="t-caption" style="color:var(--ink-700);margin-top:2px">18 orders after 11 pm. Set a monthly limit?</div></div></div>')
    s["profile"] = ("17 · You", '<div class="pad" style="padding-top:8px"><div class="row" style="gap:14px">' + av("You", 64) + '<div class="grow"><div class="t-title">Priyanshu Sharan</div><div class="t-caption muted">+91 98450 •••45</div></div></div>'
                    '<div class="card row" style="background:var(--canvas);border-radius:14px;padding:12px 14px;margin-top:16px">' + icon("upi", 22) + '<div class="grow"><div class="t-label">UPI ID for receiving</div><div class="t-caption muted">priyanshu@oksbi</div></div><span class="t-label" style="color:var(--brand-600)">Change</span></div></div>'
                    + "".join(f'<div class="list-row" {"data-goto=" + chr(34) + g + chr(34) if g else ""}>{icon(i)}<span class="t-body grow">{t}</span>{icon("chevron", 20)}</div>' for i, t, g in (("pie", "Monthly insights", "insights"), ("bell", "Reminders", "remind"), ("lock", "Privacy &amp; security", ""), ("gear", "Settings", "")))
                    + '<div class="list-row"><span class="t-body owe grow" style="font-weight:600">Log out</span></div>', tabs(4))
    s["remind"] = ("18 · Friendly reminder", top("Remind Kabir", "home") + '<div class="pad"><p class="t-body" style="color:var(--ink-700)">Kabir owes you ₹320 for “Cab to Majestic”. Pick a tone, then we send it on WhatsApp from your number.</p>'
                   '<div class="seg" style="margin-top:16px"><span class="on">Friendly</span><span>Direct</span><span>Funny</span></div>'
                   '<div class="card" style="background:#DCF8C6;border-radius:16px 16px 4px 16px;padding:14px;margin-top:16px;color:var(--ink-900)"><p class="t-body">Hey Kabir! Whenever you get a sec, ₹320 for the Majestic cab 🚕 One tap to pay: hisaab.app/p/k3x9</p></div>'
                   '<p class="t-caption muted" style="margin-top:8px">We never send reminders automatically. You decide when.</p></div><div class="bar" style="margin-top:auto;border:0">' + btn("Send on WhatsApp", "home") + "</div>")
    return s


def page(title, body, extra_css=""):
    body = body.replace(' data-goto="', ' role="button" tabindex="0" data-goto="')   # every tappable element is a real, focusable button
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>'
            f'<link rel="stylesheet" href="tokens.css"><style>{BASE_CSS}{CSS}{extra_css}</style></head><body class="theme-hisaab">{body}</body></html>')


WF_CSS = """.wf{--brand-600:#333;--brand-100:#e8e8e8;--brand-900:#555;--owe-700:#333;--owe-100:#eee;--owed-700:#333;--owed-100:#eee;--amber-700:#333;--amber-100:#eee;
  --ink-900:#222;--ink-700:#555;--ink-500:#777;--line:#ccc;--canvas:#f2f2f2} .wf .frame{filter:grayscale(1)} .wf .illus svg,.wf .hero .amt{opacity:.35}
.wf .frame *{font-family:var(--font-body)!important}"""
PROTO_CSS = """body{padding:0;min-height:100vh;align-items:center;justify-content:center;background:#dfe7e5;flex-direction:column;gap:16px}
.stage{position:relative;width:390px;height:844px} .stage .wrap{position:absolute;inset:0;margin:0;transition:transform 380ms cubic-bezier(.2,.8,.2,1),opacity 380ms}
.stage .wrap .label-out{display:none} .stage .wrap.off-r,.stage .wrap.off-l,.stage .wrap.off-u{pointer-events:none;z-index:0} .stage .wrap{z-index:2} .stage .wrap.off-r{transform:translateX(110%);opacity:0} .stage .wrap.off-l{transform:translateX(-30%);opacity:0} .stage .wrap.off-u{transform:translateY(8%) scale(.96);opacity:0}
.hint{font:600 13px var(--font-body);color:#3a4a47} [data-goto]:hover{filter:brightness(.97)}
@media (prefers-reduced-motion: reduce){.stage .wrap{transition:none}}"""
SPEC_CSS = """[data-spec]{outline:1.5px dashed #E5484D;outline-offset:-1px} [data-spec]:not([style*="absolute"]){position:relative}
[data-spec]::after{content:attr(data-spec);position:absolute;left:2px;top:2px;background:#E5484D;color:#fff;
  font:600 9px/14px Inter,sans-serif;padding:0 5px;border-radius:3px;white-space:nowrap;z-index:5;pointer-events:none}
.legend{width:100%;font:600 14px var(--font-body);color:#555}"""
SPEC_JS = """<script>
const tag={'.top':'app bar · title 20/28 600 · p 8/16','.btn.p':'button h52 · r12 · brand-600 · label 14/20 600 white','.list-row':'row · p 12/16 · gap 14 · divider line',
 '.chip':'chip h36 · r pill · border line · label 14/20','.key':'key h56 · 24 600 display','.tabbar':'tab bar h84 · icon 24 · caption 12/16 · active brand-600',
 '.cat':'tile 44 · r14','.pill':'pill · caption 12/16 600 · r pill','.inp':'input h52 · r12 · border 1.5 ink-500'};
document.querySelectorAll('.spec .frame').forEach(f=>{ for(const [sel,txt] of Object.entries(tag)) f.querySelectorAll(sel).forEach((e,i)=>{ if(!e.dataset.spec && i<1 && !e.closest('[data-spec]')) e.dataset.spec=txt; }); });
</script>"""

if __name__ == "__main__":
    S = screens()
    board = "".join(frame(k, label, body, None if not isinstance(body, tuple) else None) for k, (label, *rest) in S.items() for body in [rest[0]])
    # screens with a tab bar carry it as a third element
    board = "".join(frame(k, v[0], v[1], v[2] if len(v) > 2 else None) for k, v in S.items())
    open(os.path.join(HERE, "screens.html"), "w").write(page("Hisaab: high-fidelity screens", board))
    flow = ["ob1", "home", "group", "add", "split", "settle"]
    open(os.path.join(HERE, "wireframes.html"), "w").write(page("Hisaab: wireframes", '<div class="wf" style="display:contents">' + "".join(frame(k, "WF · " + S[k][0].split("· ")[1], S[k][1], S[k][2] if len(S[k]) > 2 else None) for k in flow) + "</div>", WF_CSS))
    proto = ('<div class="hint">Hisaab prototype · tap the highlighted buttons (Esc or the back arrow goes back)</div><div class="stage">'
             + "".join(frame(k, v[0], v[1], v[2] if len(v) > 2 else None).replace('class="wrap"', 'class="wrap off-r"') for k, v in S.items()) + "</div>"
             """<script>
const stack=[]; let cur=null;
function show(id, dir){const next=document.getElementById('w-'+id); if(!next||id===cur) return; const prev=cur&&document.getElementById('w-'+cur);
  if(prev){prev.classList.add(dir==='back'?'off-r':(next.querySelector('.check')?'off-u':'off-l'));}
  next.classList.remove('off-r','off-l','off-u'); if(dir!=='back'&&cur) stack.push(cur);
  if(dir!=='back'&&['saved','paid'].includes(id)) stack.splice(0,stack.length,'home');   // a finished flow: Back goes home, not into the form
  if(dir!=='back'&&id==='home') stack.length=0; cur=id; history.replaceState(null,'','#'+id);}
document.addEventListener('click',e=>{const t=e.target.closest('[data-goto]'); if(!t) return; const g=t.dataset.goto; const isBack=t.getAttribute('aria-label')==='Back';
  if(isBack&&stack.length){show(stack.pop(),'back');} else show(g,'fwd');});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&stack.length) show(stack.pop(),'back'); if((e.key==='Enter'||e.key===' ')&&e.target.dataset&&e.target.dataset.goto){e.preventDefault();e.target.click();}});
show(location.hash.slice(1)||'ob1','fwd');
</script>""")
    open(os.path.join(HERE, "prototype.html"), "w").write(page("Hisaab: prototype", proto, PROTO_CSS))
    spec = '<div class="legend">Spec mode: dashed boxes are annotated with size, radius, type token and colour token. Full values in handoff/handoff.md</div><div class="spec" style="display:contents">' + "".join(
        frame(k, "SPEC · " + S[k][0].split("· ")[1], S[k][1], S[k][2] if len(S[k]) > 2 else None) for k in ("home", "group", "add")) + "</div>"
    open(os.path.join(HERE, "spec.html"), "w").write(page("Hisaab: spec", spec + SPEC_JS, SPEC_CSS))
    print(len(S), "screens")
