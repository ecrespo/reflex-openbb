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

    @rx.var
    def market_cap_display(self) -> str:
        """Display-friendly market cap (e.g. '$2.50T')."""
        if self.quote is None:
            return "n/a"
        v = float(self.quote.market_cap)
        if v >= 1_000_000_000_000:
            return f"${v / 1_000_000_000_000:.2f}T"
        if v >= 1_000_000_000:
            return f"${v / 1_000_000_000:.2f}B"
        if v >= 1_000_000:
            return f"${v / 1_000_000:.2f}M"
        return f"${v:,.0f}"

    @rx.var
    def volume_display(self) -> str:
        """Display-friendly volume (e.g. '10.50M')."""
        if self.quote is None:
            return "n/a"
        v = float(self.quote.volume)
        if v >= 1_000_000_000:
            return f"{v / 1_000_000_000:.2f}B"
        if v >= 1_000_000:
            return f"{v / 1_000_000:.2f}M"
        if v >= 1_000:
            return f"{v / 1_000:.2f}K"
        return f"{v:,.0f}"

    @rx.var
    def price_display(self) -> str:
        """Display-friendly price (e.g. '$150.00')."""
        if self.quote is None:
            return "n/a"
        return f"${self.quote.price}"

    @rx.var
    def day_change_pct_display(self) -> str:
        """Display-friendly day change % (e.g. '1.5' or '-2.3')."""
        if self.quote is None:
            return "n/a"
        return f"{self.quote.day_change_pct}"

    @rx.var
    def high_52w_display(self) -> str:
        """Display-friendly 52-week high (e.g. '$200.00')."""
        if self.quote is None:
            return "n/a"
        return f"${self.quote.fifty_two_week_high}"

    @rx.var
    def low_52w_display(self) -> str:
        """Display-friendly 52-week low (e.g. '$100.00')."""
        if self.quote is None:
            return "n/a"
        return f"${self.quote.fifty_two_week_low}"

    @rx.var
    def has_quote(self) -> bool:
        """True if a quote is loaded."""
        return self.quote is not None

    @rx.var
    def has_fundamentals(self) -> bool:
        """True if fundamentals are loaded."""
        return self.fundamentals is not None

    @rx.var
    def has_news(self) -> bool:
        """True if there is any news."""
        return len(self.news) > 0

    @rx.var
    def news_display(self) -> list[str]:
        """News items pre-rendered as HTML strings (server-side).

        This avoids the TypedDict / HttpUrl / datetime issues that
        happen when passing Pydantic models directly to components.
        Each string is a full <div>...</div> with title, source, date, link.
        """
        from html import escape
        items = []
        for n in self.news:
            title = escape(n.title)
            source = escape(n.source)
            when = escape(n.published_at.strftime("%Y-%m-%d %H:%M"))
            url = escape(str(n.url))
            items.append(
                f'<div class="news-card">'
                f'<h3>{title}</h3>'
                f'<p class="meta">{source} · {when}</p>'
                f'<a href="{url}" target="_blank" rel="noopener">Read more</a>'
                f'</div>'
            )
        return items
    def _fmt(self, value) -> str:
        """Format a Decimal/None as a string."""
        return "n/a" if value is None else str(value)

    @rx.var
    def fund_pe_ratio_display(self) -> str:
        if self.fundamentals is None:
            return "n/a"
        return self._fmt(self.fundamentals.pe_ratio)

    @rx.var
    def fund_eps_display(self) -> str:
        if self.fundamentals is None:
            return "n/a"
        return self._fmt(self.fundamentals.eps)

    @rx.var
    def fund_dividend_yield_display(self) -> str:
        if self.fundamentals is None:
            return "n/a"
        return self._fmt(self.fundamentals.dividend_yield)

    @rx.var
    def fund_beta_display(self) -> str:
        if self.fundamentals is None:
            return "n/a"
        return self._fmt(self.fundamentals.beta)

    @rx.var
    def fund_book_value_display(self) -> str:
        if self.fundamentals is None:
            return "n/a"
        return self._fmt(self.fundamentals.book_value_per_share)

    @rx.var
    def fund_price_to_book_display(self) -> str:
        if self.fundamentals is None:
            return "n/a"
        return self._fmt(self.fundamentals.price_to_book)

    @rx.var
    def fund_roe_display(self) -> str:
        if self.fundamentals is None:
            return "n/a"
        return self._fmt(self.fundamentals.roe)

    # ─── Event handlers ──────────────────────────────────────────────

    async def load_initial(self) -> None:
        """T-007: called by app.add_page(on_load=...) when the page mounts.

        Loads data for the default ticker (AAPL) so the page isn't empty.
        """
        if self.quote is not None:
            return  # already loaded (e.g. navigating back)
        await self._load_all(self.ticker)

    async def _load_all(self, ticker: str) -> None:
        """Load all 4 data sources for a ticker. Shared by load_initial and set_ticker."""
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

    async def set_ticker(self, form_data: dict) -> None:
        """REQ-001..005: load all 4 data sources for a new ticker.

        On success, populates quote, price_bars, fundamentals, news.
        On ProviderError, sets stale_data=True and stores the error message.
        Raises InvalidTickerError on validation failure (propagated from
        the data layer's _validate_ticker call).
        """
        from reflex_openbb.data.equity import _validate_ticker

        ticker = form_data.get("ticker", "AAPL") if isinstance(form_data, dict) else "AAPL"
        normalized = _validate_ticker(ticker)
        await self._load_all(normalized)

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

    async def add_to_comparison(self, form_data: dict) -> None:
        """REQ-009: add a ticker to the comparison overlay (max 5).

        REQ-009 UW: if the user attempts to add a 6th ticker, the system
        shall reject the request and display a notification.
        """
        from reflex_openbb.data.equity import _validate_ticker

        ticker = form_data.get("ticker", "") if isinstance(form_data, dict) else ""
        if not ticker:
            return
        if len(self.comparison_tickers) >= 5:
            raise ValueError(
                "Comparison overlay supports at most 5 tickers. "
                "Remove one before adding another."
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
            self.comparison_tickers = [
                t for t in self.comparison_tickers if t != normalized
            ]

    async def remove_from_comparison(self, ticker: str) -> None:
        """REQ-009: remove a ticker from the comparison overlay."""
        self.comparison_tickers = [t for t in self.comparison_tickers if t != ticker]
        new_bars = {k: v for k, v in self.comparison_bars.items() if k != ticker}
        self.comparison_bars = new_bars
