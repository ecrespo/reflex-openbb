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
from datetime import datetime, timezone
from typing import Literal

from reflex_openbb.data.cache import CacheName, get_or_compute
from reflex_openbb.data.errors import InvalidTickerError, ProviderError
from reflex_openbb.data.schemas import ohlc_bars_from_dataframe
from reflex_openbb.data.types import (
    EquityFundamentals,
    EquityQuote,
    NewsItem,
    OHLCBar,
)

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


def _result_to_dict(result) -> dict:
    """Convert a Pydantic OpenBB result to a plain dict (model_dump)."""
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return dict(result)


def _to_equity_quote(result) -> EquityQuote:
    """Build an EquityQuote from a single OpenBB result.

    REQ: REQ-005 + Art. 5 (Decimal coercion).

    T-006 update: works with the new YFinanceEquityQuoteData from
    `obb.equity.price.quote`. The result is a Pydantic model.

    - last_price → price
    - prev_close + last_price → day_change_pct (computed, yfinance
      returns change_percent as None sometimes)
    - year_high → fifty_two_week_high
    - year_low → fifty_two_week_low
    - market_cap is not in price.quote; left as None.
    """
    d = _result_to_dict(result)
    last_price = d.get("last_price")
    if last_price is None:
        # price is required by EquityQuote — fall back to prev_close
        last_price = d.get("prev_close")
    if last_price is None:
        last_price = 0
    prev_close = d.get("prev_close")
    # Prefer yfinance's change_percent; fall back to computing from prev_close
    change_pct = d.get("change_percent")
    if change_pct is None and prev_close:
        change_pct = (float(last_price) - float(prev_close)) / float(prev_close) * 100
    if change_pct is None:
        change_pct = 0
    # 52-week high/low: prefer year_high/year_low; fall back to high/low (daily)
    high_52w = d.get("year_high") or d.get("high")
    if high_52w is None:
        high_52w = 0
    low_52w = d.get("year_low") or d.get("low")
    if low_52w is None:
        low_52w = 0
    return EquityQuote(
        ticker=d.get("symbol", ""),
        price=last_price,
        day_change_pct=change_pct,
        market_cap=d.get("market_cap"),
        volume=d.get("volume", 0) or 0,
        fifty_two_week_high=high_52w,
        fifty_two_week_low=low_52w,
        fetched_at=datetime.now(timezone.utc),
        provider=d.get("provider", "yfinance"),
    )


def _to_equity_fundamentals(result) -> EquityFundamentals:
    """Build an EquityFundamentals from a single OpenBB result.

    REQ: REQ-003 + Art. 5.

    T-006 update: works with YFinanceKeyMetricsData from
    `obb.equity.fundamental.metrics`. The result is a Pydantic model.
    """
    d = _result_to_dict(result)
    return EquityFundamentals(
        ticker=d.get("symbol", ""),
        pe_ratio=d.get("pe_ratio"),
        # T-006: yfinance uses `eps_ttm`; old API used `eps`. Accept both.
        eps=d.get("eps_ttm", d.get("eps")),
        dividend_yield=d.get("dividend_yield"),
        beta=d.get("beta"),
        # yfinance uses `book_value`; old API used `book_value_per_share`.
        book_value_per_share=d.get("book_value", d.get("book_value_per_share")),
        price_to_book=d.get("price_to_book"),
        # yfinance uses `return_on_equity`; old API used `roe`.
        roe=d.get("return_on_equity", d.get("roe")),
        fetched_at=datetime.now(timezone.utc),
        provider=d.get("provider", "yfinance"),
    )


def _to_news_items(results) -> list[NewsItem]:
    """Build a list of NewsItem from a list of OpenBB results.

    REQ: REQ-004 + data-model §NewsItem.
    Returns a list sorted descending by published_at.

    T-006 update: works with YFinanceCompanyNewsData from
    `obb.news.company`. The result is a Pydantic model with
    fields: id, title, source, url, date, summary.
    """
    items: list[NewsItem] = []
    for r in results:
        d = _result_to_dict(r)
        # `date` may be a string, datetime, or pd.Timestamp
        published = d.get("date") or d.get("published_at")
        if isinstance(published, str):
            if published.endswith("Z"):
                published = published[:-1] + "+00:00"
            published = datetime.fromisoformat(published)
        if published is None:
            continue
        # id might be missing; synthesize one
        article_id = d.get("id") or f"{d.get('url', '')}-{published.isoformat()}"
        items.append(
            NewsItem(
                id=str(article_id),
                title=d.get("title", ""),
                source=d.get("source", ""),
                url=d.get("url", "https://example.com"),
                published_at=published,
                summary=d.get("summary") or d.get("text") or d.get("body"),
            )
        )
    # Sort descending by published_at (data-model requirement)
    items.sort(key=lambda n: n.published_at, reverse=True)
    return items


# ─── Public API ─────────────────────────────────────────────────────────────


async def get_equity_quote(ticker: str) -> EquityQuote:
    """Get the current quote for a ticker. REQ: REQ-005.

    Cache: 5 min, key = `quote:{TICKER}`.

    T-006 fix: OpenBB v4 moved `quote` from `obb.equity.quote` to
    `obb.equity.price.quote`. The YFinanceEquityQuoteData has many
    fields; we map the relevant ones to EquityQuote.
    """
    normalized = _validate_ticker(ticker)
    cache_key = f"quote:{normalized}"

    def _fetch() -> EquityQuote:
        # Imported here to allow test-time monkeypatching of `openbb.obb`
        import openbb as _openbb

        try:
            obb_obj = _openbb.obb.equity.price.quote(
                symbol=normalized, provider="yfinance"
            )
        except Exception as e:
            raise ProviderError(
                provider="yfinance",
                status_code=None,
                retry_after=None,
                original=str(e),
            ) from e

        results = getattr(obb_obj, "results", None) or []
        if not results:
            raise ProviderError(
                provider="yfinance",
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

    T-006 fix: the yfinance historical returns a pandas DataFrame
    (not polars). Use .empty (pandas) instead of .is_empty() (polars).
    """
    normalized = _validate_ticker(ticker)
    cache_key = f"price:{normalized}:{period}"

    def _fetch() -> list[OHLCBar]:
        import openbb as _openbb

        try:
            obb_obj = _openbb.obb.equity.price.historical(
                symbol=normalized, period=period, provider="yfinance"
            )
        except Exception as e:
            raise ProviderError(
                provider="yfinance",
                status_code=None,
                retry_after=None,
                original=str(e),
            ) from e

        df = obb_obj.to_dataframe()
        if df is None or len(df) == 0:
            raise ProviderError(
                provider="yfinance",
                status_code=None,
                retry_after=None,
                original=f"No price history for {normalized} ({period})",
            )

        # T-006 fix: yfinance returns a pandas DataFrame; our schema
        # expects a polars DataFrame. Convert (the dataframe is small
        # — typically 1-1000 rows).
        import polars as pl
        if not isinstance(df, pl.DataFrame):
            if hasattr(df, "to_pandas"):  # polars → pandas (shouldn't happen here)
                df = df.to_pandas()
            # pandas: ensure 'date' is a column
            if hasattr(df, "reset_index") and df.index.name is not None and "date" not in df.columns:
                df = df.reset_index()
            # Convert pandas → polars
            try:
                df = pl.from_pandas(df)
            except Exception as e:
                raise ProviderError(
                    provider="yfinance",
                    status_code=None,
                    retry_after=None,
                    original=f"Could not convert historical df to polars: {e}",
                ) from e
        # Normalize: rename 'date' if index was named differently
        if "date" not in df.columns and df.columns[0] not in ("date",):
            df = df.rename({df.columns[0]: "date"})

        return ohlc_bars_from_dataframe(df)

    value, _ = get_or_compute(cache_key, CacheName.PRICE, _fetch)
    return value


async def get_equity_fundamentals(ticker: str) -> EquityFundamentals:
    """Get fundamental metrics for a ticker. REQ: REQ-003.

    Cache: 1 day, key = `fund:{TICKER}`.

    T-006 fix: pass provider explicitly. Result is a Pydantic model.
    """
    normalized = _validate_ticker(ticker)
    cache_key = f"fund:{normalized}"

    def _fetch() -> EquityFundamentals:
        import openbb as _openbb

        try:
            obb_obj = _openbb.obb.equity.fundamental.metrics(
                symbol=normalized, provider="yfinance"
            )
        except Exception as e:
            raise ProviderError(
                provider="yfinance",
                status_code=None,
                retry_after=None,
                original=str(e),
            ) from e

        results = getattr(obb_obj, "results", None) or []
        if not results:
            raise ProviderError(
                provider="yfinance",
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
            obb_obj = _openbb.obb.news.company(
                symbol=normalized, limit=limit, provider="yfinance"
            )
        except Exception as e:
            raise ProviderError(
                provider="yfinance",
                status_code=None,
                retry_after=None,
                original=str(e),
            ) from e

        results = getattr(obb_obj, "results", None) or []
        return _to_news_items(results)

    value, _ = get_or_compute(cache_key, CacheName.NEWS, _fetch)
    return value
