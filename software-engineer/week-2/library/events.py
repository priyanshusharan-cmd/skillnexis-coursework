"""Observer-based notification system: the service publishes events and never knows who listens."""
from datetime import datetime, timezone


class EventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event, observer):
        self._subscribers.setdefault(event, []).append(observer)

    def unsubscribe(self, event, observer):
        self._subscribers.get(event, []).remove(observer)

    def publish(self, event, **data):
        for observer in list(self._subscribers.get(event, [])):
            observer.update(event, data)


class Observer:
    def update(self, event, data):  # pragma: no cover - interface
        raise NotImplementedError


class MemberNotifier(Observer):
    """Writes messages to members. The outbox stands in for sending real email."""

    def __init__(self):
        self.outbox = []

    def update(self, event, data):
        templates = {
            "book_borrowed": "Hi {name}, you borrowed '{title}'. Enjoy!",
            "book_returned": "Thanks {name}, '{title}' is returned.",
            "book_available": "Good news {name}: '{title}' is available. It is held for you.",
        }
        if event in templates:
            self.outbox.append((data["email"], templates[event].format(**data)))


class AuditLog(Observer):
    def __init__(self, clock=lambda: datetime.now(timezone.utc)):
        self.entries, self._clock = [], clock

    def update(self, event, data):
        self.entries.append(f"{self._clock():%Y-%m-%dT%H:%M:%SZ} {event} " + " ".join(f"{k}={data[k]}" for k in sorted(data) if k != "email"))


class LowStockAlert(Observer):
    """Tells staff when the last copy of a title goes out."""

    def __init__(self):
        self.alerts = []

    def update(self, event, data):
        if event == "book_borrowed" and data.get("available") == 0:
            self.alerts.append(f"Last copy of '{data['title']}' is out")
