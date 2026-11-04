# IoT security: encryption, authentication and best practice

## What we protect against

| Threat | Example | Control in this system | Verified by |
|---|---|---|---|
| Eavesdropping on WiFi/LAN | Neighbour sniffs traffic to learn when the house is empty | TLS 1.2+ on every hop, no plain-text listener | `test_plaintext_mqtt_is_refused`, `test_tls_traffic_is_not_readable_on_the_wire` |
| Rogue device or app | Attacker's laptop connects to the broker and switches the fans | Mutual TLS: every client needs a certificate from our private CA | `test_client_without_certificate_is_refused`, `test_certificate_from_another_ca_is_refused` |
| Stolen or compromised node | Bedroom node's key extracted; attacker spoofs living-room data | Per-device identity (cert CN = MQTT user) + least-privilege ACL | `test_acl_stops_a_device_from_writing_another_rooms_topics` |
| Malicious or cloud broker | Broker operator reads or edits messages in transit | End-to-end AES-256-GCM per device; broker only sees ciphertext | `test_payload_round_trip_and_ciphertext_hides_values`, `test_tampered_payload_is_rejected` |
| Replay | Recorded "fan on" or telemetry is re-sent later | Monotonic message counter in the authenticated data; receiver keeps the highest counter seen | `test_replayed_message_is_rejected`, e2e demo (replay rejected, phone alerted) |
| Message redirection | Valid living-room command re-published to the bedroom topic | Topic and device id are part of the GCM associated data | `test_message_moved_to_another_topic_is_rejected` |
| Node goes dark | Power cut, jammed WiFi, tampering | MQTT last-will → "node offline" alert; node runs its own model meanwhile | e2e demo / `test_whole_home_end_to_end` |
| Firmware theft or modification | Flash dumped to read keys or flash malicious code | Production units: Secure Boot v2 + flash encryption + NVS encryption (keys in eFuse) | configuration, see below |

The ESP32 C code (`firmware/main/secure_payload.cc`, mbedTLS) and the hub's Python (`security/secure_payload.py`,
`cryptography`) are checked against each other both ways in `tests/test_firmware_host.py`.

## Design choices
* **ECDSA P-256 certificates** instead of RSA-2048: smaller (≈ 500 B), and the TLS handshake on an ESP32 takes about
  a third of the time. Certificates follow a strict X.509 profile (CA key usage, AKI/SKI). Python 3.13's strict
  verification rejected my first CA for missing these, so the profile was fixed rather than verification relaxed.
* **TLS and payload encryption together.** TLS protects each link. AES-GCM protects data from end to end, so the
  broker could be moved to a cloud service without trusting it.
* **AES-GCM nonces** are 96-bit random values, and the counter in the AAD prevents replays. Counters are saved to
  NVS every 100 messages; after a reboot the device skips ahead 100, so a counter is never reused.
* **Keys stay out of git.** `security/gen_certs.sh` creates a fresh CA per installation (`security/certs/` is
  git-ignored, keys are `chmod 600`). `firmware/provision.sh` copies one device's certificate into its build.
* **Fail safe, not fail open.** Unverifiable messages are dropped and logged, and the phone is told. A node that
  loses the hub keeps working on its own instead of leaving lights on or fans off.

## Production hardening checklist (ESP32)
- [ ] `CONFIG_SECURE_BOOT_V2_ENABLED=y`: only signed firmware boots
- [ ] `CONFIG_SECURE_FLASH_ENC_ENABLED=y` (release mode): flash dumps are useless
- [ ] `CONFIG_NVS_ENCRYPTION=y`: AES key and counters in encrypted NVS, provisioned with `nvs_partition_gen.py`
- [ ] Disable JTAG and UART download mode in release eFuses
- [ ] Signed OTA updates only, with rollback (as in IoT-C week 4)
- [ ] Separate IoT WiFi network or VLAN; the broker is not exposed to the internet (use a VPN such as WireGuard for remote access)
- [ ] Rotate device certificates before their 825-day expiry; keep a revocation list on the broker (`crlfile`)
- [ ] Mosquitto: keys owned by the `mosquitto` user with mode 600, ACL file not world-readable
