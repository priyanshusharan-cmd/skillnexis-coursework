"""Token-bucket rate limiter, keyed by client (user id when logged in, else IP)."""
import threading
import time


class TokenBucket:
    def __init__(self, capacity: int, refill_per_second: float, clock=time.monotonic):
        self.capacity, self.rate, self.clock = capacity, refill_per_second, clock
        self._buckets = {}  # key -> (tokens, last_time)
        self._lock = threading.Lock()

    def take(self, key: str):
        """Return (allowed, remaining, retry_after_seconds)."""
        with self._lock:
            now = self.clock()
            tokens, last = self._buckets.get(key, (self.capacity, now))
            tokens = min(self.capacity, tokens + (now - last) * self.rate)
            if tokens >= 1:
                self._buckets[key] = (tokens - 1, now)
                return True, int(tokens - 1), 0
            self._buckets[key] = (tokens, now)
            return False, 0, max(1, int((1 - tokens) / self.rate + 0.999))

    def prune(self, idle_seconds=3600):
        """Drop buckets for clients that have been idle, so memory stays bounded."""
        cutoff = self.clock() - idle_seconds
        with self._lock:
            for key in [k for k, (_, t) in self._buckets.items() if t < cutoff]:
                del self._buckets[key]
