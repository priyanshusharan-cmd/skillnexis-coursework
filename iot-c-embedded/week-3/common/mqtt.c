#include "mqtt.h"

#include <string.h>

enum { CONNECT = 1, CONNACK = 2, PUBLISH = 3, SUBSCRIBE = 8, SUBACK = 9, PINGREQ = 12, PINGRESP = 13, DISCONNECT = 14 };

size_t mqtt_encode_length(uint32_t value, uint8_t out[4]) {
    if (value > 268435455u) return 0;
    size_t n = 0;
    do {
        uint8_t byte = value % 128u;
        value /= 128u;
        if (value) byte |= 0x80u;
        out[n++] = byte;
    } while (value);
    return n;
}

int mqtt_decode_length(const uint8_t *in, size_t avail, uint32_t *value) {
    uint32_t v = 0, mult = 1;
    for (size_t i = 0; i < 4; i++) {
        if (i >= avail) return 0;
        v += (uint32_t)(in[i] & 0x7Fu) * mult;
        if (!(in[i] & 0x80u)) { *value = v; return (int)i + 1; }
        mult *= 128u;
    }
    return -1; /* more than 4 bytes */
}

/* Writes the fixed header for a body of body_len bytes at the start of buf; returns header size or 0. */
static size_t put_header(uint8_t *buf, size_t size, uint8_t first, size_t body_len) {
    uint8_t len[4];
    size_t n = mqtt_encode_length((uint32_t)body_len, len);
    if (!n || 1 + n + body_len > size) return 0;
    buf[0] = first;
    memcpy(buf + 1, len, n);
    return 1 + n;
}

static uint8_t *put_str(uint8_t *p, const char *s, size_t len) {
    *p++ = (uint8_t)(len >> 8);
    *p++ = (uint8_t)len;
    memcpy(p, s, len);
    return p + len;
}

size_t mqtt_build_connect(uint8_t *buf, size_t size, const char *client_id, uint16_t keepalive_s,
                          const char *will_topic, const char *will_msg) {
    size_t id_len = strlen(client_id);
    int will = will_topic && will_msg;
    size_t body = 10 + 2 + id_len + (will ? 2 + strlen(will_topic) + 2 + strlen(will_msg) : 0);
    size_t h = put_header(buf, size, CONNECT << 4, body);
    if (!h) return 0;
    uint8_t *p = buf + h;
    p = put_str(p, "MQTT", 4);
    *p++ = 4;                                             /* protocol level 3.1.1 */
    *p++ = (uint8_t)(0x02u | (will ? 0x04u | 0x20u : 0)); /* clean session; will flag + will retain */
    *p++ = (uint8_t)(keepalive_s >> 8);
    *p++ = (uint8_t)keepalive_s;
    p = put_str(p, client_id, id_len);
    if (will) {
        p = put_str(p, will_topic, strlen(will_topic));
        p = put_str(p, will_msg, strlen(will_msg));
    }
    return (size_t)(p - buf);
}

size_t mqtt_build_publish(uint8_t *buf, size_t size, const char *topic, const uint8_t *payload, size_t len, int retain) {
    size_t t_len = strlen(topic);
    size_t h = put_header(buf, size, (uint8_t)(PUBLISH << 4 | (retain ? 1 : 0)), 2 + t_len + len);
    if (!h) return 0;
    uint8_t *p = put_str(buf + h, topic, t_len);
    memcpy(p, payload, len);
    return (size_t)(p - buf) + len;
}

size_t mqtt_build_subscribe(uint8_t *buf, size_t size, uint16_t packet_id, const char *topic) {
    size_t t_len = strlen(topic);
    size_t h = put_header(buf, size, SUBSCRIBE << 4 | 0x02, 2 + 2 + t_len + 1); /* reserved bits 0010 */
    if (!h) return 0;
    uint8_t *p = buf + h;
    *p++ = (uint8_t)(packet_id >> 8);
    *p++ = (uint8_t)packet_id;
    p = put_str(p, topic, t_len);
    *p++ = 0; /* requested QoS 0 */
    return (size_t)(p - buf);
}

/* ------------------------------------------------------------------ client */
static int send_all(mqtt_client_t *c, const uint8_t *buf, size_t len) {
    while (len) {
        int n = c->io.send(c->io.ctx, buf, len);
        if (n <= 0) return MQTT_ERR_IO;
        buf += n;
        len -= (size_t)n;
    }
    return MQTT_OK;
}

/* Reads one complete packet into c->rx. Returns packet type (1..15), 0 on timeout, or an error. */
static int read_packet(mqtt_client_t *c, int timeout_ms, uint32_t *body_off, uint32_t *body_len) {
    for (;;) {
        if (c->rx_len >= 2) {
            uint32_t rl;
            int n = mqtt_decode_length(c->rx + 1, c->rx_len - 1, &rl);
            if (n < 0) return MQTT_ERR_PROTOCOL;
            if (n > 0) {
                size_t total = 1u + (size_t)n + rl;
                if (total > sizeof c->rx) return MQTT_ERR_TOO_BIG;
                if (c->rx_len >= total) {
                    *body_off = 1u + (uint32_t)n;
                    *body_len = rl;
                    return c->rx[0] >> 4;
                }
            }
        }
        int got = c->io.recv(c->io.ctx, c->rx + c->rx_len, sizeof c->rx - c->rx_len, timeout_ms);
        if (got < 0) return MQTT_ERR_IO;
        if (got == 0) return 0;
        c->rx_len += (size_t)got;
    }
}

static void consume(mqtt_client_t *c, uint32_t off, uint32_t len) {
    size_t used = off + len;
    memmove(c->rx, c->rx + used, c->rx_len - used);
    c->rx_len -= used;
}

static int handle(mqtt_client_t *c, int type, uint32_t off, uint32_t len) {
    const uint8_t *b = c->rx + off;
    if (type == PUBLISH) {
        if (len < 2) return MQTT_ERR_PROTOCOL;
        size_t t_len = (size_t)(b[0] << 8 | b[1]);
        size_t skip = 2 + t_len + (((c->rx[0] >> 1) & 3) ? 2 : 0); /* packet id only when QoS > 0 */
        if (skip > len) return MQTT_ERR_PROTOCOL;
        if (c->on_message) c->on_message(c->user, (const char *)b + 2, t_len, b + skip, len - skip);
    }
    consume(c, off, len);
    return MQTT_OK;
}

/* Waits for a packet of the given type, dispatching any PUBLISH that arrives first. */
static int expect(mqtt_client_t *c, int want, int timeout_ms, uint8_t *first_bytes, size_t n) {
    for (int tries = 0; tries < 32; tries++) {
        uint32_t off, len;
        int type = read_packet(c, timeout_ms, &off, &len);
        if (type <= 0) return type == 0 ? MQTT_ERR_TIMEOUT : type;
        if (type == want) {
            if (len < n) return MQTT_ERR_PROTOCOL;
            if (first_bytes) memcpy(first_bytes, c->rx + off, n);
            consume(c, off, len);
            return MQTT_OK;
        }
        int r = handle(c, type, off, len);
        if (r) return r;
    }
    return MQTT_ERR_PROTOCOL;
}

int mqtt_connect(mqtt_client_t *c, const char *client_id, uint16_t keepalive_s, const char *will_topic, const char *will_msg) {
    uint8_t buf[256];
    c->rx_len = 0;
    c->keepalive_s = keepalive_s;
    c->next_packet_id = 1;
    size_t n = mqtt_build_connect(buf, sizeof buf, client_id, keepalive_s, will_topic, will_msg);
    if (!n) return MQTT_ERR_TOO_BIG;
    int r = send_all(c, buf, n);
    if (r) return r;
    uint8_t ack[2];
    r = expect(c, CONNACK, 5000, ack, 2);
    if (r) return r;
    return ack[1] == 0 ? MQTT_OK : MQTT_ERR_REFUSED;
}

int mqtt_publish(mqtt_client_t *c, const char *topic, const char *payload, int retain) {
    uint8_t buf[512];
    size_t n = mqtt_build_publish(buf, sizeof buf, topic, (const uint8_t *)payload, strlen(payload), retain);
    return n ? send_all(c, buf, n) : MQTT_ERR_TOO_BIG;
}

int mqtt_subscribe(mqtt_client_t *c, const char *topic) {
    uint8_t buf[256], ack[3];
    uint16_t id = c->next_packet_id++;
    if (!c->next_packet_id) c->next_packet_id = 1;
    size_t n = mqtt_build_subscribe(buf, sizeof buf, id, topic);
    if (!n) return MQTT_ERR_TOO_BIG;
    int r = send_all(c, buf, n);
    if (r) return r;
    r = expect(c, SUBACK, 5000, ack, 3);
    if (r) return r;
    if ((uint16_t)(ack[0] << 8 | ack[1]) != id) return MQTT_ERR_PROTOCOL;
    return ack[2] == 0x80 ? MQTT_ERR_REFUSED : MQTT_OK;
}

int mqtt_ping(mqtt_client_t *c) {
    const uint8_t req[2] = { PINGREQ << 4, 0 };
    int r = send_all(c, req, 2);
    return r ? r : expect(c, PINGRESP, 5000, NULL, 0);
}

int mqtt_disconnect(mqtt_client_t *c) {
    const uint8_t req[2] = { DISCONNECT << 4, 0 };
    return send_all(c, req, 2);
}

int mqtt_poll(mqtt_client_t *c, int timeout_ms) {
    uint32_t off, len;
    int type = read_packet(c, timeout_ms, &off, &len);
    if (type <= 0) return type;  /* 0 = nothing arrived */
    return handle(c, type, off, len);
}
