"""Per-provider circuit breaker (T-103).

Protects each OpenBB data provider from being hammered after it starts
failing. When a provider returns `failure_threshold` consecutive errors,
the breaker "opens" and short-circuits all subsequent calls to that
provider for `reset_timeout` seconds. After the timeout, the breaker
half-opens: the next call is allowed through, and if it succeeds the
breaker is fully closed again.

This is the classic 3-state circuit breaker (closed / open / half-open),
in its simplest correct form. v2 may add exponential backoff or a
provider-health API.

Reference: tech-design §5.3.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    """Raised when a call is attempted while the breaker is open.

    Attributes:
        provider: The provider that was rejected.
        reset_in: Seconds until the breaker tries again.
    """

    def __init__(self, provider: str, reset_in: float) -> None:
        self.provider = provider
        self.reset_in = reset_in
        super().__init__(f"Circuit open for provider '{provider}' — retry in {reset_in:.1f}s")


class CircuitBreaker:
    """A per-provider circuit breaker.

    REQ: tech-design §5.3: "failure_threshold: int = 3, reset_timeout: float = 60"

    Args:
        failure_threshold: Consecutive failures before opening.
        reset_timeout: Seconds to keep the breaker open before half-opening.
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 60.0) -> None:
        if failure_threshold < 1:
            raise ValueError(f"failure_threshold must be >= 1, got {failure_threshold}")
        if reset_timeout <= 0:
            raise ValueError(f"reset_timeout must be > 0, got {reset_timeout}")
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._failures: dict[str, int] = {}
        self._open_until: dict[str, float] = {}

    def is_open(self, provider: str) -> bool:
        """Return True if the breaker is currently rejecting calls to `provider`.

        When the reset timeout has elapsed, the breaker is "half-open":
        we report is_open=False so the next call is allowed through.
        If that call succeeds, the breaker fully closes (record_success).
        If it fails, the breaker re-opens (record_failure).
        """
        open_until = self._open_until.get(provider, 0.0)
        # The breaker is OPEN if the open_until timestamp is still in the
        # future. If elapsed (or never set), it's closed/half-open.
        return open_until > time.monotonic()

    def time_until_retry(self, provider: str) -> float:
        """Seconds until `provider`'s breaker tries again. 0 if closed."""
        open_until = self._open_until.get(provider, 0.0)
        remaining = open_until - time.monotonic()
        return max(0.0, remaining)

    def record_failure(self, provider: str) -> None:
        """Record a failure for `provider`. Opens the breaker if threshold reached."""
        self._failures[provider] = self._failures.get(provider, 0) + 1
        if self._failures[provider] >= self.failure_threshold:
            self._open_until[provider] = time.monotonic() + self.reset_timeout

    def record_success(self, provider: str) -> None:
        """Record a success for `provider`. Closes the breaker and resets the counter."""
        self._failures.pop(provider, None)
        self._open_until.pop(provider, None)

    def call(self, provider: str, fn: Callable[[], T]) -> T:
        """Run `fn()` under the breaker for `provider`.

        - If the breaker is open, raise `CircuitOpenError` without calling fn.
        - If fn succeeds, record the success and return the result.
        - If fn raises, record the failure and re-raise the original exception.

        REQ: caller convenience — most data functions will use this helper.
        """
        if self.is_open(provider):
            raise CircuitOpenError(provider, self.time_until_retry(provider))

        try:
            result = fn()
        except Exception:
            self.record_failure(provider)
            raise

        self.record_success(provider)
        return result
