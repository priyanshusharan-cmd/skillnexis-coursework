# Google Analytics 4: set-up and custom dashboard

## 1. Property and tag
1. Create a GA4 property "Bean & Bloom", a web data stream for `beanandbloom.example`, and copy the **Measurement ID** (`G-…`).
2. Replace `G-XXXXXXXXXX` in [landing/build.py](../landing/build.py) and re-run it. The tag is already on both landing pages, with **Consent Mode v2** (everything denied until the visitor accepts the cookie banner).
3. Verify in **Admin → DebugView**: open the page with `?debug_mode=1`, accept cookies, submit the form, and look for the events below.
4. Link Google Ads (Admin → Product links) and import `generate_lead` as the Ads conversion.

## 2. Events (already implemented and tested)
| Event | When | Parameters | Mark as key event? |
|---|---|---|---|
| `page_view` | automatic | `lp_variant` | — |
| `form_start` | first keystroke in the form | `lp_variant` | no (funnel step) |
| `form_error` | submit with invalid fields | `lp_variant` | no (UX signal) |
| `generate_lead` | valid submit | `lp_variant`, `value=149`, `currency=INR`, UTM fields | **yes** |

Automated check ([tests/landing-test-results.json](../tests/landing-test-results.json)) for both variants:
* submitting empty shows the field errors;
* the three custom events fire in order;
* UTM parameters are carried into the lead;
* axe-core finds 0 accessibility violations.

## 3. Custom definitions
Admin → Custom definitions → create the event-scoped dimension **LP variant** (`lp_variant`).

## 4. Custom dashboard
Build these in a **Looker Studio** report on the GA4 property, or open [dashboard.html](dashboard.html) to see the same layout filled with the *forecast*:

| Tile | Metric / dimension |
|---|---|
| Scorecards | Sessions · `generate_lead` count · Lead rate (leads/sessions) · Cost per lead (Ads cost ÷ leads) |
| Trend | Daily sessions and leads |
| By channel | Session source/medium (google/cpc, meta/paid_social, instagram/organic, email) → sessions, leads, lead rate |
| A/B test | LP variant → sessions, leads, lead rate, with a 95 % CI calculated in the report |
| Funnel | page_view → form_start → generate_lead (a GA4 funnel exploration), with drop-off per step |
| Offline | Redemptions per day, entered weekly from the till into a Google Sheet joined by date |

Data hygiene:
* exclude internal traffic (Admin → Data filters, café Wi-Fi IP);
* set data retention to 14 months;
* annotate the campaign start date.
