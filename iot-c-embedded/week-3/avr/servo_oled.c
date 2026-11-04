/* Servo control over serial + SSD1306 OLED status display (ATmega328P / Arduino Uno, 16 MHz).
 *
 *   Type an angle (0-180) and Enter in a terminal at 57600 baud: the servo on D9 (OC1A) moves there,
 *   the OLED on I2C (A4/A5, address 0x3C) shows the angle, the pulse width and a bar.
 *   Anything else is rejected with "ERR".
 *
 * PWM: Timer1 fast PWM, TOP = ICR1 = 39999 at 2 MHz -> exactly 50 Hz; 1000-2000 us pulse = 0-180 degrees.
 */
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/pgmspace.h>
#include <stdint.h>
#include <util/delay.h>
#include <util/twi.h>

#include "font5x7.h"

#define BAUD 57600UL
#define UBRR_VALUE ((F_CPU + BAUD * 4UL) / (BAUD * 8UL) - 1UL)
#define OLED_ADDR 0x3C
#define PULSE_MIN_US 1000u
#define PULSE_MAX_US 2000u

/* ------------------------------------------------------------------ UART (polled TX, interrupt RX) */
static volatile char rx_line[8];
static volatile uint8_t rx_len, line_ready, line_overflow;

static void uart_init(void) {
    UBRR0H = (uint8_t)(UBRR_VALUE >> 8);
    UBRR0L = (uint8_t)UBRR_VALUE;
    UCSR0A = _BV(U2X0);
    UCSR0B = _BV(TXEN0) | _BV(RXEN0) | _BV(RXCIE0);
    UCSR0C = _BV(UCSZ01) | _BV(UCSZ00);
}

static void uart_putc(char c) {
    while (!(UCSR0A & _BV(UDRE0))) {}
    UDR0 = (uint8_t)c;
}

static void uart_puts(const char *s) { while (*s) uart_putc(*s++); }

static void uart_putu(uint16_t v) {
    char b[6];
    uint8_t n = 0;
    do { b[n++] = (char)('0' + v % 10); v /= 10; } while (v);
    while (n) uart_putc(b[--n]);
}

ISR(USART_RX_vect) {
    char c = (char)UDR0;
    if (line_ready) return;                  /* previous line not handled yet */
    if (c == '\r' || c == '\n') {
        if (rx_len || line_overflow) line_ready = 1;
    } else if (rx_len < sizeof rx_line - 1) {
        rx_line[rx_len++] = c;
    } else {
        line_overflow = 1;
    }
}

/* Parses "0".."180" (optional surrounding spaces). Returns the angle or -1. */
static int16_t parse_angle(const volatile char *s, uint8_t len) {
    uint8_t i = 0, digits = 0;
    uint16_t v = 0;
    while (i < len && s[i] == ' ') i++;
    while (i < len && s[i] >= '0' && s[i] <= '9') { v = (uint16_t)(v * 10u + (uint8_t)(s[i++] - '0')); if (++digits > 3) return -1; }
    while (i < len && s[i] == ' ') i++;
    if (!digits || i != len || v > 180) return -1;
    return (int16_t)v;
}

/* ------------------------------------------------------------------ servo PWM */
static void servo_init(void) {
    DDRB |= _BV(PB1);                                       /* OC1A = D9 */
    TCCR1A = _BV(COM1A1) | _BV(WGM11);                      /* non-inverting, fast PWM mode 14 */
    TCCR1B = _BV(WGM13) | _BV(WGM12) | _BV(CS11);           /* /8 -> 2 MHz */
    ICR1 = 39999;                                           /* 40000 ticks = 20 ms */
}

static uint16_t angle_to_us(uint8_t angle) { return (uint16_t)(PULSE_MIN_US + ((uint32_t)angle * (PULSE_MAX_US - PULSE_MIN_US) + 90u) / 180u); }

static void servo_set_us(uint16_t us) { OCR1A = (uint16_t)(us * 2u - 1u); }  /* high for OCR1A+1 ticks */

/* ------------------------------------------------------------------ I2C master (write only) */
static uint8_t twi_wait(void) {
    for (uint16_t i = 0; i < 2000; i++) { if (TWCR & _BV(TWINT)) return 0; _delay_us(5); }
    return 1;
}

static uint8_t twi_begin(uint8_t addr) {
    TWCR = _BV(TWINT) | _BV(TWEN) | _BV(TWSTA);
    if (twi_wait() || TW_STATUS != TW_START) return 1;
    TWDR = (uint8_t)(addr << 1);
    TWCR = _BV(TWINT) | _BV(TWEN);
    if (twi_wait()) return 1;
    for (uint16_t i = 0; i < 2000 && TW_STATUS == TW_START; i++) _delay_us(5); /* simavr 1.6 quirk, no-op on hardware */
    return TW_STATUS != TW_MT_SLA_ACK && TW_STATUS != TW_MT_DATA_ACK;          /* simavr reports 0x28 for SLA ACK */
}

static uint8_t twi_byte(uint8_t b) {
    TWDR = b;
    TWCR = _BV(TWINT) | _BV(TWEN);
    return twi_wait() || TW_STATUS != TW_MT_DATA_ACK;
}

static void twi_end(void) { TWCR = _BV(TWINT) | _BV(TWEN) | _BV(TWSTO); _delay_us(20); }

/* ------------------------------------------------------------------ SSD1306 */
static uint8_t oled_ok;

static void oled_cmds(const uint8_t *c, uint8_t n) {
    if (twi_begin(OLED_ADDR) || twi_byte(0x00)) { oled_ok = 0; twi_end(); return; }  /* 0x00 = command stream */
    while (n--) if (twi_byte(*c++)) { oled_ok = 0; break; }
    twi_end();
}

static void oled_init(void) {
    static const uint8_t init[] = {
        0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40, 0x8D, 0x14,  /* off, clock, mux 64, offset 0, start line 0, charge pump on */
        0x20, 0x00, 0xA1, 0xC8, 0xDA, 0x12, 0x81, 0xCF, 0xD9, 0xF1,  /* horizontal addressing, flip to normal orientation, contrast */
        0xDB, 0x40, 0xA4, 0xA6, 0xAF,                                /* VCOMH, resume, normal (not inverted), display on */
    };
    oled_ok = 1;
    TWSR = 0;
    TWBR = (uint8_t)((F_CPU / 400000UL - 16UL) / 2UL);              /* 400 kHz fast mode */
    TWCR = _BV(TWEN);
    oled_cmds(init, sizeof init);
}

static uint8_t page_buf[128];

static void glyph_into(uint8_t *dst, char ch) {
    uint8_t idx = 0;
    char f;
    while ((f = (char)pgm_read_byte(&FONT_CHARS[idx])) && f != ch) idx++;
    if (!f) idx = 0;                                                  /* unknown char -> space (first glyph) */
    for (uint8_t c = 0; c < 5; c++) dst[c] = pgm_read_byte(&FONT[idx][c]);
    dst[5] = 0;
}

/* Writes one 8-pixel-high text row (page 0..7). Text is up to 21 chars of 6 px. */
static void oled_text(uint8_t page, const char *s) {
    for (uint8_t i = 0; i < 128; i++) page_buf[i] = 0;
    for (uint8_t col = 0; *s && col + 6 <= 128; s++, col = (uint8_t)(col + 6)) glyph_into(page_buf + col, *s);
    const uint8_t addr[] = {0x21, 0, 127, 0x22, page, page};
    oled_cmds(addr, sizeof addr);
    if (twi_begin(OLED_ADDR) || twi_byte(0x40)) { oled_ok = 0; twi_end(); return; }  /* 0x40 = data stream */
    for (uint8_t i = 0; i < 128; i++) if (twi_byte(page_buf[i])) { oled_ok = 0; break; }
    twi_end();
}

static void oled_bar(uint8_t page, uint8_t angle) {
    uint8_t fill = (uint8_t)(4u + (uint16_t)angle * 120u / 180u);
    for (uint8_t i = 0; i < 128; i++) page_buf[i] = (i == 2 || i == 125) ? 0x7E : (i > 2 && i < 125) ? (i < fill ? 0x7E : 0x42) : 0;
    const uint8_t addr[] = {0x21, 0, 127, 0x22, page, page};
    oled_cmds(addr, sizeof addr);
    if (twi_begin(OLED_ADDR) || twi_byte(0x40)) { oled_ok = 0; twi_end(); return; }
    for (uint8_t i = 0; i < 128; i++) if (twi_byte(page_buf[i])) break;
    twi_end();
}

static void fmt_u(char *dst, uint16_t v, uint8_t width) {   /* right-aligned number */
    for (int8_t i = (int8_t)width - 1; i >= 0; i--) { dst[i] = (v || i == width - 1) ? (char)('0' + v % 10) : ' '; v /= 10; }
}

static void show(uint8_t angle, uint16_t us, uint16_t moves) {
    char l1[] = "ANGLE:    ### DEG";
    char l2[] = "PULSE:   #### US";
    char l3[] = "MOVES:  #####";
    fmt_u(l1 + 10, angle, 3);
    fmt_u(l2 + 9, us, 4);
    fmt_u(l3 + 8, moves, 5);
    oled_text(0, "SERVO CONTROL");
    oled_text(2, l1);
    oled_text(3, l2);
    oled_text(4, l3);
    oled_bar(6, angle);
}

int main(void) {
    uart_init();
    servo_init();
    oled_init();
    sei();
    uint8_t angle = 90;
    uint16_t moves = 0;
    servo_set_us(angle_to_us(angle));
    for (uint8_t p = 0; p < 8; p++) oled_text(p, "");
    show(angle, angle_to_us(angle), moves);
    uart_puts(oled_ok ? "READY oled=ok\r\n" : "READY oled=missing\r\n");

    for (;;) {
        if (!line_ready) continue;
        int16_t a = line_overflow ? -1 : parse_angle(rx_line, rx_len);
        rx_len = 0;
        line_overflow = 0;
        line_ready = 0;
        if (a < 0) { uart_puts("ERR angle must be 0-180\r\n"); continue; }
        angle = (uint8_t)a;
        uint16_t us = angle_to_us(angle);
        servo_set_us(us);
        moves++;
        show(angle, us, moves);
        uart_puts("OK angle=");
        uart_putu(angle);
        uart_puts(" pulse_us=");
        uart_putu(us);
        uart_puts("\r\n");
    }
}
