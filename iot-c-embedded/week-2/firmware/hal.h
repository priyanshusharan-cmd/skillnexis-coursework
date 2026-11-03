/* Bare-metal drivers for the ATmega328P (Arduino Uno, 16 MHz). */
#ifndef HAL_H
#define HAL_H
#include <stdint.h>

/* UART0 at 57600 baud, 8N1, interrupt-driven transmit ring buffer. */
void uart_init(void);
void uart_write(const char *s);
void uart_flush(void);

/* Timer0 compare-match interrupt every 1 ms. */
void millis_init(void);
uint32_t millis(void);

/* ADC with AVCC reference and /128 prescaler (125 kHz). Averages 4 samples, discards the first after a mux change. */
void adc_init(void);
uint16_t adc_read(uint8_t channel);

/* HC-SR04: trigger on PD7 (Arduino D7), echo on PB0 (D8). Timer1 runs at 2 MHz (0.5 us ticks).
 * Returns echo high time in microseconds, or 0 on timeout (no object within ~4 m). */
void ultrasonic_init(void);
uint32_t ultrasonic_echo_us(void);

/* Active buzzer on PD3 (D3). */
void buzzer_init(void);
void buzzer_set(uint8_t on);

/* I2C (TWI) master at 100 kHz. Return 0 on success, non-zero TWI status on failure. */
void twi_init(void);
uint8_t twi_read_regs(uint8_t addr, uint8_t reg, uint8_t *buf, uint8_t len);

#endif
