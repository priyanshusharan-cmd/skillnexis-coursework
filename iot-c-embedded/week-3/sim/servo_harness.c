/* simavr test bench for avr/servo_oled.c.
 *  - types angle commands into the UART like a person in a serial terminal
 *  - measures every PWM pulse on D9 (OC1A): width and period
 *  - plays an SSD1306 OLED at I2C 0x3C and keeps its 128x64 framebuffer, saved as PGM images
 */
#define _DEFAULT_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <simavr/avr_ioport.h>
#include <simavr/avr_timer.h>
#include <simavr/avr_twi.h>
#include <simavr/avr_uart.h>
#include <simavr/sim_avr.h>
#include <simavr/sim_elf.h>

#define FREQ 16000000ULL

static avr_t *avr;
static avr_irq_t *uart_in, *twi_in;

/* ---------------------------------------------------------------- commands typed into the terminal */
typedef struct { uint32_t at_ms; const char *text; int expect_angle; } cmd_t;  /* -1 = expect ERR */
static const cmd_t CMDS[] = {
    {150, "0", 0}, {350, "90", 90}, {550, "180", 180}, {750, "45", 45},
    {950, "abc", -1}, {1150, "200", -1}, {1350, "  135 ", 135}, {1550, "1234567890", -1},
};
#define NCMD (sizeof CMDS / sizeof CMDS[0])
static size_t cmd_idx, char_idx;
static char pending[32];

static avr_cycle_count_t type_next_char(avr_t *a, avr_cycle_count_t when, void *param) {
    (void)a; (void)param;
    if (!pending[char_idx]) return 0;
    avr_raise_irq(uart_in, (uint8_t)pending[char_idx++]);
    return when + FREQ / 5760;   /* one character time at 57600 baud (10 bits) */
}

/* ---------------------------------------------------------------- UART output */
static char line[128];
static int line_len;
static char replies[NCMD + 1][128];
static int n_replies;

static void uart_out(struct avr_irq_t *irq, uint32_t v, void *param) {
    (void)irq; (void)param;
    if (v == '\r') return;
    if (v != '\n') { if (line_len < 127) line[line_len++] = (char)v; return; }
    line[line_len] = 0;
    printf("  [%5llu ms] serial: %s\n", (unsigned long long)(avr->cycle * 1000 / FREQ), line);
    if (n_replies <= (int)NCMD) snprintf(replies[n_replies++], sizeof replies[0], "%s", line);
    line_len = 0;
}

/* ---------------------------------------------------------------- PWM measurement
 * simavr 1.6 does not draw the fast-PWM waveform on the OC1A pin; it reports the compare value through
 * Timer1's PWM IRQ instead. The pulse width and period are therefore computed from what the firmware
 * programmed, exactly as the hardware would produce them: high for OCR1A+1 ticks, period ICR1+1 ticks,
 * at 16 MHz / 8 = 2 MHz. The mode, prescaler, output-compare and pin-direction bits are checked too. */
static uint32_t last_width_us, last_period_us, pulses;
static uint32_t ocr1a;

static void pwm_value(struct avr_irq_t *irq, uint32_t v, void *param) { (void)irq; (void)param; ocr1a = v; pulses++; }

static void read_pwm(void) {
    uint8_t tccr1a = avr->data[0x80], tccr1b = avr->data[0x81];
    uint16_t icr1 = (uint16_t)(avr->data[0x86] | avr->data[0x87] << 8);
    uint16_t ocr = (uint16_t)(avr->data[0x88] | avr->data[0x89] << 8);
    int mode14 = (tccr1a & 0x03) == 0x02 && (tccr1b & 0x18) == 0x18;   /* WGM13:0 = 1110 */
    int div8 = (tccr1b & 0x07) == 0x02;
    int oc1a_on = (tccr1a & 0xC0) == 0x80 && (avr->data[0x24] & 0x02); /* COM1A = 10 and DDRB1 output */
    if (getenv("PWM_DEBUG")) printf("    pwm regs: TCCR1A=%02x TCCR1B=%02x ICR1=%u OCR1A=%u irq=%u DDRB=%02x\n", tccr1a, tccr1b, icr1, ocr, ocr1a, avr->data[0x24]);
    if (!mode14 || !div8 || !oc1a_on || ocr != ocr1a) { last_width_us = last_period_us = 0; return; }
    last_width_us = (ocr + 1u) / 2u;
    last_period_us = (icr1 + 1u) / 2u;
}

/* ---------------------------------------------------------------- SSD1306 */
static uint8_t fb[8][128];
static uint8_t oled_sel, ctrl_seen, data_mode, col0, col1 = 127, page0, page1 = 7, col, page;
static uint8_t cmd_pending, cmd_args[2], cmd_nargs, cmd_have;
static int display_on;

static int args_for(uint8_t c) {
    switch (c) {
    case 0x21: case 0x22: return 2;
    case 0x20: case 0x81: case 0xD5: case 0xA8: case 0xD3: case 0x8D: case 0xDA: case 0xD9: case 0xDB: return 1;
    default: return 0;
    }
}

static void oled_command(uint8_t b) {
    if (cmd_nargs) {
        cmd_args[cmd_have++] = b;
        if (cmd_have < cmd_nargs) return;
        if (cmd_pending == 0x21) { col0 = cmd_args[0] & 127; col1 = cmd_args[1] & 127; col = col0; }
        if (cmd_pending == 0x22) { page0 = cmd_args[0] & 7; page1 = cmd_args[1] & 7; page = page0; }
        cmd_nargs = 0;
        return;
    }
    if (b == 0xAF) display_on = 1;
    if (b == 0xAE) display_on = 0;
    cmd_pending = b;
    cmd_have = 0;
    cmd_nargs = (uint8_t)args_for(b);
}

static void oled_data(uint8_t b) {
    fb[page][col] = b;
    if (col == col1) { col = col0; page = page == page1 ? page0 : (uint8_t)(page + 1); }
    else col++;
}

static void twi_out(struct avr_irq_t *irq, uint32_t value, void *param) {
    (void)irq; (void)param;
    avr_twi_msg_irq_t v;
    v.u.v = value;
    if (v.u.twi.msg & TWI_COND_STOP) oled_sel = 0;
    if (v.u.twi.msg & TWI_COND_START) {
        oled_sel = 0;
        if ((v.u.twi.addr >> 1) == 0x3C && !(v.u.twi.addr & 1)) {
            oled_sel = v.u.twi.addr;
            ctrl_seen = 0;
            avr_raise_irq(twi_in, avr_twi_irq_msg(TWI_COND_ACK, oled_sel, 1));
        }
    }
    if (!oled_sel || !(v.u.twi.msg & TWI_COND_WRITE)) return;
    avr_raise_irq(twi_in, avr_twi_irq_msg(TWI_COND_ACK, oled_sel, 1));
    if (!ctrl_seen) { ctrl_seen = 1; data_mode = (v.u.twi.data & 0x40) != 0; return; }
    if (data_mode) oled_data(v.u.twi.data); else oled_command(v.u.twi.data);
}

static void save_pgm(const char *path) {
    FILE *f = fopen(path, "w");
    if (!f) return;
    fprintf(f, "P2\n128 64\n1\n");
    for (int y = 0; y < 64; y++) {
        for (int x = 0; x < 128; x++) fprintf(f, "%d ", display_on && ((fb[y / 8][x] >> (y % 8)) & 1));
        fprintf(f, "\n");
    }
    fclose(f);
}

static void print_oled(void) {
    for (int y = 0; y < 56; y += 1) {
        if (y % 8 == 7) continue;  /* skip blank 8th row of each text line for a compact view */
        char row[129];
        for (int x = 0; x < 128; x++) row[x] = ((fb[y / 8][x] >> (y % 8)) & 1) ? '#' : ' ';
        row[128] = 0;
        int empty = 1;
        for (int x = 0; x < 128; x++) if (row[x] != ' ') { empty = 0; break; }
        if (!empty) printf("    |%s|\n", row);
    }
}

int main(int argc, char **argv) {
    const char *elf = argc > 1 ? argv[1] : "build/servo_oled.elf";
    elf_firmware_t fw;
    memset(&fw, 0, sizeof fw);
    if (elf_read_firmware(elf, &fw)) { fprintf(stderr, "cannot read %s\n", elf); return 2; }
    avr = avr_make_mcu_by_name("atmega328p");
    avr_init(avr);
    avr_load_firmware(avr, &fw);
    avr->frequency = FREQ;
    avr->log = LOG_ERROR;

    uint32_t flags = 0;
    avr_ioctl(avr, AVR_IOCTL_UART_GET_FLAGS('0'), &flags);
    flags &= ~AVR_UART_FLAG_STDIO;
    avr_ioctl(avr, AVR_IOCTL_UART_SET_FLAGS('0'), &flags);
    avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_UART_GETIRQ('0'), UART_IRQ_OUTPUT), uart_out, NULL);
    uart_in = avr_io_getirq(avr, AVR_IOCTL_UART_GETIRQ('0'), UART_IRQ_INPUT);
    avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_TIMER_GETIRQ('1'), TIMER_IRQ_OUT_PWM0), pwm_value, NULL);
    avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_TWI_GETIRQ(0), TWI_IRQ_OUTPUT), twi_out, NULL);
    twi_in = avr_io_getirq(avr, AVR_IOCTL_TWI_GETIRQ(0), TWI_IRQ_INPUT);

    printf("simavr: %s on atmega328p @ 16 MHz\n", elf);
    int failures = 0;
    uint32_t moves = 0;
    uint64_t end = 1800 * FREQ / 1000;
    while (avr->cycle < end) {
        int st = avr_run(avr);
        if (st == cpu_Done || st == cpu_Crashed) { fprintf(stderr, "CPU stopped (%d)\n", st); return 3; }
        uint64_t ms = avr->cycle * 1000 / FREQ;
        if (cmd_idx < NCMD && ms >= CMDS[cmd_idx].at_ms) {
            /* check the previous command's effect just before typing the next one */
            snprintf(pending, sizeof pending, "%s\n", CMDS[cmd_idx].text);
            char_idx = 0;
            printf("  [%5llu ms] typed : \"%s\"\n", (unsigned long long)ms, CMDS[cmd_idx].text);
            avr_cycle_timer_register(avr, 1, type_next_char, NULL);
            cmd_idx++;
        }
        static size_t checked;
        if (checked < cmd_idx && ms >= CMDS[checked].at_ms + 180) {
            const cmd_t *c = &CMDS[checked];
            const char *reply = replies[n_replies - 1];
            int ok;
            if (c->expect_angle < 0) {
                ok = strncmp(reply, "ERR", 3) == 0;
                printf("  check \"%s\": rejected=%s  -> %s\n", c->text, ok ? "yes" : "no", ok ? "PASS" : "FAIL");
            } else {
                read_pwm();
                uint32_t want_us = 1000 + ((uint32_t)c->expect_angle * 1000 + 90) / 180;
                char want_reply[64];
                snprintf(want_reply, sizeof want_reply, "OK angle=%d pulse_us=%u", c->expect_angle, want_us);
                ok = strcmp(reply, want_reply) == 0 && last_width_us >= want_us - 1 && last_width_us <= want_us + 1 && last_period_us == 20000;
                moves++;
                printf("  check \"%s\": pulse %u us (want %u), period %u us  -> %s\n", c->text, last_width_us, want_us, last_period_us, ok ? "PASS" : "FAIL");
                if (c->expect_angle == 180) { save_pgm("results/oled-180.pgm"); }
            }
            if (!ok) failures++;
            checked++;
        }
    }
    save_pgm("results/oled-final.pgm");
    printf("\nOLED framebuffer at the end (rows of the 128x64 display):\n");
    print_oled();
    printf("\n%u OCR1A updates seen, %zu commands, %d failure(s)\n", pulses, NCMD, failures);
    if (strcmp(replies[0], "READY oled=ok") != 0) { printf("FAIL: expected READY oled=ok, got '%s'\n", replies[0]); failures++; }
    return failures != 0;
}
