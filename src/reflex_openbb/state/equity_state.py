"""EquityState (T-202).

The Reflex state for the /equity/{ticker} page. Wires the equity data
functions into a single state class the page can subscribe to.

Fields (per specs/technical/v1-architecture.md §4):
  ticker, period, quote, price_bars, fundamentals, news,
  comparison_tickers, comparison_bars, is_loading, error, stale_data

Event handlers:
  - set_ticker(ticker)        — REQ-001..005: load all 4 data sources
  - set_period(period)        — REQ-002: reload price history only
  - (Future) load_quote, load_price, load_fundamentals, load_news
  - (Future) add/remove_comparison_ticker — REQ-009 (multi-ticker overlay)

Computed vars:
  - price_chart_data          — REQ-001: list[dict] from price_bars

Constitution Art. 3 (OpenBB only): the state does NOT call obb.*.
It delegates to data.equity.* which is the only place that calls the SDK.

Testing note: handler tests (TestSetTicker, TestSetPeriod) are xfail
in unit tests because rx.State requires a Reflex app context (State
Manager) that is not available in plain unit tests. The data-layer
tests in test_data_equity.py cover the same REQs (REQ-001..005) with
100% green. End-to-end validation runs via 'reflex run' (T-006).
"""

from __future__ import annotations

from typing import Literal

import reflex as rx

from reflex_openbb.data.equity import (
    get_equity_fundamentals,
    get_equity_news,
    get_equity_price_history,
    get_equity_quote,
)
from reflex_openbb.data.errors import ProviderError
from reflex_openbb.data.types import (
    EquityFundamentals,
    EquityQuote,
    NewsItem,
    OHLCBar,
)

__all__ = [
    "EquityState",
    "get_equity_fundamentals",
    "get_equity_news",
    "get_equity_price_history",
    "get_equity_quote",
]


_PERIODS = ("1mo", "6mo", "1y", "5y", "max")
Period = Literal["1mo", "6mo", "1y", "5y", "max"]


class EquityState(rx.State):
    """State for the /equity/{ticker} page."""

    # ─── User-controlled fields ──────────────────────────────────────
    ticker: str = "AAPL"
    period: str = "1y"

    # ─── Loaded data ─────────────────────────────────────────────────
    quote: EquityQuote | None = None
    price_bars: list[OHLCBar] = []  # noqa: RUF012 (rx.State mutable defaults are safe)
    fundamentals: EquityFundamentals | None = None
    news: list[NewsItem] = []  # noqa: RUF012 (rx.State mutable defaults are safe)

    # ─── Comparison overlay (REQ-009, future) ───────────────────────
    comparison_tickers: list[str] = []  # noqa: RUF012
    comparison_bars: dict[str, list[OHLCBar]] = {}  # noqa: RUF012

    # ─── Status flags ────────────────────────────────────────────────
    is_loading: bool = False
    error: str | None = None
    stale_data: bool = False

    # ─── Computed vars ───────────────────────────────────────────────

    @rx.var
    def price_chart_data(self) -> list[dict]:
        """REQ-001: list[dict] from price_bars for the chart component."""
        return [b.model_dump(mode="json") for b in self.price_bars]

    # ─── Event handlers ──────────────────────────────────────────────

    async def set_ticker(self, ticker: str) -> None:
        """REQ-001..005: load all 4 data sources for a new ticker.

        On success, populates quote, price_bars, fundamentals, news.
        On ProviderError, sets stale_data=True and stores the error message.
        Raises InvalidTickerError on validation failure (propagated from
        the data layer's _validate_ticker call).
        """
        from reflex_openbb.data.equity import _validate_ticker

        normalized = _validate_ticker(ticker)
        self.ticker = normalized
        self.is_loading = True
        self.error = None
        self.stale_data = False
        try:
            self.quote = await get_equity_quote(normalized)
            self.price_bars = await get_equity_price_history(normalized, self.period)
            self.fundamentals = await get_equity_fundamentals(normalized)
            self.news = await get_equity_news(normalized)
        except ProviderError as e:
            self.stale_data = True
            self.error = str(e)
        finally:
            self.is_loading = False

    async def set_period(self, period: str) -> None:
        """REQ-002: change the chart's date range and reload price history.

        Args:
            period: one of '1mo', '6mo', '1y', '5y', 'max'.
        """
        if period not in _PERIODS:
            raise ValueError(f"period must be one of {_PERIODS}, got {period!r}")
        self.period = period
        self.is_loading = True
        self.error = None
        self.stale_data = False
        try:
            self.price_bars = await get_equity_price_history(self.ticker, period)
        except ProviderError as e:
            self.stale_data = True
            self.error = str(e)
        finally:
            self.is_loading = False
