# Meta (Facebook + Instagram) campaign: BB | Meta | Study Fuel | Nov26

| Setting | Value |
|---|---|
| Objective | **Leads** (on-site conversion: the landing-page `generate_lead` event via the Meta Pixel / Conversions API), optimised for leads |
| Budget | ₹150/day campaign budget (Advantage campaign budget), 10–23 Nov, starts **paused** |
| Placements | Instagram feed, stories, reels, Facebook feed (Advantage+ placements off: students are on Instagram) |
| Location | 3 km around the café; people *living in or recently in* the area |
| Age | 18–26 |
| Creatives | [feed 1080×1080](../exports/creatives/meta-feed-1080x1080.png), [story 1080×1920](../exports/creatives/meta-story-1080x1920.png), plus the reel covers and the carousel from week 2 |

## Ad sets (audiences)
| Ad set | Audience | Why | Share of budget |
|---|---|---|---|
| 1 · Interest | 18–26, 3 km, interests: university students, coffee, studying, competitive exams (GATE, CAT) | Cold reach near campus | 40 % |
| 2 · **Custom audience: engagers** | People who engaged with @beanandbloom.blr on Instagram in the last 60 days + visited the website (pixel) in 30 days | Warm: already know the café | 30 % |
| 3 · **Custom audience: customer list** | Hashed emails of subscribers who joined at the counter with consent (from week 2's list), excluding redeemed leads | Win back and remind | 10 % |
| 4 · Lookalike | 1 % lookalike (India) of subscribers, then narrowed to 3 km | Find people like current customers | 20 % |
Exclusions: anyone who already submitted the form (lead event, 30 days), and staff.

## Ads (3 per ad set, rotated)
| Ad | Primary text (≤ 125 chars shown) | Headline (≤ 40) | CTA |
|---|---|---|---|
| Offer | Exam season? Coffee or chai + banana bread for ₹149, weekdays 3–7 pm. Show your college ID. | Study Fuel combo ₹149 | Get offer |
| Problem | Can't focus in the hostel? Quiet loft, 100 Mbps Wi-Fi, a plug at every seat, 2 min from campus. | Your exam-season study spot | Learn more |
| Social | Study 5 days with us, the 6th coffee is on us. Ask for the Study Streak card. | Study Streak: 6th coffee free | Get offer |

## Tracking
* Destination: `landing/a.html` or `b.html?utm_source=meta&utm_medium=paid_social&utm_campaign=study_fuel_nov26&utm_content={{ad.name}}`
* Meta Pixel `Lead` event fired together with GA4's `generate_lead`, deduplicated with an event ID when the Conversions API is added. Both respect cookie consent.
* Special category: none (food and beverage). Ads avoid targeting by sensitive attributes.
