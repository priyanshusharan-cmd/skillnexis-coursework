# Campaign forecast (pre-launch plan: these are projections, not results)

Total budget ₹6,020 over 14 days. Ranges come from the assumptions in `forecast.py`.

## Low case

| Channel | Spend | Impressions | Clicks | Leads | Redemptions | Cost/lead | Cost/redemption |
|---|---:|---:|---:|---:|---:|---:|---:|
| Google Search | ₹2,800 | 8,750 | 350 | 28 | 7 | ₹100 | ₹400 |
| Google Display | ₹1,120 | 28,000 | 84 | 2 | 0 | ₹667 | ₹2,667 |
| Meta (FB/IG) | ₹2,100 | 35,000 | 280 | 17 | 4 | ₹125 | ₹500 |
| **Total** | ₹6,020 | | 714 | 46 | 12 | ₹130 | ₹518 |

Gross margin from redemptions ≈ ₹988 vs spend ₹6,020 → first-visit ROAS 0.16. Below 1 means the campaign only pays back through repeat visits (the Study Streak card), so that is measured too.

## Expected case

| Channel | Spend | Impressions | Clicks | Leads | Redemptions | Cost/lead | Cost/redemption |
|---|---:|---:|---:|---:|---:|---:|---:|
| Google Search | ₹2,800 | 3,889 | 233 | 28 | 10 | ₹100 | ₹286 |
| Google Display | ₹1,120 | 18,667 | 93 | 4 | 1 | ₹300 | ₹857 |
| Meta (FB/IG) | ₹2,100 | 23,333 | 280 | 28 | 10 | ₹75 | ₹214 |
| **Total** | ₹6,020 | | 607 | 60 | 21 | ₹101 | ₹288 |

Gross margin from redemptions ≈ ₹1,777 vs spend ₹6,020 → first-visit ROAS 0.30. Below 1 means the campaign only pays back through repeat visits (the Study Streak card), so that is measured too.

## High case

| Channel | Spend | Impressions | Clicks | Leads | Redemptions | Cost/lead | Cost/redemption |
|---|---:|---:|---:|---:|---:|---:|---:|
| Google Search | ₹2,800 | 1,728 | 156 | 28 | 14 | ₹100 | ₹200 |
| Google Display | ₹1,120 | 12,444 | 100 | 6 | 3 | ₹188 | ₹375 |
| Meta (FB/IG) | ₹2,100 | 16,154 | 291 | 44 | 22 | ₹48 | ₹96 |
| **Total** | ₹6,020 | | 546 | 78 | 39 | ₹78 | ₹155 |

Gross margin from redemptions ≈ ₹3,298 vs spend ₹6,020 → first-visit ROAS 0.55. Below 1 means the campaign only pays back through repeat visits (the Study Streak card), so that is measured too.

## A/B test: landing page A vs B
* Baseline form conversion assumed at 12 %; to detect a 25 % relative lift (12 % → 15 %) at 95 % confidence and 80 % power needs **2,034 visitors per variant**.
* Expected paid clicks in 14 days are far below 2 × 2,034, so the test **cannot reach significance on paid traffic alone**. Plan: run it for the full campaign plus organic Instagram traffic, report the observed difference with its confidence interval, and treat it as directional unless the lift is much larger.
* Split 50/50 with Google Ads ad variations (or a Meta A/B test). Primary metric: `generate_lead` per session. Guardrail: redemption rate per lead (B asks for less, so it may bring lower-intent sign-ups).

## Decision rules during the flight
* After day 4: pause any keyword with ≥ 40 clicks and 0 leads, and any Meta ad set with CTR < 0.6 %.
* Move budget weekly towards the channel with the lowest cost per redemption (not per click).
* Display is a remarketing and awareness test: judge it on assisted conversions in GA4, not last-click leads.
