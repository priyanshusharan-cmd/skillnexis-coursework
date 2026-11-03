#define _DEFAULT_SOURCE
/* simavr test bench for the multi-sensor logger.
 *
 * Runs the real build/logger.elf on a simulated ATmega328P at 16 MHz and plays the parts of the hardware:
 *   - LM35 and LDR: analog voltages on ADC0/ADC1
 *   - HC-SR04: watches the trigger pin (PD7) and answers with an echo pulse on PB0 whose width matches the distance
 *   - humidity node: an I2C slave at 0x42 that speaks the same protocol as node/humidity_node.c
 *   - buzzer: records the PD3 pin level
 * The UART output is saved to results/sim-serial.log and checked against what each scenario should produce.
 *
 *   make sim
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <simavr/avr_adc.h>
#include <simavr/avr_ioport.h>
#include <simavr/avr_twi.h>
#include <simavr/avr_uart.h>
#include <simavr/sim_avr.h>
#include <simavr/sim_elf.h>

#define FREQ 16000000UL

typedef struct {
    const char *name;
    uint32_t until_ms;     /* scenario lasts until this simulated time */
    uint32_t temp_mv;      /* LM35 output: 10 mV per degree */
    uint32_t light_mv;     /* LDR divider output */
    uint32_t distance_mm;  /* 0 = nothing in range (no echo) */
    int humidity_tenths;   /* < 0 = node does not answer on I2C */
    const char *expect;    /* alert letters expected by the end of the scenario */
} scenario_t;

static const scenario_t S[] = {
    {"normal",           2000, 250, 3000, 800, 552, "-"},
    {"hot 36.5 C",       4000, 365, 3000, 800, 560, "H"},
    {"cooling 34.5 C",   5000, 345, 3000, 800, 560, "H"},   /* inside the hysteresis band: stays on */
    {"cool + object 6cm",7000, 250, 3000,  60, 548, "N"},
    {"dark 10 %",        9000, 250,  500, 800, 548, "D"},
    {"node offline",    11000, 250, 3000,   0,  -1, "-"},   /* humidity NA, nothing in range */
    {"LM35 unplugged",  12000,   0, 3000, 800, 552, "S"},
};
#define NS (sizeof S / sizeof S[0])

static avr_t *avr;
static const scenario_t *cur = &S[0];
static char line[128];
static int line_len;
static FILE *serial_log;
static int buzzer_on;
static uint8_t last_trigger;
static avr_irq_t *echo_irq, *twi_in;
static int lines_checked, lines_failed, lines_total;
static char last_alerts_seen[NS][16];
static int buzzer_ok[NS], buzzer_bad[NS], humid_ok[NS], humid_bad[NS];

static uint32_t now_ms(void) { return (uint32_t)(avr->cycle / (FREQ / 1000)); }

/* ---------------------------------------------------------------- UART capture */
static void uart_out(struct avr_irq_t *irq, uint32_t value, void *param) {
    (void)irq; (void)param;
    char c = (char)value;
    if (c == '\r') return;
    if (c != '\n') { if (line_len < (int)sizeof line - 1) line[line_len++] = c; return; }
    line[line_len] = 0;
    fprintf(serial_log, "%s\n", line);
    printf("  [%6u ms %-17s buzzer %s] %s\n", now_ms(), cur->name, buzzer_on ? "ON " : "off", line);
    if (line[0] != '#') {
        lines_total++;
        const char *flags = strrchr(line, ',');
        int idx = (int)(cur - S);
        if (flags) snprintf(last_alerts_seen[idx], sizeof last_alerts_seen[idx], "%s", flags + 1);
        int has_alert = flags && strcmp(flags + 1, "-") != 0;
        /* 5th CSV field is humidity: must match what the simulated node is serving, or NA when offline */
        char copy[128], expect_h[16], *f = copy, *field = NULL;
        snprintf(copy, sizeof copy, "%s", line);
        for (int k = 0; k < 5 && f; k++) { field = strsep(&f, ","); }
        if (cur->humidity_tenths < 0) snprintf(expect_h, sizeof expect_h, "NA");
        else snprintf(expect_h, sizeof expect_h, "%d.%d", cur->humidity_tenths / 10, cur->humidity_tenths % 10);
        if (field && strcmp(field, expect_h) == 0) humid_ok[idx]++; else humid_bad[idx]++;
        if (has_alert == buzzer_on) buzzer_ok[idx]++; else buzzer_bad[idx]++;
    }
    line_len = 0;
}

/* ---------------------------------------------------------------- buzzer */
static void buzzer_pin(struct avr_irq_t *irq, uint32_t value, void *param) { (void)irq; (void)param; buzzer_on = (int)value; }

/* ---------------------------------------------------------------- HC-SR04 */
static avr_cycle_count_t echo_low(avr_t *a, avr_cycle_count_t when, void *param) {
    (void)a; (void)when; (void)param;
    avr_raise_irq(echo_irq, 0);
    return 0;
}

static avr_cycle_count_t echo_high(avr_t *a, avr_cycle_count_t when, void *param) {
    (void)when; (void)param;
    uint32_t us = (uint32_t)((cur->distance_mm * 10000ULL + 857) / 1715);  /* inverse of echo_us_to_mm */
    avr_raise_irq(echo_irq, 1);
    avr_cycle_timer_register_usec(a, us, echo_low, NULL);
    return 0;
}

static void trigger_pin(struct avr_irq_t *irq, uint32_t value, void *param) {
    (void)irq; (void)param;
    if (last_trigger && !value && cur->distance_mm) {        /* falling edge of the 10 us trigger */
        avr_cycle_timer_register_usec(avr, 450, echo_high, NULL); /* sensor answers after ~450 us */
    }
    last_trigger = (uint8_t)value;
}

/* ---------------------------------------------------------------- I2C humidity node at 0x42 */
static uint8_t node_selected, node_reg, node_reg_set, node_pos, node_frame[3];

static void node_load(void) {
    uint16_t h = (uint16_t)cur->humidity_tenths;
    node_frame[0] = (uint8_t)h;
    node_frame[1] = (uint8_t)(h >> 8);
    uint8_t crc = 0;
    for (int i = 0; i < 2; i++) {
        crc ^= node_frame[i];
        for (int b = 0; b < 8; b++) crc = (uint8_t)((crc & 0x80) ? (crc << 1) ^ 0x07 : crc << 1);
    }
    node_frame[2] = crc;
    node_pos = 0;
}

static void twi_out(struct avr_irq_t *irq, uint32_t value, void *param) {
    (void)irq; (void)param;
    avr_twi_msg_irq_t v;
    v.u.v = value;
    if (v.u.twi.msg & TWI_COND_STOP) node_selected = 0;
    if (v.u.twi.msg & TWI_COND_START) {
        node_selected = 0;
        if ((v.u.twi.addr >> 1) == 0x42 && cur->humidity_tenths >= 0) {   /* offline node never ACKs */
            node_selected = v.u.twi.addr;
            if (!(v.u.twi.addr & 1)) node_reg_set = 0;                    /* write phase: register byte next */
            avr_raise_irq(twi_in, avr_twi_irq_msg(TWI_COND_ACK, node_selected, 1));
        }
    }
    if (!node_selected) return;
    if (v.u.twi.msg & TWI_COND_WRITE) {
        avr_raise_irq(twi_in, avr_twi_irq_msg(TWI_COND_ACK, node_selected, 1));
        if (!node_reg_set) { node_reg = v.u.twi.data; node_reg_set = 1; node_load(); }
    }
    if (v.u.twi.msg & TWI_COND_READ) {
        uint8_t data = (node_reg == 0x00 && node_pos < 3) ? node_frame[node_pos++] : 0xFF;
        avr_raise_irq(twi_in, avr_twi_irq_msg(TWI_COND_READ, node_selected, data));
    }
}

/* ---------------------------------------------------------------- analog inputs */
static void set_analog(void) {
    avr_raise_irq(avr_io_getirq(avr, AVR_IOCTL_ADC_GETIRQ, ADC_IRQ_ADC0), cur->temp_mv);
    avr_raise_irq(avr_io_getirq(avr, AVR_IOCTL_ADC_GETIRQ, ADC_IRQ_ADC1), cur->light_mv);
}

int main(int argc, char **argv) {
    const char *elf = argc > 1 ? argv[1] : "build/logger.elf";
    elf_firmware_t fw;
    memset(&fw, 0, sizeof fw);
    if (elf_read_firmware(elf, &fw)) { fprintf(stderr, "cannot read %s\n", elf); return 2; }
    avr = avr_make_mcu_by_name("atmega328p");
    avr_init(avr);
    avr_load_firmware(avr, &fw);
    avr->frequency = FREQ;
    avr->avcc = avr->aref = 5000;
    avr->log = LOG_ERROR;

    serial_log = fopen("results/sim-serial.log", "w");
    if (!serial_log) { perror("results/sim-serial.log"); return 2; }

    uint32_t uart_flags = 0;
    avr_ioctl(avr, AVR_IOCTL_UART_GET_FLAGS('0'), &uart_flags);
    uart_flags &= ~AVR_UART_FLAG_STDIO;    /* we print it ourselves */
    avr_ioctl(avr, AVR_IOCTL_UART_SET_FLAGS('0'), &uart_flags);
    avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_UART_GETIRQ('0'), UART_IRQ_OUTPUT), uart_out, NULL);
    avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ('D'), 3), buzzer_pin, NULL);
    avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ('D'), 7), trigger_pin, NULL);
    echo_irq = avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ('B'), 0);
    avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_TWI_GETIRQ(0), TWI_IRQ_OUTPUT), twi_out, NULL);
    twi_in = avr_io_getirq(avr, AVR_IOCTL_TWI_GETIRQ(0), TWI_IRQ_INPUT);

    printf("simavr: %s on atmega328p @ 16 MHz\n", elf);
    set_analog();
    uint32_t end_ms = S[NS - 1].until_ms;
    while (now_ms() < end_ms) {
        int state = avr_run(avr);
        if (state == cpu_Done || state == cpu_Crashed) { fprintf(stderr, "CPU stopped: state %d\n", state); return 3; }
        if (now_ms() >= cur->until_ms && cur < &S[NS - 1]) {
            cur++;
            set_analog();
            printf("---- %u ms: scenario '%s'\n", now_ms(), cur->name);
        }
    }
    fclose(serial_log);

    printf("\nScenario results (alerts shown on the last line of each scenario):\n");
    for (size_t i = 0; i < NS; i++) {
        /* the first line after a scenario change may still carry the previous humidity (read before the switch) */
        int ok = strcmp(last_alerts_seen[i], S[i].expect) == 0 && buzzer_bad[i] == 0 && humid_bad[i] <= 1 && humid_ok[i] > 0;
        lines_checked++;
        if (!ok) lines_failed++;
        printf("  %-18s expected %-3s got %-4s buzzer ok %d/%d  humidity ok %d/%d  %s\n", S[i].name, S[i].expect, last_alerts_seen[i],
               buzzer_ok[i], buzzer_ok[i] + buzzer_bad[i], humid_ok[i], humid_ok[i] + humid_bad[i], ok ? "PASS" : "FAIL");
    }
    printf("%d log lines, %d/%d scenarios passed\n", lines_total, lines_checked - lines_failed, lines_checked);
    return lines_failed != 0;
}
