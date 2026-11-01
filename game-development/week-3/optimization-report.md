# Optimization report

Profile the game, find three bottlenecks, fix them, record before and after.

## How it was measured
`bench.js` plays 6,000 frames of scripted movement (a fixed random seed, so every run is the same) through the real update-and-draw code and reports the average time per frame. It runs 5 times and the table shows the **median**. Open `index.html?profile&bench` and read `window.__benchResult` in the console. Each optimization has its own switch: `?opt=0` turns all off, `?only=tiles`, `?only=cull` or `?only=hud` turns on just one.

## Results (median ms per frame, level 2, this Mac)
| Build | ms / frame | vs baseline |
| --- | --- | --- |
| Baseline, no optimizations | 0.0797 | |
| 1. Pre-render tiles and cache the sky gradient | 0.0432 | 46% less |
| 2. Cull off-screen objects | 0.0714 | 10% less, **within run-to-run noise** (runs ranged 0.063 to 0.080 against 0.076 to 0.084 for the baseline) |
| 3. Cache the HUD text layer | 0.0610 | 23% less |
| All three together | 0.0200 | 75% less, about 4 times faster |

## The three bottlenecks
1. **Redrawing every tile and rebuilding the sky gradient every frame.** The level's solid tiles never change, but each frame redrew every visible tile with up to three rectangles each and created a new gradient object. Fix: draw all tiles once into an offscreen canvas per level, then copy the visible part with one `drawImage`, and build the gradient once per level. This was the biggest win.
2. **Re-laying-out HUD text every frame.** Five strings were measured and drawn 60 times a second even though they change only when health, score, level or whole seconds change. Fix: keep the HUD on its own canvas and redraw it only when its text changes.
3. **Drawing objects that are off screen.** Coins, spikes, flags and enemies across the whole level were drawn even when far from the camera. Fix: skip any object outside the camera view. The measured gain is small and not clearly above the noise, so it is kept because it is correct and cheap, not because it is proven to help.

## Limits of these numbers
- They measure CPU time for drawing calls in a desktop browser tab (which was in the background, so the browser did not draw to the screen). They say nothing about GPU cost or real phones. The game needs about 0.02 ms of drawing and update work per frame here, against a 16.7 ms budget at 60 fps, so it was never slow on this Mac. The fixes matter for low-end phones, which I could not test.
- Memory, loading time, battery and thermal behavior were not measured.
