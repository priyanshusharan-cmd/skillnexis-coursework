/* ESP32 implementation of app/hal.h.
 *
 *  GPIO34 ADC1_CH6  soil probe (capacitive v1.2, powered from GPIO32 only while sampling)
 *  GPIO36 ADC1_CH0  LDR divider            GPIO33 ADC1_CH5  battery via 100k/100k divider
 *  GPIO27           tank float switch (to GND, internal pull-up; closed = water present)
 *  GPIO26           pump relay / MOSFET gate (active high)
 *  GPIO21/22        I2C: BME280 0x76 + SSD1306 0x3C
 *  GPIO25           "wake / water now" button to GND (RTC GPIO, ext0 wake-up)
 */
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/time.h>

#include "../../app/hal.h"
#include "bme280.h"
#include "driver/gpio.h"
#include "driver/i2c.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_crt_bundle.h"
#include "esp_https_ota.h"
#include "esp_log.h"
#include "esp_ota_ops.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "hal_esp32.h"
#include "mqtt.h"
#include "oled.h"

static const char *TAG = "hal";

#define PIN_SOIL_PWR GPIO_NUM_32
#define PIN_TANK GPIO_NUM_27
#define PIN_PUMP GPIO_NUM_26
#define I2C_PORT I2C_NUM_0

static adc_oneshot_unit_handle_t s_adc;
static bme280_calib_t s_cal;
static bool s_bme_ok, s_oled_ok;
static mqtt_client_t *s_mqtt;
static char s_topic_base[48];
static char s_cmd[160];
static volatile bool s_cmd_ready;

/* ---------------------------------------------------------------- time and delays */
uint32_t hal_now_s(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);   /* the RTC keeps counting through deep sleep */
    return (uint32_t)tv.tv_sec;
}

void hal_delay_s(uint32_t s) { vTaskDelay(pdMS_TO_TICKS(s * 1000u)); }

void hal_log(const char *msg) { ESP_LOGI("app", "%s", msg); }

/* ---------------------------------------------------------------- sensors */
static int adc_avg(adc_channel_t ch) {
    int sum = 0, v;
    for (int i = 0; i < 8; i++) { adc_oneshot_read(s_adc, ch, &v); sum += v; }
    return sum / 8;
}

static esp_err_t bme_rd(uint8_t reg, uint8_t *b, size_t n) {
    return i2c_master_write_read_device(I2C_PORT, BME280_ADDR, &reg, 1, b, n, pdMS_TO_TICKS(50));
}

static esp_err_t bme_wr(uint8_t reg, uint8_t v) {
    uint8_t b[2] = {reg, v};
    return i2c_master_write_to_device(I2C_PORT, BME280_ADDR, b, 2, pdMS_TO_TICKS(50));
}

bool hal_read(hal_sample_t *o) {
    gpio_set_level(PIN_SOIL_PWR, 1);
    vTaskDelay(pdMS_TO_TICKS(100));           /* probe settles */
    o->soil_raw = (uint16_t)adc_avg(ADC_CHANNEL_6);
    gpio_set_level(PIN_SOIL_PWR, 0);
    o->light_raw = (uint16_t)adc_avg(ADC_CHANNEL_0);
    o->batt_raw = (uint16_t)adc_avg(ADC_CHANNEL_5);
    o->tank_ok = gpio_get_level(PIN_TANK) == 0;
    o->temp_ok = false;
    if (s_bme_ok) {
        bme_wr(BME280_REG_CTRL_MEAS, 0x25);   /* forced mode: one measurement, then the chip sleeps */
        vTaskDelay(pdMS_TO_TICKS(10));
        uint8_t d[8];
        if (bme_rd(BME280_REG_DATA, d, 8) == ESP_OK) {
            int32_t p, t, h;
            bme280_parse_raw(d, &p, &t, &h);
            bme280_reading_t r = bme280_compensate(&s_cal, p, t, h);
            o->temp_c10 = (int16_t)(r.temp_centi_c / 10);
            o->humidity = (uint8_t)(r.humidity_milli / 1000u);
            o->temp_ok = true;
        }
    }
    return true;
}

void hal_pump(bool on) { gpio_set_level(PIN_PUMP, on); }

void hal_display(const char lines[4][22]) {
    if (!s_oled_ok) return;
    for (int i = 0; i < 4; i++) oled_text(i * 2, lines[i]);
}

/* ---------------------------------------------------------------- MQTT */
bool hal_publish(const char *suffix, const char *payload, bool retain) {
    if (!s_mqtt) return false;
    char topic[80];
    snprintf(topic, sizeof topic, "%s/%s", s_topic_base, suffix);
    return mqtt_publish(s_mqtt, topic, payload, retain) == MQTT_OK;
}

void hal_esp32_on_command(const char *payload, size_t len) {
    if (len >= sizeof s_cmd) return;
    memcpy(s_cmd, payload, len);
    s_cmd[len] = '\0';
    s_cmd_ready = true;
}

bool hal_poll_command(char *buf, unsigned size) {
    if (!s_cmd_ready) {
        if (s_mqtt) mqtt_poll(s_mqtt, 0);    /* lets the client deliver any queued command */
        if (!s_cmd_ready) return false;
    }
    snprintf(buf, size, "%s", s_cmd);
    s_cmd_ready = false;
    return true;
}

/* ---------------------------------------------------------------- OTA */
bool hal_ota(const char *url) {
    if (strncmp(url, "https://", 8) != 0) { ESP_LOGE(TAG, "OTA refused: only https:// URLs"); return false; }
    ESP_LOGW(TAG, "OTA from %s", url);
    hal_publish("ota", "{\"status\":\"downloading\"}", false);
    esp_http_client_config_t http = {.url = url, .crt_bundle_attach = esp_crt_bundle_attach, .timeout_ms = 15000};
    esp_https_ota_config_t cfg = {.http_config = &http};
    esp_err_t err = esp_https_ota(&cfg);     /* writes the inactive slot and verifies the image */
    if (err != ESP_OK) {
        char msg[80];
        snprintf(msg, sizeof msg, "{\"status\":\"failed\",\"error\":\"%s\"}", esp_err_to_name(err));
        hal_publish("ota", msg, false);
        return false;
    }
    hal_publish("ota", "{\"status\":\"rebooting\"}", false);
    vTaskDelay(pdMS_TO_TICKS(500));
    esp_restart();                           /* boots the new image in "pending verify" state */
    return true;
}

/* ---------------------------------------------------------------- setup */
void hal_esp32_init(mqtt_client_t *mqtt, const char *node_id) {
    gpio_config_t out = {.pin_bit_mask = 1ULL << PIN_PUMP | 1ULL << PIN_SOIL_PWR, .mode = GPIO_MODE_OUTPUT};
    gpio_config(&out);
    gpio_set_level(PIN_PUMP, 0);
    gpio_config_t in = {.pin_bit_mask = 1ULL << PIN_TANK, .mode = GPIO_MODE_INPUT, .pull_up_en = GPIO_PULLUP_ENABLE};
    gpio_config(&in);

    adc_oneshot_unit_init_cfg_t unit = {.unit_id = ADC_UNIT_1};
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&unit, &s_adc));
    adc_oneshot_chan_cfg_t ch = {.atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_12};
    adc_oneshot_config_channel(s_adc, ADC_CHANNEL_5, &ch);
    adc_oneshot_config_channel(s_adc, ADC_CHANNEL_6, &ch);
    adc_oneshot_config_channel(s_adc, ADC_CHANNEL_0, &ch);

    i2c_config_t i2c = {.mode = I2C_MODE_MASTER, .sda_io_num = 21, .scl_io_num = 22, .sda_pullup_en = GPIO_PULLUP_ENABLE,
                        .scl_pullup_en = GPIO_PULLUP_ENABLE, .master.clk_speed = 400000};
    i2c_param_config(I2C_PORT, &i2c);
    i2c_driver_install(I2C_PORT, I2C_MODE_MASTER, 0, 0, 0);
    s_oled_ok = oled_init(I2C_PORT) == ESP_OK;

    uint8_t id = 0, c1[26], c2[7];
    s_bme_ok = bme_rd(BME280_REG_ID, &id, 1) == ESP_OK && id == 0x60 && bme_rd(BME280_REG_CALIB1, c1, 26) == ESP_OK &&
               bme_rd(BME280_REG_CALIB2, c2, 7) == ESP_OK;
    if (s_bme_ok) {
        bme280_parse_calib(c1, c2, &s_cal);
        bme_wr(BME280_REG_CTRL_HUM, 0x01);
    } else {
        ESP_LOGW(TAG, "BME280 missing: temperature rules disabled");
    }
    s_mqtt = mqtt;
    snprintf(s_topic_base, sizeof s_topic_base, "farm/%s", node_id);
}
