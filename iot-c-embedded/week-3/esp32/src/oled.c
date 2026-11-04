/* SSD1306 128x64 over I2C, text only (5x7 font, 21 columns x 8 rows). Same command sequence as avr/servo_oled.c. */
#include "oled.h"

#include <string.h>

#include "driver/i2c.h"
#include "font5x7.h"

#define OLED_ADDR 0x3C

static i2c_port_t s_port;

static esp_err_t oled_send(uint8_t control, const uint8_t *bytes, size_t n) {
    i2c_cmd_handle_t c = i2c_cmd_link_create();
    i2c_master_start(c);
    i2c_master_write_byte(c, OLED_ADDR << 1 | I2C_MASTER_WRITE, true);
    i2c_master_write_byte(c, control, true);
    i2c_master_write(c, bytes, n, true);
    i2c_master_stop(c);
    esp_err_t err = i2c_master_cmd_begin(s_port, c, pdMS_TO_TICKS(50));
    i2c_cmd_link_delete(c);
    return err;
}

esp_err_t oled_init(i2c_port_t port) {
    static const uint8_t init[] = {0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40, 0x8D, 0x14, 0x20, 0x00, 0xA1, 0xC8,
                                   0xDA, 0x12, 0x81, 0xCF, 0xD9, 0xF1, 0xDB, 0x40, 0xA4, 0xA6, 0xAF};
    s_port = port;
    esp_err_t err = oled_send(0x00, init, sizeof init);
    for (int p = 0; err == ESP_OK && p < 8; p++) err = oled_text(p, "");
    return err;
}

esp_err_t oled_text(int page, const char *s) {
    uint8_t row[128] = {0};
    for (int col = 0; *s && col + 6 <= 128; s++, col += 6) {
        const char *hit = strchr(FONT_CHARS, *s);
        int idx = hit && *s ? (int)(hit - FONT_CHARS) : 0;   /* unknown char -> space */
        memcpy(row + col, FONT[idx], 5);
    }
    const uint8_t addr[] = {0x21, 0, 127, 0x22, (uint8_t)page, (uint8_t)page};
    esp_err_t err = oled_send(0x00, addr, sizeof addr);
    return err == ESP_OK ? oled_send(0x40, row, sizeof row) : err;
}
