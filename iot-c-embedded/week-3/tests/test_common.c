/* Host unit tests for the MQTT encoder and the BME280 compensation. Run: make test */
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "../common/bme280.h"
#include "../common/mqtt.h"

static int checks, failures;
#define EXPECT(cond) do { checks++; if (!(cond)) { failures++; printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond); } } while (0)

/* Example calibration and raw values from the Bosch BMP280/BME280 datasheet (section 3.12 / 8.1). */
static bme280_calib_t datasheet_cal(void) {
    bme280_calib_t c = { .T1 = 27504, .T2 = 26435, .T3 = -1000, .P1 = 36477, .P2 = -10685, .P3 = 3024, .P4 = 2855,
                         .P5 = 140, .P6 = -7, .P7 = 15500, .P8 = -14600, .P9 = 6000,
                         .H1 = 75, .H2 = 362, .H3 = 0, .H4 = 324, .H5 = 0, .H6 = 30 };
    return c;
}

/* Datasheet floating-point humidity formula, used as an independent reference for the integer one. */
static double humidity_ref(const bme280_calib_t *c, int32_t adc_h, int32_t t_fine) {
    double h = (double)t_fine - 76800.0;
    h = (adc_h - (c->H4 * 64.0 + c->H5 / 16384.0 * h)) *
        (c->H2 / 65536.0 * (1.0 + c->H6 / 67108864.0 * h * (1.0 + c->H3 / 67108864.0 * h)));
    h = h * (1.0 - c->H1 * h / 524288.0);
    return h > 100.0 ? 100.0 : h < 0.0 ? 0.0 : h;
}

static void test_bme280(void) {
    bme280_calib_t c = datasheet_cal();
    int32_t t_fine = bme280_t_fine(&c, 519888);
    bme280_reading_t r = bme280_compensate(&c, 415148, 519888, 30000);
    EXPECT(r.temp_centi_c == 2508);                         /* datasheet: 25.08 C */
    EXPECT(r.pressure_pa >= 100652 && r.pressure_pa <= 100654); /* datasheet: 100653.27 Pa */
    for (int32_t adc_h = 20000; adc_h <= 45000; adc_h += 2500) {
        double ref = humidity_ref(&c, adc_h, t_fine);
        double got = bme280_humidity_q22_10(&c, adc_h, t_fine) / 1024.0;
        EXPECT(fabs(got - ref) < 0.05);
    }
    EXPECT(bme280_humidity_q22_10(&c, 0, t_fine) == 0);             /* clamps at 0 %RH */
    EXPECT(bme280_humidity_q22_10(&c, 65535, t_fine) == 100 * 1024); /* clamps at 100 %RH */
    c.P1 = 0;
    EXPECT(bme280_pressure_q24_8(&c, 415148, t_fine) == 0);         /* bad calibration: no divide by zero */
}

static void test_bme280_register_parsing(void) {
    /* little-endian registers 0x88.. for the datasheet values, plus H values packed the way the chip does */
    const uint8_t c1[26] = { 0x70, 0x6B, 0x43, 0x67, 0x18, 0xFC, 0x7D, 0x8E, 0x43, 0xD6, 0xD0, 0x0B, 0x27, 0x0B,
                             0x8C, 0x00, 0xF9, 0xFF, 0x8C, 0x3C, 0xF8, 0xC6, 0x70, 0x17, 0x00, 0x4B };
    const uint8_t c2[7] = { 0x6A, 0x01, 0x00, 0x14, 0x04, 0x00, 0x1E };  /* H2=362 H3=0 H4=324 H5=0 H6=30 */
    bme280_calib_t c;
    bme280_parse_calib(c1, c2, &c);
    bme280_calib_t want = datasheet_cal();
    EXPECT(memcmp(&c, &want, sizeof c) == 0);
    const uint8_t c2neg[7] = { 0, 0, 0, 0xFF, 0xF8, 0xFF, 0x80 };        /* H4 = -8? H5 = -1, H6 = -128 */
    bme280_parse_calib(c1, c2neg, &c);
    EXPECT(c.H4 == -8 && c.H5 == -1 && c.H6 == -128);
    const uint8_t raw[8] = { 0x65, 0x5A, 0xC0, 0x7E, 0xED, 0x00, 0x75, 0x30 };
    int32_t p, t, h;
    bme280_parse_raw(raw, &p, &t, &h);
    EXPECT(p == 415148 && t == 519888 && h == 30000);
}

static void test_mqtt_length(void) {
    uint8_t b[4];
    uint32_t v;
    struct { uint32_t value; size_t n; uint8_t bytes[4]; } cases[] = {
        {0, 1, {0x00}}, {127, 1, {0x7F}}, {128, 2, {0x80, 0x01}}, {16383, 2, {0xFF, 0x7F}},
        {16384, 3, {0x80, 0x80, 0x01}}, {268435455, 4, {0xFF, 0xFF, 0xFF, 0x7F}},   /* MQTT spec table 2.4 */
    };
    for (size_t i = 0; i < sizeof cases / sizeof cases[0]; i++) {
        EXPECT(mqtt_encode_length(cases[i].value, b) == cases[i].n && memcmp(b, cases[i].bytes, cases[i].n) == 0);
        EXPECT(mqtt_decode_length(cases[i].bytes, cases[i].n, &v) == (int)cases[i].n && v == cases[i].value);
    }
    EXPECT(mqtt_encode_length(268435456u, b) == 0);
    const uint8_t partial[] = {0x80, 0x80};
    EXPECT(mqtt_decode_length(partial, 2, &v) == 0);
    const uint8_t bad[] = {0xFF, 0xFF, 0xFF, 0xFF, 0x01};
    EXPECT(mqtt_decode_length(bad, 5, &v) == -1);
}

static void test_mqtt_packets(void) {
    uint8_t b[128];
    size_t n = mqtt_build_connect(b, sizeof b, "ws-01", 30, NULL, NULL);
    const uint8_t want_connect[] = {0x10, 17, 0, 4, 'M', 'Q', 'T', 'T', 4, 0x02, 0, 30, 0, 5, 'w', 's', '-', '0', '1'};
    EXPECT(n == sizeof want_connect && memcmp(b, want_connect, n) == 0);
    n = mqtt_build_connect(b, sizeof b, "ws", 60, "s/st", "off");
    EXPECT(n > 0 && b[9] == (0x02 | 0x04 | 0x20) && memcmp(b + n - 3, "off", 3) == 0);
    n = mqtt_build_publish(b, sizeof b, "a/b", (const uint8_t *)"hi", 2, 1);
    const uint8_t want_pub[] = {0x31, 7, 0, 3, 'a', '/', 'b', 'h', 'i'};
    EXPECT(n == sizeof want_pub && memcmp(b, want_pub, n) == 0);
    n = mqtt_build_subscribe(b, sizeof b, 10, "c/#");
    const uint8_t want_sub[] = {0x82, 8, 0, 10, 0, 3, 'c', '/', '#', 0};
    EXPECT(n == sizeof want_sub && memcmp(b, want_sub, n) == 0);
    EXPECT(mqtt_build_publish(b, 8, "a/b", (const uint8_t *)"hi", 2, 0) == 0); /* buffer too small */
}

int main(void) {
    test_bme280();
    test_bme280_register_parsing();
    test_mqtt_length();
    test_mqtt_packets();
    printf("%d checks, %d failures\n", checks, failures);
    return failures != 0;
}
