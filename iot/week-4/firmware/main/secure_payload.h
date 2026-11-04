// AES-256-GCM payload sealing with mbedTLS, wire-compatible with security/secure_payload.py.
// {"dev":"<id>","ctr":<n>,"iv":"<b64 12 B>","ct":"<b64 ciphertext+tag>"}, AAD = "<topic>|<dev>|<ctr>"
#pragma once
#include <cstddef>
#include <cstdint>

struct SecureChannel {
  const char* device;
  uint8_t key[32];
  uint32_t tx_counter;  // persisted in NVS by the caller
  uint32_t rx_counter;  // highest counter accepted from the hub
};

// random bytes: esp_fill_random on the ESP32, /dev/urandom on the host test build
void sp_random(uint8_t* out, size_t n);

// returns length written to out (NUL-terminated JSON), or -1
int sp_seal(SecureChannel* ch, const char* topic, const char* plaintext, char* out, size_t out_len);

// verifies and decrypts a message from the hub; returns plaintext length, or -1 (bad tag, replay, malformed)
int sp_open(SecureChannel* ch, const char* topic, const char* msg, char* out, size_t out_len);
