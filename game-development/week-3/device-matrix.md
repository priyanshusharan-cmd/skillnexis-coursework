# Device test matrix

**Status key:** **Pass** = tested and worked. **Emulated** = checked at that screen size in a desktop browser, not on a real device. **Not tested** = no evidence, so do not read it as a pass. No real phone or tablet was available, so nothing below was tested on physical hardware.

## Screen sizes and orientation
| Device / size | Orientation | Result | Notes |
| --- | --- | --- | --- |
| 360 × 640 (small Android phone) | Portrait | Emulated: pass | Canvas fits and a "rotate your device" message is shown. All touch targets are at least 44 px (64 px for the direction buttons, 84 px for jump). |
| 568 × 320 (iPhone SE, 1st gen) | Landscape | Emulated: pass | Canvas 538 × 296, no scrolling. |
| 640 × 360 | Landscape | Emulated: pass | Fits. |
| 812 × 375 (iPhone X class) | Landscape | Emulated: pass after a fix | **Failed first**: the canvas was 433 px tall in a 375 px screen, cutting off the bottom. Fixed by sizing the stage by both width and height. |
| 915 × 412 (large Android phone) | Landscape | Emulated: pass | Fits. |
| 1024 × 768 (tablet) | Landscape | Emulated: pass | Fits. |
| 1920 × 1080 (desktop) | Landscape | Emulated: pass | Fits, capped at 960 px wide. |
| Notch / rounded corners | Landscape | Not tested | The page adds `env(safe-area-inset-*)` padding, but this needs a real notched device to confirm. |

## Behavior
| Area | Check | Result |
| --- | --- | --- |
| Touch input | Holding a direction moves the player; jump while moving (two fingers) works | Pass (simulated pointer events) |
| Touch input | A cancelled touch or lost pointer capture clears the direction, so the player does not run on by itself | Pass (simulated pointer events) |
| Touch input | Feel and accuracy on a real touch screen, thumb reach, accidental touches | Not tested |
| Pause | On-screen pause button works | Pass (simulated) |
| Audio | Starts only after the first tap or key press, as mobile browsers require | By design; not tested on a phone |
| Audio | Loudness, silent-switch behavior on iOS, headphones | Not tested |
| Performance | Frame time per frame on a desktop | Pass (see `optimization-report.md`) |
| Performance | Frame rate on a real mid-range or low-end phone | Not tested |
| Interruptions | Switching tabs or the window pauses the game | Pass (the `blur` handler pauses it) |
| Interruptions | Incoming call, notification, screen lock, rotation mid-level, low battery | Not tested |
| Offline | Service worker caches the game for offline play | Logic tested with stubs; **not verified in a browser** (see `build-notes.md`) |

## OS and browser versions
| Platform | Result |
| --- | --- |
| Android 10 to 15, Chrome | Not tested |
| iOS 16 to 18, Safari | Not tested |
| Desktop Chrome on macOS | Pass |
