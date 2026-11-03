#include "sensors.h"

int16_t lm35_tenths_c(uint16_t adc) {
    /* 10 mV per degree means tenths of a degree == millivolts, so round once: adc * 5000 / 1023. */
    return (int16_t)(((uint32_t)adc * ADC_REF_MV + ADC_MAX / 2u) / ADC_MAX);
}

uint8_t ldr_percent(uint16_t adc) {
    if (adc > ADC_MAX) adc = ADC_MAX;
    return (uint8_t)(((uint32_t)adc * 100u + ADC_MAX / 2u) / ADC_MAX);
}

uint16_t echo_us_to_mm(uint32_t echo_us) {
    /* distance = time * 343 m/s / 2 = time_us * 0.1715 mm */
    uint32_t mm = (echo_us * 1715u + 5000u) / 10000u;
    if (echo_us == 0 || mm > 4000u) return 0xFFFFu;
    return (uint16_t)mm;
}

uint8_t update_alerts(uint8_t cur, const thresholds_t *t, int16_t temp, uint16_t dist, uint8_t light) {
    uint8_t a = cur & (uint8_t)~ALERT_SENSOR;

    if (temp > t->temp_high_tenths) a |= ALERT_HOT;
    else if (temp < t->temp_high_tenths - t->temp_hyst_tenths) a &= (uint8_t)~ALERT_HOT;

    if (dist == 0xFFFFu) {
        a &= (uint8_t)~ALERT_NEAR;   /* nothing in range */
    } else if (dist < t->near_mm) {
        a |= ALERT_NEAR;
    } else if (dist > t->near_mm + t->dist_hyst_mm) {
        a &= (uint8_t)~ALERT_NEAR;
    }

    if (light < t->dark_percent) a |= ALERT_DARK;
    else if (light > t->dark_percent + t->light_hyst_percent) a &= (uint8_t)~ALERT_DARK;

    /* LM35 cannot read below 2 C on a single supply, and above 150 C is out of its range: wiring fault. */
    if (temp < 20 || temp > 1500) a |= ALERT_SENSOR;
    return a;
}

static uint8_t put_uint(char *buf, uint8_t pos, uint8_t size, uint32_t v) {
    char tmp[10];
    uint8_t n = 0;
    do { tmp[n++] = (char)('0' + v % 10u); v /= 10u; } while (v && n < sizeof tmp);
    while (n && pos + 1 < size) buf[pos++] = tmp[--n];
    return pos;
}

static uint8_t put_tenths(char *buf, uint8_t pos, uint8_t size, int16_t v) {
    if (v < 0 && pos + 1 < size) { buf[pos++] = '-'; v = (int16_t)-v; }
    pos = put_uint(buf, pos, size, (uint16_t)v / 10u);
    if (pos + 2 < size) { buf[pos++] = '.'; buf[pos++] = (char)('0' + (uint16_t)v % 10u); }
    return pos;
}

static uint8_t put_char(char *buf, uint8_t pos, uint8_t size, char c) {
    if (pos + 1 < size) buf[pos++] = c;
    return pos;
}

uint8_t format_log_line(char *buf, uint8_t size, uint32_t ms, int16_t temp, uint16_t dist_mm,
                        uint8_t light, int16_t humidity, uint8_t alerts) {
    uint8_t p = 0;
    p = put_uint(buf, p, size, ms);
    p = put_char(buf, p, size, ',');
    p = put_tenths(buf, p, size, temp);
    p = put_char(buf, p, size, ',');
    if (dist_mm == 0xFFFFu) { p = put_char(buf, p, size, 'N'); p = put_char(buf, p, size, 'A'); }
    else p = put_tenths(buf, p, size, (int16_t)dist_mm);   /* mm / 10 shown as cm with one decimal */
    p = put_char(buf, p, size, ',');
    p = put_uint(buf, p, size, light);
    p = put_char(buf, p, size, ',');
    if (humidity < 0) { p = put_char(buf, p, size, 'N'); p = put_char(buf, p, size, 'A'); }
    else p = put_tenths(buf, p, size, humidity);
    p = put_char(buf, p, size, ',');
    if (!alerts) p = put_char(buf, p, size, '-');
    if (alerts & ALERT_HOT) p = put_char(buf, p, size, 'H');
    if (alerts & ALERT_NEAR) p = put_char(buf, p, size, 'N');
    if (alerts & ALERT_DARK) p = put_char(buf, p, size, 'D');
    if (alerts & ALERT_SENSOR) p = put_char(buf, p, size, 'S');
    p = put_char(buf, p, size, '\r');
    p = put_char(buf, p, size, '\n');
    buf[p] = '\0';
    return p;
}

uint8_t crc8(const uint8_t *data, uint8_t len) {
    uint8_t crc = 0;
    while (len--) {
        crc ^= *data++;
        for (uint8_t i = 0; i < 8; i++) crc = (uint8_t)((crc & 0x80u) ? (uint8_t)(crc << 1) ^ 0x07u : (uint8_t)(crc << 1));
    }
    return crc;
}
