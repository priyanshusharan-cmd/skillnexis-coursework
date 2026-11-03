"""Factory: callers ask for a kind of object by name and never import the concrete classes.
New kinds register themselves, so the factory never needs editing (open/closed principle).

Example: notification channels.
"""
from abc import ABC, abstractmethod


class Notifier(ABC):
    @abstractmethod
    def send(self, to, message) -> str: ...


class NotifierFactory:
    _registry = {}

    @classmethod
    def register(cls, kind):
        def decorator(klass):
            cls._registry[kind] = klass
            return klass
        return decorator

    @classmethod
    def create(cls, kind, **options) -> Notifier:
        try:
            return cls._registry[kind](**options)
        except KeyError:
            raise ValueError(f"unknown notifier {kind!r}; choose from {sorted(cls._registry)}") from None

    @classmethod
    def kinds(cls):
        return sorted(cls._registry)


@NotifierFactory.register("email")
class EmailNotifier(Notifier):
    def __init__(self, sender="noreply@example.com"):
        self.sender = sender

    def send(self, to, message):
        return f"EMAIL from {self.sender} to {to}: {message}"


@NotifierFactory.register("sms")
class SmsNotifier(Notifier):
    MAX = 160

    def send(self, to, message):
        return f"SMS to {to}: {message[: self.MAX]}"


@NotifierFactory.register("push")
class PushNotifier(Notifier):
    def __init__(self, app="Library"):
        self.app = app

    def send(self, to, message):
        return f"PUSH [{self.app}] to {to}: {message}"
