// Smart-home room node (ESP32, ESP-IDF 5.3): sensors -> on-device occupancy model (TensorFlow Lite Micro)
// -> AES-GCM sealed telemetry over MQTT/TLS with a client certificate -> relays for light and fan.
//
//   PIR HC-SR501 GPIO27 | MAX4466 mic GPIO34 (ADC1_CH6) | LDR divider GPIO35 (ADC1_CH7) | LM35 GPIO32 (ADC1_CH4)
//   light relay GPIO25  | fan relay GPIO26
//
// Every boot starts with a model self-test against vectors from the Python interpreter (also run in QEMU in CI).
// If the hub is unreachable for 10 minutes the node keeps the house usable on its own with the same model.
#include <cmath>
#include <cstdio>
#include <cstring>
#include <ctime>

#include "driver/gpio.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_netif_sntp.h"
#include "esp_random.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "mqtt_client.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "features.h"
#include "model_data.h"
#include "secure_payload.h"
#include "test_vectors.h"

static const char* TAG = "node";
extern const char ca_crt[] asm("_binary_ca_crt_start");
extern const char device_crt[] asm("_binary_device_crt_start");
extern const char device_key[] asm("_binary_device_key_start");

constexpr gpio_num_t PIN_PIR = GPIO_NUM_27, PIN_LIGHT = GPIO_NUM_25, PIN_FAN = GPIO_NUM_26;
constexpr adc_channel_t CH_MIC = ADC_CHANNEL_6, CH_LDR = ADC_CHANNEL_7, CH_TEMP = ADC_CHANNEL_4;

// ---------------- model ----------------
namespace {
constexpr int kArenaSize = 4 * 1024;
alignas(16) uint8_t g_arena[kArenaSize];
tflite::MicroInterpreter* g_interp = nullptr;

void model_init() {
  const tflite::Model* model = tflite::GetModel(g_occupancy_model);
  if (model->version() != TFLITE_SCHEMA_VERSION) ESP_LOGE(TAG, "model schema %lu != %d", model->version(), TFLITE_SCHEMA_VERSION);
  static tflite::MicroMutableOpResolver<2> resolver;   // only the ops this network uses
  resolver.AddFullyConnected();
  resolver.AddLogistic();
  static tflite::MicroInterpreter interp(model, resolver, g_arena, kArenaSize);
  if (interp.AllocateTensors() != kTfLiteOk) ESP_LOGE(TAG, "AllocateTensors failed");
  g_interp = &interp;
}

// raw features -> standardise -> int8 -> invoke; returns the raw int8 output and the probability
float model_predict(const float* raw, int8_t* q_out = nullptr) {
  TfLiteTensor* in = g_interp->input(0);
  for (int i = 0; i < kNumFeatures; i++) {
    float z = (raw[i] - kFeatureMean[i]) / kFeatureStd[i];
    int q = static_cast<int>(lroundf(z / in->params.scale)) + in->params.zero_point;
    in->data.int8[i] = static_cast<int8_t>(q < -128 ? -128 : q > 127 ? 127 : q);
  }
  g_interp->Invoke();
  TfLiteTensor* out = g_interp->output(0);
  if (q_out) *q_out = out->data.int8[0];
  return (out->data.int8[0] - out->params.zero_point) * out->params.scale;
}

bool model_selftest() {
  int exact = 0, within1 = 0, correct = 0;
  int64_t t0 = esp_timer_get_time();
  for (int v = 0; v < kNumVectors; v++) {
    int8_t q;
    float p = model_predict(kVectorFeatures[v], &q);
    exact += q == kVectorExpected[v];
    within1 += abs(q - kVectorExpected[v]) <= 1;
    correct += (p > 0.5f) == (kVectorLabel[v] == 1);
  }
  int64_t us = (esp_timer_get_time() - t0) / kNumVectors;
  bool ok = within1 == kNumVectors;
  printf("SELFTEST %s: %d/%d outputs identical to the Python interpreter, %d/%d within 1 LSB, %d/%d labels correct, "
         "%lld us per inference, arena used %u of %d bytes, model %u bytes\n",
         ok ? "PASS" : "FAIL", exact, kNumVectors, within1, kNumVectors, correct, kNumVectors, us,
         static_cast<unsigned>(g_interp->arena_used_bytes()), kArenaSize, g_occupancy_model_len);
  return ok;
}
}  // namespace

// ---------------- sensors ----------------
namespace {
adc_oneshot_unit_handle_t g_adc;
volatile bool g_motion = false;

void IRAM_ATTR pir_isr(void*) { g_motion = true; }

int adc_mv(adc_channel_t ch) {
  int raw = 0;
  adc_oneshot_read(g_adc, ch, &raw);
  return raw * 3300 / 4095;  // ~linear in the 150-2450 mV range at 12 dB attenuation
}

void sensors_init() {
  adc_oneshot_unit_init_cfg_t u = {};
  u.unit_id = ADC_UNIT_1;
  ESP_ERROR_CHECK(adc_oneshot_new_unit(&u, &g_adc));
  adc_oneshot_chan_cfg_t c = {};
  c.atten = ADC_ATTEN_DB_12;
  c.bitwidth = ADC_BITWIDTH_12;
  for (adc_channel_t ch : {CH_MIC, CH_LDR, CH_TEMP}) ESP_ERROR_CHECK(adc_oneshot_config_channel(g_adc, ch, &c));
  gpio_config_t in = {};
  in.pin_bit_mask = 1ULL << PIN_PIR;
  in.mode = GPIO_MODE_INPUT;
  in.intr_type = GPIO_INTR_POSEDGE;
  gpio_config(&in);
  gpio_install_isr_service(0);
  gpio_isr_handler_add(PIN_PIR, pir_isr, nullptr);
  gpio_config_t out = {};
  out.pin_bit_mask = (1ULL << PIN_LIGHT) | (1ULL << PIN_FAN);
  out.mode = GPIO_MODE_OUTPUT;
  gpio_config(&out);
}

// sound level over 100 ms: RMS of the AC part of the mic signal, as dB with a per-unit calibration offset
float sound_db() {
  static int s[200];
  double mean = 0, ss = 0;
  for (int i = 0; i < 200; i++) {
    s[i] = adc_mv(CH_MIC);
    mean += s[i];
    esp_rom_delay_us(500);
  }
  mean /= 200;
  for (int i = 0; i < 200; i++) ss += (s[i] - mean) * (s[i] - mean);
  double rms = sqrt(ss / 200) + 0.1;
  return static_cast<float>(20 * log10(rms) + CONFIG_SOUND_DB_OFFSET);
}

float temp_c() {
  int sum = 0;
  for (int i = 0; i < 16; i++) sum += adc_mv(CH_TEMP);
  return sum / 16 / 10.0f;  // LM35: 10 mV per °C
}

float lux() { return adc_mv(CH_LDR) * CONFIG_LDR_LUX_PER_V / 1000.0f; }
}  // namespace

// ---------------- network ----------------
namespace {
SecureChannel g_ch;
esp_mqtt_client_handle_t g_mqtt;
char g_topic_tel[48], g_topic_cmd[48], g_topic_status[48];
volatile int64_t g_last_cmd_us = 0;
volatile bool g_light = false, g_fan = false;
nvs_handle_t g_nvs;

void set_outputs(bool light, bool fan) {
  g_light = light;
  g_fan = fan;
  gpio_set_level(PIN_LIGHT, light);
  gpio_set_level(PIN_FAN, fan);
}

void mqtt_event(void*, esp_event_base_t, int32_t id, void* data) {
  auto* e = static_cast<esp_mqtt_event_handle_t>(data);
  if (id == MQTT_EVENT_CONNECTED) {
    esp_mqtt_client_subscribe(g_mqtt, g_topic_cmd, 1);
    esp_mqtt_client_publish(g_mqtt, g_topic_status, "online", 0, 1, 1);
  } else if (id == MQTT_EVENT_DATA && e->topic_len < 47 && e->data_len < 900) {
    char topic[48], msg[900], plain[256];
    memcpy(topic, e->topic, e->topic_len);
    topic[e->topic_len] = 0;
    memcpy(msg, e->data, e->data_len);
    msg[e->data_len] = 0;
    if (strcmp(topic, g_topic_cmd) || sp_open(&g_ch, topic, msg, plain, sizeof plain) < 0) {
      ESP_LOGW(TAG, "rejected message on %s", topic);
      return;
    }
    set_outputs(strstr(plain, "\"light\":1") != nullptr, strstr(plain, "\"fan\":1") != nullptr);
    g_last_cmd_us = esp_timer_get_time();
  }
}

void wifi_event(void*, esp_event_base_t base, int32_t id, void*) {
  if (base == WIFI_EVENT && (id == WIFI_EVENT_STA_START || id == WIFI_EVENT_STA_DISCONNECTED)) esp_wifi_connect();
}

void network_init() {
  ESP_ERROR_CHECK(esp_netif_init());
  ESP_ERROR_CHECK(esp_event_loop_create_default());
  esp_netif_create_default_wifi_sta();
  wifi_init_config_t wc = WIFI_INIT_CONFIG_DEFAULT();
  ESP_ERROR_CHECK(esp_wifi_init(&wc));
  esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_event, nullptr);
  wifi_config_t sta = {};
  strncpy(reinterpret_cast<char*>(sta.sta.ssid), CONFIG_WIFI_SSID, sizeof sta.sta.ssid);
  strncpy(reinterpret_cast<char*>(sta.sta.password), CONFIG_WIFI_PASSWORD, sizeof sta.sta.password);
  sta.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
  ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
  ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &sta));
  ESP_ERROR_CHECK(esp_wifi_start());

  esp_sntp_config_t sc = ESP_NETIF_SNTP_DEFAULT_CONFIG("pool.ntp.org");
  esp_netif_sntp_init(&sc);
  setenv("TZ", CONFIG_NODE_TZ, 1);
  tzset();

  esp_mqtt_client_config_t mc = {};
  mc.broker.address.uri = CONFIG_BROKER_URI;
  mc.broker.verification.certificate = ca_crt;           // only our CA's broker is trusted
  mc.credentials.client_id = CONFIG_DEVICE_ID;
  mc.credentials.authentication.certificate = device_crt;  // the CN is the device's identity in the broker ACL
  mc.credentials.authentication.key = device_key;
  mc.session.last_will.topic = g_topic_status;
  mc.session.last_will.msg = "offline";
  mc.session.last_will.qos = 1;
  mc.session.last_will.retain = 1;
  g_mqtt = esp_mqtt_client_init(&mc);
  esp_mqtt_client_register_event(g_mqtt, MQTT_EVENT_ANY, mqtt_event, nullptr);
  esp_mqtt_client_start(g_mqtt);
}

void keys_init() {
  g_ch.device = CONFIG_DEVICE_ID;
  size_t len = sizeof g_ch.key;
  // production: key provisioned into (encrypted) NVS at the factory; development: from menuconfig
  if (nvs_get_blob(g_nvs, "aeskey", g_ch.key, &len) != ESP_OK || len != 32)
    for (int i = 0; i < 32; i++) sscanf(CONFIG_AES_KEY_HEX + 2 * i, "%2hhx", &g_ch.key[i]);
  uint32_t ctr = 0;
  nvs_get_u32(g_nvs, "txctr", &ctr);
  g_ch.tx_counter = ctr + 100;  // counters are saved every 100 messages: skipping ahead never reuses one
  g_ch.rx_counter = 0;
}
}  // namespace

void sp_random(uint8_t* out, size_t n) { esp_fill_random(out, n); }

extern "C" void app_main() {
  model_init();
  bool ok = model_selftest();
#if CONFIG_NODE_SELFTEST_HALT
  // CI runs this build in QEMU, which emulates the CPU, flash and timers but not the WiFi/PHY radio
  printf("self-test-only build: halting (%s)\n", ok ? "ok" : "failed");
  while (true) vTaskDelay(portMAX_DELAY);
#endif
  if (!ok) ESP_LOGE(TAG, "model self-test failed: check the model/firmware versions");

  esp_err_t err = nvs_flash_init();
  if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
    nvs_flash_erase();
    nvs_flash_init();
  }
  nvs_open("node", NVS_READWRITE, &g_nvs);
  keys_init();
  snprintf(g_topic_tel, sizeof g_topic_tel, "home/%s/telemetry", CONFIG_ROOM);
  snprintf(g_topic_cmd, sizeof g_topic_cmd, "home/%s/cmd", CONFIG_ROOM);
  snprintf(g_topic_status, sizeof g_topic_status, "home/%s/status", CONFIG_ROOM);
  sensors_init();
  network_init();

  FeatureExtractor fx(strcmp(CONFIG_ROOM, "bedroom") == 0);
  float sound_sum = 0;
  int sound_n = 0;
  int64_t next_minute = esp_timer_get_time() + 60'000'000;
  while (true) {
    sound_sum += sound_db();  // ~10 sound windows per second, averaged over the minute
    sound_n++;
    vTaskDelay(pdMS_TO_TICKS(1));
    if (esp_timer_get_time() < next_minute) continue;
    next_minute += 60'000'000;

    time_t now = time(nullptr);
    struct tm t;
    localtime_r(&now, &t);
    bool motion = g_motion;
    g_motion = false;
    float temp = temp_c(), lx = lux(), snd = sound_sum / sound_n;
    sound_sum = 0;
    sound_n = 0;
    fx.push(motion, snd, temp, t.tm_hour * 60 + t.tm_min, t.tm_wday == 0 || t.tm_wday == 6);
    float f[kNumFeatures];
    fx.get(f);
    float p = model_predict(f);

    // edge autonomy: no command from the hub for 10 min -> decide locally with the same model
    if (esp_timer_get_time() - g_last_cmd_us > 600'000'000LL) set_outputs(p > 0.5f && lx < 100, p > 0.5f && temp > 28);

    char plain[200], sealed[700];
    snprintf(plain, sizeof plain, "{\"occ\":%.3f,\"motion\":%d,\"sound_db\":%.1f,\"temp_c\":%.2f,\"lux\":%.0f,\"light\":%d,\"fan\":%d}",
             p, motion, snd, temp, lx, g_light, g_fan);
    if (sp_seal(&g_ch, g_topic_tel, plain, sealed, sizeof sealed) > 0) esp_mqtt_client_publish(g_mqtt, g_topic_tel, sealed, 0, 1, 0);
    if (g_ch.tx_counter % 100 == 0) {
      nvs_set_u32(g_nvs, "txctr", g_ch.tx_counter);
      nvs_commit(g_nvs);
    }
  }
}
