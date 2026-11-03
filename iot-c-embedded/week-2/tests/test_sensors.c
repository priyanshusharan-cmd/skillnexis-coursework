/* Host unit tests for firmware/sensors.c. Build and run: make test */
#include <stdio.h>
#include <string.h>

#include "../firmware/sensors.h"

static int failures, checks;
#define EXPECT_EQ(a, b) do { long _a = (long)(a), _b = (long)(b); checks++; \
    if (_a != _b) { failures++; printf("FAIL %s:%d  %s == %ld, expected %ld\n", __FILE__, __LINE__, #a, _a, _b); } } while (0)
#define EXPECT_STR(a, b) do { checks++; if (strcmp((a), (b)) != 0) { failures++; \
    printf("FAIL %s:%d  got \"%s\" expected \"%s\"\n", __FILE__, __LINE__, (a), (b)); } } while (0)

static const thresholds_t T = { .temp_high_tenths = 350, .temp_hyst_tenths = 10, .near_mm = 100, .dist_hyst_mm = 20,
                                .dark_percent = 20, .light_hyst_percent = 5 };

static void test_lm35(void) {
    EXPECT_EQ(lm35_tenths_c(0), 0);
    EXPECT_EQ(lm35_tenths_c(51), 249);     /* 51 * 5000/1023 = 249.3 mV -> 24.9 C */
    EXPECT_EQ(lm35_tenths_c(52), 254);
    EXPECT_EQ(lm35_tenths_c(72), 352);     /* 35.2 C */
    EXPECT_EQ(lm35_tenths_c(307), 1500);   /* 1.5 V = 150 C, top of the LM35 range */
    EXPECT_EQ(lm35_tenths_c(1023), 5000);
}

static void test_ldr(void) {
    EXPECT_EQ(ldr_percent(0), 0);
    EXPECT_EQ(ldr_percent(512), 50);
    EXPECT_EQ(ldr_percent(1023), 100);
    EXPECT_EQ(ldr_percent(5000), 100);     /* clamps impossible readings */
}

static void test_ultrasonic(void) {
    EXPECT_EQ(echo_us_to_mm(0), 0xFFFF);   /* timeout */
    EXPECT_EQ(echo_us_to_mm(583), 100);    /* 10.0 cm */
    EXPECT_EQ(echo_us_to_mm(1166), 200);
    EXPECT_EQ(echo_us_to_mm(23324), 4000); /* 4 m: the sensor's limit */
    EXPECT_EQ(echo_us_to_mm(23400), 0xFFFF);
}

static void test_alerts_and_hysteresis(void) {
    uint8_t a = update_alerts(0, &T, 250, 500, 60);
    EXPECT_EQ(a, 0);
    a = update_alerts(a, &T, 351, 500, 60);
    EXPECT_EQ(a, ALERT_HOT);
    a = update_alerts(a, &T, 345, 500, 60);            /* 34.5 C: inside the 1 C band, stays on */
    EXPECT_EQ(a, ALERT_HOT);
    a = update_alerts(a, &T, 339, 500, 60);            /* below 34.0 C: clears */
    EXPECT_EQ(a, 0);
    a = update_alerts(a, &T, 250, 99, 60);
    EXPECT_EQ(a, ALERT_NEAR);
    a = update_alerts(a, &T, 250, 110, 60);            /* 11 cm: still inside the band */
    EXPECT_EQ(a, ALERT_NEAR);
    a = update_alerts(a, &T, 250, 0xFFFF, 60);         /* object gone completely */
    EXPECT_EQ(a, 0);
    a = update_alerts(a, &T, 250, 500, 10);
    EXPECT_EQ(a, ALERT_DARK);
    a = update_alerts(a, &T, 250, 500, 24);
    EXPECT_EQ(a, ALERT_DARK);
    a = update_alerts(a, &T, 250, 500, 26);
    EXPECT_EQ(a, 0);
    EXPECT_EQ(update_alerts(0, &T, 0, 500, 60), ALERT_SENSOR);      /* LM35 unplugged reads 0 */
    EXPECT_EQ(update_alerts(ALERT_SENSOR, &T, 250, 500, 60), 0);    /* sensor flag never latches */
    EXPECT_EQ(update_alerts(0, &T, 400, 50, 5), ALERT_HOT | ALERT_NEAR | ALERT_DARK);
}

static void test_log_line(void) {
    char buf[64];
    format_log_line(buf, sizeof buf, 1500, 253, 1234, 47, 552, 0);
    EXPECT_STR(buf, "1500,25.3,123.4,47,55.2,-\r\n");
    format_log_line(buf, sizeof buf, 0, -15, 0xFFFF, 100, -1, ALERT_HOT | ALERT_DARK | ALERT_SENSOR);
    EXPECT_STR(buf, "0,-1.5,NA,100,NA,HDS\r\n");
    char small[12];
    uint8_t n = format_log_line(small, sizeof small, 4294967295u, 253, 1234, 47, 552, 0);
    EXPECT_EQ(n, 11);                                           /* truncated, never overflows */
    EXPECT_EQ(small[11], '\0');
}

static void test_crc8(void) {
    const uint8_t check[] = "123456789";
    EXPECT_EQ(crc8(check, 9), 0xF4);                            /* standard CRC-8/SMBUS check value */
    const uint8_t frame[2] = { 0x28, 0x02 };                    /* 552 = 55.2 %RH */
    uint8_t c = crc8(frame, 2);
    const uint8_t corrupted[2] = { 0x29, 0x02 };
    EXPECT_EQ(crc8(corrupted, 2) != c, 1);
}

int main(void) {
    test_lm35();
    test_ldr();
    test_ultrasonic();
    test_alerts_and_hysteresis();
    test_log_line();
    test_crc8();
    printf("%d checks, %d failures\n", checks, failures);
    return failures != 0;
}
