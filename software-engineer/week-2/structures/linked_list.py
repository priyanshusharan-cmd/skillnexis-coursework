class _Node:
    __slots__ = ("value", "next")

    def __init__(self, value, nxt=None):
        self.value = value
        self.next = nxt


class LinkedList:
    """Singly linked list with head and tail pointers.

    append/prepend/pop_front are O(1); index-based operations are O(n).
    """

    def __init__(self, items=()):
        self._head = self._tail = None
        self._size = 0
        for item in items:
            self.append(item)

    def append(self, value):
        node = _Node(value)
        if self._tail is None:
            self._head = self._tail = node
        else:
            self._tail.next = node
            self._tail = node
        self._size += 1

    def prepend(self, value):
        self._head = _Node(value, self._head)
        if self._tail is None:
            self._tail = self._head
        self._size += 1

    def insert(self, index, value):
        if not 0 <= index <= self._size:
            raise IndexError("insert index out of range")
        if index == 0:
            return self.prepend(value)
        if index == self._size:
            return self.append(value)
        prev = self._node_at(index - 1)
        prev.next = _Node(value, prev.next)
        self._size += 1

    def pop_front(self):
        if self._head is None:
            raise IndexError("pop from empty list")
        node = self._head
        self._head = node.next
        if self._head is None:
            self._tail = None
        self._size -= 1
        return node.value

    def remove(self, value):
        """Remove the first node holding value. Raises ValueError if absent."""
        prev, node = None, self._head
        while node and node.value != value:
            prev, node = node, node.next
        if node is None:
            raise ValueError(f"{value!r} not in list")
        if prev is None:
            self._head = node.next
        else:
            prev.next = node.next
        if node is self._tail:
            self._tail = prev
        self._size -= 1

    def find(self, value):
        for i, v in enumerate(self):
            if v == value:
                return i
        return -1

    def reverse(self):
        prev, node = None, self._head
        self._tail = self._head
        while node:
            node.next, prev, node = prev, node, node.next
        self._head = prev

    def _node_at(self, index):
        node = self._head
        for _ in range(index):
            node = node.next
        return node

    def __getitem__(self, index):
        if index < 0:
            index += self._size
        if not 0 <= index < self._size:
            raise IndexError("list index out of range")
        return self._node_at(index).value

    def __len__(self):
        return self._size

    def __iter__(self):
        node = self._head
        while node:
            yield node.value
            node = node.next

    def __repr__(self):
        return "LinkedList([" + " -> ".join(map(repr, self)) + "])"
