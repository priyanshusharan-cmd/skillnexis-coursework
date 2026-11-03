/* Pure conversion and alert logic. No register access, so it compiles for AVR and for the host
 * (tests/test_sensors.c runs it with gcc). */
#ifndef SENSORS_H
#define SENSORS_H
#include <stdint.h>

#define ADC_REF_MV 5000u     /* AVCC reference on an Arduino Uno */
#define ADC_MAX    1023u

/* LM35: 10 mV per degree C. Returns tenths of a degree, e.g. 253 = 25.3 C. */
int16_t lm35_tenths_c(uint16_t adc);

/* LDR in a divider with a 10k resistor to GND (LDR to 5 V): more light -> higher reading.
 * Returns 0..100 %. */
uint8_t ldr_percent(uint16_t adc);

/* HC-SR04 echo high time in microseconds -> distance in millimetres (speed of sound 343 m/s at 20 C).
 * Returns 0xFFFF for "no echo / out of range" (> 4 m). */
uint16_t echo_us_to_mm(uint32_t echo_us);

/* Threshold alerts with hysteresis so a reading hovering at the limit does not make the buzzer chatter. */
typedef struct {
    int16_t temp_high_tenths;   /* alert above, clear below (limit - hyst) */
    uint16_t near_mm;           /* alert below, clear above (limit + hyst) */
    uint8_t dark_percent;       /* alert below, clear above (limit + hyst) */
    int16_t temp_hyst_tenths;
    uint16_t dist_hyst_mm;
    uint8_t light_hyst_percent;
} thresholds_t;

enum { ALERT_HOT = 1u << 0, ALERT_NEAR = 1u << 1, ALERT_DARK = 1u << 2, ALERT_SENSOR = 1u << 3 };

uint8_t update_alerts(uint8_t current, const thresholds_t *t, int16_t temp_tenths, uint16_t dist_mm, uint8_t light_pct);

/* Format one CSV log line: "<ms>,<temp>,<dist_cm>,<light>,<humidity>,<flags>\r\n". Returns length.
 * humidity_tenths < 0 means "remote node did not answer". */
uint8_t format_log_line(char *buf, uint8_t size, uint32_t ms, int16_t temp_tenths, uint16_t dist_mm,
                        uint8_t light_pct, int16_t humidity_tenths, uint8_t alerts);

/* CRC-8 (poly 0x07) used on the I2C link between the two microcontrollers. */
uint8_t crc8(const uint8_t *data, uint8_t len);

#endif
