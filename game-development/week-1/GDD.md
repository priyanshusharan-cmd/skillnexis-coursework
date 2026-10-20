# Mini GDD — Signal Sprint

**Genre:** 2D one-screen arcade prototype. **Player:** a courier collecting three signal chips before a 60-second timer expires. **Core loop:** move, collect, avoid hazards, reach exit. **Win:** all chips collected and exit reached. **Lose:** health reaches zero or timer expires.

## Scene and controls

One compact top-down room; keyboard arrows/WASD move; collision with walls blocks movement. HUD shows score, health, and remaining time.

## Prototype acceptance checklist

- Player movement responds to input and stays within bounds.
- Score increments once per collectible.
- Hazard collision decreases health once per contact window.
- Timer counts down and ends the round.

This is a design brief and implementation checklist. A Unity project/build was not provided or run.
