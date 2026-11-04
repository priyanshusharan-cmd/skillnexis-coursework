/* pthread implementation of the shim. One tick = 1 ms of real time. Tasks are detached threads;
 * vTaskDelete marks a task dead (app.c only deletes tasks that have parked themselves in vTaskSuspend). */
#define _GNU_SOURCE
#include <errno.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "event_groups.h"
#include "queue.h"
#include "semphr.h"
#include "task.h"

static struct timespec t0;
static pthread_once_t once = PTHREAD_ONCE_INIT;
static void init_clock(void) { clock_gettime(CLOCK_MONOTONIC, &t0); }

TickType_t xTaskGetTickCount(void) {
    pthread_once(&once, init_clock);
    struct timespec n;
    clock_gettime(CLOCK_MONOTONIC, &n);
    return (TickType_t)((n.tv_sec - t0.tv_sec) * 1000 + (n.tv_nsec - t0.tv_nsec) / 1000000);
}

static void deadline(struct timespec *ts, TickType_t wait) {
    clock_gettime(CLOCK_REALTIME, ts);
    ts->tv_sec += wait / 1000;
    ts->tv_nsec += (long)(wait % 1000) * 1000000;
    if (ts->tv_nsec >= 1000000000) { ts->tv_sec++; ts->tv_nsec -= 1000000000; }
}

struct shim_task { pthread_t th; TaskFunction_t fn; void *arg; };
static void *trampoline(void *p) { struct shim_task *t = p; t->fn(t->arg); return NULL; }

BaseType_t xTaskCreate(TaskFunction_t fn, const char *name, uint32_t stack, void *arg, UBaseType_t prio, TaskHandle_t *out) {
    (void)name; (void)stack; (void)prio;
    struct shim_task *t = calloc(1, sizeof *t);
    t->fn = fn; t->arg = arg;
    pthread_attr_t a;
    pthread_attr_init(&a);
    pthread_attr_setdetachstate(&a, PTHREAD_CREATE_DETACHED);
    pthread_create(&t->th, &a, trampoline, t);
    pthread_attr_destroy(&a);
    if (out) *out = t;
    return pdPASS;
}

void vTaskSuspend(TaskHandle_t t) { (void)t; for (;;) pause(); }   /* parks the calling thread for good */
void vTaskDelete(TaskHandle_t t) { if (t) { pthread_cancel(t->th); } }
void vTaskDelay(TickType_t ticks) { usleep((useconds_t)ticks * 1000u); }
void vTaskStartScheduler(void) { for (;;) pause(); }

struct shim_queue { pthread_mutex_t m; pthread_cond_t c; unsigned char *buf; UBaseType_t len, item, head, count; };
QueueHandle_t xQueueCreate(UBaseType_t len, UBaseType_t item) {
    struct shim_queue *q = calloc(1, sizeof *q);
    pthread_mutex_init(&q->m, NULL); pthread_cond_init(&q->c, NULL);
    q->buf = calloc(len, item); q->len = len; q->item = item;
    return q;
}
BaseType_t xQueueSend(QueueHandle_t q, const void *it, TickType_t wait) {
    (void)wait;
    pthread_mutex_lock(&q->m);
    if (q->count == q->len) { pthread_mutex_unlock(&q->m); return pdFALSE; }
    memcpy(q->buf + ((q->head + q->count) % q->len) * q->item, it, q->item);
    q->count++;
    pthread_cond_broadcast(&q->c);
    pthread_mutex_unlock(&q->m);
    return pdTRUE;
}
BaseType_t xQueueReceive(QueueHandle_t q, void *it, TickType_t wait) {
    struct timespec ts;
    deadline(&ts, wait);
    pthread_mutex_lock(&q->m);
    while (!q->count) {
        int r = wait == portMAX_DELAY ? pthread_cond_wait(&q->c, &q->m) : pthread_cond_timedwait(&q->c, &q->m, &ts);
        if (r == ETIMEDOUT) { pthread_mutex_unlock(&q->m); return pdFALSE; }
    }
    memcpy(it, q->buf + q->head * q->item, q->item);
    q->head = (q->head + 1) % q->len;
    q->count--;
    pthread_mutex_unlock(&q->m);
    return pdTRUE;
}
void vQueueDelete(QueueHandle_t q) { (void)q; /* tasks were cancelled while possibly holding it: leak on purpose */ }

struct shim_mutex { pthread_mutex_t m; };
SemaphoreHandle_t xSemaphoreCreateMutex(void) { struct shim_mutex *m = calloc(1, sizeof *m); pthread_mutex_init(&m->m, NULL); return m; }
BaseType_t xSemaphoreTake(SemaphoreHandle_t m, TickType_t w) { (void)w; pthread_mutex_lock(&m->m); return pdTRUE; }
BaseType_t xSemaphoreGive(SemaphoreHandle_t m) { pthread_mutex_unlock(&m->m); return pdTRUE; }
void vSemaphoreDelete(SemaphoreHandle_t m) { (void)m; }

struct shim_events { pthread_mutex_t m; pthread_cond_t c; EventBits_t bits; };
EventGroupHandle_t xEventGroupCreate(void) {
    struct shim_events *e = calloc(1, sizeof *e);
    pthread_mutex_init(&e->m, NULL); pthread_cond_init(&e->c, NULL);
    return e;
}
EventBits_t xEventGroupSetBits(EventGroupHandle_t e, EventBits_t b) {
    pthread_mutex_lock(&e->m); e->bits |= b; EventBits_t v = e->bits; pthread_cond_broadcast(&e->c); pthread_mutex_unlock(&e->m); return v;
}
EventBits_t xEventGroupClearBits(EventGroupHandle_t e, EventBits_t b) {
    pthread_mutex_lock(&e->m); EventBits_t v = e->bits; e->bits &= ~b; pthread_mutex_unlock(&e->m); return v;
}
EventBits_t xEventGroupGetBits(EventGroupHandle_t e) { pthread_mutex_lock(&e->m); EventBits_t v = e->bits; pthread_mutex_unlock(&e->m); return v; }
EventBits_t xEventGroupWaitBits(EventGroupHandle_t e, EventBits_t b, BaseType_t clear, BaseType_t all, TickType_t wait) {
    struct timespec ts;
    deadline(&ts, wait);
    pthread_mutex_lock(&e->m);
    for (;;) {
        EventBits_t have = e->bits & b;
        if (all ? have == b : have != 0) break;
        int r = wait == portMAX_DELAY ? pthread_cond_wait(&e->c, &e->m) : pthread_cond_timedwait(&e->c, &e->m, &ts);
        if (r == ETIMEDOUT) break;
    }
    EventBits_t v = e->bits;
    if (clear) e->bits &= ~b;
    pthread_mutex_unlock(&e->m);
    return v;
}
void vEventGroupDelete(EventGroupHandle_t e) { (void)e; }
