class HashMap:
    """Hash map with separate chaining. Doubles its bucket array above a 0.75 load factor,
    so get/put/delete are O(1) on average."""

    _MAX_LOAD = 0.75

    def __init__(self, capacity=8):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._buckets = [[] for _ in range(capacity)]
        self._size = 0

    def _bucket(self, key):
        return self._buckets[hash(key) % len(self._buckets)]

    def put(self, key, value):
        bucket = self._bucket(key)
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))
        self._size += 1
        if self._size / len(self._buckets) > self._MAX_LOAD:
            self._resize(len(self._buckets) * 2)

    def get(self, key, default=None):
        for k, v in self._bucket(key):
            if k == key:
                return v
        return default

    def delete(self, key):
        bucket = self._bucket(key)
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket.pop(i)
                self._size -= 1
                return
        raise KeyError(key)

    def _resize(self, capacity):
        old = [pair for bucket in self._buckets for pair in bucket]
        self._buckets = [[] for _ in range(capacity)]
        for k, v in old:
            self._bucket(k).append((k, v))

    @property
    def capacity(self):
        return len(self._buckets)

    def keys(self):
        return [k for bucket in self._buckets for k, _ in bucket]

    def items(self):
        return [pair for bucket in self._buckets for pair in bucket]

    def __contains__(self, key):
        return any(k == key for k, _ in self._bucket(key))

    def __getitem__(self, key):
        sentinel = object()
        value = self.get(key, sentinel)
        if value is sentinel:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self.put(key, value)

    def __delitem__(self, key):
        self.delete(key)

    def __len__(self):
        return self._size

    def __iter__(self):
        return iter(self.keys())
