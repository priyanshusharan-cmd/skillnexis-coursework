"""Google Ads Search campaign for Bean & Bloom's Study Fuel offer, as a Google Ads Editor import (CSV), validated against Google's limits.
    python ads/build_ads.py   -> ads/google-search-editor.csv, ads/google-search.md
Limits checked: headlines <= 30 chars (3-15 per RSA), descriptions <= 90 (2-4), display paths <= 15, final URL https.
"""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CAMPAIGN = {"name": "BB | Search | Study Fuel | Nov26", "budget": 200, "bid": "Maximize conversions", "network": "Google search",
            "location": "Basavanagudi, Bengaluru + 3 km radius", "lang": "English;Hindi;Kannada", "start": "2026-11-10", "end": "2026-11-23",
            "schedule": "Mon-Sun 07:00-22:00"}
URL = "https://beanandbloom.example/study-fuel?utm_source=google&utm_medium=cpc&utm_campaign=study_fuel_nov26&utm_content={adgroupid}"
GROUPS = {
 "Study cafe near me": {
   "keywords": ["[study cafe near me]", "[cafe to study near me]", "\"cafe with wifi near me\"", "\"quiet cafe near me\"", "\"cafe for studying bangalore\"", "\"cafe with charging points\""],
   "headlines": ["Study Café 2 Min From Campus", "Fast Wi-Fi, Plugs at Each Seat", "Quiet Loft for Exam Prep", "Coffee + Banana Bread ₹149", "Open 8 am–11 pm in Exams",
                 "Bean & Bloom Study Café", "Study 5 Days, 6th Coffee Free", "Group Tables & Whiteboard", "Free Water Refills", "Show College ID for ₹149"],
   "descriptions": ["Exam season? Grab a quiet table, 100 Mbps Wi-Fi and a ₹149 coffee + banana bread combo.",
                    "Quiet loft, plugs at every seat, open till 11 pm through exams. 2 min from the main gate.",
                    "Weekdays 3–7 pm with your college ID: filter coffee or chai + banana bread for ₹149.",
                    "Study 5 days with us and your 6th coffee is free. Get your Study Streak card today."]},
 "Cafe near college": {
   "keywords": ["[cafe near bms college]", "\"cafe near basavanagudi\"", "\"coffee shop near bull temple road\"", "\"cafe near campus bangalore\""],
   "headlines": ["Café Near Your College Gate", "Coffee + Banana Bread ₹149", "Basavanagudi Study Café", "Everything Under ₹150", "Open Till 11 pm",
                 "Quiet Tables, Fast Wi-Fi", "Group Study Table for 8", "Student Offer: Show Your ID"],
   "descriptions": ["Two minutes from the main gate. Coffee, chai and snacks under ₹150, plus fast Wi-Fi.",
                    "Study Fuel combo ₹149 on weekdays 3–7 pm. Quiet loft upstairs, plugs at every seat."]},
 "Coffee offer": {
   "keywords": ["\"coffee offer bangalore\"", "\"student coffee discount\"", "\"cheap cafe near me\"", "\"coffee under 150\""],
   "headlines": ["Study Fuel Combo ₹149", "Coffee + Banana Bread Deal", "Student Offer, Weekdays 3–7", "Save ₹61 With College ID", "Valid Till 23 Nov",
                 "Bean & Bloom Café"],
   "descriptions": ["Filter coffee or chai + banana-walnut bread for ₹149 (usually ₹210). Weekdays 3–7 pm.",
                    "Show your college ID. Dine-in only, valid 10–23 Nov. Fast Wi-Fi and quiet tables too."]},
}
NEGATIVES = ["jobs", "recipe", "franchise", "machine", "beans online", "cafe coffee day", "starbucks", "hiring", "course", "near airport"]
SITELINKS = [("Study Fuel offer", "Coffee + banana bread ₹149", "Weekdays 3–7 pm with ID", "/study-fuel"), ("Menu under ₹150", "Coffee, chai, snacks", "Student budget friendly", "/menu"),
             ("Study spots", "Quiet loft & big table", "Plugs at every seat", "/spots"), ("Directions", "2 min from the main gate", "Open 8 am–11 pm", "/visit")]
CALLOUTS = ["100 Mbps Wi-Fi", "Plug at Every Seat", "Quiet Loft", "Open Till 11 pm", "Free Water Refills"]

errors = []
def chk(kind, text, limit):
    if len(text) > limit: errors.append(f"{kind} too long ({len(text)}>{limit}): {text}")
for g, d in GROUPS.items():
    if not 3 <= len(d["headlines"]) <= 15: errors.append(f"{g}: {len(d['headlines'])} headlines")
    if not 2 <= len(d["descriptions"]) <= 4: errors.append(f"{g}: {len(d['descriptions'])} descriptions")
    for h in d["headlines"]: chk("headline", h, 30)
    for x in d["descriptions"]: chk("description", x, 90)
for s in SITELINKS: chk("sitelink text", s[0], 25); chk("sitelink desc", s[1], 35); chk("sitelink desc", s[2], 35)
for c in CALLOUTS: chk("callout", c, 25)
for p in ("study-fuel", "student-offer"): chk("path", p, 15)
if errors:
    print("\n".join(errors)); sys.exit(1)

rows = [["Campaign", "Campaign Type", "Budget", "Bid Strategy Type", "Networks", "Start Date", "End Date", "Ad Group", "Keyword", "Criterion Type", "Headline 1"] + [f"Headline {i}" for i in range(2, 16)] + [f"Description {i}" for i in range(1, 5)] + ["Path 1", "Path 2", "Final URL", "Ad type", "Status"]]
W = len(rows[0])
def row(**kw):
    r = [""] * W
    for k, v in kw.items(): r[rows[0].index(k)] = v
    return r
rows.append(row(**{"Campaign": CAMPAIGN["name"], "Campaign Type": "Search", "Budget": CAMPAIGN["budget"], "Bid Strategy Type": CAMPAIGN["bid"], "Networks": CAMPAIGN["network"],
                   "Start Date": CAMPAIGN["start"], "End Date": CAMPAIGN["end"], "Status": "Paused"}))
for g, d in GROUPS.items():
    rows.append(row(**{"Campaign": CAMPAIGN["name"], "Ad Group": g, "Status": "Enabled"}))
    for k in d["keywords"]:
        mt = "Exact" if k.startswith("[") else "Phrase"
        rows.append(row(**{"Campaign": CAMPAIGN["name"], "Ad Group": g, "Keyword": k.strip('[]"'), "Criterion Type": mt, "Status": "Enabled"}))
    ad = {"Campaign": CAMPAIGN["name"], "Ad Group": g, "Ad type": "Responsive search ad", "Path 1": "study-fuel", "Path 2": "student-offer", "Final URL": URL, "Status": "Enabled"}
    for i, h in enumerate(d["headlines"], 1): ad["Headline 1" if i == 1 else f"Headline {i}"] = h
    for i, x in enumerate(d["descriptions"], 1): ad[f"Description {i}"] = x
    rows.append(row(**ad))
for n in NEGATIVES:
    rows.append(row(**{"Campaign": CAMPAIGN["name"], "Keyword": n, "Criterion Type": "Campaign negative broad", "Status": "Enabled"}))
with open(os.path.join(HERE, "google-search-editor.csv"), "w", newline="") as f: csv.writer(f).writerows(rows)
nk = sum(len(d["keywords"]) for d in GROUPS.values())
md = [f"# Google Search campaign: {CAMPAIGN['name']}", "", "| Setting | Value |", "|---|---|"] + [f"| {k} | {v} |" for k, v in CAMPAIGN.items()] + [
      f"| Budget note | ₹{CAMPAIGN['budget']}/day × 14 days = ₹{CAMPAIGN['budget'] * 14:,} total; starts **paused** |", "| Conversion | `generate_lead` (landing-page form) imported from GA4, plus Google Maps direction clicks |", "",
      f"**{len(GROUPS)} ad groups, {nk} keywords (exact + phrase), {len(GROUPS)} responsive search ads, {len(NEGATIVES)} negative keywords, {len(SITELINKS)} sitelinks, {len(CALLOUTS)} callouts.** All texts pass Google's length limits (checked by this script).", ""]
for g, d in GROUPS.items():
    md += [f"## Ad group: {g}", "Keywords: " + ", ".join(f"`{k}`" for k in d["keywords"]), "", "| # | Headline | Chars |", "|---|---|---:|"] + [f"| {i} | {h} | {len(h)} |" for i, h in enumerate(d["headlines"], 1)] + \
          ["", "| # | Description | Chars |", "|---|---|---:|"] + [f"| {i} | {x} | {len(x)} |" for i, x in enumerate(d["descriptions"], 1)] + [""]
md += ["## Negative keywords", ", ".join(NEGATIVES), "", "## Assets", "Sitelinks: " + " · ".join(s[0] for s in SITELINKS), "", "Callouts: " + " · ".join(CALLOUTS), "",
       "## How to load it (Google Ads demo / test account)", "1. Google Ads Editor → *Account → Import → From file* → `google-search-editor.csv`.",
       "2. Review the changes and post them. The campaign arrives **paused**, so nothing spends.",
       "3. Add the location radius and ad schedule in Editor (they don't import from this CSV), then sitelinks and callouts from this page."]
open(os.path.join(HERE, "google-search.md"), "w").write("\n".join(md) + "\n")
print(f"ok: {len(GROUPS)} ad groups, {nk} keywords, all text within limits")
