8 unseen test days, 2 room nodes + hub + phone + voice clients over the real TLS broker config (client certificates, ACL, AES-GCM payloads). 23,040 sealed telemetry messages, each answered by a sealed command; simulated time, ran in 55 s.

| Room | Minutes | Sensor → hub → relay round trip (median / p99) | Same decisions as the offline evaluation |
|---|---:|---:|---:|
| living | 11,520 | 4.3 ms / 9.4 ms | 99.48% |
| bedroom | 11,520 | 4.3 ms / 9.3 ms | 99.74% |

Energy used by the lights and fans: **7.0 kWh/week** (offline estimate 7.0). Decisions differ from the offline run only while a voice/phone override was active.
Hub processing per message: median 0.43 ms.

Security: 1 message(s) rejected: replay: counter 1 <= 11520.

Notifications received by the phone client:

| Level | Title | Message |
|---|---|---|
| alert | Heat in the living | Indoor temperature 32.5 °C with someone in the room; the fan is on. Consider closing the curtains or switching on the AC. |
| alert | Heat in the bedroom | Indoor temperature 34.9 °C with someone in the room; the fan is on. Consider closing the curtains or switching on the AC. |
| info | bedroom fan switched off | The fan in the bedroom was left on by request but the room has been empty for 30 min, so it is back on automatic. |
| info | Welcome home | Arrival detected in the living; the house was empty for 8.6 h with everything off. |
| info | Welcome home | Arrival detected in the living; the house was empty for 9.5 h with everything off. |
| info | Welcome home | Arrival detected in the living; the house was empty for 9.2 h with everything off. |
| info | Welcome home | Arrival detected in the living; the house was empty for 3.4 h with everything off. |
| info | Welcome home | Arrival detected in the bedroom; the house was empty for 4.8 h with everything off. |
| alert | Heat in the living | Indoor temperature 32.6 °C with someone in the room; the fan is on. Consider closing the curtains or switching on the AC. |
| alert | Heat in the living | Indoor temperature 32.5 °C with someone in the room; the fan is on. Consider closing the curtains or switching on the AC. |
| alert | Heat in the bedroom | Indoor temperature 32.5 °C with someone in the room; the fan is on. Consider closing the curtains or switching on the AC. |
| alert | Security: message rejected | A message on home/living/telemetry failed verification (replay: counter 1 <= 11520). |
| alert | living node offline | The living sensor node stopped responding. Lights and fan there now run on the node's own model (edge fallback). |
