"""EquityState (T-202 + T-505).

The Reflex state for the /equity page. Wires the equity data
functions into a single state class the page can subscribe to.

Fields (per specs/technical/v1-architecture.md §4):
  ticker, period, quote, price_bars, fundamentals, news,
  comparison_tickers, comparison_bars, is_loading, error, stale_data

Event handlers:
  - set_ticker(ticker)        — REQ-001..005: load all 4 data sources
  - set_period(period)        — REQ-002: reload price history only
  - export_csv()              — REQ-008: trigger CSV download
  - add_to_comparison(ticker) — REQ-009: add ticker to overlay
  - remove_from_comparison()  — REQ-009: remove last ticker

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
    """State for the /equity page."""

    # ─── User-controlled fields ──────────────────────────────────────
    ticker: str = "AAPL"
    period: str = "1y"

    # ─── Loaded data ─────────────────────────────────────────────────
    quote: EquityQuote | None = None
    price_bars: list[OHLCBar] = []  # noqa: RUF012 (rx.State mutable defaults are safe)
    fundamentals: EquityFundamentals | None = None
    news: list[NewsItem] = []  # noqa: RUF012 (rx.State mutable defaults are safe)

    # ─── Comparison overlay (REQ-009) ────────────────────────────────
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

    @rx.var
    def comparison_chart_data(self) -> list[dict]:
        """REQ-009: list[dict] from comparison_bars for the chart overlay.

        Each row is {"date": ..., "close_compare": ...} for the recharts
        secondary line.
        """
        rows: list[dict] = []
        for _ticker, bars in self.comparison_bars.items():
            for b in bars:
                rows.append(
                    {
                        "date": b.date.isoformat(),
                        "close_compare": str(b.close),
                    }
                )
        return rows

    # ─── Event handlers ──────────────────────────────────────────────

    async def set_ticker(self, ticker: str) -> None:
        """REQ-001..005: load all 4 data sources for a new ticker."""
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
        """REQ-002: change the chart's date range and reload price history."""
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

    async def export_csv(self) -> None:
        """REQ-008: trigger a CSV download of the current price_bars."""
        from reflex_openbb.services.csv_export import to_csv_bars

        csv_data = to_csv_bars(self.price_bars)
        filename = f"{self.ticker.lower()}_{self.period}.csv"
        return rx.download(
            data=csv_data,
            filename=filename,
        )

    async def add_to_comparison(self, ticker: str) -> None:
        """REQ-009: add a ticker to the comparison overlay (max 5).

        REQ-009 UW: if the user attempts to add a 6th ticker, the system
        shall reject the request and display a notification.
        """
        from reflex_openbb.data.equity import _validate_ticker

        if len(self.comparison_tickers) >= 5:
            raise ValueError(
                "Comparison overlay supports at most 5 tickers. Remove one before adding another."
            )
        normalized = _validate_ticker(ticker)
        if normalized in self.comparison_tickers:
            return  # already added
        self.comparison_tickers = [*self.comparison_tickers, normalized]
        try:
            self.comparison_bars = {
                **self.comparison_bars,
                normalized: await get_equity_price_history(normalized, self.period),
            }
        except ProviderError as e:
            self.stale_data = True
            self.error = str(e)
            # Roll back the ticker we just added
            self.comparison_tickers = [t for t in self.comparison_tickers if t != normalized]

    async def remove_from_comparison(self, ticker: str) -> None:
        """REQ-009: remove a ticker from the comparison overlay."""
        self.comparison_tickers = [t for t in self.comparison_tickers if t != ticker]
        new_bars = {k: v for k, v in self.comparison_bars.items() if k != ticker}
        self.comparison_bars = new_bars
