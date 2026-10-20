# Smart weather station: architecture and acceptance notes

## Data flow

DHT11 sensor → ESP32 GPIO 4 → temperature/humidity validation → HTTPS update → ThingSpeak private channel → dashboard chart. Add an email/webhook alert only after selecting a provider, authenticating safely, and testing in a sandbox.

## Acceptance checks to execute on hardware

1. Record ESP32 board revision and DHT11 pinout; verify common ground and 3.3 V logic.
2. Confirm serial output receives plausible values and reports `nan`/sensor failures clearly.
3. Confirm Wi-Fi reconnect behavior after disconnect.
4. Confirm a channel entry arrives no faster than the service's documented interval.
5. Confirm the channel is private and the write key is not in Git history.
6. Verify dashboard values and an alert using a controlled threshold.

No hardware or account evidence is included. Store credentials in a local ignored header or secret manager before actual deployment.
