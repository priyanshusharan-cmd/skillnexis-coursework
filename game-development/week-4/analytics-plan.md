# Analytics plan: 15 events

Each event is implemented in `analytics.js`, emitted from the game, and covered by tests. Events are validated against a fixed list of allowed parameters, so anything else (a name, an email, a device ID) is dropped. They are **stored on the device only and never sent anywhere**. To send them to a server you would need a privacy policy and, in many countries, the player's consent, and that is not built.

| # | Event | Parameters | Product decision it supports |
| --- | --- | --- | --- |
| 1 | `session_start` | `returning` | What share of sessions come from returning players, a basic retention signal. If returning players are rare, work on the reason to come back before adding content. |
| 2 | `control_scheme` | `scheme` (keyboard or touch) | Which controls to polish first. If most sessions are touch, button size, placement and feel get priority over keyboard. |
| 3 | `level_start` | `level` | Where players drop off: the number of starts per level against completions. |
| 4 | `level_complete` | `level`, `score`, `seconds`, `health_left` | Whether levels take the intended time (about 10 s of pure running today). Very short or very long clear times mean a level is too easy or too hard. |
| 5 | `game_over` | `level`, `score` | Which level kills the most players. The level with the highest game-over rate is the one to rebalance. |
| 6 | `player_hit` | `level`, `reason` (spike, enemy, fall) | Which hazard is hurting players, so it can be made more readable or fairer. |
| 7 | `checkpoint` | `level` | Whether checkpoints are being reached, and whether they are placed so that deaths do not cost too much progress. |
| 8 | `coins_collected` | `level`, `coins` | Whether collectibles are found. Low counts on a level mean coins are hidden or placed where players do not look. |
| 9 | `enemy_stomped` | `level` | Whether players understand the stomp mechanic. If stomps are rare and enemy hits are common, teach it better. |
| 10 | `pause` | `level` | Where players need a break or are confused. Many pauses at one point can mean a difficulty spike. |
| 11 | `level_retry` | `level`, `after` (game_over or pause_menu) | Persistence. Players who retry after a game over are engaged; players who quit instead point to frustration. Retries from the pause menu show deliberate restarts. |
| 12 | `setting_changed` | `setting` (volume or mute), `value` | Whether the default volume is right. Many mutes on first sessions mean the audio is too loud or annoying. |
| 13 | `session_end` | `seconds`, `levels_completed` | Session length and progress per session, the base for retention and for how much content is needed. |
| 14 | `pwa_install` | `outcome` (prompted or installed) | The install rate when the browser offers "Add to Home screen". Low rates mean the prompt is badly timed or the value is unclear. |
| 15 | `perf_sample` | `avg_frame_ms` | Performance in the field. A rising average on some devices tells you where to optimize next. |

## Metrics these give you
- **Funnel:** level starts, then completions, per level (events 3 and 4). Drop-off is the main balance signal.
- **Difficulty:** hits per level by reason, and game-over rate per level (events 5 and 6).
- **Retention:** returning-session share (event 1), plus sessions per player if an anonymous ID were added later.
- **Engagement:** session length and levels per session (event 13).

## What is not measured, and why
- **Installs and day-1 / day-7 retention** need a store console or an anonymous player ID sent to a server. Neither exists here.
- **Crashes** need a crash-reporting service. None is included.
- **Revenue events** are not defined because the game has no purchases or ads (see `monetization-plan.md`).
