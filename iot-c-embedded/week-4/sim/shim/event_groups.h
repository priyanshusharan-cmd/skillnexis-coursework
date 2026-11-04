#ifndef SHIM_EVENT_GROUPS_H
#define SHIM_EVENT_GROUPS_H
#include "FreeRTOS.h"
typedef struct shim_events *EventGroupHandle_t;
EventGroupHandle_t xEventGroupCreate(void);
EventBits_t xEventGroupSetBits(EventGroupHandle_t e, EventBits_t bits);
EventBits_t xEventGroupClearBits(EventGroupHandle_t e, EventBits_t bits);
EventBits_t xEventGroupGetBits(EventGroupHandle_t e);
EventBits_t xEventGroupWaitBits(EventGroupHandle_t e, EventBits_t bits, BaseType_t clear, BaseType_t all, TickType_t wait);
void vEventGroupDelete(EventGroupHandle_t e);
#endif
