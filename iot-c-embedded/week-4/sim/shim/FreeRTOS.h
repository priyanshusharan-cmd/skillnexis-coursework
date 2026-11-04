/* Minimal pthread stand-in for the FreeRTOS calls used by app/app.c, so the task code can be
 * checked quickly on any PC. The CI job runs the same code on the real FreeRTOS kernel (POSIX port). */
#ifndef SHIM_FREERTOS_H
#define SHIM_FREERTOS_H
#include <stdint.h>
typedef uint32_t TickType_t;
typedef long BaseType_t;
typedef unsigned long UBaseType_t;
typedef uint32_t EventBits_t;
#define pdTRUE 1
#define pdFALSE 0
#define pdPASS 1
#define portMAX_DELAY 0xFFFFFFFFu
#define pdMS_TO_TICKS(ms) ((TickType_t)(ms))
#endif
