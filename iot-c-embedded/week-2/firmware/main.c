/* Multi-sensor data logger (mini project).
 *
 *   A0  LM35 temperature       A1  LDR light (divider with 10k)
 *   D7  HC-SR04 trigger        D8  HC-SR04 echo
 *   D3  active buzzer          A4/A5 I2C to the humidity node MCU (address 0x42)
 *   UART 57600 8N1 -> serial terminal
 *
 * Every 500 ms it reads all sensors, asks the second microcontroller for humidity over I2C,
 * prints one CSV line with a millisecond timestamp, and sounds the buzzer while any alert is active.
 */
#include <avr/interrupt.h>
#include <avr/io.h>

#include "hal.h"
#include "sensors.h"

#define NODE_ADDR 0x42u
#define NODE_REG_HUMIDITY 0x00u
#define SAMPLE_MS 500u

static const thresholds_t LIMITS = {
    .temp_high_tenths = 350, .temp_hyst_tenths = 10, /* hot above 35.0 C, clears below 34.0 C */
    .near_mm = 100, .dist_hyst_mm = 20,               /* object nearer than 10 cm, clears beyond 12 cm */
    .dark_percent = 20, .light_hyst_percent = 5,      /* dark below 20 %, clears above 25 % */
};

static int16_t read_remote_humidity(void) {
    uint8_t frame[3]; /* humidity tenths, little endian, then CRC-8 */
    if (twi_read_regs(NODE_ADDR, NODE_REG_HUMIDITY, frame, sizeof frame) != 0) return -1;
    if (crc8(frame, 2) != frame[2]) return -1;
    return (int16_t)(frame[0] | ((uint16_t)frame[1] << 8));
}

int main(void) {
    uart_init();
    millis_init();
    adc_init();
    ultrasonic_init();
    buzzer_init();
    twi_init();
    sei();

    uart_write("# multi-sensor logger v1.0\r\n# ms,temp_c,dist_cm,light_pct,humidity_pct,alerts\r\n");

    uint8_t alerts = 0;
    uint32_t next = millis();
    char line[64];
    for (;;) {
        while ((int32_t)(millis() - next) < 0) {}
        next += SAMPLE_MS;

        int16_t temp = lm35_tenths_c(adc_read(0));
        uint8_t light = ldr_percent(adc_read(1));
        uint16_t dist = echo_us_to_mm(ultrasonic_echo_us());
        int16_t humidity = read_remote_humidity();

        alerts = update_alerts(alerts, &LIMITS, temp, dist, light);
        buzzer_set(alerts != 0);

        format_log_line(line, sizeof line, millis(), temp, dist, light, humidity, alerts);
        uart_write(line);
    }
}
