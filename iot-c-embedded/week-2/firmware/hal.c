#include "hal.h"

#include <avr/interrupt.h>
#include <avr/io.h>
#include <util/atomic.h>
#include <util/delay.h>
#include <util/twi.h>

/* ------------------------------------------------------------------ UART */
#define BAUD 57600UL
#define UBRR_VALUE ((F_CPU + BAUD * 4UL) / (BAUD * 8UL) - 1UL) /* double-speed mode, rounded */
#define TX_SIZE 128u                                          /* power of two */

static volatile char tx_buf[TX_SIZE];
static volatile uint8_t tx_head, tx_tail;

void uart_init(void) {
    UBRR0H = (uint8_t)(UBRR_VALUE >> 8);
    UBRR0L = (uint8_t)UBRR_VALUE;
    UCSR0A = _BV(U2X0);
    UCSR0B = _BV(TXEN0);
    UCSR0C = _BV(UCSZ01) | _BV(UCSZ00); /* 8 data bits, no parity, 1 stop */
}

void uart_write(const char *s) {
    while (*s) {
        uint8_t next = (uint8_t)((tx_head + 1u) & (TX_SIZE - 1u));
        while (next == tx_tail) { /* buffer full: wait for the ISR to drain it */ }
        tx_buf[tx_head] = *s++;
        tx_head = next;
        UCSR0B |= _BV(UDRIE0);
    }
}

void uart_flush(void) {
    while (tx_head != tx_tail) {}
}

ISR(USART_UDRE_vect) {
    if (tx_head == tx_tail) {
        UCSR0B &= (uint8_t)~_BV(UDRIE0);
        return;
    }
    UDR0 = tx_buf[tx_tail];
    tx_tail = (uint8_t)((tx_tail + 1u) & (TX_SIZE - 1u));
}

/* ------------------------------------------------------------------ millis */
static volatile uint32_t ms_count;

void millis_init(void) {
    TCCR0A = _BV(WGM01);              /* CTC */
    TCCR0B = _BV(CS01) | _BV(CS00);   /* /64 -> 250 kHz */
    OCR0A = 249;                      /* 250 ticks = 1 ms */
    TIMSK0 = _BV(OCIE0A);
}

ISR(TIMER0_COMPA_vect) { ms_count++; }

uint32_t millis(void) {
    uint32_t v;
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { v = ms_count; }
    return v;
}

/* ------------------------------------------------------------------ ADC */
void adc_init(void) {
    ADMUX = _BV(REFS0);                                  /* AVCC reference */
    ADCSRA = _BV(ADEN) | _BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0);
    DIDR0 = _BV(ADC0D) | _BV(ADC1D);                     /* disable digital input buffers on A0, A1 */
}

static uint16_t adc_once(void) {
    ADCSRA |= _BV(ADSC);
    while (ADCSRA & _BV(ADSC)) {}
    return ADC;
}

uint16_t adc_read(uint8_t channel) {
    ADMUX = (uint8_t)((ADMUX & 0xF0u) | (channel & 0x0Fu));
    (void)adc_once(); /* first result after a mux change may be wrong */
    uint16_t sum = 0;
    for (uint8_t i = 0; i < 4; i++) sum += adc_once();
    return (uint16_t)((sum + 2u) / 4u);
}

/* ------------------------------------------------------------------ HC-SR04 */
void ultrasonic_init(void) {
    DDRD |= _BV(PD7);
    PORTD &= (uint8_t)~_BV(PD7);
    DDRB &= (uint8_t)~_BV(PB0);
    TCCR1A = 0;
    TCCR1B = _BV(CS11); /* /8 -> 2 MHz, 0.5 us per tick, wraps every 32.8 ms */
}

uint32_t ultrasonic_echo_us(void) {
    PORTD |= _BV(PD7); /* 10 us trigger pulse */
    _delay_us(10);
    PORTD &= (uint8_t)~_BV(PD7);

    uint32_t start_ms = millis();
    while (!(PINB & _BV(PB0))) {          /* wait for the echo to start (sensor needs ~0.5 ms) */
        if (millis() - start_ms > 5) return 0;
    }
    TCNT1 = 0;
    TIFR1 = _BV(TOV1);
    uint8_t overflows = 0;
    while (PINB & _BV(PB0)) {
        if (TIFR1 & _BV(TOV1)) {
            TIFR1 = _BV(TOV1);
            if (++overflows > 1) return 0;   /* > 65 ms: out of range */
        }
    }
    uint32_t ticks = ((uint32_t)overflows << 16) | TCNT1;
    return ticks / 2u;
}

/* ------------------------------------------------------------------ buzzer */
void buzzer_init(void) { DDRD |= _BV(PD3); }

void buzzer_set(uint8_t on) {
    if (on) PORTD |= _BV(PD3);
    else PORTD &= (uint8_t)~_BV(PD3);
}

/* ------------------------------------------------------------------ TWI master */
#define TWI_TIMEOUT 2000u

static uint8_t twi_wait(void) {
    for (uint16_t i = 0; i < TWI_TIMEOUT; i++) {
        if (TWCR & _BV(TWINT)) return 0;
        _delay_us(5);
    }
    return 0xFF; /* bus stuck */
}

void twi_init(void) {
    TWSR = 0;                                  /* prescaler 1 */
    TWBR = (uint8_t)((F_CPU / 100000UL - 16UL) / 2UL); /* 100 kHz */
    TWCR = _BV(TWEN);
}

static void twi_stop(void) { TWCR = _BV(TWINT) | _BV(TWEN) | _BV(TWSTO); }

/* Two transactions: [START, SLA+W, reg, STOP] sets the slave's register pointer, then
 * [START, SLA+R, data..., NACK, STOP] reads it. Same result as a repeated START on real hardware,
 * and it also runs correctly in simavr 1.6, whose repeated-START timing is unreliable. */
static uint8_t twi_start(uint8_t sla) {
    TWCR = _BV(TWINT) | _BV(TWEN) | _BV(TWSTA);
    if (twi_wait() || TW_STATUS != TW_START) return 1;
    TWDR = sla;
    TWCR = _BV(TWINT) | _BV(TWEN);
    if (twi_wait()) return 1;
    /* simavr 1.6 can raise TWINT a second time with the old START status before the address result
     * arrives; on real hardware this loop exits at once. */
    for (uint16_t i = 0; i < TWI_TIMEOUT && TW_STATUS == TW_START; i++) _delay_us(5);
    /* Real silicon reports TW_MT_SLA_ACK (0x18) / TW_MR_SLA_ACK (0x40). simavr 1.6 reports
     * TW_MT_DATA_ACK (0x28) after SLA+W, so that also counts as "address acknowledged"; NACKs still fail. */
    if (sla & 1) return TW_STATUS != TW_MR_SLA_ACK;
    return TW_STATUS != TW_MT_SLA_ACK && TW_STATUS != TW_MT_DATA_ACK;
}

uint8_t twi_read_regs(uint8_t addr, uint8_t reg, uint8_t *buf, uint8_t len) {
    uint8_t st;
    if (twi_start((uint8_t)(addr << 1) | TW_WRITE)) goto fail;
    TWDR = reg;
    TWCR = _BV(TWINT) | _BV(TWEN);
    if (twi_wait() || (TW_STATUS != TW_MT_DATA_ACK)) goto fail;
    twi_stop();
    _delay_us(20); /* bus free time between STOP and START (4.7 us minimum at 100 kHz) */
    if (twi_start((uint8_t)(addr << 1) | TW_READ)) goto fail;
    for (uint8_t i = 0; i < len; i++) {
        TWCR = _BV(TWINT) | _BV(TWEN) | (i + 1u < len ? _BV(TWEA) : 0); /* NACK the last byte */
        if (twi_wait()) goto fail;
        buf[i] = TWDR;
    }
    twi_stop();
    return 0;
fail:
    st = TW_STATUS ? TW_STATUS : 0xFF;
    twi_stop();
    return st;
}
