#ifndef APP_H
#define APP_H
#include <stdint.h>

#include "../common/agri.h"

/* Kept in RTC memory on the ESP32 (RTC_DATA_ATTR), so it survives deep sleep. */
typedef struct {
    uint32_t magic;
    uint32_t boots;
    irrig_t irrig;
    uint32_t awake_s_total, sleep_s_total, pump_s_total;
} app_retained_t;

typedef struct {
    irrig_cfg_t irrig;
    soil_cal_t soil;
    uint32_t sample_period_s;   /* how often the sensor task samples while awake */
    uint32_t min_awake_samples; /* samples to take before the node may sleep */
} app_config_t;

extern const app_config_t APP_DEFAULT_CONFIG;

/* Runs one wake cycle: creates the sensor, control, display and network tasks, waits until the control
 * task decides the node may sleep, deletes the tasks and returns the number of seconds to deep-sleep.
 * Must be called from a FreeRTOS task. */
uint32_t app_wake_cycle(app_retained_t *ret, const app_config_t *cfg);

#endif
