"""
infrastructure/cache/in_memory_cache.py

Thread-safe LRU cache backed by an OrderedDict.
Implements the DataCache port so it can be swapped for Redis later
without touching any application-layer code.
"""

import threading
from collections import OrderedDict

from app.domain.interfaces import DataCache


class InMemoryLRUCache(DataCache):
    """
    Simple bounded LRU cache.

    Rendered PNG maps are typically a few hundred KB each.  A cap of 128
    entries keeps memory usage predictable while still covering the common
    case of repeated requests for the same variable + timestamp.
    """

    def __init__(self, max_size: int = 128) -> None:
        self._max_size = max_size
        self._store: OrderedDict[str, object] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> object | None:
        with self._lock:
            if key not in self._store:
                return None
            # Move to end (most-recently-used)
            self._store.move_to_end(key)
            return self._store[key]

    def set(self, key: str, value: object) -> None:
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = value
            if len(self._store) > self._max_size:
                self._store.popitem(last=False)  # evict LRU

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
