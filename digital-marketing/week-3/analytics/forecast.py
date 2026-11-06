"""Pre-launch forecast for the paid campaign (a plan, not results), plus the A/B test sample size.
Every input is an explicit assumption in ASSUMPTIONS; change them and re-run.  python analytics/forecast.py
"""
import math, os
HERE = os.path.dirname(os.path.abspath(__file__))
# assumption ranges: (low, expected, high). Sources: typical published ranges for local food & beverage search/social ads
# in India; to be replaced by the account's own data after week 1.
ASSUMPTIONS = {
 "Google Search": {"budget": 200 * 14, "cpc": (8, 12, 18), "ctr": (0.04, 0.06, 0.09), "lp_cvr": (0.08, 0.12, 0.18)},
 "Google Display": {"budget": 80 * 14, "cpm": (40, 60, 90), "ctr": (0.003, 0.005, 0.008), "lp_cvr": (0.02, 0.04, 0.06)},
 "Meta (FB/IG)": {"budget": 150 * 14, "cpm": (60, 90, 130), "ctr": (0.008, 0.012, 0.018), "lp_cvr": (0.06, 0.10, 0.15)},
}
REDEEM = (0.25, 0.35, 0.50)   # share of leads that come in and redeem the code
MARGIN = 85                   # ₹ gross margin per redeemed combo (₹149 price minus ingredients)

def run(level):
    i = {"low": 0, "expected": 1, "high": 2}[level]; out = {}
    for ch, a in ASSUMPTIONS.items():
        if "cpc" in a:
            clicks = a["budget"] / a["cpc"][i]; impr = clicks / a["ctr"][i]
        else:
            impr = a["budget"] / a["cpm"][i] * 1000; clicks = impr * a["ctr"][i]
        leads = clicks * a["lp_cvr"][i]; red = leads * REDEEM[i]
        out[ch] = dict(spend=a["budget"], impressions=impr, clicks=clicks, leads=leads, redemptions=red, cpl=a["budget"] / leads, cpa=a["budget"] / red)
    return out

def sample_size(p1, lift, alpha_z=1.96, power_z=0.84):
    p2 = p1 * (1 + lift); pbar = (p1 + p2) / 2
    return math.ceil(((alpha_z * math.sqrt(2 * pbar * (1 - pbar)) + power_z * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (p2 - p1) ** 2)

L = ["# Campaign forecast (pre-launch plan: these are projections, not results)", "", "Total budget ₹" + f"{sum(a['budget'] for a in ASSUMPTIONS.values()):,}" + " over 14 days. Ranges come from the assumptions in `forecast.py`.", ""]
for level in ("low", "expected", "high"):
    r = run(level); L += [f"## {level.title()} case", "", "| Channel | Spend | Impressions | Clicks | Leads | Redemptions | Cost/lead | Cost/redemption |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for ch, m in r.items():
        L.append(f"| {ch} | ₹{m['spend']:,} | {m['impressions']:,.0f} | {m['clicks']:,.0f} | {m['leads']:,.0f} | {m['redemptions']:,.0f} | ₹{m['cpl']:,.0f} | ₹{m['cpa']:,.0f} |")
    t = {k: sum(m[k] for m in r.values()) for k in ("spend", "clicks", "leads", "redemptions")}
    L += [f"| **Total** | ₹{t['spend']:,} | | {t['clicks']:,.0f} | {t['leads']:,.0f} | {t['redemptions']:,.0f} | ₹{t['spend'] / t['leads']:,.0f} | ₹{t['spend'] / t['redemptions']:,.0f} |", "",
          f"Gross margin from redemptions ≈ ₹{t['redemptions'] * MARGIN:,.0f} vs spend ₹{t['spend']:,} → first-visit ROAS {t['redemptions'] * MARGIN / t['spend']:.2f}. Below 1 means the campaign only pays back through repeat visits (the Study Streak card), so that is measured too.", ""]
n = sample_size(0.12, 0.25)
L += ["## A/B test: landing page A vs B", f"* Baseline form conversion assumed at 12 %; to detect a 25 % relative lift (12 % → 15 %) at 95 % confidence and 80 % power needs **{n:,} visitors per variant**.",
      f"* Expected paid clicks in 14 days are far below 2 × {n:,}, so the test **cannot reach significance on paid traffic alone**. Plan: run it for the full campaign plus organic Instagram traffic, report the observed difference with its confidence interval, and treat it as directional unless the lift is much larger.",
      "* Split 50/50 with Google Ads ad variations (or a Meta A/B test). Primary metric: `generate_lead` per session. Guardrail: redemption rate per lead (B asks for less, so it may bring lower-intent sign-ups).", "",
      "## Decision rules during the flight",
      "* After day 4: pause any keyword with ≥ 40 clicks and 0 leads, and any Meta ad set with CTR < 0.6 %.",
      "* Move budget weekly towards the channel with the lowest cost per redemption (not per click).",
      "* Display is a remarketing and awareness test: judge it on assisted conversions in GA4, not last-click leads."]
open(os.path.join(HERE, "forecast.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L[:20]))
