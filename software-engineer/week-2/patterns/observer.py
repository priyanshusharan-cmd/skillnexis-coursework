"""Observer: a subject keeps a list of subscribers and notifies them of events,
without knowing what they do with them.

Example: a stock ticker with price-alert observers.
"""


class Subject:
    def __init__(self):
        self._observers = {}

    def subscribe(self, event, callback):
        self._observers.setdefault(event, []).append(callback)
        return lambda: self._observers[event].remove(callback)  # call to unsubscribe

    def notify(self, event, **payload):
        delivered = 0
        for callback in list(self._observers.get(event, ())):
            callback(**payload)
            delivered += 1
        return delivered


class StockTicker(Subject):
    def __init__(self):
        super().__init__()
        self.prices = {}

    def update(self, symbol, price):
        old = self.prices.get(symbol)
        self.prices[symbol] = price
        self.notify("price", symbol=symbol, old=old, new=price)


class PriceAlert:
    """Observer that records a message when a price crosses its threshold."""

    def __init__(self, symbol, above):
        self.symbol, self.above, self.alerts = symbol, above, []

    def __call__(self, symbol, old, new):
        if symbol == self.symbol and new > self.above and (old is None or old <= self.above):
            self.alerts.append(f"{symbol} crossed {self.above}: now {new}")
