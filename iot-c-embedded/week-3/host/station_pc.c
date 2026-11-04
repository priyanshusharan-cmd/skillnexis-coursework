/* PC build of the weather station: the same MQTT client, BME280 compensation and station logic as
 * the ESP32 firmware, with POSIX sockets instead of lwIP and a virtual BME280 instead of the chip.
 *
 * The virtual sensor produces *raw* ADC values (found by searching the compensation formula), so every
 * reading goes through exactly the code path a real chip would.
 *
 *   ./build/station_pc [host] [port] [seconds] [client-id]
 */
#define _POSIX_C_SOURCE 200809L
#include <math.h>
#include <netdb.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#include "../common/bme280.h"
#include "../common/mqtt.h"
#include "../common/station.h"

static int sock_send(void *ctx, const uint8_t *b, size_t n) { return (int)send(*(int *)ctx, b, n, MSG_NOSIGNAL); }
static int sock_recv(void *ctx, uint8_t *b, size_t n, int timeout_ms) {
    struct pollfd p = {.fd = *(int *)ctx, .events = POLLIN};
    int r = poll(&p, 1, timeout_ms);
    if (r <= 0) return r;
    ssize_t got = recv(*(int *)ctx, b, n, 0);
    return got == 0 ? -1 : (int)got; /* 0 bytes = broker closed the connection */
}

static int tcp_connect(const char *host, const char *port) {
    struct addrinfo hints = {.ai_socktype = SOCK_STREAM}, *res;
    if (getaddrinfo(host, port, &hints, &res)) return -1;
    int fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (fd >= 0 && connect(fd, res->ai_addr, res->ai_addrlen)) { close(fd); fd = -1; }
    freeaddrinfo(res);
    return fd;
}

static uint32_t now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint32_t)(ts.tv_sec * 1000 + ts.tv_nsec / 1000000);
}

/* ---------------------------------------------------------------- virtual BME280 */
static const bme280_calib_t CAL = {27504, 26435, -1000, 36477, -10685, 3024, 2855, 140, -7, 15500, -14600, 6000, 75, 0, 362, 324, 0, 30};

/* Smallest raw value whose compensated output reaches the target (each formula is monotonic). */
static int32_t search(int32_t lo, int32_t hi, int increasing, double target, double (*f)(int32_t, int32_t), int32_t arg) {
    while (lo < hi) {
        int32_t mid = lo + (hi - lo) / 2;
        double v = f(mid, arg);
        if (increasing ? v < target : v > target) lo = mid + 1; else hi = mid;
    }
    return lo;
}
static double temp_of(int32_t adc_t, int32_t u) { (void)u; return ((bme280_t_fine(&CAL, adc_t) * 5 + 128) >> 8) / 100.0; }
static double press_of(int32_t adc_p, int32_t t_fine) { return bme280_pressure_q24_8(&CAL, adc_p, t_fine) / 25600.0; }
static double hum_of(int32_t adc_h, int32_t t_fine) { return bme280_humidity_q22_10(&CAL, adc_h, t_fine) / 1024.0; }

/* Weather over a simulated day squeezed into 2 minutes: temperature 22-31 C, humidity moves the other way. */
static void virtual_sensor(double t_s, int32_t *adc_p, int32_t *adc_t, int32_t *adc_h) {
    const double pi = 3.14159265358979323846;
    double phase = 2 * pi * t_s / 120.0;
    double temp = 26.5 + 4.5 * sin(phase), hum = 55.0 - 15.0 * sin(phase), hpa = 1006.5 + 1.2 * sin(phase / 3);
    *adc_t = search(300000, 700000, 1, temp, temp_of, 0);
    int32_t t_fine = bme280_t_fine(&CAL, *adc_t);
    *adc_p = search(200000, 600000, 0, hpa, press_of, t_fine);  /* pressure falls as adc_p rises */
    *adc_h = search(0, 65535, 1, hum, hum_of, t_fine);
}

/* ---------------------------------------------------------------- main loop */
static station_t st = {.id = "ws-01", .interval_ms = 2000};
static int interval_changes;

static void on_message(void *user, const char *topic, size_t tl, const uint8_t *payload, size_t len) {
    (void)user;
    printf("[cmd] %.*s <- %.*s\n", (int)tl, topic, (int)len, (const char *)payload);
    if (station_command(&st, (const char *)payload, len)) {
        interval_changes++;
        printf("[cmd] publish interval is now %u ms\n", st.interval_ms);
    }
}

int main(int argc, char **argv) {
    const char *host = argc > 1 ? argv[1] : "127.0.0.1", *port = argc > 2 ? argv[2] : "1883";
    int seconds = argc > 3 ? atoi(argv[3]) : 30;
    if (argc > 4) snprintf(st.id, sizeof st.id, "%s", argv[4]);
    char topic_state[64], topic_status[64], topic_cmd[64];
    snprintf(topic_state, sizeof topic_state, "weather/%s/state", st.id);
    snprintf(topic_status, sizeof topic_status, "weather/%s/status", st.id);
    snprintf(topic_cmd, sizeof topic_cmd, "weather/%s/cmd", st.id);

    int fd = tcp_connect(host, port);
    if (fd < 0) { fprintf(stderr, "cannot reach broker %s:%s\n", host, port); return 2; }
    mqtt_client_t c = {.io = {sock_send, sock_recv, &fd}, .on_message = on_message};
    int r = mqtt_connect(&c, st.id, 30, topic_status, "offline");  /* broker publishes "offline" if we vanish */
    if (r) { fprintf(stderr, "CONNECT failed: %d\n", r); return 3; }
    printf("[mqtt] connected to %s:%s as %s\n", host, port, st.id);
    if (mqtt_publish(&c, topic_status, "online", 1) || mqtt_subscribe(&c, topic_cmd)) return 4;
    printf("[mqtt] subscribed to %s\n", topic_cmd);

    uint32_t start = now_ms(), next = start, last_ping = start;
    while ((int)(now_ms() - start) < seconds * 1000) {
        if ((int32_t)(now_ms() - next) >= 0) {
            next += st.interval_ms;
            int32_t ap, at, ah;
            virtual_sensor((now_ms() - start) / 1000.0, &ap, &at, &ah);
            bme280_reading_t rd = bme280_compensate(&CAL, ap, at, ah);
            char json[160], lines[4][17];
            st.seq++;
            station_json(&st, &rd, (now_ms() - start) / 1000, json, sizeof json);
            if (mqtt_publish(&c, topic_state, json, 1)) { fprintf(stderr, "publish failed\n"); return 5; }
            station_oled_lines(&st, &rd, 1, lines);
            printf("[pub] %s   | OLED: %s / %s / %s / %s\n", json, lines[0], lines[1], lines[2], lines[3]);
            fflush(stdout);
        }
        if (now_ms() - last_ping > 15000) { if (mqtt_ping(&c)) return 6; last_ping = now_ms(); }
        if ((r = mqtt_poll(&c, 100)) < 0) { fprintf(stderr, "poll error %d\n", r); return 7; }
    }
    mqtt_publish(&c, topic_status, "offline", 1);
    mqtt_disconnect(&c);
    close(fd);
    printf("[mqtt] done: %u readings, %d interval change(s)\n", st.seq, interval_changes);
    return 0;
}
