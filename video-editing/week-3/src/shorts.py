"""The Reel (30 s, beat-synced montage) and the Shorts package (3 vertical videos with captions, music, zooms, speed ramps).
    python src/shorts.py [reel|a|b|c ...]   -> exports/reel-30s.mp4, short-1-split-in-10s.mp4, short-2-money-rules.mp4, short-3-group-bank.mp4, results/edl.json"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vertical import *
WANT = sys.argv[1:] or ["reel", "a", "b", "c"]
EDL = json.load(open("results/edl.json")) if os.path.exists("results/edl.json") else {}

def tile_logo(im, cx, cy, s=1.0):
    t = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(t); d.rounded_rectangle((0, 0, 299, 299), radius=72, fill=(15, 118, 110))
    d.text((150, 150), "h", font=FONT("InterDisplay-ExtraBold.otf", 150), fill=MINT, anchor="mm"); paste_center(im, t, cx, cy, s)

def end_card(lines, cta):
    def draw(im, t, dur):
        tile_logo(im, W / 2, 640, .9 * ease_out(min(1, t / .4)) + .1)
        d = ImageDraw.Draw(im)
        if t > .25: d.text((W / 2, 900), "Hisaab", font=FONT("InterDisplay-ExtraBold.otf", 130), fill="white", anchor="mm")
        for k, ln in enumerate(lines):
            if t > .4 + .15 * k: d.text((W / 2, 1040 + 70 * k), ln, font=TAG, fill=MINT, anchor="mm")
        if t > .7: sticker(im, cta, W / 2, 1390, t - .7)
        d.text((W / 2, 1500), "Concept app designed for a course project", font=SMALL, fill=(159, 201, 194), anchor="mm")
    return draw

def segs_to_durs(vo_segs, total, splits):
    """Clip durations that follow the voice-over: line i owns [start_i, start_{i+1}); `splits` divides a line's span."""
    bounds = [s[0] for s in vo_segs] + [total]; bounds[0] = 0; out = []
    for i in range(len(vo_segs)):
        span = bounds[i + 1] - bounds[i]
        for frac in splits.get(i, [1]): out.append(span * frac)
    return out

def make_short(name, lines, plan, splits, hook, tail=1.2, **kw):
    segs, words, end = voiceover(lines, **kw); total = end + tail; durs = segs_to_durs(segs, total, splits)
    assert len(durs) == len(plan), (len(durs), len(plan))
    for c, d in zip(plan, durs): c["dur"] = d
    edl = render(name, plan, total, captions=words, vo=segs, hook=hook, music_offset=8.0, music_gain=.45)
    EDL[name] = {"total": round(total, 2), "clips": edl, "captions": [[round(a, 2), round(b, 2), w] for a, b, w in words]}; print(name, round(total, 1), "s")

if "a" in WANT:
    make_short("short-1-split-in-10s", [
        "Your roommate paid three sixty for Maggi. Here's how to split it in ten seconds.",
        "Open the room, and tap plus.",
        "Enter three sixty, then choose split equally.",
        "Untick anyone who wasn't there.",
        "Save. Everyone instantly sees what they owe.",
        "Follow for more hostel money hacks."], [
        dict(src="rec_add", a=0.0, b=2.7, zoom=[(0, 1.0, .5, .5), (1, 1.18, .5, .2)]),
        dict(src="rec_add", a=2.6, b=5.3, ramp=[(0, 2.5), (.55, 2.5), (.75, .5), (1, .8)], trans="whip", zoom=[(0, 1, .5, .5), (.6, 1.25, .8, .85), (1, 1.0, .5, .5)]),
        dict(src="rec_add", a=5.2, b=15.6, ramp=[(0, 1), (.15, 6), (.85, 6), (1, 1)], trans="punch", zoom=[(0, 1.6, .5, .17), (.5, 1.6, .5, .17), (.7, 1.5, .7, .27), (1, 1.5, .7, .27)]),
        dict(src="rec_add", a=15.8, b=18.2, ramp=[(0, 1), (.4, .6), (1, 1)], trans="glitch", zoom=[(0, 1.1, .5, .3), (1, 1.45, .5, .3)]),
        dict(src="rec_add", a=18.2, b=28.3, ramp=[(0, 3), (.8, 7), (1, 2)], trans="whip"),
        dict(src="rec_add", a=28.3, b=29.3, ramp=[(0, .4), (1, .9)], trans="punch", zoom=[(0, 1.3, .5, .2), (1, 1.15, .5, .2)], texts=[(.2, 9, "Saved in 10 s", 1500)]),
        dict(card=end_card(["Split it. Settle it."], "Follow for more"), trans="flash")],
        {4: [.6, .4]}, ("Split ₹360 in 10 seconds", 2.4))

if "b" in WANT:
    def rules_card(im, t, dur):
        d = ImageDraw.Draw(im); s = ease_out(min(1, t / .35))
        paste_center(im, text_img(["3"], FONT("InterDisplay-ExtraBold.otf", 520), fill=YELLOW, stroke=0), W / 2, 620, .4 + .6 * s)
        if t > .3: paste_center(im, text_img(["MONEY", "RULES"], HOOK, stroke=0), W / 2, 900, 1, min(1, (t - .3) / .2))
        if t > .55: d.text((W / 2, 1000), "every hostel room needs", font=TAG, fill=MINT, anchor="mm")
    make_short("short-2-money-rules", [
        "Three money rules every hostel room needs.",
        "Rule one. Log it the moment you pay.",
        "Rule two. Settle every Sunday, not at month end.",
        "Rule three. Let the app send the reminder, not you.",
        "Bonus. Check where the money actually went.",
        "Save this, and send it to your roommates."], [
        dict(card=rules_card),
        dict(src="rec_add", a=2.6, b=5.6, ramp=[(0, 1.5), (.5, 1.5), (.7, .5), (1, 1)], trans="whip", texts=[(0, 9, "RULE 1", 330)], zoom=[(0, 1, .5, .5), (.7, 1.0, .5, .5), (1, 1.5, .5, .2)]),
        dict(src="rec_settle", a=2.0, b=11.6, ramp=[(0, 1), (.2, 6), (.8, 6), (1, 1)], trans="punch", texts=[(0, 9, "RULE 2", 330)], zoom=[(0, 1, .5, .5), (.4, 1.4, .5, .22), (1, 1.4, .5, .22)]),
        dict(src="rec_settle", a=11.6, b=12.3, ramp=[(0, .5), (1, .5)], zoom=[(0, 1.0, .5, .3), (1, 1.3, .5, .25)], texts=[(.1, 9, "Every Sunday", 1500)]),
        dict(src="rec_extras", a=2.6, b=8.2, ramp=[(0, 1), (.3, 3), (1, 3)], trans="glitch", texts=[(0, 9, "RULE 3", 330)], zoom=[(0, 1, .5, .5), (.5, 1.45, .5, .2), (1, 1.45, .5, .2)]),
        dict(src="rec_extras", a=8.4, b=12.0, ramp=[(0, 1), (1, 1)], trans="whip", texts=[(0, 9, "BONUS", 330, 0)], zoom=[(0, 1.0, .5, .5), (1, 1.35, .5, .3)]),
        dict(card=end_card(["Send it to your roommates."], "Save this"), trans="punch")],
        {2: [.65, .35]}, None)

if "c" in WANT:
    make_short("short-3-group-bank", [
        "If you always pay first, you're basically the group's bank.",
        "Hisaab shows you one number. Your friends owe you eight fifty four.",
        "Tap remind, pick a friendly tone, and send it on WhatsApp.",
        "No awkward texts. Just settled.",
        "Follow for part two."], [
        dict(src="gs"),
        dict(src="rec_home", a=0.9, b=3.4, ramp=[(0, 1), (1, .6)], trans="whip", zoom=[(0, 1.0, .5, .5), (.5, 1.7, .5, .18), (1, 1.75, .5, .18)], texts=[(1.2, 9, "+ ₹854", 1500)]),
        dict(src="rec_extras", a=1.6, b=8.2, ramp=[(0, 2), (.3, 2), (.45, .7), (.7, 3), (1, 3)], trans="punch", zoom=[(0, 1, .5, .5), (.3, 1.6, .7, .2), (.5, 1.4, .5, .3), (1, 1.4, .5, .3)]),
        dict(src="rec_settle", a=10.8, b=13.5, ramp=[(0, 1), (.4, .4), (1, .6)], trans="glitch", zoom=[(0, 1.0, .5, .5), (1, 1.3, .5, .28)]),
        dict(src="gs", trans="flash", texts=[(0, 9, "Part 2 soon", 1500)])],
        {}, ("Stop being the group's bank", 2.6))

if "reel" in WANT:
    def pov(im, t, dur):
        msg = "POV: you're the friend who always pays first"; k = int(len(msg) * min(1, t / 2.2)); lines = wrap_lines(msg[:k] + ("|" if int(t * 4) % 2 else ""), HOOK, 860)
        for i, ln in enumerate(l for l in lines if l): paste_center(im, text_img(ln, HOOK, stroke=0), W / 2, 820 + 120 * i)
    R = [dict(src="exports/logo-reveal.mp4", a=0, b=4.6, dur=4.0, zoom=[(0, 1.7, .5, .5), (1, 1.7, .5, .5)]),
         dict(card=pov, dur=4.0, trans="glitch"),
         dict(src="rec_home", a=1.0, b=3.0, dur=2.0, trans="whip", zoom=[(0, 1.2, .5, .2), (1, 1.7, .5, .18)], texts=[(.2, 9, "₹854 owed to you", 1500)]),
         dict(src="rec_add", a=2.6, b=5.4, dur=2.0, trans="whip", ramp=[(0, 2), (.6, .6), (1, 1)], texts=[(.1, 9, "Add it in 10 s", 1500)]),
         dict(src="rec_add", a=15.8, b=18.0, dur=2.0, trans="glitch", zoom=[(0, 1.2, .5, .3), (1, 1.5, .5, .3)], texts=[(.1, 9, "Untick who skipped", 1500)]),
         dict(src="rec_add", a=28.0, b=30.0, dur=2.0, trans="punch", ramp=[(0, 1.5), (1, .5)], texts=[(.1, 9, "Saved", 1500)]),
         dict(src="rec_settle", a=3.4, b=6.0, dur=2.0, trans="whip", zoom=[(0, 1.0, .5, .5), (1, 1.4, .5, .25)], texts=[(.1, 9, "Pay ₹266 by UPI", 1500)]),
         dict(src="rec_settle", a=10.6, b=12.8, dur=2.0, trans="punch", ramp=[(0, 1.5), (.5, .35), (1, .5)], zoom=[(0, 1.0, .5, .5), (1, 1.3, .5, .28)], texts=[(.4, 9, "Settled", 1500)]),
         dict(src="rec_extras", a=3.0, b=6.0, dur=2.0, trans="whip", zoom=[(0, 1.3, .5, .25), (1, 1.5, .5, .22)], texts=[(.1, 9, "Friendly reminder", 1500)]),
         dict(src="rec_extras", a=8.6, b=11.0, dur=2.0, trans="glitch", zoom=[(0, 1.2, .5, .3), (1, 1.35, .5, .3)], texts=[(.1, 9, "Where it all went", 1500)]),
         dict(src="gs", dur=2.0, trans="flash", texts=[(.1, 9, "Split it. Settle it.", 1500)]),
         dict(card=end_card(["Split it. Settle it."], "Save this for your roommates"), dur=4.0, trans="punch")]
    edl = render("reel-30s", R, 30.0, music_offset=0.0, music_gain=1.0)
    beats = json.load(open("build/beats.json")); cuts = [c["out_start"] for c in edl][1:]
    EDL["reel-30s"] = {"total": 30.0, "clips": edl, "cuts_on_beat": all(abs(c / beats["beat"] - round(c / beats["beat"])) < 1e-6 for c in cuts), "drop_at": beats["drop"]}; print("reel ok")
json.dump(EDL, open("results/edl.json", "w"), indent=1)
