# Test Strategy — Demo Shop

## Risk-based priorities

| Priority | Meaning | Examples | Rule |
| --- | --- | --- | --- |
| P1 | A customer cannot buy, or data or access is exposed | Login, auth on the cart API, place order, input escaping | Automated, runs on every push, blocks release |
| P2 | Wrong result with a workaround, or bad input accepted | Quantity limits, field validation, 404 handling | Automated where practical, must pass before release |
| P3 | Polish, edge input, usability | Case-insensitive search, decimal quantity, tap targets | Scripted check or manual, fixed when cheap |

## Test levels and types

| Level | Tool | What it proves |
| --- | --- | --- |
| API (service) | Postman / Newman | Status codes, JSON shape, business rules (stock, quantity 1–10), auth. These are fast, so most rule checks live here. |
| UI end-to-end | Selenium + pytest, Page Object Model | Real user journeys work in a browser, and messages are visible. |
| Non-functional: performance | JMeter | Response time and error rate at 25 users (load) and 100 users (stress). |
| Non-functional: security | Selenium + Postman | Search output is escaped (XSS), protected pages and APIs need a session, the cookie is HttpOnly and SameSite. |
| Non-functional: usability and accessibility | Scripted DOM checks | No horizontal scroll, every input has a label, tap targets are at least 24 px. |

## Test design techniques
- **Equivalence partitioning:** quantity {< 1, 1–10, > 10, non-integer}, email {valid, missing @, missing domain, missing TLD, contains space}.
- **Boundary value analysis:** quantity 0, 1, 10 and 11; PIN code with 5, 6 and 7 digits; stock limit (Desk Lamp stock 5, so try 6).
- **State transitions:** logged out → logged in → cart with items → order placed → empty cart; logout returns to logged out.
- **Error guessing:** malformed JSON, unknown ids, HTML in search, empty cart checkout.

## Automation approach
- **Page Object Model** (`week-3/selenium/pages.py`): tests read as user steps, and locators live in one place. It uses IDs first, then CSS, and XPath only where the text of a row identifies the element.
- **Independence:** each test gets a fresh browser, and each suite run starts its own shop on a free port.
- **Evidence:** JUnit XML from pytest and Newman, a screenshot saved for every failing UI test, and JMeter `.jtl` files with HTML dashboards.
- **CI gate:** `.github/workflows/qa-tests.yml` runs functional tests first and performance only if they pass. Performance fails the build above 1% errors or a p95 over 500 ms.

## Defect management
Each defect gets a report: ID, steps, expected vs actual, severity, evidence. It is fixed in code, then a regression test is added before the defect is closed. See `PORTFOLIO.md#defects`.

## Metrics tracked
Pass rate per suite, defects found per level, automation coverage (automated cases ÷ total cases), p95 and error rate per load level.
