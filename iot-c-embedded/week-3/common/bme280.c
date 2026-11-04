#include "bme280.h"

static uint16_t u16le(const uint8_t *p) { return (uint16_t)(p[0] | p[1] << 8); }
static int16_t s16le(const uint8_t *p) { return (int16_t)u16le(p); }

void bme280_parse_calib(const uint8_t c1[26], const uint8_t c2[7], bme280_calib_t *cal) {
    cal->T1 = u16le(c1 + 0);  cal->T2 = s16le(c1 + 2);  cal->T3 = s16le(c1 + 4);
    cal->P1 = u16le(c1 + 6);  cal->P2 = s16le(c1 + 8);  cal->P3 = s16le(c1 + 10);
    cal->P4 = s16le(c1 + 12); cal->P5 = s16le(c1 + 14); cal->P6 = s16le(c1 + 16);
    cal->P7 = s16le(c1 + 18); cal->P8 = s16le(c1 + 20); cal->P9 = s16le(c1 + 22);
    cal->H1 = c1[25];                                   /* 0xA1; 0xA0 is unused */
    cal->H2 = s16le(c2 + 0);                            /* 0xE1, 0xE2 */
    cal->H3 = c2[2];                                    /* 0xE3 */
    cal->H4 = (int16_t)((int16_t)(int8_t)c2[3] * 16 | (c2[4] & 0x0F));       /* 0xE4[11:4], 0xE5[3:0] */
    cal->H5 = (int16_t)((int16_t)(int8_t)c2[5] * 16 | (c2[4] >> 4));         /* 0xE6[11:4], 0xE5[7:4] */
    cal->H6 = (int8_t)c2[6];                            /* 0xE7 */
}

void bme280_parse_raw(const uint8_t d[8], int32_t *adc_p, int32_t *adc_t, int32_t *adc_h) {
    *adc_p = (int32_t)((uint32_t)d[0] << 12 | (uint32_t)d[1] << 4 | d[2] >> 4);
    *adc_t = (int32_t)((uint32_t)d[3] << 12 | (uint32_t)d[4] << 4 | d[5] >> 4);
    *adc_h = (int32_t)((uint32_t)d[6] << 8 | d[7]);
}

int32_t bme280_t_fine(const bme280_calib_t *c, int32_t adc_t) {
    int32_t var1 = ((((adc_t >> 3) - ((int32_t)c->T1 << 1))) * (int32_t)c->T2) >> 11;
    int32_t d = (adc_t >> 4) - (int32_t)c->T1;
    int32_t var2 = (((d * d) >> 12) * (int32_t)c->T3) >> 14;
    return var1 + var2;
}

uint32_t bme280_pressure_q24_8(const bme280_calib_t *c, int32_t adc_p, int32_t t_fine) {
    int64_t var1 = (int64_t)t_fine - 128000;
    int64_t var2 = var1 * var1 * (int64_t)c->P6;
    var2 += (var1 * (int64_t)c->P5) * 131072;            /* << 17 */
    var2 += (int64_t)c->P4 * 34359738368LL;              /* << 35 */
    var1 = ((var1 * var1 * (int64_t)c->P3) / 256) + ((var1 * (int64_t)c->P2) * 4096);
    var1 = ((((int64_t)1) << 47) + var1) * (int64_t)c->P1 / 8589934592LL; /* >> 33 */
    if (var1 == 0) return 0;                             /* avoid division by zero (bad calibration) */
    int64_t p = 1048576 - adc_p;
    p = (((p * 2147483648LL) - var2) * 3125) / var1;     /* << 31 */
    var1 = ((int64_t)c->P9 * (p >> 13) * (p >> 13)) >> 25;
    var2 = ((int64_t)c->P8 * p) >> 19;
    p = ((p + var1 + var2) >> 8) + ((int64_t)c->P7 << 4);
    return (uint32_t)p;
}

uint32_t bme280_humidity_q22_10(const bme280_calib_t *c, int32_t adc_h, int32_t t_fine) {
    int32_t v = t_fine - 76800;
    v = (((((adc_h << 14) - ((int32_t)c->H4 << 20) - ((int32_t)c->H5 * v)) + 16384) >> 15) *
         (((((((v * (int32_t)c->H6) >> 10) * (((v * (int32_t)c->H3) >> 11) + 32768)) >> 10) + 2097152) *
               (int32_t)c->H2 + 8192) >> 14));
    v = v - (((((v >> 15) * (v >> 15)) >> 7) * (int32_t)c->H1) >> 4);
    if (v < 0) v = 0;
    if (v > 419430400) v = 419430400;
    return (uint32_t)(v >> 12);
}

bme280_reading_t bme280_compensate(const bme280_calib_t *cal, int32_t adc_p, int32_t adc_t, int32_t adc_h) {
    bme280_reading_t r;
    int32_t t_fine = bme280_t_fine(cal, adc_t);
    r.temp_centi_c = (t_fine * 5 + 128) >> 8;
    r.pressure_pa = (bme280_pressure_q24_8(cal, adc_p, t_fine) + 128u) >> 8;
    r.humidity_milli = (uint32_t)(((uint64_t)bme280_humidity_q22_10(cal, adc_h, t_fine) * 1000u + 512u) >> 10);
    return r;
}
