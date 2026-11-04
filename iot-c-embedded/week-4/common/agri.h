/* Smart agriculture logic: sensor conversion, irrigation decisions and sleep scheduling.
 * Pure C99 with no hardware access, shared by the ESP32 firmware and the PC simulation, and unit-tested. */
#ifndef AGRI_H
#define AGRI_H
#include <stdbool.h>
#include <stdint.h>

/* ---------------------------------------------------------------- sensors */
/* Capacitive soil probe: reading falls as the soil gets wetter. Two-point calibration in the field:
 * raw value with the probe in dry air and fully in water. */
typedef struct { uint16_t raw_dry, raw_wet; } soil_cal_t;
uint8_t soil_percent(const soil_cal_t *cal, uint16_t raw);          /* 0 = bone dry, 100 = saturated */

/* LDR divider on a 12-bit ADC -> 0..100 % light. */
uint8_t light_percent(uint16_t raw12);

/* Battery through a 100k/100k divider into a 12-bit ADC with 3.3 V full scale -> millivolts. */
uint16_t battery_mv(uint16_t raw12);

/* ---------------------------------------------------------------- irrigation */
typedef struct {
    uint8_t start_below;        /* start watering when soil moisture drops below this % */
    uint8_t stop_above;         /* stop when it rises above this % (must be > start_below) */
    uint16_t max_run_s;         /* one watering never lasts longer than this (stuck sensor / leak) */
    uint16_t min_rest_s;        /* wait at least this long between waterings so water can soak in */
    uint16_t daily_budget_s;    /* total pump time allowed per day (protects the tank and the plants) */
    int16_t max_temp_c10;       /* skip watering in peak heat (water evaporates), tenths of a degree */
    uint8_t max_light_pct;      /* ...and in full midday sun */
} irrig_cfg_t;

typedef enum { IR_IDLE, IR_WATERING, IR_RESTING, IR_LOCKOUT } irrig_state_t;

typedef enum {
    WHY_NONE, WHY_DRY, WHY_WET_ENOUGH, WHY_MAX_RUN, WHY_REST, WHY_BUDGET, WHY_HEAT, WHY_TANK_EMPTY, WHY_SENSOR_FAULT, WHY_MANUAL
} irrig_reason_t;

typedef struct {
    irrig_state_t state;
    uint32_t state_since_s;
    uint32_t used_today_s;
    uint32_t day;               /* day number the budget belongs to */
    irrig_reason_t last_reason;
    uint32_t waterings;
} irrig_t;

typedef struct {
    uint32_t now_s;             /* seconds since epoch or since boot; day = now_s / 86400 */
    uint8_t soil_pct;
    bool soil_ok;               /* false if the probe reads outside its calibrated range */
    int16_t temp_c10;
    uint8_t light_pct;
    bool tank_ok;               /* float switch: false = tank empty */
    int8_t manual;              /* +1 force a watering, -1 force stop, 0 automatic */
} irrig_input_t;

void irrig_init(irrig_t *s, uint32_t now_s);
/* Advances the controller. Returns true if the pump should be ON. */
bool irrig_step(irrig_t *s, const irrig_cfg_t *cfg, const irrig_input_t *in);
const char *irrig_reason_name(irrig_reason_t r);
const char *irrig_state_name(irrig_state_t s);
bool irrig_cfg_valid(const irrig_cfg_t *cfg);

/* ---------------------------------------------------------------- power */
/* How long to deep-sleep before the next check: short when the soil is close to the threshold or the
 * pump just ran, long when everything is wet; longer still on a low battery. */
uint32_t sleep_seconds(const irrig_cfg_t *cfg, const irrig_t *s, uint8_t soil_pct, uint16_t batt_mv);

#endif
