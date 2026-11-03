# Test Plan — Demo Shop v1.0

| | |
| --- | --- |
| Product | Demo Shop: login, product search, cart, checkout, REST API (`../week-3/demo-shop/server.js`) |
| Prepared by | Priyanshu Sharan |
| Standard | Structure follows IEEE 829 / ISO/IEC/IEEE 29119-3 test plan sections |

## 1. Objective
Show that a customer can log in, find products, manage a cart and place an order through the web UI and the API, that bad input is rejected with clear messages, and that the shop holds up under 100 concurrent users.

## 2. Scope
**In scope:** login and logout, session handling, product search, cart add/update/remove, checkout validation and ordering, all 9 REST endpoints, input escaping, load and stress behaviour, basic mobile layout and accessibility checks.

**Out of scope:** payment (the shop has none), email delivery, browsers other than Firefox and Chrome, real mobile devices, penetration testing beyond the input-escaping and auth checks listed here.

## 3. Test items and features

| Feature | Test cases | Automated by |
| --- | --- | --- |
| Login and session | TC-001 – TC-010 | Selenium (S01–S04, V01–V02, C11) |
| Search | TC-011 – TC-016 | Selenium (S05, S06, C14) |
| Cart | TC-017 – TC-026 | Selenium (S07–S09, C12, C13, C15) |
| Checkout | TC-027 – TC-038 | Selenium (S10, V03–V05, C15) |
| REST API | TC-039 – TC-054 | Postman / Newman |
| Performance | TC-055 – TC-056 | JMeter |
| Usability and accessibility | TC-057 – TC-058 | Scripted checks + DEF-1 regression test |

Full list: `test-cases.csv` (58 cases).

## 4. Approach
See `test-strategy.md`. In short: risk-based priorities (P1 to P3). Every P1 case is automated, and the automated suites run in CI on every push.

## 5. Entry and exit criteria
**Entry:** the shop starts and `GET /api/health` returns 200, the test data (two users, five products) is loaded, and CI is green on the previous commit.

**Exit:** all P1 and P2 cases pass, no open P1 or P2 defect remains, load and stress runs have ≤ 1% errors and p95 ≤ 500 ms, and every defect has a regression test.

## 6. Suspension and resumption
Stop testing if login or `GET /api/products` fails, since every other flow depends on them. Resume once a fix is merged and the smoke tests (S01, TC-041) pass again.

## 7. Environment

| Layer | Detail |
| --- | --- |
| App | Node.js 22, in-memory data, `127.0.0.1:4300` |
| UI automation | Selenium 4 + pytest, headless Firefox (Chrome supported) |
| API | Postman collection v2.1, run with Newman 6 |
| Performance | Apache JMeter 5.6.3 on a GitHub Actions `ubuntu-latest` runner (2 vCPU) |
| CI | GitHub Actions, workflow `.github/workflows/qa-tests.yml` |

## 8. Deliverables
Test plan, strategy, 58 test cases, Selenium suite, Postman collection and environment, JMeter plan and analysis, CI pipeline, defect log, QA portfolio (`PORTFOLIO.md`).

## 9. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| In-memory data resets on restart | Tests could pass on stale data | Each suite starts a fresh server |
| Shared stock across tests | Order tests change stock that later tests read | Tests use small quantities; stock-sensitive tests use products nobody orders |
| CI runner speed varies | Flaky performance thresholds | p95 limit set at 500 ms, far above the local averages |
| Only two browser engines | Safari-only bugs missed | Recorded as a limit |

## 10. Schedule

| Week | Activity |
| --- | --- |
| 1 | Manual test cases, bug reports, traceability |
| 2 | Cross-browser matrix, API practice, regression pack |
| 3 | Selenium automation, Postman collection |
| 4 | Performance testing, CI, full test documentation, portfolio |
