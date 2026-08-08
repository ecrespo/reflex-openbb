"""Token-bucket rate limiter (T-102).

Protects the OpenBB SDK from being called too fast. Each data function in
`data/equity.py`, `data/crypto.py`, `data/economy.py` will call
`acquire()` before issuing the SDK request.

The bucket starts full (`capacity` tokens). Each `acquire()` consumes one
token. Tokens refill at `rate` per second. If no tokens are available,
`acquire()` blocks (via `asyncio.sleep`) until one is.

This is the simplest correct rate limiter: one process, one bucket, no
distributed coordination. For v1, a single in-process bucket is enough.

Reference: tech-design §5.2.
"""

from __future__ import annotations

import asyncio
import time


class TokenBucket:
    """An async-friendly token-bucket rate limiter.

    REQ: tech-design §5.2: "TokenBucket(rate: float = 5.0, capacity: int = 10)".

    Args:
        rate: Tokens added per second (the long-term sustained rate).
        capacity: Maximum tokens the bucket can hold (the burst size).
            The bucket starts full.
    """

    def __init__(self, rate: float = 5.0, capacity: int = 10) -> None:
        if rate <= 0:
            raise ValueError(f"rate must be > 0, got {rate}")
        if capacity <= 0:
            raise ValueError(f"capacity must be > 0, got {capacity}")
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Add tokens based on elapsed time. Caller MUST hold `_lock` or be
        the only accessor (e.g. during construction)."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

    async def acquire(self) -> None:
        """Wait until one token is available, then consume it.

        REQ: tech-design §5.2: "async def acquire(self)".

        Holds the lock for the entire wait + consume cycle to ensure
        correct rate limiting under concurrent calls. When 20 tasks call
        acquire() with capacity=5, the first 5 are instant and the rest
        are spread over (20-5)/rate seconds.
        """
        # Hold the lock for the whole operation. We use a regular `with`
        # but we also do `await asyncio.sleep` inside it — that's OK
        # because we're the only writer, and other acquires are queued
        # behind us, waiting for the lock to be released.
        async with self._lock:
            self._refill()

            while self.tokens < 1:
                # Not enough tokens. Compute wait time.
                wait_seconds = (1 - self.tokens) / self.rate
                # Add a tiny epsilon to avoid waking up slightly early
                wait_seconds += 0.001

                # Sleep while still holding the lock. Other acquirers
                # queue on the lock; they'll be served in FIFO order
                # when we release. This is what makes the rate limit
                # correct under contention.
                await asyncio.sleep(wait_seconds)
                self._refill()

            # We have at least 1 token. Consume one.
            self.tokens -= 1
