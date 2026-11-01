# 40-point pre-launch checklist

Ticked only where there is evidence in this repository. **Unticked items are not done**, and the reason is given. Items are grouped by area: gameplay, devices, performance, store assets, privacy, and release testing.

## Gameplay (1 to 8)
- [x] 1. All three levels can be completed (exhaustive physics search in `core.test.js`)
- [x] 2. Spikes, falls, enemies, checkpoints, coins and goal behave as designed (unit tests)
- [x] 3. Save and load works, including corrupt data (unit tests and browser check)
- [x] 4. Pause, resume, mute and volume work and persist (browser check)
- [x] 5. Game-over and retry flow works (browser check)
- [x] 6. Full run from menu to victory works through the real game loop (browser check, Week 2)
- [x] 7. Controls are shown on the main menu (there is no tutorial level)
- [ ] 8. Difficulty tuned with real playtesters (nobody has played it yet)

## Devices (9 to 14)
- [x] 9. Phone sizes from 360 × 640 portrait to 915 × 412 landscape fit without scrolling (emulated)
- [x] 10. Tablet and desktop sizes fit (emulated)
- [x] 11. Touch controls support left, right, jump and pause, with multi-touch and cancel-safe release (simulated events)
- [ ] 12. Tested on a real Android phone (none available)
- [ ] 13. Tested on a real iPhone (none available)
- [ ] 14. Notch and safe-area behavior confirmed on a notched device (code is in place, unverified)

## Performance (15 to 19)
- [x] 15. Profiled, three bottlenecks fixed, before and after measured (`optimization-report.md`)
- [x] 16. Download size is small: about 64 KB of files (about 15 KB of gzipped code), so it loads quickly
- [ ] 17. Frame rate measured on a real low-end phone
- [ ] 18. Memory use measured
- [ ] 19. Battery and thermal behavior checked

## Store assets (20 to 26)
- [x] 20. App icon 512 × 512 (`store/app-icon-512.png`)
- [x] 21. Feature graphic 1024 × 500 (`store/feature-graphic-1024x500.png`)
- [x] 22. Short and full description written (`store-listing.md`)
- [x] 23. Keywords and category chosen (`store-listing.md`)
- [ ] 24. At least two phone screenshots captured from a real device or emulator
- [ ] 25. Promo video
- [ ] 26. Translations (English only)

## Privacy and policy (27 to 32)
- [x] 27. No personal data collected: analytics are on-device only, and unknown parameters are dropped (`analytics.test.js`)
- [x] 28. Players can delete their saved data and stored analytics from the menu
- [x] 29. No device permissions requested
- [x] 30. Age-rating questionnaire answers drafted (`store-listing.md`)
- [x] 31. Google Play Data safety and Apple privacy-label answers drafted (`store-listing.md`)
- [ ] 32. Privacy policy published at a URL (needs a place to host it; a store requires one)

## Release testing (33 to 40)
- [x] 33. All automated tests pass: 23 tests across core logic, service worker and analytics
- [x] 34. Tap targets are at least 44 px (measured in the emulated sizes)
- [x] 35. Version number and update plan: version 1.0.0; shipping an update means bumping `VERSION` in `sw.js` so old caches are replaced
- [x] 36. Analytics events checked as emitted from real actions: all 15 (browser check, zero network requests)
- [ ] 37. Install and first-launch smoke test on a real device (no build exists)
- [ ] 38. Interruption tests: calls, notifications, screen lock, rotation mid-level, low battery
- [ ] 39. Accessibility: screen reader, color-blind check, reduced-motion on a device (reduced-motion CSS exists, unverified)
- [ ] 40. Store review submitted and a release track chosen (Google Play internal testing or TestFlight)
