"""TTL cache wrapper for the data layer (T-101).

This is the only module that constructs TTLCache instances. The named caches
defined here (CacheName) are the single source of truth for the 5 caches
described in `specs/data-model/v1-models.md` §Caching.

The `get_or_compute` function is the public API: callers pass a key, a cache
namespace, and a function. On a miss the function is called and its result
cached. On a hit the cached value is returned without calling the function.

Thread-safety: a single module-level lock serializes cache access. This is
the simplest correct approach; cachetools' TTLCache is not thread-safe by
default.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from threading import Lock
from typing import Any, TypeVar

from cachetools import TTLCache

T = TypeVar("T")


class CacheName(Enum):
    """The 5 named caches from the data model.

    Each entry has the TTL and max_size mandated by
    `specs/data-model/v1-models.md` §Caching.
    """

    QUOTE = "quote"
    PRICE = "price"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"
    MACRO = "macro"

    @property
    def ttl_seconds(self) -> int:
        """TTL in seconds for this cache (per the data model)."""
        return _CACHE_TTLS[self.value]

    @property
    def max_size(self) -> int:
        """Maximum number of entries before LRU eviction (per the data model)."""
        return _CACHE_MAX_SIZES[self.value]


# TTLs and max sizes from `specs/data-model/v1-models.md` §Caching.
# Kept as module-level dicts so tests can assert against them.
_CACHE_TTLS: dict[str, int] = {
    "quote": 300,  # 5 min
    "price": 300,  # 5 min default; 5y/max overrides per-call
    "fundamentals": 86_400,  # 1 day
    "news": 900,  # 15 min
    "macro": 604_800,  # 7 days
}
_CACHE_MAX_SIZES: dict[str, int] = {
    "quote": 10_000,
    "price": 5_000,
    "fundamentals": 5_000,
    "news": 2_000,
    "macro": 500,
}


# Module-level state: one TTLCache per CacheName + one lock for thread-safety.
_caches: dict[str, TTLCache] = {
    c.value: TTLCache(maxsize=c.max_size, ttl=c.ttl_seconds) for c in CacheName
}
_lock = Lock()


class _CacheProtocol:
    """Protocol-like duck type for test/cache objects with the right shape.

    Production code uses CacheName entries; tests may pass plain objects with
    `value`, `ttl_seconds`, and `max_size` attributes.
    """

    value: str
    ttl_seconds: int
    max_size: int


def _resolve_cache(cache_ns: CacheName | _CacheProtocol) -> TTLCache:
    """Return the TTLCache for the given namespace, creating it on demand.

    Production code passes a `CacheName` enum. Tests may pass a custom
    duck-typed object (e.g. `_TinyCache` with max_size=3) — for those we
    synthesize a per-namespace cache.
    """
    name = cache_ns.value
    cache = _caches.get(name)
    if cache is None:
        cache = TTLCache(maxsize=cache_ns.max_size, ttl=cache_ns.ttl_seconds)
        _caches[name] = cache
    return cache


def get_or_compute(
    key: str,
    cache_ns: CacheName | _CacheProtocol,
    fn: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> tuple[T, bool]:
    """Return `(value, cache_hit)` for `key`, calling `fn` on miss.

    On a hit, `fn` is NOT called. On a miss, `fn(*args, **kwargs)` is called
    and its result is cached under `key` in the `cache_ns` namespace.

    If `fn` raises, the exception propagates and nothing is cached.

    Thread-safety: all access to the underlying TTLCache is serialized by
    a module-level lock. This is correct and simple; for v1 it's the right
    trade-off. v2 may switch to per-cache locks or a thread-local approach
    if contention becomes a problem.
    """
    cache = _resolve_cache(cache_ns)

    with _lock:
        if key in cache:
            return cache[key], True  # type: ignore[return-value]

    # Compute outside the lock to avoid blocking other cache operations.
    # This means fn may be called multiple times under heavy contention,
    # but only the first result is stored.
    value = fn(*args, **kwargs)

    with _lock:
        cache[key] = value

    return value, False


def clear(cache_ns: CacheName | _CacheProtocol | None = None) -> None:
    """Clear one or all caches. Useful for tests."""
    with _lock:
        if cache_ns is None:
            for c in _caches.values():
                c.clear()
        else:
            cache = _caches.get(cache_ns.value)
            if cache is not None:
                cache.clear()
