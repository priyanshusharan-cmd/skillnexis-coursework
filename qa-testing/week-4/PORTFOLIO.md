# QA Portfolio — Priyanshu Sharan

Software QA Tester (Bug Hunter) internship, weeks 1–4. Everything below is in this repository and can be re-run.

## At a glance

| Metric | Value |
| --- | --- |
| Test cases written | 20 (week 1) + 60 (week 4) |
| Automated UI tests (Selenium / Playwright) | 27 Selenium + 11 Playwright checks × 4 browser/viewport combinations |
| API requests under test (Postman / scripts) | 15 (week 3 collection) + 22 (week 2 practice) |
| Peak load tested | 100 concurrent users, 16,931 requests, 0% errors |
| Defects found and fixed | **6** (4 in week 2, 2 in week 4), each with a regression test |
| CI | GitHub Actions on every push: functional suites, then performance |

## Skills by week

| Week | Topic | Artefacts | Highlights |
| --- | --- | --- | --- |
| 1 | Manual testing fundamentals | `../week-1/test-cases.csv`, `traceability-matrix.csv`, `bug-report-template.md` | Positive and negative login cases, checkout scenarios, requirement-to-case traceability |
| 2 | Web and cross-platform testing | `../week-2/` | Chrome + Edge × desktop + mobile matrix, API practice with expected vs actual, partitions and boundaries, P1–P3 regression pack. 4 real defects in the MERN app (500 on bad JSON, favicon 404, bcrypt 72-byte truncation, small tap targets) |
| 3 | Automation and API testing | `../week-3/` | Selenium Page Object Model with ID, CSS and XPath locators; 10 end-to-end scenarios; 5 validation scripts; Postman collection with chained environment variables (token, productId, orderId); planted-bug check proved the tests catch regressions |
| 4 | Performance and CI/CD | `./` | JMeter plan with token extraction and assertions, load (25) and stress (100) runs, percentile analysis script, GitHub Actions pipeline with performance gates, full test documentation, 2 defects found and fixed |

## Defects

| ID | Week | App | Severity | Summary | Status |
| --- | --- | --- | --- | --- | --- |
| W2 DEF-1 | 2 | MERN tasks | Medium | Bad JSON or oversized body returned 500 instead of 400/413 | Fixed + tested |
| W2 DEF-2 | 2 | MERN tasks | Low | `/favicon.ico` 404 logs a console error on every visit | Fixed + tested |
| W2 DEF-3 | 2 | MERN tasks | Medium (security) | Passwords over 72 bytes silently truncated by bcrypt | Fixed + tested |
| W2 DEF-4 | 2 | MERN tasks | Low–Medium | Checkbox and nav links under 24 px target size | Fixed (one AAA accepted risk) |
| W4 DEF-1 | 4 | Demo Shop | Minor | Nav and Checkout links 20 px tall | Fixed + `test_regression_def1.py` |
| W4 DEF-2 | 4 | Demo Shop | Major | Sessions never expired; heap grew 17 MB per 50k logins with no bound | Fixed + `regression/sessions.test.js` |

Bug report format: `../week-1/bug-report-template.md`. Full write-ups: `../week-2/findings.md` and `README.md#defects-found-and-fixed-this-week`.

## How I test (short version)
1. **Risk first.** P1 means money, access or data; these are automated and run on every push.
2. **Rules live at the API layer**, because those tests are fast and exact. User journeys live in the browser, and there are fewer of them.
3. **Every bug gets a failing test before the fix**, and that test stays in the suite.
4. **Test the tests.** Plant a defect and check that the suite goes red.
5. **Report what was not tested** as carefully as what was.

## Tools
Selenium 4, pytest, Playwright, Postman / Newman, Apache JMeter, GitHub Actions, Node test runner, Python, Git.
