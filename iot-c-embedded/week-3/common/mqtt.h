/* Minimal MQTT 3.1.1 client in portable C99 (no malloc).
 * The same file runs on the ESP32 (over lwIP sockets) and on a PC (over POSIX sockets):
 * the caller provides send/recv callbacks. Supports CONNECT, PUBLISH (QoS 0), SUBSCRIBE (QoS 0),
 * PINGREQ and DISCONNECT, which is what a sensor node needs. */
#ifndef MQTT_H
#define MQTT_H
#include <stddef.h>
#include <stdint.h>

typedef struct {
    int (*send)(void *ctx, const uint8_t *buf, size_t len);              /* returns bytes sent or < 0 */
    int (*recv)(void *ctx, uint8_t *buf, size_t len, int timeout_ms);    /* returns bytes, 0 on timeout, < 0 on error */
    void *ctx;
} mqtt_transport_t;

typedef void (*mqtt_message_cb)(void *user, const char *topic, size_t topic_len, const uint8_t *payload, size_t len);

typedef struct {
    mqtt_transport_t io;
    uint16_t keepalive_s;
    uint16_t next_packet_id;
    mqtt_message_cb on_message;
    void *user;
    uint8_t rx[512];
    size_t rx_len;
} mqtt_client_t;

enum {
    MQTT_OK = 0,
    MQTT_ERR_IO = -1,
    MQTT_ERR_PROTOCOL = -2,
    MQTT_ERR_REFUSED = -3,   /* CONNACK return code != 0 */
    MQTT_ERR_TOO_BIG = -4,
    MQTT_ERR_TIMEOUT = -5,
};

/* --- packet encoding (pure functions, unit-tested) ------------------------------------- */
/* Remaining-length varint: returns bytes written (1..4) or 0 if value > 268435455. */
size_t mqtt_encode_length(uint32_t value, uint8_t out[4]);
/* Decodes a varint; returns bytes consumed, 0 if incomplete, -1 if malformed. */
int mqtt_decode_length(const uint8_t *in, size_t avail, uint32_t *value);

size_t mqtt_build_connect(uint8_t *buf, size_t size, const char *client_id, uint16_t keepalive_s,
                          const char *will_topic, const char *will_msg);
size_t mqtt_build_publish(uint8_t *buf, size_t size, const char *topic, const uint8_t *payload, size_t len, int retain);
size_t mqtt_build_subscribe(uint8_t *buf, size_t size, uint16_t packet_id, const char *topic);

/* --- client ---------------------------------------------------------------------------- */
int mqtt_connect(mqtt_client_t *c, const char *client_id, uint16_t keepalive_s, const char *will_topic, const char *will_msg);
int mqtt_publish(mqtt_client_t *c, const char *topic, const char *payload, int retain);
int mqtt_subscribe(mqtt_client_t *c, const char *topic);
int mqtt_ping(mqtt_client_t *c);
int mqtt_disconnect(mqtt_client_t *c);
/* Reads and dispatches incoming packets for up to timeout_ms. Returns MQTT_OK or an error. */
int mqtt_poll(mqtt_client_t *c, int timeout_ms);

#endif
