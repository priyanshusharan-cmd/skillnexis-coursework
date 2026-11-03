MCU   = atmega328p
F_CPU = 16000000UL
CC    = avr-gcc
CFLAGS = -mmcu=$(MCU) -DF_CPU=$(F_CPU) -Os -std=c11 -Wall -Wextra -Werror -ffunction-sections -fdata-sections
LDFLAGS = -Wl,--gc-sections

all: build/logger.elf build/logger.hex build/node.elf build/node.hex

build/logger.elf: firmware/main.c firmware/hal.c firmware/sensors.c firmware/hal.h firmware/sensors.h | build
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ firmware/main.c firmware/hal.c firmware/sensors.c
build/node.elf: node/humidity_node.c firmware/sensors.c | build
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ node/humidity_node.c firmware/sensors.c
build/%.hex: build/%.elf
	avr-objcopy -O ihex -R .eeprom $< $@
build:
	mkdir -p build

size: all
	avr-size --mcu=$(MCU) -C build/logger.elf build/node.elf

# host unit tests for the pure logic
test: build/test_sensors
	./build/test_sensors
build/test_sensors: tests/test_sensors.c firmware/sensors.c | build
	gcc -std=c11 -Wall -Wextra -Werror -O1 -fsanitize=address,undefined -o $@ $^

# run the logger firmware in simavr with simulated sensors and a simulated humidity node
sim: build/logger.elf build/harness
	./build/harness build/logger.elf
build/harness: sim/harness.c | build
	gcc -O1 -Wall -o $@ $< -lsimavr -lelf -lm

clean:
	rm -rf build
.PHONY: all size test sim clean
