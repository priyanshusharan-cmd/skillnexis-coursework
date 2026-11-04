/* Runs the node firmware (app/app.c) on the FreeRTOS POSIX port for three simulated days.
 *
 *   day 1  hot and sunny            day 2  cloudy and cooler (less watering)
 *   day 2 14:00-17:00  tank empty (pump must not run)
 *   day 3 02:00-02:30  soil probe unplugged (must lock out, then recover)
 *   day 3 07:00        "water" command over MQTT (manual watering)
 *   day 3 12:00        "ota=..." command
 *
 * Output: results/sim-telemetry.csv, results/sim-events.csv, and a pass/fail summary of the safety rules. */
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>

#include "../app/app.h"
#include "../app/hal.h"
#include "FreeRTOS.h"
#include "sim.h"
#include "task.h"

bool sim_verbose;
#define DAYS 3

static app_retained_t ret;
static app_config_t cfg;
static int failures;
static uint32_t wakes, max_awake_s, budget_violations;

void vAssertCalled(const char *f, int l) { fprintf(stderr, "configASSERT failed %s:%d\n", f, l); fflush(NULL); _exit(9); }

static void check(const char *what, int ok) { printf("  %-62s %s\n", what, ok ? "PASS" : "FAIL"); if (!ok) failures++; }

static void supervisor(void *arg) {
    (void)arg;
    cfg = APP_DEFAULT_CONFIG;
    cfg.sample_period_s = 2;                    /* same as the real node */
    irrig_init(&ret.irrig, 0);
    sim_open("results/sim-telemetry.csv", "results/sim-events.csv");
    sim_tank_empty(24 + 14, 24 + 17);
    sim_probe_fault(2 * 86400 + 2 * 3600, 2 * 86400 + 2 * 3600 + 1800);
    sim_schedule_command(2 * 86400 + 7 * 3600, "water");
    sim_schedule_command(2 * 86400 + 12 * 3600, "ota=https://example.com/agri-node-v1.1.bin");
    uint32_t prev_day = 0, used_prev = 0;
    while (hal_now_s() < DAYS * 86400u) {
        ret.boots++;
        wakes++;
        uint32_t start = hal_now_s();
        uint32_t sleep_s = app_wake_cycle(&ret, &cfg);
        uint32_t awake = hal_now_s() - start;
        if (awake > max_awake_s) max_awake_s = awake;
        if (ret.irrig.used_today_s > cfg.irrig.daily_budget_s) budget_violations++;
        if (hal_now_s() / 86400 != prev_day) { used_prev = 0; prev_day = hal_now_s() / 86400; }
        (void)used_prev;
        sim_sleep(sleep_s);                     /* on the ESP32: esp_deep_sleep_start() */
    }
    sim_close();

    /* ---------------- analyse the run */
    FILE *f = fopen("results/sim-events.csv", "r");
    char line[512];
    int pump_on_while_tank_empty = 0, max_run_violation = 0, waterings = 0, manual_seen = 0, fault_lockout = 0, ota_seen = 0;
    uint32_t on_at = 0, last_off = 0, min_gap = UINT32_MAX;
    int pump_state = 0;
    while (f && fgets(line, sizeof line, f)) {
        unsigned t;
        char ev[32];
        if (sscanf(line, "%u,%31[^,]", &t, ev) != 2) continue;
        if (!strcmp(ev, "pump_on")) {
            waterings++;
            if (t / 3600 >= 24 + 14 && t / 3600 < 24 + 17) pump_on_while_tank_empty++;
            if (last_off && t - last_off < min_gap && !strstr(line, "manual")) min_gap = t - last_off;
            on_at = t; pump_state = 1;
        } else if (!strcmp(ev, "pump_off")) {
            if (pump_state && t - on_at > cfg.irrig.max_run_s + cfg.sample_period_s) max_run_violation++;
            last_off = t; pump_state = 0;
        } else if (strstr(line, "(manual)")) manual_seen = 1;
        else if (strstr(line, "(sensor-fault)")) fault_lockout = 1;
        else if (strstr(line, "OTA requested")) ota_seen = 1;
    }
    if (f) fclose(f);
    double awake_frac = (double)ret.awake_s_total / (ret.awake_s_total + ret.sleep_s_total);
    printf("\n3 simulated days: %u wake-ups, %d waterings, pump ran %u s, awake %.2f%% of the time (longest wake %u s)\n",
           wakes, waterings, sim_pump_seconds(), awake_frac * 100, max_awake_s);
    printf("Last OLED frame: | %s | %s | %s | %s |\n\n", sim_display()[0], sim_display()[1], sim_display()[2], sim_display()[3]);
    check("pump never ran while the tank was empty (day 2 14:00-17:00)", pump_on_while_tank_empty == 0);
    check("no watering longer than max_run_s (300 s)", max_run_violation == 0);
    check("daily water budget never exceeded", budget_violations == 0);
    check("unplugged probe caused a sensor-fault lockout", fault_lockout);
    check("MQTT 'water' command started a manual watering", manual_seen);
    check("MQTT 'ota=' command reached the OTA handler", ota_seen);
    check("node slept more than 95% of the time", awake_frac < 0.05);
    check("soil was watered at least once per day", waterings >= DAYS);
    printf("\n%d failure(s)\n", failures);
    /* _exit, not exit: exit() runs atexit/stdio teardown from inside a task thread, which can deadlock the
     * FreeRTOS POSIX port (its scheduler thread still owns signal handling). Flush, then leave immediately. */
    fflush(NULL);
    _exit(failures != 0);
}

int main(int argc, char **argv) {
    sim_verbose = argc > 1 && !strcmp(argv[1], "-v");
    srand(42);
    xTaskCreate(supervisor, "super", 8192, NULL, 5, NULL);
    vTaskStartScheduler();
    return 1;
}
