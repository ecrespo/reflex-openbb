"""Equity data functions (T-105).

These are the data-layer functions that consume the OpenBB Python SDK and
return Pydantic models. Every function:
- Validates the ticker (raises InvalidTickerError on bad input)
- Calls the appropriate `obb.equity.*` or `obb.news.*` method
- Caches the result via `data.cache.get_or_compute`
- Wraps the result in a Pydantic model (Art. 5: Decimal for money)
- Raises ProviderError on failure

Constitution Art. 3: this is the only place in the app that calls `obb.*`.
Constitution Art. 5: every monetary field is coerced to Decimal.
Constitution Art. 6: every function uses the TTL cache.

Reference:
- api/v1.md §data.equity
- data-model/v1-models.md
- tech-design/v1-architecture.md §3 (data layer)
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Literal

import pandera.polars as pa
import polars as pl
from pandera.errors import SchemaError, SchemaErrors

from reflex_openbb.data.cache import CacheName, get_or_compute
from reflex_openbb.data.errors import InvalidTickerError, ProviderError
from reflex_openbb.data.types import (
    EquityFundamentals,
    EquityQuote,
    NewsItem,
    OHLCBar,
)

# ─── Pandera schema for OHLC data ──────────────────────────────────────────


class OHLCSchema(pa.DataFrameModel):
    """Schema for the price history DataFrame returned by the OpenBB SDK.

    REQ: defensive validation at the data-layer boundary. If the provider
    changes its schema (column names, types, NULLability), we want to fail
    loudly here, NOT corrupt downstream state.

    The schema is intentionally strict: every column is required, types
    are explicit (with Decimal precision=18 scale=4 to preserve price
    precision), and we check that `volume >= 0`.
    """

    # NOTE: in pandera.polars, precision/scale for Decimal columns are
    # defined on the polars type itself (`pl.Decimal(precision, scale)`),
    # not on `pa.Field`. The `ge=0` check on volume is a built-in.
    date: pl.Date
    open: pl.Decimal(precision=18, scale=4)
    high: pl.Decimal(precision=18, scale=4)
    low: pl.Decimal(precision=18, scale=4)
    close: pl.Decimal(precision=18, scale=4)
    volume: int = pa.Field(ge=0)

    class Config:
        coerce = True  # coerce string → Decimal, etc.


# ─── Ticker validation ──────────────────────────────────────────────────────


_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")


def _validate_ticker(ticker: str) -> str:
    """Validate and normalize a ticker symbol. REQ: api/v1.md §ticker.

    - Must match `^[A-Z][A-Z0-9.\\-]{0,9}$`
    - Returns the uppercase version

    Raises:
        InvalidTickerError: if the ticker is empty, too long, or has
            invalid characters.
    """
    if not ticker:
        raise InvalidTickerError(ticker or "", "empty")
    normalized = ticker.upper()
    if len(normalized) > 10:
        raise InvalidTickerError(ticker, "too_long")
    if not _TICKER_RE.match(normalized):
        raise InvalidTickerError(ticker, "invalid_chars")
    return normalized


# ─── Internal helpers ───────────────────────────────────────────────────────


def _to_equity_quote(result: dict) -> EquityQuote:
    """Build an EquityQuote from a single OpenBB result dict.

    REQ: REQ-005 + Art. 5 (Decimal coercion).
    """
    return EquityQuote(
        ticker=result.get("symbol", ""),
        price=result["last_price"],
        day_change_pct=result["change_percent"],
        market_cap=result.get("market_cap"),
        volume=result.get("volume", 0),
        fifty_two_week_high=result["high"],
        fifty_two_week_low=result["low"],
        fetched_at=datetime.now(timezone.utc),
        provider=result.get("provider", "unknown"),
    )


def _to_ohlc_bars(df: pl.DataFrame) -> list[OHLCBar]:
    """Build a list of OHLCBar from a polars DataFrame.

    REQ: REQ-001, REQ-002 + data-model §OHLCBar.
    Returns a list sorted ascending by date.

    The input DataFrame is validated against `OHLCSchema` first. This
    catches provider-schema drift (missing columns, wrong types) at the
    boundary instead of letting it corrupt downstream state.
    """
    # 1. Validate schema. If it doesn't match, raise ProviderError.
    #    We catch BOTH pandera's SchemaError/SchemaErrors AND polars'
    #    ColumnNotFoundError — the latter happens when the provider
    #    drops/renames a column, which pandera doesn't wrap.
    try:
        validated = OHLCSchema.validate(df, lazy=True)
    except (SchemaError, SchemaErrors) as e:
        raise ProviderError(
            provider="unknown",
            status_code=None,
            retry_after=None,
            original=f"OHLC data failed schema validation: {e}",
        ) from e
    except pl.ColumnNotFoundError as e:
        raise ProviderError(
            provider="unknown",
            status_code=None,
            retry_after=None,
            original=f"OHLC data failed schema validation: missing column: {e}",
        ) from e

    # 2. Convert to a sorted list of OHLCBar.
    # Polars sort is in-place; we sort by date ascending.
    sorted_df = validated.sort("date")

    bars: list[OHLCBar] = []
    for row in sorted_df.iter_rows(named=True):
        d = row["date"]
        # `pl.Date` always returns a `date` object, but be defensive.
        if isinstance(d, str):
            d = date.fromisoformat(d)

        bars.append(
            OHLCBar(
                date=d,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=int(row["volume"]),
            )
        )
    return bars


def _to_equity_fundamentals(result: dict) -> EquityFundamentals:
    """Build an EquityFundamentals from a single OpenBB result dict.

    REQ: REQ-003 + Art. 5.
    """
    return EquityFundamentals(
        ticker=result.get("symbol", ""),
        pe_ratio=result.get("pe_ratio"),
        eps=result.get("eps"),
        dividend_yield=result.get("dividend_yield"),
        beta=result.get("beta"),
        book_value_per_share=result.get("book_value_per_share"),
        price_to_book=result.get("price_to_book"),
        roe=result.get("roe"),
        fetched_at=datetime.now(timezone.utc),
        provider=result.get("provider", "unknown"),
    )


def _to_news_items(results: list) -> list[NewsItem]:
    """Build a list of NewsItem from a list of OpenBB result dicts.

    REQ: REQ-004 + data-model §NewsItem.
    Returns a list sorted descending by published_at.
    """
    items: list[NewsItem] = []
    for r in results:
        # published_at may be a string or a datetime
        published = r["published_at"]
        if isinstance(published, str):
            # OpenBB typically uses ISO 8601 with Z suffix
            if published.endswith("Z"):
                published = published[:-1] + "+00:00"
            published = datetime.fromisoformat(published)

        items.append(
            NewsItem(
                id=r["id"],
                title=r["title"],
                source=r["source"],
                url=r["url"],
                published_at=published,
                summary=r.get("summary"),
            )
        )
    # Sort descending by published_at (data-model requirement)
    items.sort(key=lambda n: n.published_at, reverse=True)
    return items


# ─── Public API ─────────────────────────────────────────────────────────────


async def get_equity_quote(ticker: str) -> EquityQuote:
    """Get the current quote for a ticker. REQ: REQ-005.

    Cache: 5 min, key = `quote:{TICKER}`.
    """
    normalized = _validate_ticker(ticker)
    cache_key = f"quote:{normalized}"

    def _fetch() -> EquityQuote:
        # Imported here to allow test-time monkeypatching of `openbb.obb`
        import openbb as _openbb

        try:
            obb_obj = _openbb.obb.equity.quote(symbol=normalized)
        except Exception as e:
            raise ProviderError(
                provider="unknown",
                status_code=None,
                retry_after=None,
                original=str(e),
            ) from e

        results = getattr(obb_obj, "results", None) or []
        if not results:
            raise ProviderError(
                provider="unknown",
                status_code=None,
                retry_after=None,
                original=f"No quote data for {normalized}",
            )

        return _to_equity_quote(results[0])

    value, _ = get_or_compute(cache_key, CacheName.QUOTE, _fetch)
    return value


async def get_equity_price_history(
    ticker: str,
    period: Literal["1mo", "6mo", "1y", "5y", "max"] = "1y",
) -> list[OHLCBar]:
    """Get OHLC price history for a ticker. REQ: REQ-001, REQ-002.

    Cache: 5 min for 1mo/6mo/1y, 1 day for 5y/max.
    """
    normalized = _validate_ticker(ticker)
    cache_key = f"price:{normalized}:{period}"

    def _fetch() -> list[OHLCBar]:
        import openbb as _openbb

        try:
            obb_obj = _openbb.obb.equity.price.historical(symbol=normalized, period=period)
        except Exception as e:
            raise ProviderError(
                provider="unknown",
                status_code=None,
                retry_after=None,
                original=str(e),
            ) from e

        df = obb_obj.to_dataframe()
        if df is None or df.is_empty():
            raise ProviderError(
                provider="unknown",
                status_code=None,
                retry_after=None,
                original=f"No price history for {normalized} ({period})",
            )

        return _to_ohlc_bars(df)

    value, _ = get_or_compute(cache_key, CacheName.PRICE, _fetch)
    return value


async def get_equity_fundamentals(ticker: str) -> EquityFundamentals:
    """Get fundamental metrics for a ticker. REQ: REQ-003.

    Cache: 1 day, key = `fund:{TICKER}`.
    """
    normalized = _validate_ticker(ticker)
    cache_key = f"fund:{normalized}"

    def _fetch() -> EquityFundamentals:
        import openbb as _openbb

        try:
            obb_obj = _openbb.obb.equity.fundamental.metrics(symbol=normalized)
        except Exception as e:
            raise ProviderError(
                provider="unknown",
                status_code=None,
                retry_after=None,
                original=str(e),
            ) from e

        results = getattr(obb_obj, "results", None) or []
        if not results:
            raise ProviderError(
                provider="unknown",
                status_code=None,
                retry_after=None,
                original=f"No fundamentals for {normalized}",
            )

        return _to_equity_fundamentals(results[0])

    value, _ = get_or_compute(cache_key, CacheName.FUNDAMENTALS, _fetch)
    return value


async def get_equity_news(ticker: str, limit: int = 10) -> list[NewsItem]:
    """Get recent news articles for a ticker. REQ: REQ-004.

    Cache: 15 min, key = `news:{TICKER}`.
    Returns an empty list if no news (NOT an error).
    """
    normalized = _validate_ticker(ticker)
    if not 1 <= limit <= 50:
        raise ValueError(f"limit must be in 1..50, got {limit}")
    cache_key = f"news:{normalized}"

    def _fetch() -> list[NewsItem]:
        import openbb as _openbb

        try:
            obb_obj = _openbb.obb.news.company(symbol=normalized, limit=limit)
        except Exception as e:
            raise ProviderError(
                provider="unknown",
                status_code=None,
                retry_after=None,
                original=str(e),
            ) from e

        results = getattr(obb_obj, "results", None) or []
        return _to_news_items(results)

    value, _ = get_or_compute(cache_key, CacheName.NEWS, _fetch)
    return value
