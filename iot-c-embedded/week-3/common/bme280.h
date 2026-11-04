/* BME280 temperature / humidity / pressure: calibration parsing and Bosch's integer compensation
 * formulas (datasheet section 4.2.3 / 8.2). Pure C, no I/O, so it is unit-tested on a PC. */
#ifndef BME280_H
#define BME280_H
#include <stdint.h>

#define BME280_ADDR 0x76
#define BME280_REG_CALIB1 0x88   /* 26 bytes: dig_T1 .. dig_H1 */
#define BME280_REG_CALIB2 0xE1   /* 7 bytes:  dig_H2 .. dig_H6 */
#define BME280_REG_ID 0xD0       /* reads 0x60 */
#define BME280_REG_CTRL_HUM 0xF2
#define BME280_REG_CTRL_MEAS 0xF4
#define BME280_REG_CONFIG 0xF5
#define BME280_REG_DATA 0xF7     /* 8 bytes: press[3] temp[3] hum[2] */

typedef struct {
    uint16_t T1; int16_t T2, T3;
    uint16_t P1; int16_t P2, P3, P4, P5, P6, P7, P8, P9;
    uint8_t H1, H3; int16_t H2, H4, H5; int8_t H6;
} bme280_calib_t;

typedef struct {
    int32_t temp_centi_c;     /* 2508 = 25.08 C */
    uint32_t pressure_pa;     /* 100653 */
    uint32_t humidity_milli;  /* 45123 = 45.123 %RH */
} bme280_reading_t;

void bme280_parse_calib(const uint8_t c1[26], const uint8_t c2[7], bme280_calib_t *cal);
void bme280_parse_raw(const uint8_t data[8], int32_t *adc_p, int32_t *adc_t, int32_t *adc_h);
bme280_reading_t bme280_compensate(const bme280_calib_t *cal, int32_t adc_p, int32_t adc_t, int32_t adc_h);

/* Lower-level formulas, exposed for testing. */
int32_t bme280_t_fine(const bme280_calib_t *cal, int32_t adc_t);
uint32_t bme280_pressure_q24_8(const bme280_calib_t *cal, int32_t adc_p, int32_t t_fine);
uint32_t bme280_humidity_q22_10(const bme280_calib_t *cal, int32_t adc_h, int32_t t_fine);

#endif
