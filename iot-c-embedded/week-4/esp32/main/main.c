/* Smart agriculture node: one wake cycle per boot.
 *
 *   boot (timer or button) -> WiFi + MQTT (bounded time; the farm keeps working offline)
 *   -> app_wake_cycle(): FreeRTOS tasks sample, decide, water, publish
 *   -> deep sleep for the time the controller chose (5 min .. 2 h), button on GPIO25 wakes early
 *
 * OTA safety: the bootloader's rollback is enabled. A freshly updated image boots "pending verify" and
 * is marked valid only after it reaches the MQTT broker. If it crashes or cannot connect three boots in
 * a row, it rolls back to the previous firmware. */
#include <string.h>

#include "../../app/app.h"
#include "../../app/hal.h"
#include "driver/rtc_io.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_ota_ops.h"
#include "esp_sleep.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"
#include "hal_esp32.h"
#include "lwip/netdb.h"
#include "lwip/sockets.h"
#include "mqtt.h"
#include "nvs_flash.h"

#if __has_include("secrets.h")
#include "secrets.h"
#else
#include "secrets.example.h"   /* CI builds with placeholders; copy to secrets.h for a real node */
#endif

static const char *TAG = "node";
#define WAKE_BUTTON GPIO_NUM_25
#define WIFI_TIMEOUT_MS 8000

RTC_DATA_ATTR static app_retained_t s_ret;           /* survives deep sleep */
RTC_DATA_ATTR static uint8_t s_failed_verify_boots;

static EventGroupHandle_t s_wifi;

static void on_event(void *a, esp_event_base_t base, int32_t id, void *d) {
    (void)a; (void)d;
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START) esp_wifi_connect();
    else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) esp_wifi_connect();
    else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) xEventGroupSetBits(s_wifi, BIT0);
}

static bool wifi_up(void) {
    s_wifi = xEventGroupCreate();
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, on_event, NULL);
    esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, on_event, NULL);
    wifi_config_t wc = {0};
    strncpy((char *)wc.sta.ssid, WIFI_SSID, sizeof wc.sta.ssid);
    strncpy((char *)wc.sta.password, WIFI_PASS, sizeof wc.sta.password);
    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_set_config(WIFI_IF_STA, &wc);
    esp_wifi_start();
    return xEventGroupWaitBits(s_wifi, BIT0, pdFALSE, pdTRUE, pdMS_TO_TICKS(WIFI_TIMEOUT_MS)) & BIT0;
}

static int s_fd = -1;
static int sock_send(void *c, const uint8_t *b, size_t n) { return send(*(int *)c, b, n, 0); }
static int sock_recv(void *c, uint8_t *b, size_t n, int timeout_ms) {
    int fd = *(int *)c;
    fd_set rd;
    FD_ZERO(&rd);
    FD_SET(fd, &rd);
    struct timeval tv = {.tv_sec = timeout_ms / 1000, .tv_usec = (timeout_ms % 1000) * 1000};
    int r = select(fd + 1, &rd, NULL, NULL, &tv);
    if (r <= 0) return r;
    int got = recv(fd, b, n, 0);
    return got == 0 ? -1 : got;
}

static void on_message(void *u, const char *topic, size_t tl, const uint8_t *p, size_t n) {
    (void)u; (void)topic; (void)tl;
    hal_esp32_on_command((const char *)p, n);
}

static bool mqtt_up(mqtt_client_t *c) {
    char port[8];
    snprintf(port, sizeof port, "%d", MQTT_PORT);
    struct addrinfo hints = {.ai_socktype = SOCK_STREAM}, *res = NULL;
    if (getaddrinfo(MQTT_HOST, port, &hints, &res) || !res) return false;
    s_fd = socket(res->ai_family, res->ai_socktype, 0);
    bool ok = s_fd >= 0 && connect(s_fd, res->ai_addr, res->ai_addrlen) == 0;
    freeaddrinfo(res);
    if (!ok) return false;
    char status[48], cmd[48];
    snprintf(status, sizeof status, "farm/%s/status", NODE_ID);
    snprintf(cmd, sizeof cmd, "farm/%s/cmd", NODE_ID);
    *c = (mqtt_client_t){.io = {sock_send, sock_recv, &s_fd}, .on_message = on_message};
    /* persistent session is not needed: commands are sent retained by the dashboard and cleared after use */
    return mqtt_connect(c, NODE_ID, 60, status, "offline") == MQTT_OK && mqtt_publish(c, status, "online", true) == MQTT_OK &&
           mqtt_subscribe(c, cmd) == MQTT_OK;
}

static void confirm_or_rollback(bool connected) {
    esp_ota_img_states_t st;
    const esp_partition_t *running = esp_ota_get_running_partition();
    if (esp_ota_get_state_partition(running, &st) != ESP_OK || st != ESP_OTA_IMG_PENDING_VERIFY) return;
    if (connected) {
        ESP_LOGI(TAG, "new firmware reached the broker: marking it valid");
        esp_ota_mark_app_valid_cancel_rollback();
        s_failed_verify_boots = 0;
    } else if (++s_failed_verify_boots >= 3) {
        ESP_LOGE(TAG, "new firmware failed to connect 3 times: rolling back");
        esp_ota_mark_app_invalid_rollback_and_reboot();
    }
}

static void node_task(void *arg) {
    (void)arg;
    esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
    if (s_ret.magic != 0xA6510001u) {        /* power-on: start fresh */
        memset(&s_ret, 0, sizeof s_ret);
        s_ret.magic = 0xA6510001u;
        irrig_init(&s_ret.irrig, hal_now_s());
    }
    s_ret.boots++;

    static mqtt_client_t mqtt;
    bool online = wifi_up() && mqtt_up(&mqtt);
    confirm_or_rollback(online);
    hal_esp32_init(online ? &mqtt : NULL, NODE_ID);
    if (cause == ESP_SLEEP_WAKEUP_EXT0) hal_esp32_on_command("water", 5);   /* button = water now */
    ESP_LOGI(TAG, "boot %lu, wake cause %d, %s", (unsigned long)s_ret.boots, cause, online ? "online" : "OFFLINE (local control only)");

    app_config_t cfg = APP_DEFAULT_CONFIG;
    uint32_t sleep_s = app_wake_cycle(&s_ret, &cfg);

    if (online) {
        mqtt_disconnect(&mqtt);
        close(s_fd);
    }
    esp_wifi_stop();
    ESP_LOGI(TAG, "deep sleep for %lu s", (unsigned long)sleep_s);
    esp_sleep_enable_timer_wakeup((uint64_t)sleep_s * 1000000ULL);
    rtc_gpio_pullup_en(WAKE_BUTTON);
    rtc_gpio_pulldown_dis(WAKE_BUTTON);
    esp_sleep_enable_ext0_wakeup(WAKE_BUTTON, 0);           /* button pulls the pin low */
    esp_deep_sleep_start();
}

void app_main(void) {
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) { nvs_flash_erase(); nvs_flash_init(); }
    xTaskCreate(node_task, "node", 6144, NULL, 5, NULL);
}
