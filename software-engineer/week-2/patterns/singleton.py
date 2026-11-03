"""Singleton: exactly one instance, created lazily and safely across threads.

Example: an application-wide configuration object.
"""
import threading


class SingletonMeta(type):
    """Metaclass that returns the same instance for every call to the class."""

    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:  # double-checked so the lock is only taken on first use
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    def reset(cls):
        """Testing hook: forget the instance."""
        cls._instances.pop(cls, None)


class AppConfig(metaclass=SingletonMeta):
    def __init__(self, env="development"):
        self.env = env
        self.settings = {}

    def set(self, key, value):
        self.settings[key] = value

    def get(self, key, default=None):
        return self.settings.get(key, default)
