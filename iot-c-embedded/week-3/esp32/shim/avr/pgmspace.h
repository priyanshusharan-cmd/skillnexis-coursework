/* Lets the AVR font table compile on the ESP32, where flash constants need no special access. */
#pragma once
#include <stdint.h>
#define PROGMEM
#define pgm_read_byte(addr) (*(const uint8_t *)(addr))
