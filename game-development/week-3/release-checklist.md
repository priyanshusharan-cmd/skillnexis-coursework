# Release candidate checklist

Items are ticked only where there is evidence in this repository. Unticked items are not done.

## Gameplay
- [x] All three levels can be completed (exhaustive physics search, `core.test.js`)
- [x] Hazards, checkpoints, enemies, coins and goal behave as designed (unit tests)
- [x] Save and load works, including corrupt data (unit tests, browser check)
- [ ] Difficulty tuned by real players

## Mobile
- [x] Touch controls for left, right, jump and pause, with multi-touch
- [x] Layout fits phone, tablet and desktop sizes (emulated), including a fix for short landscape screens
- [x] Rotate-to-landscape message in portrait
- [ ] Tested on real Android and iOS devices
- [ ] Safe-area behavior confirmed on a notched device

## Performance
- [x] Profiled, three bottlenecks addressed, before and after measured (`optimization-report.md`)
- [ ] Frame rate measured on a real low-end phone
- [ ] Memory and battery checked

## Build and release
- [x] Web app manifest, icons and service worker written
- [ ] Service worker verified in a browser
- [ ] Android APK or bundle built
- [ ] iOS build run in Xcode
- [ ] Store listing, privacy policy and age rating prepared (Week 4)
