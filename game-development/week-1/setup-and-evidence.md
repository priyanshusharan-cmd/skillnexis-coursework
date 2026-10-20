# Unity scene setup and verification record

## Scene setup

Create a 2D Core project. Under `Assets/`, add `Scenes/`, `Scripts/`, `Prefabs/`, `Sprites/`, and `Audio/`. Save `Main.unity`. Add a player sprite with Rigidbody2D (gravity scale 0) and a CapsuleCollider2D; add three collectible prefabs with trigger CircleCollider2D; add a hazard with a non-trigger collider; add a wall boundary and an orthographic camera. Add a Canvas HUD for score, health, and time.

## Components still needed for a playable mini project

Attach `PlayerController` to the player. Add a pickup component that increments score once and destroys the pickup; a hazard component that applies damage with invulnerability timing; a round manager that starts a 60-second timer and presents win/lose panels with restart. Keep scoring and game state in one manager so collision events do not double count.

## Test cases (execute in Unity and replace Pending with observations)

| ID | Action | Expected | Result |
|---|---|---|---|
| GAME-01 | Press each arrow key | Player moves in matching direction | Pending |
| GAME-02 | Hold two perpendicular keys | Movement remains normalized | Pending |
| GAME-03 | Move into wall | Player cannot pass through wall | Pending |
| GAME-04 | Enter collectible trigger | Score increases once; pickup disappears | Pending |
| GAME-05 | Enter hazard | Health decreases once per damage window | Pending |
| GAME-06 | Collect all chips then reach exit | Win panel appears | Pending |
| GAME-07 | Let timer reach zero | Lose panel appears | Pending |
| GAME-08 | Select restart | Score, health, timer and scene reset | Pending |

Evidence checklist: Unity version, hierarchy/Inspector, play-mode capture, Console errors, and a short result for each test. No execution results are claimed in this source pack.
