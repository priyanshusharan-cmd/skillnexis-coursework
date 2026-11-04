// Host build of the firmware's portable parts, driven by tests/test_firmware_host.py.
//   features  < rows "motion sound temp minute weekend bedroom"   -> 13 features per line
//   seal  <hexkey> <device> <topic> <plaintext>                     -> sealed JSON
//   open  <hexkey> <device> <topic> <json> [rx_counter]             -> plaintext or "REJECTED"
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "../main/features.h"
#include "../main/secure_payload.h"

void sp_random(uint8_t* out, size_t n) {
  FILE* f = fopen("/dev/urandom", "rb");
  if (!f || fread(out, 1, n, f) != n) abort();
  fclose(f);
}

static void hexkey(const char* h, uint8_t* k) {
  for (int i = 0; i < 32; i++) sscanf(h + 2 * i, "%2hhx", &k[i]);
}

int main(int argc, char** argv) {
  if (argc >= 2 && !strcmp(argv[1], "features")) {
    FeatureExtractor* fx = nullptr;
    int motion, minute, weekend, bedroom;
    float sound, temp, f[FeatureExtractor::kN];
    while (scanf("%d %f %f %d %d %d", &motion, &sound, &temp, &minute, &weekend, &bedroom) == 6) {
      if (!fx) fx = new FeatureExtractor(bedroom);
      fx->push(motion, sound, temp, minute, weekend);
      fx->get(f);
      for (int i = 0; i < FeatureExtractor::kN; i++) printf(i ? " %.6f" : "%.6f", f[i]);
      printf("\n");
    }
    return 0;
  }
  if (argc >= 6 && (!strcmp(argv[1], "seal") || !strcmp(argv[1], "open"))) {
    SecureChannel ch{argv[3], {}, 41, argc > 6 ? static_cast<uint32_t>(atol(argv[6])) : 0};
    hexkey(argv[2], ch.key);
    char out[1024];
    int n = !strcmp(argv[1], "seal") ? sp_seal(&ch, argv[4], argv[5], out, sizeof out) : sp_open(&ch, argv[4], argv[5], out, sizeof out);
    puts(n < 0 ? "REJECTED" : out);
    return n < 0;
  }
  fprintf(stderr, "usage: see header\n");
  return 2;
}
