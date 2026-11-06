# Paid campaigns: Google + Meta (launch, 4 weeks)

Budget ₹20,000 total (₹5,000/week). Objective: **waitlist sign-ups** before launch, then **installs** after launch.
Tracking: GA4 `sign_up` (waitlist form, already implemented on the [site](../site/index.html)) imported into Google Ads. The Meta Pixel `CompleteRegistration` event fires on the same submit. Both run under Consent Mode.

## Google
| Campaign | Type | Budget/week | Targeting | Ads |
|---|---|---:|---|---|
| Search: high intent | Search, Max conversions | ₹2,000 | Exact/phrase: "split expenses app", "splitwise alternative", "split bills with friends upi", "expense sharing app india", "trip expense splitter"; negatives: jobs, excel template, salary, gst | 2 RSAs (headlines below) |
| Search: problem | Search | ₹500 | "how to split hostel expenses", "roommate expense tracker" → the blog guide | 1 RSA |
| App campaign (after launch) | App installs | replaces Search: problem | Android, India, 18–30 | Auto-generated from text, screenshots and the reel |

RSA headlines (all ≤ 30 characters): *Split Expenses With Friends* · *Settle Up With Any UPI App* · *Free, No Daily Limits* · *Running Balance With Friends* · *Hostel, Flat & Trip Splits* · *We Never Hold Your Money* · *Split Equally or by Shares* · *Join the Hisaab Waitlist*
Descriptions (≤ 90 characters): *Add a shared expense in 10 seconds and see one balance with every friend.* · *Settle what you owe with any UPI app. Free, no daily limits, friends don't need the app.*

## Meta (Instagram first)
| Ad set | Audience | Budget/week | Creative |
|---|---|---:|---|
| Students cold | 18–24, India metros + college towns, interests: hostels, college fests, UPI apps, travel with friends | ₹1,200 | Reel "Settle a ₹386 debt in 9 seconds", meme post 07 |
| Lookalike | 1 % lookalike of waitlist sign-ups (after 300+ sign-ups) | ₹800 | Creator reel 13 |
| Retargeting | Site visitors 14 days + IG engagers 30 days, excluding sign-ups | ₹500 | "We never hold your money" (04), FAQ carousel |

Rules:
* Kill any ad with CTR < 0.7 % after 1,500 impressions.
* Scale ad sets with a cost per sign-up under ₹25 by 20 % every 3 days.
* Frequency cap of about 3 a week on retargeting.

## Forecast (assumptions, to replace with real data)
At an assumed ₹6–10 per click and an 18–25 % waitlist conversion on the landing page, ₹20,000 brings roughly **2,000–3,300 clicks → 400–800 sign-ups (₹25–₹50 each)**. If 40 % install at launch and each new user invites 1.5 roommates, that becomes about 400–800 paid-attributed installs feeding the invite loop.
