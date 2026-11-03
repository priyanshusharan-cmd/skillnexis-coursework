import threading

import pytest

from patterns.factory import EmailNotifier, NotifierFactory, PushNotifier, SmsNotifier
from patterns.observer import PriceAlert, StockTicker
from patterns.singleton import AppConfig


@pytest.fixture(autouse=True)
def fresh_config():
    AppConfig.reset()
    yield
    AppConfig.reset()


def test_singleton_same_instance_and_first_args_win():
    a = AppConfig("production")
    b = AppConfig("development")
    a.set("debug", False)
    assert a is b and b.env == "production" and b.get("debug") is False and b.get("missing", 1) == 1


def test_singleton_is_thread_safe():
    seen, barrier = [], threading.Barrier(16)

    def make():
        barrier.wait()
        seen.append(id(AppConfig()))

    threads = [threading.Thread(target=make) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(set(seen)) == 1


def test_factory_creates_each_kind():
    assert isinstance(NotifierFactory.create("email"), EmailNotifier)
    assert isinstance(NotifierFactory.create("sms"), SmsNotifier)
    assert NotifierFactory.create("push", app="Shop").send("u1", "hi") == "PUSH [Shop] to u1: hi"
    assert NotifierFactory.create("email", sender="a@b.co").send("x@y.co", "hi") == "EMAIL from a@b.co to x@y.co: hi"
    assert NotifierFactory.create("sms").send("+91", "x" * 200) == "SMS to +91: " + "x" * 160


def test_factory_unknown_kind_and_registration():
    with pytest.raises(ValueError, match="unknown notifier 'fax'"):
        NotifierFactory.create("fax")

    @NotifierFactory.register("fax")
    class Fax(PushNotifier):
        pass

    assert "fax" in NotifierFactory.kinds() and isinstance(NotifierFactory.create("fax"), Fax)


def test_observer_alerts_only_on_crossing_and_unsubscribe():
    ticker, alert = StockTicker(), PriceAlert("INFY", above=1500)
    unsubscribe = ticker.subscribe("price", alert)
    calls = []
    ticker.subscribe("price", lambda **kw: calls.append(kw["symbol"]))
    for price in (1490, 1510, 1520, 1480, 1505):
        ticker.update("INFY", price)
    ticker.update("TCS", 4000)
    assert alert.alerts == ["INFY crossed 1500: now 1510", "INFY crossed 1500: now 1505"]
    assert calls == ["INFY"] * 5 + ["TCS"]
    unsubscribe()
    assert ticker.notify("price", symbol="INFY", old=1, new=2000) == 1
    assert ticker.notify("nobody-listens") == 0
