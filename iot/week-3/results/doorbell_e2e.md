End-to-end: 90 composed doorbell visits (3-frame bursts on a brick-wall porch with uneven light), run through detection -> int8 classifier -> SQLite -> MQTT.

| Visit type | Visits | Correct outcome | Notes |
|---|---:|---:|---|
| Resident (2 people × 20) | 40 | 34 named correctly | 0 named as the other resident, 1 called unknown, 5 face not found |
| Stranger (30 unseen LFW faces) | 30 | 29 flagged "unknown visitor" | **0 taken for a resident**, 1 face not found |
| Bell pressed, nobody there | 20 | 20 no false face | |

Processing per visit (3 frames, detection + classification): median **114 ms**, max 151 ms on this PC (expect roughly 4-6x on a Raspberry Pi 4).
Cooldown: same resident rang twice 20 s apart -> notified 1 + 0 times, logged twice.
MQTT: the subscribing "phone" received **65 of 65** expected notifications, each with a JPEG snapshot (~10 KB).
