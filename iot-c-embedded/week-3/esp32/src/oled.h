#pragma once
#include "driver/i2c.h"
#include "esp_err.h"

esp_err_t oled_init(i2c_port_t port);
esp_err_t oled_text(int page, const char *text);
