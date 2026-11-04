/* Weather-station logic shared by the ESP32 firmware and the PC build:
 * JSON payload, OLED text lines and command handling. */
#ifndef STATION_H
#define STATION_H
#include <stddef.h>
#include <stdint.h>

#include "bme280.h"

typedef struct {
    char id[16];
    uint32_t interval_ms;     /* publish period, changed by the "interval=<s>" command */
    uint32_t seq;             /* message counter, lets the dashboard spot gaps */
} station_t;

/* {"id":"ws-01","seq":12,"t":25.08,"h":45.12,"p":1006.53,"uptime":36} */
size_t station_json(const station_t *s, const bme280_reading_t *r, uint32_t uptime_s, char *out, size_t size);

/* Four 16-character lines for a 128x64 OLED (8x8 font, 16 columns). */
void station_oled_lines(const station_t *s, const bme280_reading_t *r, int mqtt_up, char lines[4][17]);

/* Handles a command payload. Returns 1 if the command changed something. */
int station_command(station_t *s, const char *payload, size_t len);

#endif
