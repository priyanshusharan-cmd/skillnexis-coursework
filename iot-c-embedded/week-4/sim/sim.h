#ifndef SIM_H
#define SIM_H
#include <stdbool.h>
#include <stdint.h>

extern bool sim_verbose;
void sim_open(const char *csv_path, const char *events_path);
void sim_close(void);
void sim_sleep(uint32_t s);
void sim_schedule_command(uint32_t at_s, const char *cmd);
void sim_tank_empty(int from_hour, int to_hour);
void sim_probe_fault(uint32_t from_s, uint32_t to_s);
uint32_t sim_pump_seconds(void);
uint32_t sim_published(void);
const char (*sim_display(void))[22];
const char *sim_clock(uint32_t t);

#endif
