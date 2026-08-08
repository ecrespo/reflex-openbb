"""Pydantic data models for the data layer (T-104).

These models are the single source of truth for the shape of data flowing
through the app. Every data function in `data/equity.py`, `data/crypto.py`,
etc. returns one of these models.

Constitution Art. 5 (mandatory): every monetary / ratio / percentage field
is `Decimal`. NEVER `float`. The validators coerce incoming values via
`str(...)` to avoid binary-float precision loss.

Reference: specs/data-model/v1-models.md
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, HttpUrl


def _coerce_to_decimal(v: object) -> Decimal:
    """Coerce a value to Decimal via str() to avoid float precision loss.

    REQ: Constitution Art. 5 — NEVER Decimal(float) (precision loss),
    ALWAYS Decimal(str(v)) for incoming values.

    Accepts: int, float (coerced via str), str, Decimal, None.
    Raises: ValueError if the string is not a valid number.
    """
    if v is None:
        # Pydantic's Optional type should catch None before this,
        # but be defensive.
        raise ValueError("None cannot be coerced to Decimal")
    if isinstance(v, Decimal):
        return v
    if isinstance(v, str):
        try:
            return Decimal(v)
        except Exception as e:
            raise ValueError(f"Invalid decimal string: {v!r}") from e
    if isinstance(v, (int, float)):
        # Convert through str to avoid float precision artifacts:
        # Decimal(0.1) gives 0.1000000000000000055...,
        # but Decimal(str(0.1)) gives 0.1 exactly.
        return Decimal(str(v))
    raise ValueError(f"Cannot coerce {type(v).__name__} to Decimal")


# A reusable type alias: anything coercible to Decimal, with a sentinel of
# "invalid" so Pydantic reports a clear error if conversion fails.
DecimalLike = Annotated[Decimal, BeforeValidator(_coerce_to_decimal)]


class _Base(BaseModel):
    """Common configuration for all our models."""

    model_config = ConfigDict(
        # Forbid extra fields by default; data layer is the schema owner.
        extra="forbid",
        # Validate assignment too (mutations on instances).
        validate_assignment=True,
    )


class EquityQuote(_Base):
    """A snapshot quote for an equity ticker. REQ: REQ-005 (KPI cards)."""

    ticker: str = Field(min_length=1, max_length=10)
    price: DecimalLike
    day_change_pct: DecimalLike  # signed, e.g. -1.23 means -1.23%
    market_cap: DecimalLike | None = None
    volume: int = Field(ge=0)
    fifty_two_week_high: DecimalLike
    fifty_two_week_low: DecimalLike
    fetched_at: datetime
    provider: str


class OHLCBar(_Base):
    """A single OHLC bar. REQ: REQ-001 (Equity price chart).

    Lists of OHLCBar are always sorted by `date` ascending (the data layer
    enforces this; this model is just the shape).
    """

    date: date
    open: DecimalLike
    high: DecimalLike
    low: DecimalLike
    close: DecimalLike
    volume: int = Field(ge=0)


class EquityFundamentals(_Base):
    """Fundamental metrics for a ticker. REQ: REQ-003 (Fundamentals table).

    Every metric is Optional because providers often return `null` for
    less-common fields. The UI displays "n/a" for None (REQ-003 O-where).
    """

    ticker: str = Field(min_length=1, max_length=10)
    pe_ratio: DecimalLike | None = None
    eps: DecimalLike | None = None
    dividend_yield: DecimalLike | None = None  # as a percentage
    beta: DecimalLike | None = None
    book_value_per_share: DecimalLike | None = None
    price_to_book: DecimalLike | None = None
    roe: DecimalLike | None = None  # return on equity, %
    fetched_at: datetime
    provider: str


class NewsItem(_Base):
    """A single news article. REQ: REQ-004 (News feed).

    Sorted descending by `published_at` (the data layer enforces this).
    """

    id: str
    title: str = Field(min_length=1)
    source: str
    url: HttpUrl  # Pydantic validates it's a real http(s) URL
    published_at: datetime
    summary: str | None = None


class MacroPoint(_Base):
    """A single year/value observation. REQ: REQ-007 (Economy dashboard)."""

    year: int = Field(ge=1900, le=2200)
    value: DecimalLike
    country: str = Field(min_length=2, max_length=2)  # ISO-3166 alpha-2
    indicator: str  # one of: GDP, CPI, UNRATE


class SearchResult(_Base):
    """The output of `data/search.search()`. REQ: REQ-010 (Search).

    `equity_match` and `crypto_match` are mutually exclusive in practice
    (the resolver picks one or the other), but the model allows both
    to be set for flexibility.
    """

    query: str
    equity_match: str | None = None
    crypto_match: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
