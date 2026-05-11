import threading
import time
from typing import Generic, TypeVar

T = TypeVar("T")


class StaleCache(Generic[T]):
    """
    In-process cache supporting stale-on-failure reads.

    Each entry stores (value, expires_at, last_updated_at) as epoch seconds.
    Expiry is checked on get_fresh; get_stale ignores expiry and returns the
    last written value regardless of age.

    Thread-safe under FastAPI's default threadpool via a single Lock.
    No eviction — keyspace is bounded by the number of game IDs per day plus
    one bulk key. Process restarts handle long-term cleanup.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[T, float, float]] = {}
        self._lock = threading.Lock()

    def get_fresh(self, key: str) -> T | None:
        """Return the cached value if its TTL has not expired; else None."""
        with self._lock:
            entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at, _ = entry
        if time.time() < expires_at:
            return value
        return None

    def get_stale(self, key: str) -> tuple[T, float] | None:
        """Return (value, last_updated_at) regardless of expiry, or None if never set."""
        with self._lock:
            entry = self._store.get(key)
        if entry is None:
            return None
        value, _, last_updated_at = entry
        return value, last_updated_at

    def set(self, key: str, value: T, ttl: float) -> None:
        """Store value with expiry = now + ttl seconds."""
        now = time.time()
        with self._lock:
            self._store[key] = (value, now + ttl, now)

    def clear(self) -> None:
        """Remove all entries. Used by tests to reset shared cache state."""
        with self._lock:
            self._store.clear()
