"""Monitoring and logging: Prometheus metrics, one JSON log line per request, request IDs."""
import json
import logging
import sys
import time
import uuid

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest

log = logging.getLogger("blogly")


def setup_logging(level="INFO"):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.handlers[:] = [handler]
    log.setLevel(level)
    log.propagate = False


class Metrics:
    """Own registry per app instance, so tests and multiple apps never share counters."""

    def __init__(self):
        self.registry = CollectorRegistry()
        self.requests = Counter("blogly_http_requests_total", "HTTP requests", ["method", "route", "status"], registry=self.registry)
        self.latency = Histogram("blogly_http_request_duration_seconds", "Request latency", ["method", "route"],
                                 buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5), registry=self.registry)
        self.in_flight = Gauge("blogly_http_requests_in_flight", "Requests being served", registry=self.registry)
        self.ws_clients = Gauge("blogly_websocket_clients", "Connected WebSocket clients", registry=self.registry)
        self.events = Counter("blogly_events_published_total", "Real-time events broadcast", ["type"], registry=self.registry)
        self.signups = Counter("blogly_signups_total", "Accounts created", registry=self.registry)
        self.started = time.time()

    def render(self):
        return generate_latest(self.registry), CONTENT_TYPE_LATEST

    def summary(self):
        """Numbers for the built-in status dashboard."""
        total = errors = 0
        by_route = {}
        for metric in self.requests.collect():
            for s in metric.samples:
                if not s.name.endswith("_total"):
                    continue
                n = s.value
                total += n
                if s.labels["status"].startswith("5"):
                    errors += n
                key = f'{s.labels["method"]} {s.labels["route"]}'
                by_route[key] = by_route.get(key, 0) + n
        buckets, count = {}, 0
        for metric in self.latency.collect():
            for s in metric.samples:
                if s.name.endswith("_bucket"):
                    buckets[s.labels["le"]] = buckets.get(s.labels["le"], 0) + s.value
                elif s.name.endswith("_count"):
                    count += s.value
        p95 = None
        if count:
            for le, c in sorted(((float(k), v) for k, v in buckets.items())):
                if c >= 0.95 * count:
                    p95 = le
                    break
        return {
            "uptime_seconds": round(time.time() - self.started),
            "requests_total": int(total),
            "errors_5xx": int(errors),
            "error_rate": round(errors / total, 4) if total else 0,
            "p95_latency_ms_upper_bound": None if p95 is None or p95 == float("inf") else p95 * 1000,
            "requests_in_flight": int(self.in_flight._value.get()),
            "websocket_clients": int(self.ws_clients._value.get()),
            "signups": int(self.signups._value.get()),
            "top_routes": sorted(by_route.items(), key=lambda kv: -kv[1])[:8],
        }


def route_template(request):
    """Use the route pattern (/posts/{post_id}), not the raw path, so metrics have bounded labels."""
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if path:
        return path
    if request.url.path.startswith("/static/"):
        return "/static/*"
    return "unmatched"


def install(app, metrics):
    @app.middleware("http")
    async def observe(request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        start = time.perf_counter()
        metrics.in_flight.inc()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            elapsed = time.perf_counter() - start
            metrics.in_flight.dec()
            route = route_template(request)
            if route not in ("/metrics",):
                metrics.requests.labels(request.method, route, str(status)).inc()
                metrics.latency.labels(request.method, route).observe(elapsed)
            log.info(json.dumps({
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "level": "error" if status >= 500 else "info",
                "request_id": rid, "method": request.method, "route": route, "status": status,
                "duration_ms": round(elapsed * 1000, 2), "client": request.client.host if request.client else None,
            }))
