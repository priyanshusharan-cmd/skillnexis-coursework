Classes: astronaut, grace_hopper, unknown. Input 25x25 grey, 3,891 parameters, **9.1 KB** int8, 39 µs per face on this PC.

| True class | Test faces | Recognised correctly |
|---|---:|---:|
| astronaut | 60 | 0.92 |
| grace_hopper | 60 | 0.78 |
| unknown | 60 | 1.00 |

**Strangers recognised as a resident: 0.0%** (the number that matters for a door). Residents not recognised: 15.0% (they just get an "unknown visitor" notification). Decision rule: a resident is only accepted at ≥ 75% confidence.
