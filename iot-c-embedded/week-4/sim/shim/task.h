#ifndef SHIM_TASK_H
#define SHIM_TASK_H
#include "FreeRTOS.h"
typedef struct shim_task *TaskHandle_t;
typedef void (*TaskFunction_t)(void *);
BaseType_t xTaskCreate(TaskFunction_t fn, const char *name, uint32_t stack, void *arg, UBaseType_t prio, TaskHandle_t *out);
void vTaskDelete(TaskHandle_t t);
void vTaskSuspend(TaskHandle_t t);
void vTaskDelay(TickType_t ticks);
TickType_t xTaskGetTickCount(void);
void vTaskStartScheduler(void);
#endif
