/* Hardware abstraction for the smart-agriculture node. Implemented twice:
 *   esp32/main/hal_esp32.c  real ADC, GPIO relay, BME280 + OLED on I2C, MQTT over WiFi, deep sleep, OTA
 *   sim/hal_sim.c           a soil/weather model, FreeRTOS POSIX port on Linux, accelerated clock
 * app/app.c (the FreeRTOS tasks) is identical for both. */
#ifndef HAL_H
#define HAL_H
#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint16_t soil_raw;      /* capacitive probe, 12-bit ADC */
    uint16_t light_raw;     /* LDR divider, 12-bit ADC */
    uint16_t batt_raw;      /* battery divider, 12-bit ADC */
    int16_t temp_c10;       /* air temperature from the BME280, tenths of C */
    uint8_t humidity;       /* %RH from the BME280 */
    bool tank_ok;           /* float switch closed = water available */
    bool temp_ok;           /* BME280 answered */
} hal_sample_t;

uint32_t hal_now_s(void);                       /* wall-clock seconds; survives deep sleep */
void hal_delay_s(uint32_t s);                   /* FreeRTOS delay in (possibly simulated) seconds */
bool hal_read(hal_sample_t *out);
void hal_pump(bool on);
void hal_display(const char lines[4][22]);
bool hal_publish(const char *topic_suffix, const char *payload, bool retain);   /* false if offline */
/* Non-blocking: copies a pending command into buf and returns true. */
bool hal_poll_command(char *buf, unsigned size);
void hal_log(const char *msg);
/* Starts an OTA update from url; on success the device reboots into the new image (never returns). */
bool hal_ota(const char *url);

#endif
