/* Simulated hardware for app/app.c on the FreeRTOS POSIX port.
 *
 * Clock: 1 FreeRTOS tick (1 ms of real time) = SIM_S_PER_TICK simulated seconds, so three days run in
 * a few seconds. Deep sleep is "instant": the clock jumps forward while the soil model keeps evolving.
 *
 * Soil model: moisture falls through evapotranspiration (faster when it is hot and sunny) and rises
 * while the pump runs. Sensors return raw ADC values derived from the model through the same
 * calibration the firmware uses, so the conversion code is exercised too. */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../app/hal.h"
#include "FreeRTOS.h"
#include "task.h"
#include "sim.h"

#define SIM_S_PER_TICK 1u

static double soil = 52.0;          /* % volumetric, the "truth" the probe measures */
static bool pump_on;
static uint32_t offset_s;           /* simulated seconds added by deep sleep */
static uint32_t last_model_s;
static FILE *csv, *events;
static struct { uint32_t at; char cmd[160]; } cmds[8];   /* scheduled MQTT commands, in time order */
static unsigned n_cmds, next_cmd;
static uint32_t pump_s, published, ota_requests;
static int tank_empty_from = -1, tank_empty_to = -1;
static uint32_t probe_fault_from = UINT32_MAX, probe_fault_to = 0;

uint32_t hal_now_s(void) { return offset_s + (uint32_t)xTaskGetTickCount() * SIM_S_PER_TICK; }

static double hour_of(uint32_t t) { return fmod(t / 3600.0, 24.0); }

static void weather(uint32_t t, double *temp_c, double *light) {
    const double pi = 3.14159265358979;
    double h = hour_of(t), day = t / 86400.0;
    double cloud = (day > 1.0 && day < 2.0) ? 0.5 - 0.5 * cos(2 * pi * (day - 1.0)) : 0.0;   /* smooth cloudy spell on day 2 */
    double sun = sin((h - 6.0) / 12.0 * pi);                                                /* 0 at 6:00 and 18:00 */
    *light = sun > 0 ? fmin(100.0, 100.0 * sun * (1.0 - 0.45 * cloud)) : 0.0;
    *temp_c = 24.0 + 11.0 * sin((h - 9.0) / 24.0 * 2 * pi) - 4.0 * cloud;
}

/* advance the soil model to time t */
static void model_to(uint32_t t) {
    while (last_model_s < t) {
        uint32_t step = t - last_model_s > 60 ? 60 : t - last_model_s;
        double temp, light;
        weather(last_model_s, &temp, &light);
        double et_per_h = 0.35 + 0.045 * fmax(0.0, temp - 15.0) + 0.02 * light; /* % per hour */
        soil -= et_per_h * step / 3600.0 * (soil / 50.0);                     /* drier soil loses water slower */
        if (pump_on) soil += 0.10 * step;                                     /* 6 % per minute of pumping */
        if (soil > 95) soil = 95;
        if (soil < 3) soil = 3;
        last_model_s += step;
    }
}

void hal_delay_s(uint32_t s) { vTaskDelay(s / SIM_S_PER_TICK ? s / SIM_S_PER_TICK : 1); }

bool hal_read(hal_sample_t *o) {
    uint32_t t = hal_now_s();
    model_to(t);
    double temp, light;
    weather(t, &temp, &light);
    double noise = ((rand() % 21) - 10) / 10.0;                               /* +-1 % sensor noise */
    double pct = fmax(0, fmin(100, soil + noise));
    o->soil_raw = (uint16_t)(3000 - pct / 100.0 * 1800);                     /* inverse of the 3000/1200 calibration */
    if (t >= probe_fault_from && t < probe_fault_to) o->soil_raw = 4095;      /* probe unplugged */
    o->light_raw = (uint16_t)(light / 100.0 * 4095);
    o->temp_c10 = (int16_t)lround(temp * 10);
    o->humidity = (uint8_t)fmax(20, fmin(95, 85 - 1.5 * (temp - 20)));
    o->batt_raw = 2420;                                                       /* ~3.9 V */
    o->temp_ok = true;
    int hour_abs = (int)(t / 3600);
    o->tank_ok = !(hour_abs >= tank_empty_from && hour_abs < tank_empty_to);
    if (csv) fprintf(csv, "%u,%.2f,%.1f,%.0f,%d,%d\n", t, soil, temp, light, pump_on, o->tank_ok);
    return true;
}

void hal_pump(bool on) {
    uint32_t t = hal_now_s();
    model_to(t);
    static uint32_t on_since;
    if (on && !pump_on) { on_since = t; if (events) fprintf(events, "%u,pump_on,%.1f\n", t, soil); }
    if (!on && pump_on) { pump_s += t - on_since; if (events) fprintf(events, "%u,pump_off,%.1f\n", t, soil); }
    pump_on = on;
}

static char last_lines[4][22];
void hal_display(const char lines[4][22]) { memcpy(last_lines, lines, sizeof last_lines); }

bool hal_publish(const char *topic, const char *payload, bool retain) {
    (void)retain;
    published++;
    if (sim_verbose) printf("[%s] mqtt farm/node-01/%s %s\n", sim_clock(hal_now_s()), topic, payload);
    if (events) fprintf(events, "%u,publish,\"%s\"\n", hal_now_s(), payload);
    return true;
}

bool hal_poll_command(char *buf, unsigned size) {
    /* like a retained/queued MQTT message: delivered at the first wake-up after it was sent */
    if (next_cmd >= n_cmds || hal_now_s() < cmds[next_cmd].at) return false;
    snprintf(buf, size, "%s", cmds[next_cmd++].cmd);
    return true;
}

void hal_log(const char *msg) {
    printf("[%s] %s\n", sim_clock(hal_now_s()), msg);
    if (events) fprintf(events, "%u,log,\"%s\"\n", hal_now_s(), msg);
}

bool hal_ota(const char *url) {
    ota_requests++;
    hal_log(url[0] ? "OTA requested (simulated: no flash to write)" : "OTA URL missing");
    return false;
}

/* ---------------------------------------------------------------- used by main_sim.c */
void sim_sleep(uint32_t s) {
    model_to(hal_now_s() + s);       /* soil keeps drying while the node sleeps */
    offset_s += s;
}

void sim_open(const char *csv_path, const char *events_path) {
    csv = fopen(csv_path, "w");
    events = fopen(events_path, "w");
    if (csv) fprintf(csv, "t_s,soil_true_pct,temp_c,light_pct,pump,tank_ok\n");
    if (events) fprintf(events, "t_s,event,detail\n");
}

void sim_close(void) { if (csv) fclose(csv); if (events) fclose(events); }
void sim_schedule_command(uint32_t at_s, const char *cmd) {
    if (n_cmds < sizeof cmds / sizeof cmds[0]) { cmds[n_cmds].at = at_s; snprintf(cmds[n_cmds].cmd, sizeof cmds[0].cmd, "%s", cmd); n_cmds++; }
}
void sim_tank_empty(int from_hour, int to_hour) { tank_empty_from = from_hour; tank_empty_to = to_hour; }
void sim_probe_fault(uint32_t from_s, uint32_t to_s) { probe_fault_from = from_s; probe_fault_to = to_s; }
uint32_t sim_pump_seconds(void) { return pump_s; }
uint32_t sim_published(void) { return published; }
const char (*sim_display(void))[22] { return last_lines; }

const char *sim_clock(uint32_t t) {
    static char b[32];
    snprintf(b, sizeof b, "day %u %02u:%02u", t / 86400 + 1, t % 86400 / 3600, t % 3600 / 60);
    return b;
}
