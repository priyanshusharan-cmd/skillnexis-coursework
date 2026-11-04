/* The node's FreeRTOS tasks.
 *
 *   sensor_task   samples every sample_period_s, sends hal_sample_t to the control queue
 *   control_task  converts readings, runs the irrigation state machine, drives the pump relay,
 *                 updates the shared status (mutex), and decides when the node may sleep
 *   display_task  redraws the OLED from the shared status once per period
 *   net_task      publishes status/telemetry, handles commands (water, stop, ota=<url>)
 *
 * Synchronisation: a queue (sensor -> control), a mutex around the shared status, and an event group
 * for "publish now", "published" and "sleep now". */
#include "app.h"

#include <stdio.h>
#include <string.h>

#include "FreeRTOS.h"
#include "event_groups.h"
#include "hal.h"
#include "queue.h"
#include "semphr.h"
#include "task.h"

const app_config_t APP_DEFAULT_CONFIG = {
    .irrig = {.start_below = 35, .stop_above = 60, .max_run_s = 300, .min_rest_s = 1800, .daily_budget_s = 1200,
              .max_temp_c10 = 340, .max_light_pct = 85},
    .soil = {.raw_dry = 3000, .raw_wet = 1200},
    .sample_period_s = 2,
    .min_awake_samples = 3,
};

#define EV_PUBLISH (1u << 0)
#define EV_PUBLISHED (1u << 1)
#define EV_SLEEP (1u << 2)
#define EV_STOP (1u << 3)

typedef struct {
    uint8_t soil, light, humidity;
    int16_t temp_c10;
    uint16_t batt_mv;
    bool pump, tank_ok, soil_ok;
    uint32_t sleep_s;
    uint32_t seq;
} status_t;

static struct {
    const app_config_t *cfg;
    app_retained_t *ret;
    QueueHandle_t samples;
    SemaphoreHandle_t lock;
    EventGroupHandle_t ev;
    status_t st;
    volatile int8_t manual;
    TaskHandle_t tasks[4];
} g;

static void log_fmt(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
#include <stdarg.h>
static void log_fmt(const char *fmt, ...) {
    char b[160];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(b, sizeof b, fmt, ap);
    va_end(ap);
    hal_log(b);
}

static bool stopping(void) { return (xEventGroupGetBits(g.ev) & EV_STOP) != 0; }

static void sensor_task(void *arg) {
    (void)arg;
    while (!stopping()) {
        hal_sample_t s;
        if (hal_read(&s)) xQueueSend(g.samples, &s, 0);
        hal_delay_s(g.cfg->sample_period_s);
    }
    vTaskSuspend(NULL);
}

static void control_task(void *arg) {
    (void)arg;
    uint32_t processed = 0;
    for (;;) {
        hal_sample_t s;
        if (xQueueReceive(g.samples, &s, portMAX_DELAY) != pdTRUE) continue;
        processed++;
        irrig_input_t in = {
            .now_s = hal_now_s(),
            .soil_pct = soil_percent(&g.cfg->soil, s.soil_raw),
            /* a probe reading far outside its calibration means it is unplugged or shorted */
            .soil_ok = s.soil_raw > g.cfg->soil.raw_wet - 400 && s.soil_raw < g.cfg->soil.raw_dry + 400,
            .temp_c10 = s.temp_ok ? s.temp_c10 : 250,
            .light_pct = light_percent(s.light_raw),
            .tank_ok = s.tank_ok,
            .manual = g.manual,
        };
        g.manual = 0;
        irrig_state_t before = g.ret->irrig.state;
        bool pump = irrig_step(&g.ret->irrig, &g.cfg->irrig, &in);
        hal_pump(pump);
        if (g.ret->irrig.state != before)
            log_fmt("state %s -> %s (%s) soil=%u%%", irrig_state_name(before), irrig_state_name(g.ret->irrig.state),
                    irrig_reason_name(g.ret->irrig.last_reason), in.soil_pct);

        uint16_t batt = battery_mv(s.batt_raw);
        xSemaphoreTake(g.lock, portMAX_DELAY);
        g.st.soil = in.soil_pct;
        g.st.light = in.light_pct;
        g.st.humidity = s.humidity;
        g.st.temp_c10 = in.temp_c10;
        g.st.batt_mv = batt;
        g.st.pump = pump;
        g.st.tank_ok = in.tank_ok;
        g.st.soil_ok = in.soil_ok;
        g.st.seq++;
        xSemaphoreGive(g.lock);

        if (processed >= g.cfg->min_awake_samples && !pump) {
            uint32_t sleep_s = sleep_seconds(&g.cfg->irrig, &g.ret->irrig, in.soil_pct, batt);
            if (sleep_s) {
                xSemaphoreTake(g.lock, portMAX_DELAY);
                g.st.sleep_s = sleep_s;
                xSemaphoreGive(g.lock);
                /* tell the network task to send the final status, wait (bounded) for it, then sleep */
                xEventGroupSetBits(g.ev, EV_PUBLISH);
                xEventGroupWaitBits(g.ev, EV_PUBLISHED, pdTRUE, pdTRUE, pdMS_TO_TICKS(5000));
                xEventGroupSetBits(g.ev, EV_SLEEP);
                vTaskSuspend(NULL);
            }
        }
    }
}

static void snapshot(status_t *out) {
    xSemaphoreTake(g.lock, portMAX_DELAY);
    *out = g.st;
    xSemaphoreGive(g.lock);
}

static void display_task(void *arg) {
    (void)arg;
    while (!stopping()) {
        status_t s;
        snapshot(&s);
        char lines[4][22], tmp[48];
        snprintf(tmp, sizeof tmp, "SOIL %3u%% %s", s.soil, s.pump ? "PUMP ON" : irrig_state_name(g.ret->irrig.state));
        snprintf(lines[0], 22, "%.21s", tmp);
        snprintf(tmp, sizeof tmp, "TEMP %3d.%dC HUM %2u%%", s.temp_c10 / 10, (s.temp_c10 < 0 ? -s.temp_c10 : s.temp_c10) % 10, s.humidity);
        snprintf(lines[1], 22, "%.21s", tmp);
        snprintf(tmp, sizeof tmp, "LIGHT %3u%% TANK %s", s.light, s.tank_ok ? "OK" : "LOW");
        snprintf(lines[2], 22, "%.21s", tmp);
        snprintf(tmp, sizeof tmp, "BAT %u.%02uV H2O %lus", s.batt_mv / 1000, s.batt_mv % 1000 / 10, (unsigned long)g.ret->irrig.used_today_s);
        snprintf(lines[3], 22, "%.21s", tmp);
        hal_display(lines);
        hal_delay_s(g.cfg->sample_period_s);
    }
    vTaskSuspend(NULL);
}

static void publish_status(void) {
    status_t s;
    snapshot(&s);
    char json[256];
    snprintf(json, sizeof json,
             "{\"seq\":%lu,\"soil\":%u,\"temp\":%d.%d,\"hum\":%u,\"light\":%u,\"batt_mv\":%u,\"pump\":%s,\"tank\":%s,"
             "\"state\":\"%s\",\"reason\":\"%s\",\"water_today_s\":%lu,\"boots\":%lu,\"sleep_s\":%lu}",
             (unsigned long)s.seq, s.soil, s.temp_c10 / 10, (s.temp_c10 < 0 ? -s.temp_c10 : s.temp_c10) % 10, s.humidity, s.light,
             s.batt_mv, s.pump ? "true" : "false", s.tank_ok ? "true" : "false", irrig_state_name(g.ret->irrig.state),
             irrig_reason_name(g.ret->irrig.last_reason), (unsigned long)g.ret->irrig.used_today_s, (unsigned long)g.ret->boots,
             (unsigned long)s.sleep_s);
    hal_publish("state", json, true);
}

static void net_task(void *arg) {
    (void)arg;
    bool last_pump = false;
    while (!stopping()) {
        char cmd[160];
        if (hal_poll_command(cmd, sizeof cmd)) {
            log_fmt("command: %s", cmd);
            if (strcmp(cmd, "water") == 0) g.manual = 1;
            else if (strcmp(cmd, "stop") == 0) g.manual = -1;
            else if (strncmp(cmd, "ota=", 4) == 0) {
                hal_pump(false);                 /* never leave the pump running through a reboot */
                if (!hal_ota(cmd + 4)) log_fmt("OTA failed, staying on the current firmware");
            }
        }
        status_t s;
        snapshot(&s);
        EventBits_t bits = xEventGroupGetBits(g.ev);
        if ((bits & EV_PUBLISH) || s.pump != last_pump) {   /* publish on every pump change and before sleep */
            publish_status();
            last_pump = s.pump;
            if (bits & EV_PUBLISH) {
                xEventGroupClearBits(g.ev, EV_PUBLISH);
                xEventGroupSetBits(g.ev, EV_PUBLISHED);
            }
        }
        vTaskDelay(1);
    }
    vTaskSuspend(NULL);
}

uint32_t app_wake_cycle(app_retained_t *ret, const app_config_t *cfg) {
    memset(&g, 0, sizeof g);
    g.cfg = cfg;
    g.ret = ret;
    g.samples = xQueueCreate(8, sizeof(hal_sample_t));
    g.lock = xSemaphoreCreateMutex();
    g.ev = xEventGroupCreate();
    uint32_t woke = hal_now_s();

    xTaskCreate(control_task, "control", 4096, NULL, 4, &g.tasks[0]);   /* highest: owns the pump */
    xTaskCreate(sensor_task, "sensor", 3072, NULL, 3, &g.tasks[1]);
    xTaskCreate(net_task, "net", 4096, NULL, 2, &g.tasks[2]);
    xTaskCreate(display_task, "display", 3072, NULL, 1, &g.tasks[3]);

    xEventGroupWaitBits(g.ev, EV_SLEEP, pdFALSE, pdTRUE, portMAX_DELAY);
    hal_pump(false);
    xEventGroupSetBits(g.ev, EV_STOP);
    hal_delay_s(g.cfg->sample_period_s);   /* let the looping tasks notice EV_STOP and park themselves */
    for (int i = 0; i < 4; i++) vTaskDelete(g.tasks[i]);
    vQueueDelete(g.samples);
    vSemaphoreDelete(g.lock);
    uint32_t sleep_s = g.st.sleep_s;
    vEventGroupDelete(g.ev);
    ret->awake_s_total += hal_now_s() - woke;
    ret->sleep_s_total += sleep_s;
    return sleep_s;
}
