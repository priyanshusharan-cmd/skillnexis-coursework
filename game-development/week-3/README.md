# Game Developer — Week 3: Optimization & Device Builds

This extends the Week 2 game (**Gem Run**) into a mobile release candidate. As in Week 2, it is an HTML5 canvas game, not a Unity project.

| Brief item | Result |
| --- | --- |
| Optimization exercise: profile, three bottlenecks, fixes, before/after | Done and measured. About 4 times less per-frame work with all three fixes. See `optimization-report.md`. |
| Device matrix | `device-matrix.md`. Screen sizes were checked in an emulated browser and **one real bug was found and fixed**. Real devices were not available, so those rows say "not tested". |
| Android test build and iOS steps | **No Android build was produced** (no Android SDK or Unity here). An installable PWA is included as a stand-in, plus exact steps for a real Android and iOS build. See `build-notes.md`. |
| Mini project: touch controls, multiple resolutions, release checklist, documented build | Touch controls (multi-touch, cancel-safe), responsive layout and safe-area padding, `release-checklist.md` and `build-notes.md`. |

Run it with `python3 -m http.server` in this folder and open `localhost:8000/?touch` (the touch buttons appear automatically on touch screens). Tests: `node --test core.test.js sw.test.js` (15 tests, all passing).

New files: `bench.js` (benchmark), `manifest.webmanifest`, `sw.js`, `icon-*.png` and `tools/make_icons.py`.
