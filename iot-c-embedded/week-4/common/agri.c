#include "agri.h"

uint8_t soil_percent(const soil_cal_t *cal, uint16_t raw) {
    if (cal->raw_dry <= cal->raw_wet) return 0;          /* bad calibration */
    if (raw >= cal->raw_dry) return 0;
    if (raw <= cal->raw_wet) return 100;
    uint32_t span = (uint32_t)(cal->raw_dry - cal->raw_wet);
    return (uint8_t)(((uint32_t)(cal->raw_dry - raw) * 100u + span / 2u) / span);
}

uint8_t light_percent(uint16_t raw12) {
    if (raw12 > 4095) raw12 = 4095;
    return (uint8_t)(((uint32_t)raw12 * 100u + 2047u) / 4095u);
}

uint16_t battery_mv(uint16_t raw12) {
    if (raw12 > 4095) raw12 = 4095;
    return (uint16_t)(((uint32_t)raw12 * 3300u * 2u + 2047u) / 4095u);  /* x2 for the divider */
}

bool irrig_cfg_valid(const irrig_cfg_t *c) {
    return c->stop_above > c->start_below && c->stop_above <= 100 && c->max_run_s > 0 && c->daily_budget_s >= c->max_run_s;
}

void irrig_init(irrig_t *s, uint32_t now_s) {
    s->state = IR_IDLE;
    s->state_since_s = now_s;
    s->used_today_s = 0;
    s->day = now_s / 86400u;
    s->last_reason = WHY_NONE;
    s->waterings = 0;
}

static void go(irrig_t *s, irrig_state_t st, uint32_t now, irrig_reason_t why) {
    s->state = st;
    s->state_since_s = now;
    s->last_reason = why;
}

bool irrig_step(irrig_t *s, const irrig_cfg_t *c, const irrig_input_t *in) {
    uint32_t now = in->now_s;
    if (now / 86400u != s->day) {            /* new day: refill the budget */
        s->day = now / 86400u;
        s->used_today_s = 0;
        if (s->state == IR_LOCKOUT && s->last_reason == WHY_BUDGET) go(s, IR_IDLE, now, WHY_NONE);
    }
    uint32_t in_state = now - s->state_since_s;

    if (s->state == IR_WATERING) {
        uint32_t ran = in_state;
        irrig_reason_t stop = WHY_NONE;
        if (in->manual < 0) stop = WHY_MANUAL;
        else if (!in->tank_ok) stop = WHY_TANK_EMPTY;          /* never run the pump dry */
        else if (!in->soil_ok && in->manual <= 0) stop = WHY_SENSOR_FAULT;
        else if (ran >= c->max_run_s) stop = WHY_MAX_RUN;
        else if (s->used_today_s + ran >= c->daily_budget_s) stop = WHY_BUDGET;
        else if (in->soil_ok && in->soil_pct >= c->stop_above && in->manual <= 0) stop = WHY_WET_ENOUGH;
        if (stop == WHY_NONE) return true;
        s->used_today_s += ran;
        if (stop == WHY_TANK_EMPTY || stop == WHY_SENSOR_FAULT) go(s, IR_LOCKOUT, now, stop);
        else if (stop == WHY_BUDGET) go(s, IR_LOCKOUT, now, stop);
        else go(s, IR_RESTING, now, stop);
        return false;
    }

    if (s->state == IR_LOCKOUT) {
        /* faults clear on their own once fixed; the budget lockout clears at midnight (above) */
        bool fixed = (s->last_reason == WHY_TANK_EMPTY && in->tank_ok) || (s->last_reason == WHY_SENSOR_FAULT && in->soil_ok);
        if (!fixed && in->manual <= 0) return false;
        if (!fixed && s->last_reason == WHY_BUDGET) return false;   /* manual cannot exceed the budget */
        go(s, IR_IDLE, now, WHY_NONE);   /* fault cleared (or manual override): decide afresh below */
        in_state = 0;
    }

    if (s->state == IR_RESTING && in_state < c->min_rest_s && in->manual <= 0) {
        s->last_reason = WHY_REST;
        return false;
    }
    if (s->state == IR_RESTING) go(s, IR_IDLE, now, s->last_reason);

    /* IDLE: decide whether to start */
    if (!in->tank_ok) { go(s, IR_LOCKOUT, now, WHY_TANK_EMPTY); return false; }
    if (s->used_today_s >= c->daily_budget_s) { go(s, IR_LOCKOUT, now, WHY_BUDGET); return false; }
    if (in->manual > 0) { go(s, IR_WATERING, now, WHY_MANUAL); s->waterings++; return true; }
    if (!in->soil_ok) { go(s, IR_LOCKOUT, now, WHY_SENSOR_FAULT); return false; }
    if (in->soil_pct >= c->start_below) { s->last_reason = WHY_NONE; return false; }
    /* dry, but wait out peak heat and full sun unless the soil is critically dry (< half the threshold) */
    bool critical = in->soil_pct < c->start_below / 2u;
    if (!critical && (in->temp_c10 > c->max_temp_c10 || in->light_pct > c->max_light_pct)) { s->last_reason = WHY_HEAT; return false; }
    go(s, IR_WATERING, now, WHY_DRY);
    s->waterings++;
    return true;
}

const char *irrig_reason_name(irrig_reason_t r) {
    static const char *const n[] = {"none", "dry", "wet-enough", "max-run", "resting", "budget", "heat", "tank-empty", "sensor-fault", "manual"};
    return (unsigned)r < sizeof n / sizeof n[0] ? n[r] : "?";
}

const char *irrig_state_name(irrig_state_t s) {
    static const char *const n[] = {"idle", "watering", "resting", "lockout"};
    return (unsigned)s < 4 ? n[s] : "?";
}

uint32_t sleep_seconds(const irrig_cfg_t *c, const irrig_t *s, uint8_t soil, uint16_t batt_mv) {
    uint32_t t;
    if (s->state == IR_WATERING) return 0;                       /* stay awake while the pump runs */
    if (s->state == IR_RESTING) t = c->min_rest_s;               /* wake when the rest period ends */
    else if (soil < c->start_below + 10u) t = 5 * 60;            /* close to the threshold: check often */
    else if (soil < c->stop_above) t = 15 * 60;
    else t = 30 * 60;                                            /* wet: check rarely */
    if (batt_mv < 3400) t *= 2;                                  /* low battery: stretch the intervals */
    if (batt_mv < 3200) t = 2 * 60 * 60;                         /* critical: once every two hours */
    return t;
}
