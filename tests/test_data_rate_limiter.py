"""
Tests for the token-bucket rate limiter (T-102).

TDD: this file is written BEFORE data/rate_limiter.py.
The tests must FAIL initially, then pass after implementation.

REQs:
- tech-design/v1-architecture.md §5.2: "TokenBucket(rate=5.0, capacity=10)"
- api/v1.md §Rate limiting: "A token-bucket rate limiter (default 5
  requests / second) before calling the SDK"
- Constitution Art. 6 (cache) — related: protect external APIs
"""

from __future__ import annotations

import asyncio
import time

import pytest

from reflex_openbb.data import rate_limiter as rl_mod
from reflex_openbb.data.rate_limiter import TokenBucket

# ─── Domain / smoke tests ───────────────────────────────────────────────────


def test_rate_limiter_module_imports() -> None:
    """The rate limiter module must export `TokenBucket`."""
    assert callable(getattr(rl_mod, "TokenBucket", None))


def test_token_bucket_constructs_with_defaults() -> None:
    """TokenBucket() defaults to rate=5, capacity=10 (per tech-design §5.2).

    REQ: tech-design §5.2: "TokenBucket(rate=5.0, capacity=10)".
    """
    bucket = TokenBucket()
    assert bucket.rate == 5.0
    assert bucket.capacity == 10
    assert bucket.tokens == 10  # starts full


def test_token_bucket_accepts_custom_rate_and_capacity() -> None:
    """TokenBucket(rate, capacity) is configurable for tests and prod."""
    bucket = TokenBucket(rate=2.0, capacity=5)
    assert bucket.rate == 2.0
    assert bucket.capacity == 5
    assert bucket.tokens == 5


# ─── Behavior tests ─────────────────────────────────────────────────────────


def test_acquire_is_async() -> None:
    """acquire() must be a coroutine.

    REQ: tech-design §5.2: "async def acquire(self)".
    """
    bucket = TokenBucket()
    coro = bucket.acquire()
    assert asyncio.iscoroutine(coro)
    # Clean up the coroutine to avoid warnings
    coro.close()


@pytest.mark.asyncio
async def test_acquire_succeeds_when_tokens_available() -> None:
    """When tokens are available, acquire() completes immediately."""
    bucket = TokenBucket(rate=5.0, capacity=10)
    start = time.monotonic()
    await bucket.acquire()
    elapsed = time.monotonic() - start
    # Should be near-instant (well under 100ms)
    assert elapsed < 0.1, f"acquire took {elapsed * 1000:.1f}ms — should be instant"


@pytest.mark.asyncio
async def test_acquire_consumes_one_token() -> None:
    """Each successful acquire() decrements the token count by 1."""
    bucket = TokenBucket(rate=5.0, capacity=10)
    assert bucket.tokens == 10
    await bucket.acquire()
    assert bucket.tokens == pytest.approx(9, abs=0.5)


@pytest.mark.asyncio
async def test_acquire_blocks_when_empty() -> None:
    """When no tokens are available, acquire() waits for refill.

    REQ: tech-design §5.2: "if self.tokens < 1: wait = (1 - tokens) / rate"
    """
    # rate=10/sec means each token takes 0.1s to regenerate
    bucket = TokenBucket(rate=10.0, capacity=2)

    # Consume both tokens
    await bucket.acquire()
    await bucket.acquire()
    assert bucket.tokens < 0.1  # should be ~0

    # Third acquire should wait ~0.1s
    start = time.monotonic()
    await bucket.acquire()
    elapsed = time.monotonic() - start
    assert 0.05 < elapsed < 0.3, f"Expected wait ~0.1s, got {elapsed * 1000:.1f}ms"


@pytest.mark.asyncio
async def test_tokens_refill_over_time() -> None:
    """Tokens refill at `rate` per second.

    REQ: tech-design §5.2: refill formula.

    We verify refill by calling acquire() repeatedly and counting how many
    succeed within a window — that's the user-observable behavior, not
    the internal `tokens` counter (which is private state).
    """
    bucket = TokenBucket(rate=10.0, capacity=10)

    # Drain to ~0
    for _ in range(10):
        await bucket.acquire()

    # Wait 0.5s — should refill ~5 tokens (at 10/sec)
    await asyncio.sleep(0.5)

    # How many acquires succeed in 0.05s? If refill is 10/s, we should
    # get 5 tokens worth (since the 0.5s wait generated ~5 new tokens).
    count = 0
    for _ in range(10):  # try to drain everything
        if await _try_acquire(bucket):
            count += 1
        else:
            break

    assert 3 <= count <= 7, f"Expected ~5 refilled tokens in 0.5s (rate=10/s), got {count}"


async def _try_acquire(bucket: TokenBucket) -> bool:
    """Try to acquire one token without blocking. Returns True if successful.

    REQ: helper for test_tokens_refill_over_time.
    """
    # Use a snapshot of the internal state to check, then either consume
    # or return False. The lock-based acquire() always blocks, so we
    # implement a non-blocking version here.
    async with bucket._lock:
        bucket._refill()
        if bucket.tokens >= 1:
            bucket.tokens -= 1
            return True
        return False


@pytest.mark.asyncio
async def test_tokens_dont_exceed_capacity() -> None:
    """Token count never exceeds `capacity`, even after long idle.

    REQ: tech-design §5.2: "self.tokens = min(self.capacity, ...)".
    """
    bucket = TokenBucket(rate=10.0, capacity=3)

    # Wait 1 second — would naively refill to 10, but capped at 3
    await asyncio.sleep(1.0)
    current = bucket.tokens
    assert current == 3, f"Expected tokens capped at 3, got {current}"


# ─── Concurrency tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_concurrent_acquires_respect_rate_limit() -> None:
    """When 20 concurrent tasks call acquire() with capacity=5, rate=10/s,
    the first 5 should be instant and the rest spread over time.

    REQ: tech-design §5.2 — the bucket serializes concurrent access via
    an asyncio lock.
    """
    bucket = TokenBucket(rate=10.0, capacity=5)

    start = time.monotonic()
    await asyncio.gather(*[bucket.acquire() for _ in range(20)])
    elapsed = time.monotonic() - start

    # 20 acquires, 5 capacity → 15 extra acquires at 10/sec = 1.5s
    # Allow generous tolerance for CI
    assert 1.2 < elapsed < 2.5, (
        f"Expected ~1.5s for 20 acquires (cap=5, rate=10), got {elapsed:.2f}s"
    )


@pytest.mark.asyncio
async def test_lock_prevents_race_on_tokens() -> None:
    """Under concurrent acquire(), the token count is consistent.

    This is a regression test for the lock — without the lock, two tasks
    could both see tokens=1 and both acquire, leaving tokens=-1.
    """
    bucket = TokenBucket(rate=100.0, capacity=10)

    # 100 concurrent acquires
    await asyncio.gather(*[bucket.acquire() for _ in range(100)])

    # tokens should be between -epsilon and capacity (well, slightly negative
    # is fine because acquire is allowed to "borrow" — but no NaN, no huge neg)
    assert -1.0 < bucket.tokens <= 10, f"Token count looks corrupt: {bucket.tokens}"
