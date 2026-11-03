class _Node:
    __slots__ = ("key", "value", "left", "right")

    def __init__(self, key, value):
        self.key, self.value = key, value
        self.left = self.right = None


class BST:
    """Unbalanced binary search tree mapping keys to values.

    insert/search/delete are O(h): O(log n) on random input, O(n) on sorted input.
    Iterative where it matters so a degenerate tree cannot overflow the recursion stack.
    """

    def __init__(self):
        self._root = None
        self._size = 0

    def insert(self, key, value=None):
        if self._root is None:
            self._root = _Node(key, value)
            self._size = 1
            return
        node = self._root
        while True:
            if key == node.key:
                node.value = value  # update in place
                return
            side = "left" if key < node.key else "right"
            child = getattr(node, side)
            if child is None:
                setattr(node, side, _Node(key, value))
                self._size += 1
                return
            node = child

    def search(self, key, default=None):
        node = self._root
        while node:
            if key == node.key:
                return node.value
            node = node.left if key < node.key else node.right
        return default

    def __contains__(self, key):
        sentinel = object()
        return self.search(key, sentinel) is not sentinel

    def delete(self, key):
        parent, node = None, self._root
        while node and node.key != key:
            parent, node = node, (node.left if key < node.key else node.right)
        if node is None:
            raise KeyError(key)
        if node.left and node.right:  # two children: copy in the in-order successor
            succ_parent, succ = node, node.right
            while succ.left:
                succ_parent, succ = succ, succ.left
            node.key, node.value = succ.key, succ.value
            parent, node = succ_parent, succ
        child = node.left or node.right
        if parent is None:
            self._root = child
        elif parent.left is node:
            parent.left = child
        else:
            parent.right = child
        self._size -= 1

    def min(self):
        if self._root is None:
            raise ValueError("empty tree")
        node = self._root
        while node.left:
            node = node.left
        return node.key

    def max(self):
        if self._root is None:
            raise ValueError("empty tree")
        node = self._root
        while node.right:
            node = node.right
        return node.key

    def height(self):
        """Edges on the longest root-to-leaf path; -1 for an empty tree."""
        best, stack = -1, [(self._root, 0)] if self._root else []
        while stack:
            node, depth = stack.pop()
            best = max(best, depth)
            stack.extend((c, depth + 1) for c in (node.left, node.right) if c)
        return best

    def inorder(self):
        stack, node = [], self._root
        while stack or node:
            while node:
                stack.append(node)
                node = node.left
            node = stack.pop()
            yield node.key
            node = node.right

    def __iter__(self):
        return self.inorder()

    def __len__(self):
        return self._size
