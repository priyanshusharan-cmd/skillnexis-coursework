# Email sequences (3 sequences, 9 emails)

All emails use the templates in this folder ([welcome](welcome.html), [promotional](promotional.html), [re-engagement](reengagement.html)).
Merge tags: `{{first_name}}`, `{{code}}`. List built **with consent only**: a sign-up QR at the counter and an Instagram link-in-bio form, both stating "max one email a week".

## Segments
| Segment | Rule | Size goal |
|---|---|---|
| New subscribers | Joined in the last 14 days | — |
| Students | Ticked "I'm a student" on sign-up, or redeemed with a college ID | 70 % of list |
| Regulars | 3+ visits in 30 days (from the Study Streak card) | — |
| Lapsed | No visit or email click in 60 days | — |

## Sequence 1: Welcome (trigger: joins the list)
| # | Send | Subject | Preview text | Goal |
|---|---|---|---|---|
| 1 | Immediately | Welcome! Your first coffee's on us ☕ | Show HELLO-{{code}} at the counter. Valid 14 days. | First visit |
| 2 | Day 3, 5 pm | The 4 best study spots in our café | Window bar, quiet loft, big table, or the garden nook? | Teach what makes us different |
| 3 | Day 10 (only if the code isn't redeemed) | Your free coffee expires in 4 days | One tap to see where we are. | Redeem before it expires |

## Sequence 2: Study Fuel promotion (segment: students + regulars)
| # | Send | Subject | Preview text | Goal |
|---|---|---|---|---|
| 1 | Sun 9 Nov, 6 pm | Exam season? We saved you a corner 📚 | ₹149 coffee + banana bread, weekdays 3–7 pm. | Awareness before launch |
| 2 | Mon 17 Nov, 12 pm (opened #1 but no visit) | Halfway through exams? Here's your 6th coffee free | The Study Streak card: 5 visits, 6th drink on us. | Repeat visits |
| 3 | Fri 21 Nov, 5 pm | Last weekend of Study Fuel | Offer ends Sunday 23 Nov. Good luck from all of us. | Last-chance redemptions |

## Sequence 3: Re-engagement (trigger: 60 days without a visit or click)
| # | Send | Subject | Preview text | Goal |
|---|---|---|---|---|
| 1 | Day 60 | Your table's been missing you, {{first_name}} | A free brownie to say hi. Valid 7 days. | Win back |
| 2 | Day 67 (no visit) | What changed at Bean & Bloom (you'll like #2) | New quiet loft, open till 11 pm, everything under ₹150. | Remind of value |
| 3 | Day 74 (no open) | Should we stop emailing you? | One click to stay, otherwise we'll remove you in 7 days. | **List hygiene**: unengaged contacts are removed, which protects deliverability |

## Rules
* Max one email a week per person across all sequences (promotion pauses the welcome series, never stacks).
* Every email has a plain-text version, an unsubscribe link and the sender's location. This matches the expectations of India's DPDP Act and of Gmail/Yahoo's bulk-sender rules.
* **Metrics:** open rate (directional only, since Apple Mail Privacy inflates it), click rate, redemptions per email (unique codes per sequence), unsubscribe rate below 0.5 %.
* **A/B test:** subject line of promo #1, emoji vs no emoji, 50/50 split on the first 20 % of the list, winner to the rest after 4 hours.
