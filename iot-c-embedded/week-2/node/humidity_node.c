/* Second microcontroller: I2C slave "humidity node" at address 0x42.
 *
 * Reads a humidity sensor on A0 (analog output, 0-5 V = 0-100 %RH, e.g. HIH-4030 style)
 * and answers register reads from the logger:
 *   reg 0x00 -> 3 bytes: humidity in tenths of %RH (little endian) + CRC-8 of those 2 bytes
 *   reg 0x10 -> 1 byte: firmware version
 * Wiring: SDA (A4) and SCL (A5) to the logger's A4/A5, common GND, 4.7k pull-ups to 5 V on both lines.
 */
#include <avr/interrupt.h>
#include <avr/io.h>
#include <util/twi.h>

#include "../firmware/sensors.h"

#define MY_ADDR 0x42u
#define VERSION 0x01u

static volatile uint8_t reg_ptr;
static volatile uint8_t tx[3];
static volatile uint8_t tx_len, tx_pos;
static volatile uint16_t humidity_tenths;

static void load_register(uint8_t reg) {
    if (reg == 0x00) {
        uint16_t h = humidity_tenths;
        tx[0] = (uint8_t)h;
        tx[1] = (uint8_t)(h >> 8);
        tx[2] = crc8((const uint8_t *)tx, 2);
        tx_len = 3;
    } else if (reg == 0x10) {
        tx[0] = VERSION;
        tx_len = 1;
    } else {
        tx[0] = 0xFF;
        tx_len = 1;
    }
    tx_pos = 0;
}

ISR(TWI_vect) {
    switch (TW_STATUS) {
    case TW_SR_SLA_ACK:            /* addressed for write: next byte is the register */
        reg_ptr = 0xFF;
        break;
    case TW_SR_DATA_ACK:
        if (reg_ptr == 0xFF) { reg_ptr = TWDR; load_register(reg_ptr); }
        break;
    case TW_ST_SLA_ACK:            /* addressed for read */
    case TW_ST_DATA_ACK:
        TWDR = tx_pos < tx_len ? tx[tx_pos++] : 0xFF;
        break;
    case TW_BUS_ERROR:
        TWCR = _BV(TWSTO) | _BV(TWINT) | _BV(TWEN) | _BV(TWEA) | _BV(TWIE);
        return;
    default:
        break;
    }
    TWCR = _BV(TWINT) | _BV(TWEN) | _BV(TWEA) | _BV(TWIE);
}

int main(void) {
    ADMUX = _BV(REFS0);
    ADCSRA = _BV(ADEN) | _BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0);
    TWAR = (uint8_t)(MY_ADDR << 1);
    TWCR = _BV(TWEN) | _BV(TWEA) | _BV(TWIE);
    sei();
    for (;;) {
        ADCSRA |= _BV(ADSC);
        while (ADCSRA & _BV(ADSC)) {}
        uint16_t h = (uint16_t)(((uint32_t)ADC * 1000u + 511u) / 1023u);  /* 0..1000 tenths of %RH */
        cli();
        humidity_tenths = h;
        sei();
    }
}
