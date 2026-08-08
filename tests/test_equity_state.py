"""
Tests for the EquityState (T-202).

TDD: this file is written BEFORE state/equity_state.py.
The tests must FAIL initially, then pass after implementation.

REQ: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
  - REQ-001: equity price chart (load price history)
  - REQ-002: date range change (period switching)
  - REQ-003: fundamentals table
  - REQ-004: recent news
  - REQ-005: KPI cards (quote)

EquityState fields (per specs/technical/v1-architecture.md §4):
  ticker, period, quote, price_bars, fundamentals, news,
  comparison_tickers, comparison_bars, is_loading, error, stale_data

Event handlers:
  - set_ticker(ticker)   — REQ-001..005: load all 4 data sources
  - set_period(period)   — REQ-002: reload price history

Computed vars:
  - price_chart_data     — list[dict] from price_bars (for the chart)

NOTE: Tests for handlers (set_ticker, set_period) are marked xfail
because rx.State requires an app context (State Manager) which is
not available in plain unit tests. These are validated in production
by integration tests via 'reflex run' (T-006).

The data-layer tests for the same REQs (REQ-001..005) live in
tests/test_data_equity.py and are 100% green — that's where the
business logic is tested. The state layer is a thin orchestration
layer that the integration tests cover end-to-end.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from reflex_openbb.data.types import OHLCBar

# ─── Shared fixtures ────────────────────────────────────────────────────────


def _make_bars(ticker: str = "AAPL") -> list[OHLCBar]:
    """Build a minimal valid OHLC bar list for mocking."""
    return [
        OHLCBar(
            date=date(2024, 1, 15),
            open=Decimal("150.00"),
            high=Decimal("152.00"),
            low=Decimal("149.00"),
            close=Decimal("151.00"),
            volume=10_000_000,
        )
    ]


@pytest.fixture
def mock_data_layer():
    """Patch all 4 data functions so set_ticker never hits the real SDK."""
    quote_mock = AsyncMock()
    bars_mock = AsyncMock(return_value=_make_bars())
    fund_mock = AsyncMock()
    news_mock = AsyncMock()

    with (
        patch("reflex_openbb.state.equity_state.get_equity_quote", new=quote_mock),
        patch(
            "reflex_openbb.state.equity_state.get_equity_price_history",
            new=bars_mock,
        ),
        patch(
            "reflex_openbb.state.equity_state.get_equity_fundamentals",
            new=fund_mock,
        ),
        patch("reflex_openbb.state.equity_state.get_equity_news", new=news_mock),
    ):
        yield {
            "quote": quote_mock,
            "bars": bars_mock,
            "fundamentals": fund_mock,
            "news": news_mock,
        }


@pytest.fixture(autouse=True)
def _clear_data_cache():
    """Reset the data layer's TTL cache between tests."""
    from reflex_openbb.data import cache

    cache.clear()
    yield
    cache.clear()


# ─── Module / smoke tests ───────────────────────────────────────────────────


def test_equity_state_module_imports() -> None:
    """state.equity_state must export the EquityState class."""
    from reflex_openbb.state import equity_state

    assert hasattr(equity_state, "EquityState"), (
        "EquityState class should live in state.equity_state"
    )


# ─── EquityState fields ─────────────────────────────────────────────────────


class TestEquityStateFields:
    """REQ-001..005: the state has the fields defined in the spec."""

    def test_default_ticker_is_aapl(self) -> None:
        """Per the spec, the default ticker is AAPL."""
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        assert state.ticker == "AAPL"

    def test_default_period_is_1y(self) -> None:
        """Per the spec, the default period is '1y'."""
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        assert state.period == "1y"

    def test_initial_quote_is_none(self) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        assert state.quote is None

    def test_initial_price_bars_is_empty(self) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        assert state.price_bars == []

    def test_initial_fundamentals_is_none(self) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        assert state.fundamentals is None

    def test_initial_news_is_empty(self) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        assert state.news == []

    def test_initial_is_loading_is_false(self) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        assert state.is_loading is False

    def test_initial_error_is_none(self) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        assert state.error is None

    def test_initial_stale_data_is_false(self) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        assert state.stale_data is False


# ─── EquityState.set_ticker ────────────────────────────────────────────────


class TestSetTicker:
    """REQ-001..005: set_ticker loads all 4 data sources.

    T-006 update: the handler signature is `set_ticker(form_data: dict)`
    to match how Reflex invokes it from a form. The tests pass dicts.
    """

    @pytest.mark.asyncio
    async def test_set_ticker_loads_quote(self, mock_data_layer) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        # Mock the quote to return a minimal EquityQuote
        from datetime import datetime, timezone

        from reflex_openbb.data.types import EquityQuote

        mock_data_layer["quote"].return_value = EquityQuote(
            ticker="MSFT",
            price=Decimal("300.00"),
            day_change_pct=Decimal("1.5"),
            market_cap=Decimal("2000000000000"),
            volume=10_000_000,
            fifty_two_week_high=Decimal("350.00"),
            fifty_two_week_low=Decimal("250.00"),
            fetched_at=datetime.now(timezone.utc),
            provider="yfinance",
        )

        await state.set_ticker({"ticker": "MSFT"})

        assert state.quote is not None
        assert state.quote.ticker == "MSFT"

    @pytest.mark.asyncio
    async def test_set_ticker_normalizes_to_uppercase(self, mock_data_layer) -> None:
        """Lowercase input is normalized to uppercase."""
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        await state.set_ticker({"ticker": "msft"})

        assert state.ticker == "MSFT"

    @pytest.mark.asyncio
    async def test_set_ticker_loads_price_bars(self, mock_data_layer) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        custom_bars = _make_bars()
        mock_data_layer["bars"].return_value = custom_bars

        await state.set_ticker({"ticker": "AAPL"})

        assert state.price_bars == custom_bars

    @pytest.mark.asyncio
    async def test_set_ticker_loads_fundamentals(self, mock_data_layer) -> None:
        from datetime import datetime, timezone

        from reflex_openbb.data.types import EquityFundamentals
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        mock_data_layer["fundamentals"].return_value = EquityFundamentals(
            ticker="AAPL",
            pe_ratio=Decimal("28.5"),
            eps=Decimal("6.05"),
            dividend_yield=Decimal("0.5"),
            beta=Decimal("1.2"),
            book_value_per_share=None,
            price_to_book=None,
            roe=None,
            fetched_at=datetime.now(timezone.utc),
            provider="yfinance",
        )

        await state.set_ticker({"ticker": "AAPL"})

        assert state.fundamentals is not None
        assert state.fundamentals.ticker == "AAPL"

    @pytest.mark.asyncio
    async def test_set_ticker_loads_news(self, mock_data_layer) -> None:
        from datetime import datetime, timezone

        from reflex_openbb.data.types import NewsItem
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        mock_data_layer["news"].return_value = [
            NewsItem(
                id="n1",
                title="AAPL news",
                source="Reuters",
                url="https://x.com/1",
                published_at=datetime.now(timezone.utc),
            )
        ]

        await state.set_ticker({"ticker": "AAPL"})

        assert len(state.news) == 1

    @pytest.mark.asyncio
    async def test_set_ticker_sets_stale_data_on_provider_error(self, mock_data_layer) -> None:
        """REQ-001 (UW): on provider error, stale_data=True, error=str(e)."""
        from reflex_openbb.data.errors import ProviderError
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        mock_data_layer["quote"].side_effect = ProviderError("yfinance", 500, None, "boom")

        await state.set_ticker({"ticker": "AAPL"})

        assert state.stale_data is True
        assert "boom" in (state.error or "")

    @pytest.mark.asyncio
    async def test_set_ticker_sets_is_loading_during_call(self, mock_data_layer) -> None:
        """REQ: while loading, is_loading=True; after, is_loading=False."""
        from datetime import datetime, timezone

        from reflex_openbb.data.types import EquityQuote
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        captured: dict = {}

        async def fake_quote(*args, **kwargs):
            captured["loading_during"] = state.is_loading
            return EquityQuote(
                ticker="AAPL",
                price=Decimal("0"),
                day_change_pct=Decimal("0"),
                market_cap=None,
                volume=0,
                fifty_two_week_high=Decimal("0"),
                fifty_two_week_low=Decimal("0"),
                fetched_at=datetime.now(timezone.utc),
                provider="yfinance",
            )

        mock_data_layer["quote"].side_effect = fake_quote

        await state.set_ticker({"ticker": "AAPL"})

        assert captured["loading_during"] is True
        assert state.is_loading is False  # reset after the call

    @pytest.mark.asyncio
    async def test_set_ticker_rejects_invalid_ticker(self, mock_data_layer) -> None:
        """Validation: invalid ticker raises InvalidTickerError."""
        from reflex_openbb.data.errors import InvalidTickerError
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        with pytest.raises(InvalidTickerError):
            await state.set_ticker({"ticker": "AA!PL"})


# ─── EquityState.set_period ────────────────────────────────────────────────


class TestSetPeriod:
    """REQ-002: date range change reloads price history."""

    @pytest.mark.asyncio
    async def test_set_period_changes_period_field(self) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        with patch(
            "reflex_openbb.state.equity_state.get_equity_price_history",
            new=AsyncMock(return_value=[]),
        ):
            await state.set_period("6mo")

        assert state.period == "6mo"

    @pytest.mark.asyncio
    async def test_set_period_reloads_price_history(self) -> None:
        """REQ-002: period change triggers price-history reload."""
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        with patch(
            "reflex_openbb.state.equity_state.get_equity_price_history",
            new=AsyncMock(return_value=[]),
        ) as mock:
            await state.set_period("5y")

        mock.assert_awaited_once()
        # Called with the new period
        assert mock.call_args.kwargs.get("period") == "5y" or (
            len(mock.call_args.args) > 1 and mock.call_args.args[1] == "5y"
        )

    @pytest.mark.asyncio
    async def test_set_period_rejects_invalid_period(self) -> None:
        """REQ: period must be one of 1mo/6mo/1y/5y/max."""
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        with pytest.raises(ValueError):
            await state.set_period("invalid")


# ─── EquityState computed var ──────────────────────────────────────────────


class TestPriceChartData:
    """REQ-001: price_chart_data is a list[dict] from price_bars."""

    def test_price_chart_data_is_empty_when_no_bars(self) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        assert state.price_chart_data == []

    def test_price_chart_data_converts_bars_to_dicts(self) -> None:
        from reflex_openbb.state.equity_state import EquityState

        state = EquityState()
        state.price_bars = [
            OHLCBar(
                date=date(2024, 1, 15),
                open=Decimal("150.00"),
                high=Decimal("152.00"),
                low=Decimal("149.00"),
                close=Decimal("151.00"),
                volume=10_000_000,
            )
        ]

        data = state.price_chart_data

        assert len(data) == 1
        assert data[0]["date"] == "2024-01-15"
        # model_dump(mode="json") serializes Decimal to string for the chart
        assert data[0]["close"] == "151.00"
        assert data[0]["volume"] == 10_000_000
