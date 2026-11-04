#include "secure_payload.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "mbedtls/base64.h"
#include "mbedtls/gcm.h"

namespace {

// tiny extractor for our own fixed message format: finds "name":"value" or "name":number
bool json_field(const char* msg, const char* name, char* out, size_t out_len) {
  char pat[16];
  snprintf(pat, sizeof pat, "\"%s\":", name);
  const char* p = strstr(msg, pat);
  if (!p) return false;
  p += strlen(pat);
  while (*p == ' ') p++;
  bool quoted = *p == '"';
  if (quoted) p++;
  size_t i = 0;
  while (*p && (quoted ? *p != '"' : (*p != ',' && *p != '}' && *p != ' ')) && i + 1 < out_len) out[i++] = *p++;
  out[i] = 0;
  return quoted ? *p == '"' : i > 0;
}

}  // namespace

int sp_seal(SecureChannel* ch, const char* topic, const char* plaintext, char* out, size_t out_len) {
  uint8_t iv[12], tag[16];
  size_t n = strlen(plaintext);
  if (n > 480) return -1;
  uint8_t ct[512];
  char aad[160];
  ch->tx_counter++;
  int aad_len = snprintf(aad, sizeof aad, "%s|%s|%lu", topic, ch->device, static_cast<unsigned long>(ch->tx_counter));
  sp_random(iv, sizeof iv);
  mbedtls_gcm_context g;
  mbedtls_gcm_init(&g);
  int rc = mbedtls_gcm_setkey(&g, MBEDTLS_CIPHER_ID_AES, ch->key, 256);
  if (!rc) rc = mbedtls_gcm_crypt_and_tag(&g, MBEDTLS_GCM_ENCRYPT, n, iv, sizeof iv, reinterpret_cast<uint8_t*>(aad), aad_len,
                                         reinterpret_cast<const uint8_t*>(plaintext), ct, sizeof tag, tag);
  mbedtls_gcm_free(&g);
  if (rc) return -1;
  memcpy(ct + n, tag, sizeof tag);  // Python's AESGCM appends the tag to the ciphertext
  unsigned char iv64[24], ct64[700];
  size_t iv64_len, ct64_len;
  if (mbedtls_base64_encode(iv64, sizeof iv64, &iv64_len, iv, sizeof iv) ||
      mbedtls_base64_encode(ct64, sizeof ct64, &ct64_len, ct, n + sizeof tag))
    return -1;
  int len = snprintf(out, out_len, "{\"dev\":\"%s\",\"ctr\":%lu,\"iv\":\"%.*s\",\"ct\":\"%.*s\"}", ch->device,
                     static_cast<unsigned long>(ch->tx_counter), static_cast<int>(iv64_len), iv64, static_cast<int>(ct64_len), ct64);
  return (len > 0 && static_cast<size_t>(len) < out_len) ? len : -1;
}

int sp_open(SecureChannel* ch, const char* topic, const char* msg, char* out, size_t out_len) {
  char dev[48], ctr_s[16], iv64[32], ct64[700];
  if (!json_field(msg, "dev", dev, sizeof dev) || !json_field(msg, "ctr", ctr_s, sizeof ctr_s) ||
      !json_field(msg, "iv", iv64, sizeof iv64) || !json_field(msg, "ct", ct64, sizeof ct64))
    return -1;
  unsigned long ctr = strtoul(ctr_s, nullptr, 10);
  if (ctr <= ch->rx_counter) return -1;  // replay
  uint8_t iv[16], ct[520];
  size_t iv_len, ct_len;
  if (mbedtls_base64_decode(iv, sizeof iv, &iv_len, reinterpret_cast<uint8_t*>(iv64), strlen(iv64)) || iv_len != 12 ||
      mbedtls_base64_decode(ct, sizeof ct, &ct_len, reinterpret_cast<uint8_t*>(ct64), strlen(ct64)) || ct_len < 16 ||
      ct_len - 16 + 1 > out_len)
    return -1;
  char aad[160];
  int aad_len = snprintf(aad, sizeof aad, "%s|%s|%lu", topic, dev, ctr);
  mbedtls_gcm_context g;
  mbedtls_gcm_init(&g);
  int rc = mbedtls_gcm_setkey(&g, MBEDTLS_CIPHER_ID_AES, ch->key, 256);
  size_t n = ct_len - 16;
  if (!rc) rc = mbedtls_gcm_auth_decrypt(&g, n, iv, 12, reinterpret_cast<uint8_t*>(aad), aad_len, ct + n, 16, ct,
                                        reinterpret_cast<uint8_t*>(out));
  mbedtls_gcm_free(&g);
  if (rc) return -1;
  out[n] = 0;
  ch->rx_counter = ctr;
  return static_cast<int>(n);
}
