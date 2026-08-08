"""Error models for the data layer (T-104).

REQ: api/v1.md §Error model — these are the exceptions that bubble up
from `data/*` functions to the event handlers in the state layer.

Constitution Art. 8: errors are part of the data layer's contract; the
state layer catches them and surfaces a banner in the UI.
"""


class InvalidTickerError(ValueError):
    """Raised when a ticker/symbol fails validation.

    Attributes:
        ticker: The invalid ticker.
        reason: One of: "empty", "invalid_chars", "too_long".
    """

    def __init__(self, ticker: str, reason: str) -> None:
        self.ticker = ticker
        self.reason = reason
        super().__init__(f"Invalid ticker {ticker!r}: {reason}")


class ProviderError(RuntimeError):
    """Raised when a data provider returns an error.

    Attributes:
        provider: The provider name (e.g. "yfinance", "fred").
        status_code: HTTP status code (None if not applicable).
        retry_after: Seconds to wait before retrying (from Retry-After header).
        original: The original error message.
    """

    def __init__(
        self,
        provider: str,
        status_code: int | None,
        retry_after: int | None,
        original: str,
    ) -> None:
        self.provider = provider
        self.status_code = status_code
        self.retry_after = retry_after
        self.original = original
        super().__init__(
            f"Provider {provider!r} error "
            f"(status={status_code}, retry_after={retry_after}s): {original}"
        )
