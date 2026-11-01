# Game Developer — Week 4: Publishing, Monetization & Capstone

**Gem Run** is the finished capstone prototype: the Week 2 game plus the Week 3 mobile work, with an analytics layer and the publishing documents the final week asks for. It is an HTML5 canvas game (not Unity) and it is **not published anywhere**.

## Brief → what is here
| Requirement | Where |
| --- | --- |
| **Release checklist (40 points)** | `release-checklist.md`. 25 of 40 are ticked, each with its evidence. The 15 unticked items are things that could not be done here, such as real-device testing, a published privacy policy, real screenshots and a store build, and each says why. |
| **Analytics exercise (15 events and the decision each supports)** | `analytics-plan.md`. All 15 are implemented in `analytics.js` and emitted from the game, with tests. |
| **Monetization plan** | `monetization-plan.md`. A plan only; the game has no ads or purchases. |
| **Capstone: menus, gameplay, touch input** | The game itself (`index.html` and the scripts), from Weeks 2 and 3. |
| **Capstone: optimization evidence** | `optimization-report.md`, with the device matrix in `device-matrix.md`. |
| **Capstone: store listing draft** | `store-listing.md`, plus `store/app-icon-512.png` and `store/feature-graphic-1024x500.png`. |
| **Capstone: release checklist** | `release-checklist.md`. |

## Run and test
Run `python3 -m http.server` in this folder and open `localhost:8000` (add `?touch` to see the touch controls on a desktop). Tests: `node --test core.test.js sw.test.js analytics.test.js` runs 23 tests, all passing.

## Verified, and not
- **Verified:** the physics and all three levels (an exhaustive route search), saving, the 15 analytics events from real actions with zero network requests, touch input with simulated events, layouts at seven screen sizes (one bug found and fixed), and the speed measurements.
- **Not done:** an Android or iOS build, any test on a real device, real screenshots, a privacy policy URL, and any store submission. The service worker's logic is tested but the browser I had would not register one, so offline play is unconfirmed. Audio was never listened to.
- **Honest scope:** the course is Unity-based. Unity was not available, so this is a web game. Treat the store documents as a draft for a native release, not as proof that one exists.

## Privacy
Analytics are kept on the device only and contain no personal data. There is a "Delete my saved data" button in the main menu.
