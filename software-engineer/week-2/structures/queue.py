class Queue:
    """FIFO queue on a growable circular buffer. enqueue is amortised O(1), dequeue is O(1)."""

    def __init__(self, items=(), capacity=4):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._buf = [None] * capacity
        self._head = 0
        self._size = 0
        for item in items:
            self.enqueue(item)

    def enqueue(self, value):
        if self._size == len(self._buf):
            self._grow()
        self._buf[(self._head + self._size) % len(self._buf)] = value
        self._size += 1

    def dequeue(self):
        if self._size == 0:
            raise IndexError("dequeue from empty queue")
        value = self._buf[self._head]
        self._buf[self._head] = None  # drop the reference
        self._head = (self._head + 1) % len(self._buf)
        self._size -= 1
        return value

    def peek(self):
        if self._size == 0:
            raise IndexError("peek at empty queue")
        return self._buf[self._head]

    def _grow(self):
        old = list(self)
        self._buf = old + [None] * len(old)
        self._head = 0

    def is_empty(self):
        return self._size == 0

    def __len__(self):
        return self._size

    def __iter__(self):  # front to back
        for i in range(self._size):
            yield self._buf[(self._head + i) % len(self._buf)]

    def __repr__(self):
        return f"Queue({list(self)!r})"
