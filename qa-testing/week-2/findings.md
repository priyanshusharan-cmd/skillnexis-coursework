# Defects found (all in the Week 3 MERN app, which is the application under test)

Severity: **High** blocks use or exposes data, **Medium** wrong behavior with a workaround, **Low** minor or cosmetic. Every defect below was found by a test in this folder, reproduced, fixed, and then confirmed fixed by re-running the same test. The "before" evidence is kept in `results/*BEFORE-fix*`.

| ID | Defect | Severity | How it was found | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| DEF-1 | **Malformed JSON and oversized request bodies returned `500 Server error`.** The error handler treated every body-parser error as a server crash. A client mistake looked like a server fault, which hides real errors in monitoring and misleads API users. | Medium | `api-practice.js` rows 12 and 13: expected 400 and 413, got 500 | The handler maps `entity.parse.failed` to 400 and `entity.too.large` to 413 (`mern/week-2`, `week-3`, `week-4` servers) | Fixed. API run went from 20 of 22 to 22 of 22 |
| DEF-2 | **`/favicon.ico` returns 404 and desktop Chrome and Edge log a console error** on every visit. Mobile emulation did not request it, so the check failed only on desktop. | Low | Matrix check 11, desktop columns; the 404 was confirmed with `curl` | The page declares an inline icon, so browsers stop asking for `/favicon.ico` | Fixed. Check 11 passes in all four combinations |
| DEF-3 | **Passwords longer than 72 bytes were silently cut short.** bcrypt reads only the first 72 bytes, so logging in with just the first 72 characters of a longer password worked, and everything after was ignored. | Medium (security) | `bva.test.js`: a 94-character password, then login with its first 72 characters | Reject passwords over 72 bytes at registration and login (all three MERN servers), with tests | Fixed. All 12 boundary tests pass |
| DEF-4 | **Controls too small to tap reliably.** The task checkbox was 13 × 13 px and the nav links 18 px tall, against the WCAG 2.2 minimum target size of 24 px. Ten controls were under the 44 px touch guideline. | Low to Medium (accessibility) | Matrix checks 8 and 9, all four combinations | Larger link padding, 24 px checkbox, 44 px minimum height for buttons and inputs | Fixed for the 24 px rule. One **accepted risk** remains: the checkbox is 24 px, which meets WCAG AA but is under the 44 px AAA guideline |

## Observations that are not defects
- Unknown URLs return `200` with the app's HTML (single-page-app fallback). That is normal for this kind of app, but it means a broken link does not produce a 404.
- Ticking a task waits for the server before the box changes, so there is a short delay on a slow connection. Playwright's `check()` fails on this, so the test uses a click and waits for the result. An optimistic update would feel faster, and it is a design choice rather than a bug.

## What was not covered
Firefox and Safari (only Chrome and Edge are installed here, and both use the same Chromium engine, so this is not true cross-engine coverage), real mobile devices, screen readers, and load testing.
