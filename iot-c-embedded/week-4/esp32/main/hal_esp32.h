#pragma once
#include <stddef.h>

#include "mqtt.h"

void hal_esp32_init(mqtt_client_t *mqtt, const char *node_id);   /* mqtt may be NULL when offline */
void hal_esp32_on_command(const char *payload, size_t len);
