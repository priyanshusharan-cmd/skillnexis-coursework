class _Node:
    __slots__ = ("value", "below")

    def __init__(self, value, below):
        self.value = value
        self.below = below


class Stack:
    """LIFO stack on singly linked nodes. push/pop/peek are O(1)."""

    def __init__(self, items=()):
        self._top = None
        self._size = 0
        for item in items:
            self.push(item)

    def push(self, value):
        self._top = _Node(value, self._top)
        self._size += 1

    def pop(self):
        if self._top is None:
            raise IndexError("pop from empty stack")
        node = self._top
        self._top = node.below
        self._size -= 1
        return node.value

    def peek(self):
        if self._top is None:
            raise IndexError("peek at empty stack")
        return self._top.value

    def is_empty(self):
        return self._size == 0

    def __len__(self):
        return self._size

    def __iter__(self):  # top to bottom
        node = self._top
        while node:
            yield node.value
            node = node.below

    def __repr__(self):
        return f"Stack({list(reversed(list(self)))!r})"
