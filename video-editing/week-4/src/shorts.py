"""3 Shorts repurposed from the long-form video (one habit each), using the week-3 vertical compositor
(speed ramps, zooms, transitions, word-by-word captions, ducked beat, -14 LUFS).
    python src/shorts.py  -> exports/short-*.mp4, results/shorts-edl.json"""
import json, os, sys
sys.path.insert(0, "../week-3/src"); import vertical as V
from vertical import *
V.GS = "../week-3/exports/greenscreen-raw.mp4"; os.makedirs("results", exist_ok=True)
def tile_logo(im, cx, cy, s=1.0):
    t = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(t); d.rounded_rectangle((0, 0, 299, 299), radius=72, fill=(15, 118, 110))
    d.text((150, 150), "h", font=FONT("InterDisplay-ExtraBold.otf", 150), fill=MINT, anchor="mm"); paste_center(im, t, cx, cy, s)
def end_card(line, cta):
    def draw(im, t, dur):
        tile_logo(im, W / 2, 640, .9 * ease_out(min(1, t / .4)) + .1); d = ImageDraw.Draw(im)
        if t > .25: d.text((W / 2, 900), "Hisaab", font=FONT("InterDisplay-ExtraBold.otf", 130), fill="white", anchor="mm")
        if t > .4: d.text((W / 2, 1040), line, font=TAG, fill=MINT, anchor="mm")
        if t > .7: sticker(im, cta, W / 2, 1390, t - .7)
        d.text((W / 2, 1500), "Concept app designed for a course project", font=SMALL, fill=(159, 201, 194), anchor="mm")
    return draw
def make(name, lines, plan, splits, hook, tail=1.4):
    segs, words, end = voiceover(lines); total = end + tail; bounds = [s[0] for s in segs] + [total]; bounds[0] = 0; durs = []
    for i in range(len(segs)):
        for f in splits.get(i, [1]): durs.append((bounds[i + 1] - bounds[i]) * f)
    assert len(durs) == len(plan)
    for c, d in zip(plan, durs): c["dur"] = d
    edl = render(name, plan, total, captions=words, vo=segs, hook=hook, music_offset=8.0, music_gain=.45)
    return {"total": round(total, 2), "clips": edl}
EDL = {}
EDL["short-a-settle-sunday"] = make("short-a-settle-sunday", [
    "Stop settling money at the end of the month.",
    "Pick one settle day. Ours is Sunday evening.",
    "Open home and tap settle up.",
    "Pick any UPI app and confirm. It goes bank to bank.",
    "Small amounts every week. No awkward month end.",
    "Follow for more hostel money habits."], [
    dict(src="gs"),
    dict(src="rec_settle", a=0.0, b=2.0, trans="whip", zoom=[(0, 1, .5, .5), (1, 1.5, .5, .15)], texts=[(.3, 9, "Every Sunday", 1500)]),
    dict(src="rec_settle", a=2.0, b=4.6, ramp=[(0, 1), (.5, .5), (1, 1)], trans="punch", zoom=[(0, 1.3, .3, .2), (.6, 1.3, .3, .2), (1, 1, .5, .5)]),
    dict(src="rec_settle", a=4.6, b=11.6, ramp=[(0, 1), (.2, 5), (.85, 5), (1, 1)], zoom=[(0, 1, .5, .5), (1, 1.35, .5, .75)]),
    dict(src="rec_settle", a=11.6, b=12.4, ramp=[(0, .5), (1, .5)], trans="glitch", zoom=[(0, 1, .5, .3), (1, 1.3, .5, .27)]),
    dict(card=end_card("Settle small, settle often.", "Follow for more"), trans="flash")], {}, ("Settle every Sunday", 2.4))
EDL["short-b-fair-not-equal"] = make("short-b-fair-not-equal", [
    "Equal splits are quietly annoying your roommates.",
    "If Aarav wasn't at the Maggi run, why is he paying?",
    "Open the split, and untick whoever wasn't there.",
    "A hundred and twenty each, and the total still adds up to three sixty.",
    "Save this for your next trip."], [
    dict(src="gs"),
    dict(src="rec_add", a=15.2, b=16.4, trans="whip", zoom=[(0, 1.4, .5, .3), (1, 1.6, .5, .3)]),
    dict(src="rec_add", a=16.4, b=18.4, ramp=[(0, 1), (.4, .5), (1, 1)], trans="punch", zoom=[(0, 1.2, .5, .3), (1, 1.5, .55, .3)], texts=[(.5, 9, "Untick who skipped", 1500)]),
    dict(src="rec_add", a=18.4, b=25.0, ramp=[(0, 1), (1, 1)], trans="glitch", zoom=[(0, 1.2, .5, .38), (1, 1.6, .4, .4)], texts=[(.3, 9, "₹120 × 3 = ₹360", 1500)]),
    dict(card=end_card("Fair, not equal.", "Save this"), trans="flash")], {}, ("Fair, not equal", 2.4))
EDL["short-c-app-asks"] = make("short-c-app-asks", [
    "Hate asking friends for money? Let the app be the bad guy.",
    "Tap remind, and pick a tone. Friendly, direct, or funny.",
    "It goes from your own WhatsApp, with the exact amount and a pay link.",
    "Nothing is ever sent automatically.",
    "You get to stay the friend. Follow for part two."], [
    dict(src="gs"),
    dict(src="rec_extras", a=1.6, b=6.0, ramp=[(0, 2), (.35, .6), (1, 1)], trans="whip", zoom=[(0, 1, .5, .5), (.4, 1.6, .7, .17), (1, 1.4, .5, .25)]),
    dict(src="rec_extras", a=6.0, b=8.2, ramp=[(0, 1), (1, .8)], trans="punch", zoom=[(0, 1.5, .5, .25), (1, 1.7, .5, .27)], texts=[(.4, 9, "From your WhatsApp", 1500)]),
    dict(src="rec_extras", a=8.0, b=8.3, trans="glitch", zoom=[(0, 1.5, .5, .68), (1, 1.6, .5, .68)]),
    dict(card=end_card("Let the app ask.", "Follow for part 2"), trans="flash")], {}, ("Let the app be the bad guy", 2.6))
json.dump(EDL, open("results/shorts-edl.json", "w"), indent=1); print({k: v["total"] for k, v in EDL.items()})
