/* Host unit tests for common/agri.c. Run: make test */
#include <stdio.h>
#include <string.h>

#include "../common/agri.h"

static int checks, failures;
#define EXPECT(c) do { checks++; if (!(c)) { failures++; printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

static const irrig_cfg_t CFG = {.start_below = 35, .stop_above = 60, .max_run_s = 300, .min_rest_s = 1800,
                                .daily_budget_s = 1200, .max_temp_c10 = 340, .max_light_pct = 85};

static irrig_input_t in(uint32_t t, uint8_t soil) {
    irrig_input_t i = {.now_s = t, .soil_pct = soil, .soil_ok = true, .temp_c10 = 250, .light_pct = 40, .tank_ok = true, .manual = 0};
    return i;
}

static void test_sensors(void) {
    soil_cal_t cal = {.raw_dry = 3000, .raw_wet = 1200};
    EXPECT(soil_percent(&cal, 3000) == 0 && soil_percent(&cal, 3500) == 0);
    EXPECT(soil_percent(&cal, 1200) == 100 && soil_percent(&cal, 900) == 100);
    EXPECT(soil_percent(&cal, 2100) == 50);
    soil_cal_t bad = {.raw_dry = 1000, .raw_wet = 2000};
    EXPECT(soil_percent(&bad, 1500) == 0);
    EXPECT(light_percent(0) == 0 && light_percent(4095) == 100 && light_percent(2048) == 50 && light_percent(9999) == 100);
    EXPECT(battery_mv(4095) == 6600 && battery_mv(2482) == 4000);
    EXPECT(irrig_cfg_valid(&CFG));
    irrig_cfg_t b = CFG; b.stop_above = 30;
    EXPECT(!irrig_cfg_valid(&b));
}

static void test_basic_cycle(void) {
    irrig_t s;
    irrig_init(&s, 0);
    irrig_input_t i = in(10, 50);
    EXPECT(!irrig_step(&s, &CFG, &i) && s.state == IR_IDLE);
    i = in(20, 30);
    EXPECT(irrig_step(&s, &CFG, &i) && s.state == IR_WATERING && s.last_reason == WHY_DRY);
    i = in(100, 45);
    EXPECT(irrig_step(&s, &CFG, &i));                      /* between thresholds: keep going (hysteresis) */
    i = in(140, 61);
    EXPECT(!irrig_step(&s, &CFG, &i) && s.state == IR_RESTING && s.last_reason == WHY_WET_ENOUGH);
    EXPECT(s.used_today_s == 120);
    i = in(500, 20);
    EXPECT(!irrig_step(&s, &CFG, &i) && s.last_reason == WHY_REST);   /* dry again but still resting */
    i = in(140 + 1800, 20);
    EXPECT(irrig_step(&s, &CFG, &i) && s.waterings == 2);
}

static void test_max_run_and_budget(void) {
    irrig_t s;
    irrig_init(&s, 0);
    uint32_t t = 0;
    int runs = 0;
    for (int k = 0; k < 10; k++) {                         /* soil never gets wet: stuck or leaking */
        irrig_input_t i = in(t, 10);
        if (irrig_step(&s, &CFG, &i)) runs++;
        t += 300;
        i = in(t, 10);
        irrig_step(&s, &CFG, &i);
        t += 1800;
    }
    EXPECT(runs == 4);                                     /* 4 x 300 s = the 1200 s daily budget */
    EXPECT(s.used_today_s == 1200 && s.state == IR_LOCKOUT && s.last_reason == WHY_BUDGET);
    irrig_input_t m = in(t, 10); m.manual = 1;
    EXPECT(!irrig_step(&s, &CFG, &m));                     /* manual cannot exceed the budget */
    irrig_input_t next_day = in(86400 + 60, 10);
    EXPECT(irrig_step(&s, &CFG, &next_day) && s.used_today_s == 0);   /* budget refills at midnight */
}

static void test_safety(void) {
    irrig_t s;
    irrig_init(&s, 0);
    irrig_input_t i = in(0, 20);
    irrig_step(&s, &CFG, &i);
    i = in(30, 25); i.tank_ok = false;
    EXPECT(!irrig_step(&s, &CFG, &i) && s.state == IR_LOCKOUT && s.last_reason == WHY_TANK_EMPTY);
    i = in(60, 25); i.tank_ok = false; i.manual = 1;
    EXPECT(!irrig_step(&s, &CFG, &i));                     /* manual never runs the pump dry */
    i = in(90, 25);
    EXPECT(irrig_step(&s, &CFG, &i) && s.state == IR_WATERING);   /* refilled and still dry: water now */

    irrig_init(&s, 0);
    i = in(0, 0); i.soil_ok = false;
    EXPECT(!irrig_step(&s, &CFG, &i) && s.last_reason == WHY_SENSOR_FAULT);
    i = in(10, 50);
    EXPECT(!irrig_step(&s, &CFG, &i) && s.state == IR_IDLE);       /* probe back, soil fine: normal again */

    irrig_init(&s, 0);
    i = in(0, 30); i.temp_c10 = 380;
    EXPECT(!irrig_step(&s, &CFG, &i) && s.last_reason == WHY_HEAT);   /* dry but 38 C: wait */
    i = in(10, 30); i.light_pct = 95;
    EXPECT(!irrig_step(&s, &CFG, &i) && s.last_reason == WHY_HEAT);
    i = in(20, 15); i.temp_c10 = 380;
    EXPECT(irrig_step(&s, &CFG, &i));                      /* critically dry: water anyway */
    i = in(40, 15); i.manual = -1;
    EXPECT(!irrig_step(&s, &CFG, &i) && s.last_reason == WHY_MANUAL);
}

static void test_sleep(void) {
    irrig_t s;
    irrig_init(&s, 0);
    EXPECT(sleep_seconds(&CFG, &s, 80, 4000) == 1800);
    EXPECT(sleep_seconds(&CFG, &s, 50, 4000) == 900);
    EXPECT(sleep_seconds(&CFG, &s, 40, 4000) == 300);
    EXPECT(sleep_seconds(&CFG, &s, 80, 3300) == 3600);
    EXPECT(sleep_seconds(&CFG, &s, 80, 3100) == 7200);
    s.state = IR_WATERING;
    EXPECT(sleep_seconds(&CFG, &s, 20, 4000) == 0);
    s.state = IR_RESTING;
    EXPECT(sleep_seconds(&CFG, &s, 20, 4000) == 1800);
    EXPECT(strcmp(irrig_reason_name(WHY_TANK_EMPTY), "tank-empty") == 0 && strcmp(irrig_state_name(IR_LOCKOUT), "lockout") == 0);
}

int main(void) {
    test_sensors();
    test_basic_cycle();
    test_max_run_and_budget();
    test_safety();
    test_sleep();
    printf("%d checks, %d failures\n", checks, failures);
    return failures != 0;
}
