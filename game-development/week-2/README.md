# Game Developer — Week 2: Gameplay, UI, Physics & Audio

**Gem Run** is a playable 2D platformer with three levels, built with HTML5 canvas and JavaScript. The course notes use Unity, but Unity is not installed on this Mac and the Week 1 Unity project was never opened or built, so this is a from-scratch playable prototype rather than a Unity project. It follows the Week 1 design (a 2D prototype with score and health) and expands it as the Week 2 mini project describes. Open `index.html` in a browser, or run `python3 -m http.server` in this folder and visit `localhost:8000`.

## Brief → what is here
| Requirement | Where |
| --- | --- |
| Three gameplay objects with clear feedback | Coins (pickup sound, particles, "+10"), spikes (hurt sound, screen shake, blink), checkpoints (flag turns green and waves, jingle). Enemies can be stomped or avoided. |
| Menus: main, pause, HUD, game over, victory | Main menu with level select, volume and mute; pause menu; HUD with hearts, score, level and timer; game-over and victory screens; a level-complete screen. |
| Two animations | Spinning coins and a squash-and-stretch player (jump and landing, running bob). Enemies waddle and flags wave too. |
| Five or more sound events, consistent levels | Jump, coin, hurt, checkpoint, stomp, win and game over, plus a music loop. Each has a fixed level and all pass through one master volume and mute control. |
| Three-level mini game with enemies, hazards, checkpoints | Meadow, Caverns and Summit (`core.js`). |
| Basic save system | Unlocked levels, best scores, volume and mute are saved in `localStorage`. Corrupt or tampered data falls back to defaults. |
| Physics, prefabs-style reuse, state machine | Gravity, collision, jumping and stomping are in `core.js`. The game is a state machine of menu, playing, paused, between levels, game over and victory. |

Audio is synthesized with the Web Audio API, so no sound files are included. Browsers only start audio after a click or key press, so sound begins when you press Play.

## Testing
- `node --test core.test.js` runs 12 tests: physics, jumping rules, coins, spike damage and protection, game over, checkpoints, stomping, the goal, save and load including bad data, and **an exhaustive search of the real physics code for a hazard-free route through every level**. That search found a real design bug, a ceiling block in Summit that stopped the jump over a spike patch, which was fixed. All three levels are now provably completable.
- In a real browser I replayed a winning route through the actual game loop and key handling: menu, level 1, 2, 3, victory, and checked the save afterwards. I also checked pause and resume (time stays frozen), mute, volume saving, the game-over screen and retry, and "Continue" after a reload.
- Not verified: how the music and sound effects actually *sound*, because I can't listen from here, and real keyboard timing, because the test browser was in the background and only runs about one frame per second. Play it once and adjust the volume levels in `audio.js` if any effect is too loud or quiet.

## Controls
Move with arrows or A/D, jump with Space, Up or W, pause with P or Esc, mute with M.
