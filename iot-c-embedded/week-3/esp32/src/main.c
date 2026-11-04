/* ESP32 WiFi weather station (ESP-IDF).
 *
 *   BME280 (temperature, humidity, pressure) and SSD1306 OLED share I2C: SDA GPIO21, SCL GPIO22.
 *   Publishes JSON to weather/<id>/state every few seconds over MQTT, keeps weather/<id>/status at
 *   "online" (the broker's last-will turns it to "offline" if the board dies), and listens on
 *   weather/<id>/cmd for "interval=<seconds>".
 *
 * MQTT is the project's own C client (../../common/mqtt.c) over lwIP sockets: the same code that the
 * PC build runs against Mosquitto in the tests.
 */
#include <errno.h>
#include <stdio.h>
#include <string.h>

#include "bme280.h"
#include "driver/i2c.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"
#include "lwip/netdb.h"
#include "lwip/sockets.h"
#include "mqtt.h"
#include "nvs_flash.h"
#include "oled.h"
#include "station.h"

#if __has_include("secrets.h")
#include "secrets.h"
#define USING_PLACEHOLDER_SECRETS 0
#else
#include "secrets.example.h"   /* CI builds use the placeholders; copy it to secrets.h for a real board */
#define USING_PLACEHOLDER_SECRETS 1
#endif

static const char *TAG = "station";
#define I2C_PORT I2C_NUM_0
#define WIFI_UP BIT0

static EventGroupHandle_t s_net;
static station_t s_station = {.id = STATION_ID, .interval_ms = 5000};

/* ---------------------------------------------------------------- WiFi */
static void on_wifi(void *arg, esp_event_base_t base, int32_t id, void *data) {
    (void)arg; (void)data;
    if (base == WIFI_EVENT && (id == WIFI_EVENT_STA_START || id == WIFI_EVENT_STA_DISCONNECTED)) {
        xEventGroupClearBits(s_net, WIFI_UP);
        esp_wifi_connect();                       /* the driver retries; we just keep asking */
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        ESP_LOGI(TAG, "WiFi connected, got IP");
        xEventGroupSetBits(s_net, WIFI_UP);
    }
}

static void wifi_start(void) {
    s_net = xEventGroupCreate();
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, on_wifi, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, on_wifi, NULL));
    wifi_config_t wc = {0};
    strncpy((char *)wc.sta.ssid, WIFI_SSID, sizeof wc.sta.ssid);
    strncpy((char *)wc.sta.password, WIFI_PASS, sizeof wc.sta.password);
    wc.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wc));
    ESP_ERROR_CHECK(esp_wifi_start());
}

/* ---------------------------------------------------------------- I2C + BME280 */
static esp_err_t i2c_init(void) {
    i2c_config_t c = {.mode = I2C_MODE_MASTER, .sda_io_num = 21, .scl_io_num = 22, .sda_pullup_en = GPIO_PULLUP_ENABLE,
                      .scl_pullup_en = GPIO_PULLUP_ENABLE, .master.clk_speed = 400000};
    esp_err_t err = i2c_param_config(I2C_PORT, &c);
    return err == ESP_OK ? i2c_driver_install(I2C_PORT, c.mode, 0, 0, 0) : err;
}

static esp_err_t bme_read(uint8_t reg, uint8_t *buf, size_t n) {
    return i2c_master_write_read_device(I2C_PORT, BME280_ADDR, &reg, 1, buf, n, pdMS_TO_TICKS(50));
}

static esp_err_t bme_write(uint8_t reg, uint8_t v) {
    uint8_t b[2] = {reg, v};
    return i2c_master_write_to_device(I2C_PORT, BME280_ADDR, b, 2, pdMS_TO_TICKS(50));
}

static bme280_calib_t s_cal;

static esp_err_t bme_init(void) {
    uint8_t id = 0, c1[26], c2[7];
    esp_err_t err = bme_read(BME280_REG_ID, &id, 1);
    if (err != ESP_OK) return err;
    if (id != 0x60) { ESP_LOGE(TAG, "chip id 0x%02x is not a BME280 (0x60)", id); return ESP_ERR_NOT_FOUND; }
    if ((err = bme_read(BME280_REG_CALIB1, c1, sizeof c1)) || (err = bme_read(BME280_REG_CALIB2, c2, sizeof c2))) return err;
    bme280_parse_calib(c1, c2, &s_cal);
    /* x1 oversampling for all three, normal mode, 1000 ms standby, IIR filter off (weather-station settings, datasheet 3.5.1) */
    if ((err = bme_write(BME280_REG_CTRL_HUM, 0x01))) return err;   /* must be written before ctrl_meas */
    if ((err = bme_write(BME280_REG_CONFIG, 0xA0))) return err;
    return bme_write(BME280_REG_CTRL_MEAS, 0x27);
}

static esp_err_t bme_sample(bme280_reading_t *out) {
    uint8_t d[8];
    esp_err_t err = bme_read(BME280_REG_DATA, d, sizeof d);
    if (err != ESP_OK) return err;
    int32_t p, t, h;
    bme280_parse_raw(d, &p, &t, &h);
    if (t == 0x80000) return ESP_ERR_INVALID_STATE;     /* "skipped" marker: no measurement yet */
    *out = bme280_compensate(&s_cal, p, t, h);
    return ESP_OK;
}

/* ---------------------------------------------------------------- MQTT over lwIP */
static int sock_send(void *ctx, const uint8_t *b, size_t n) { return send(*(int *)ctx, b, n, 0); }

static int sock_recv(void *ctx, uint8_t *b, size_t n, int timeout_ms) {
    int fd = *(int *)ctx;
    fd_set rd;
    FD_ZERO(&rd);
    FD_SET(fd, &rd);
    struct timeval tv = {.tv_sec = timeout_ms / 1000, .tv_usec = (timeout_ms % 1000) * 1000};
    int r = select(fd + 1, &rd, NULL, NULL, &tv);
    if (r <= 0) return r;
    int got = recv(fd, b, n, 0);
    return got == 0 ? -1 : got;
}

static int tcp_connect(void) {
    char port[8];
    snprintf(port, sizeof port, "%d", MQTT_PORT);
    struct addrinfo hints = {.ai_socktype = SOCK_STREAM}, *res = NULL;
    if (getaddrinfo(MQTT_HOST, port, &hints, &res) != 0 || !res) return -1;
    int fd = socket(res->ai_family, res->ai_socktype, 0);
    if (fd >= 0 && connect(fd, res->ai_addr, res->ai_addrlen) != 0) { close(fd); fd = -1; }
    freeaddrinfo(res);
    return fd;
}

static void on_command(void *user, const char *topic, size_t tl, const uint8_t *payload, size_t len) {
    (void)user;
    if (station_command(&s_station, (const char *)payload, len))
        ESP_LOGI(TAG, "command on %.*s: interval now %u ms", (int)tl, topic, (unsigned)s_station.interval_ms);
}

/* ---------------------------------------------------------------- main loop */
static void show(const bme280_reading_t *r, int mqtt_up) {
    char lines[4][17];
    station_oled_lines(&s_station, r, mqtt_up, lines);
    for (int i = 0; i < 4; i++) oled_text(i * 2, lines[i]);
}

void app_main(void) {
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) { nvs_flash_erase(); nvs_flash_init(); }
    if (USING_PLACEHOLDER_SECRETS) ESP_LOGW(TAG, "built without secrets.h: WiFi/MQTT settings are placeholders");
    ESP_ERROR_CHECK(i2c_init());
    if (oled_init(I2C_PORT) != ESP_OK) ESP_LOGW(TAG, "no OLED at 0x3C, continuing without display");
    while (bme_init() != ESP_OK) { ESP_LOGE(TAG, "BME280 not found at 0x76, retrying"); vTaskDelay(pdMS_TO_TICKS(2000)); }
    wifi_start();

    char t_state[48], t_status[48], t_cmd[48], json[160];
    snprintf(t_state, sizeof t_state, "weather/%s/state", s_station.id);
    snprintf(t_status, sizeof t_status, "weather/%s/status", s_station.id);
    snprintf(t_cmd, sizeof t_cmd, "weather/%s/cmd", s_station.id);
    int backoff_ms = 1000;

    for (;;) {  /* outer loop: (re)connect */
        xEventGroupWaitBits(s_net, WIFI_UP, pdFALSE, pdTRUE, portMAX_DELAY);
        int fd = tcp_connect();
        mqtt_client_t c = {.io = {sock_send, sock_recv, &fd}, .on_message = on_command};
        if (fd < 0 || mqtt_connect(&c, s_station.id, 30, t_status, "offline") || mqtt_publish(&c, t_status, "online", 1) ||
            mqtt_subscribe(&c, t_cmd)) {
            ESP_LOGW(TAG, "MQTT connect to %s failed, retry in %d ms", MQTT_HOST, backoff_ms);
            if (fd >= 0) close(fd);
            vTaskDelay(pdMS_TO_TICKS(backoff_ms));
            backoff_ms = backoff_ms < 30000 ? backoff_ms * 2 : 30000;   /* exponential back-off */
            continue;
        }
        ESP_LOGI(TAG, "MQTT connected to %s:%d", MQTT_HOST, MQTT_PORT);
        backoff_ms = 1000;
        int64_t next = esp_timer_get_time(), last_ping = next;
        for (;;) {  /* inner loop: sample, publish, listen */
            int64_t now = esp_timer_get_time();
            if (now >= next) {
                next = now + (int64_t)s_station.interval_ms * 1000;
                bme280_reading_t r;
                if (bme_sample(&r) == ESP_OK) {
                    s_station.seq++;
                    station_json(&s_station, &r, (uint32_t)(now / 1000000), json, sizeof json);
                    if (mqtt_publish(&c, t_state, json, 1)) break;
                    show(&r, 1);
                    ESP_LOGI(TAG, "%s", json);
                }
            }
            if (now - last_ping > 15 * 1000000LL) { if (mqtt_ping(&c)) break; last_ping = now; }
            if (mqtt_poll(&c, 200) < 0) break;
        }
        ESP_LOGW(TAG, "connection lost, reconnecting");
        close(fd);
    }
}
