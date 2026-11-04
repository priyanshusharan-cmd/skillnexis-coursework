AVR_CFLAGS = -mmcu=atmega328p -DF_CPU=16000000UL -Os -std=c11 -Wall -Wextra -Werror
HOST_CFLAGS = -std=c11 -Wall -Wextra -Werror -O1

all: build/servo_oled.elf build/servo_oled.hex build/station_pc build/test_common

build:
	mkdir -p build results
build/servo_oled.elf: avr/servo_oled.c avr/font5x7.h | build
	avr-gcc $(AVR_CFLAGS) -o $@ avr/servo_oled.c
build/servo_oled.hex: build/servo_oled.elf
	avr-objcopy -O ihex -R .eeprom $< $@
build/station_pc: host/station_pc.c common/*.c common/*.h | build
	gcc $(HOST_CFLAGS) -O2 -o $@ host/station_pc.c common/mqtt.c common/bme280.c common/station.c -lm
build/test_common: tests/test_common.c common/*.c common/*.h | build
	gcc $(HOST_CFLAGS) -fsanitize=address,undefined -o $@ tests/test_common.c common/mqtt.c common/bme280.c -lm
build/servo_harness: sim/servo_harness.c | build
	gcc -O1 -Wall -o $@ $< -lsimavr -lelf -lm

test: build/test_common
	./build/test_common

# servo + OLED firmware in simavr: typed commands, PWM registers, OLED framebuffer -> results/*.png
sim: build/servo_oled.elf build/servo_harness
	./build/servo_harness build/servo_oled.elf
	python3 sim/pgm_to_png.py results/oled-180.pgm results/oled-final.pgm && rm -f results/*.pgm

# end-to-end MQTT test against a real broker (needs mosquitto + mosquitto_sub/pub on PATH)
mqtt-test: build/station_pc
	sh tests/mqtt_integration.sh

clean:
	rm -rf build
.PHONY: all test sim mqtt-test clean
