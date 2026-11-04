#include "station.h"

#include <stdio.h>
#include <string.h>

static void fixed2(char *buf, size_t size, int32_t hundredths) {
    const char *sign = hundredths < 0 ? "-" : "";
    if (hundredths < 0) hundredths = -hundredths;
    snprintf(buf, size, "%s%ld.%02ld", sign, (long)(hundredths / 100), (long)(hundredths % 100));
}

size_t station_json(const station_t *s, const bme280_reading_t *r, uint32_t uptime_s, char *out, size_t size) {
    char t[16], h[16], p[16];
    fixed2(t, sizeof t, r->temp_centi_c);
    fixed2(h, sizeof h, (int32_t)((r->humidity_milli + 5u) / 10u));
    fixed2(p, sizeof p, (int32_t)r->pressure_pa);       /* Pa / 100 = hPa with two decimals */
    int n = snprintf(out, size, "{\"id\":\"%s\",\"seq\":%lu,\"t\":%s,\"h\":%s,\"p\":%s,\"uptime\":%lu}",
                     s->id, (unsigned long)s->seq, t, h, p, (unsigned long)uptime_s);
    return (n < 0 || (size_t)n >= size) ? 0 : (size_t)n;
}

void station_oled_lines(const station_t *s, const bme280_reading_t *r, int mqtt_up, char lines[4][17]) {
    char t[16], h[16];
    fixed2(t, sizeof t, r->temp_centi_c / 10 * 10);    /* one decimal on the small screen */
    t[strlen(t) - 1] = '\0';
    fixed2(h, sizeof h, (int32_t)(r->humidity_milli / 100u) * 10);
    h[strlen(h) - 1] = '\0';
    snprintf(lines[0], 17, "%-10.10s%s", s->id, mqtt_up ? "  MQTT" : "  ----");
    snprintf(lines[1], 17, "Temp %7.7s C", t);
    snprintf(lines[2], 17, "Hum  %7.7s %%", h);
    char whole[12];
    snprintf(whole, sizeof whole, "%lu", (unsigned long)(r->pressure_pa / 100u) % 100000u);
    snprintf(lines[3], 17, "P %6.6s.%u hPa", whole, (unsigned)(r->pressure_pa % 100u / 10u));
}

int station_command(station_t *s, const char *payload, size_t len) {
    char cmd[32];
    if (len >= sizeof cmd) return 0;
    memcpy(cmd, payload, len);
    cmd[len] = '\0';
    unsigned secs;
    char extra;
    if (sscanf(cmd, "interval=%u%c", &secs, &extra) == 1 && secs >= 1 && secs <= 3600) {
        s->interval_ms = secs * 1000u;
        return 1;
    }
    return 0;
}
