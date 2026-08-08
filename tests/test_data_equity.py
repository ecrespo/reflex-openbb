"""
Tests for the equity data functions (T-105).

TDD: this file is written BEFORE data/equity.py.
The tests must FAIL initially, then pass after implementation.

REQs:
- api/v1.md §data.equity: 4 functions
  - get_equity_quote(ticker) -> EquityQuote         (REQ-005)
  - get_equity_price_history(ticker, period) -> list[OHLCBar]  (REQ-001, REQ-002)
  - get_equity_fundamentals(ticker) -> EquityFundamentals       (REQ-003)
  - get_equity_news(ticker, limit=10) -> list[NewsItem]         (REQ-004)
- data-model/v1-models.md: the 4 return types
- Constitution Art. 3: only OpenBB SDK is called
- Constitution Art. 6: cache via get_or_compute
- Constitution Art. 5: monetary fields are Decimal

Strategy: mock the `openbb` SDK at the import boundary. The data functions
import `from openbb import obb`; we replace that with a `MagicMock` in the
fixture so no real network is hit.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from reflex_openbb.data import errors as data_errors
from reflex_openbb.data import types as data_types

# ─── Fixtures: mock the OpenBB SDK ──────────────────────────────────────────


class _FakeOBBject:
    """Mimics the OpenBB SDK's OBBject: has a `results` attribute and `.to_dataframe()`.

    The real OBBject's `to_dataframe()` returns a polars DataFrame (since
    OpenBB 4.x). Our mock does the same.
    """

    def __init__(self, results: list | None = None, df=None) -> None:
        # Attribute is `results` (public), not `_results`, to match the real OBBject.
        self.results = results or []
        self._df = df

    def to_dataframe(self):
        return self._df


def _make_obb_mock(
    *,
    quote_result: dict | None = None,
    price_df=None,
    fundamentals_result: dict | None = None,
    news_results: list | None = None,
) -> MagicMock:
    """Build a MagicMock that mimics `obb.equity.*` and `obb.news.*` paths.

    T-006 update: the OpenBB v4 API moved `quote` to `equity.price.quote`.
    The result is a Pydantic model with `.model_dump()`, not a plain dict.
    Our wrapper `equity._result_to_dict` handles both via hasattr checks.
    """
    obb = MagicMock()

    # T-006: quote is now at obb.equity.price.quote (with provider kwarg)
    obb.equity.price.quote.return_value = _FakeOBBject(
        results=[quote_result] if quote_result else []
    )
    # obb.equity.price.historical(symbol=..., period=...) returns OBBject with .to_dataframe()
    obb.equity.price.historical.return_value = _FakeOBBject(df=price_df)
    # obb.equity.fundamental.metrics(symbol=...) returns OBBject with .results
    obb.equity.fundamental.metrics.return_value = _FakeOBBject(
        results=[fundamentals_result] if fundamentals_result else []
    )
    # obb.news.company(symbol=..., limit=...) returns OBBject with .results
    obb.news.company.return_value = _FakeOBBject(results=news_results or [])

    return obb


@pytest.fixture
def fake_obb(monkeypatch: pytest.MonkeyPatch):
    """Inject a fake `openbb.obb` so the data layer can be tested offline.

    Implementation:
    - We can't easily replace the `openbb` module itself because pytest
      has already imported it. Instead, we patch the `obb` attribute on
      the live `openbb` module — and we also patch the four call sites
      the data layer uses (equity.price.quote, equity.price.historical,
      equity.fundamental.metrics, news.company) by stubbing them at
      the openbb module level.
    - We then clear all caches so each test starts fresh.

    The data layer uses `import openbb as _openbb` inside each function,
    so this attribute patch IS visible — the test sets return values on
    the mock, and the data layer reads them through `_openbb.obb`.
    """
    import openbb as real_openbb

    fake = MagicMock()
    monkeypatch.setattr(real_openbb, "obb", fake)
    return fake


@pytest.fixture(autouse=True)
def _clear_cache():
    """Each test starts with empty caches so hit/miss is deterministic."""
    from reflex_openbb.data import cache

    cache.clear()
    yield
    cache.clear()


# ─── Module / smoke tests ───────────────────────────────────────────────────


def test_equity_module_imports() -> None:
    """data.equity must export the 4 functions from the API spec."""
    from reflex_openbb.data import equity

    assert callable(getattr(equity, "get_equity_quote", None))
    assert callable(getattr(equity, "get_equity_price_history", None))
    assert callable(getattr(equity, "get_equity_fundamentals", None))
    assert callable(getattr(equity, "get_equity_news", None))


# ─── get_equity_quote ───────────────────────────────────────────────────────


class TestGetEquityQuote:
    """REQ-005: get_equity_quote(ticker) -> EquityQuote."""

    @pytest.mark.asyncio
    async def test_returns_equity_quote(self, fake_obb: MagicMock) -> None:
        """Happy path: returns an EquityQuote built from the SDK result."""
        from reflex_openbb.data import equity

        fake_obb.equity.price.quote.return_value = _FakeOBBject(
            results=[
                {
                    "symbol": "AAPL",
                    "last_price": 150.25,
                    "change_percent": 1.5,
                    "market_cap": 2_500_000_000_000,
                    "volume": 50_000_000,
                    "high": 199.62,
                    "low": 124.17,
                    "provider": "yfinance",
                }
            ]
        )

        quote = await equity.get_equity_quote("AAPL")

        assert isinstance(quote, data_types.EquityQuote)
        assert quote.ticker == "AAPL"
        # Art. 5: monetary fields are Decimal, not float
        assert isinstance(quote.price, Decimal)
        assert quote.price == Decimal("150.25")
        assert isinstance(quote.day_change_pct, Decimal)
        assert quote.day_change_pct == Decimal("1.5")
        assert isinstance(quote.market_cap, Decimal)
        assert quote.market_cap == Decimal("2500000000000")
        assert quote.volume == 50_000_000
        assert quote.provider == "yfinance"

    @pytest.mark.asyncio
    async def test_caches_result(self, fake_obb: MagicMock) -> None:
        """REQ: Art. 6 — second call with same ticker hits the cache."""
        from reflex_openbb.data import equity

        fake_obb.equity.price.quote.return_value = _FakeOBBject(
            results=[
                {
                    "symbol": "AAPL",
                    "last_price": 150.0,
                    "change_percent": 0.0,
                    "market_cap": 1_000,
                    "volume": 0,
                    "high": 200.0,
                    "low": 100.0,
                    "provider": "yfinance",
                }
            ]
        )

        q1 = await equity.get_equity_quote("AAPL")
        q2 = await equity.get_equity_quote("AAPL")

        assert q1 is q2  # cached
        # SDK was only called once (first call was a miss, second was a hit)
        assert fake_obb.equity.price.quote.call_count == 1

    @pytest.mark.asyncio
    async def test_normalizes_ticker_to_uppercase(self, fake_obb: MagicMock) -> None:
        """Lowercase input is normalized to uppercase."""
        from reflex_openbb.data import equity

        fake_obb.equity.price.quote.return_value = _FakeOBBject(
            results=[
                {
                    "symbol": "AAPL",
                    "last_price": 150.0,
                    "change_percent": 0.0,
                    "market_cap": 1_000,
                    "volume": 0,
                    "high": 200.0,
                    "low": 100.0,
                    "provider": "yfinance",
                }
            ]
        )

        quote = await equity.get_equity_quote("aapl")
        assert quote.ticker == "AAPL"
        # SDK was called with uppercase
        fake_obb.equity.price.quote.assert_called_once()
        call_kwargs = fake_obb.equity.price.quote.call_args.kwargs
        assert call_kwargs.get("symbol") == "AAPL"

    @pytest.mark.asyncio
    async def test_rejects_empty_ticker(self) -> None:
        from reflex_openbb.data import equity

        with pytest.raises(data_errors.InvalidTickerError):
            await equity.get_equity_quote("")

    @pytest.mark.asyncio
    async def test_rejects_invalid_chars(self) -> None:
        from reflex_openbb.data import equity

        with pytest.raises(data_errors.InvalidTickerError):
            await equity.get_equity_quote("AA!PL")

    @pytest.mark.asyncio
    async def test_rejects_too_long_ticker(self) -> None:
        from reflex_openbb.data import equity

        with pytest.raises(data_errors.InvalidTickerError):
            await equity.get_equity_quote("A" * 11)

    @pytest.mark.asyncio
    async def test_empty_result_raises_provider_error(self, fake_obb: MagicMock) -> None:
        """When the SDK returns no results, raise ProviderError."""
        from reflex_openbb.data import equity

        fake_obb.equity.price.quote.return_value = _FakeOBBject(results=[])

        with pytest.raises(data_errors.ProviderError):
            await equity.get_equity_quote("AAPL")


# ─── get_equity_price_history ───────────────────────────────────────────────


class TestGetEquityPriceHistory:
    """REQ-001, REQ-002: get_equity_price_history(ticker, period) -> list[OHLCBar]."""

    @pytest.mark.asyncio
    async def test_returns_list_of_ohlc_bars(self, fake_obb: MagicMock) -> None:
        import polars as pl

        from reflex_openbb.data import equity

        # Build a polars DataFrame with the EXACT schema the data layer
        # expects (Decimal(precision=18, scale=4) + pl.Date + Int64).
        df = pl.DataFrame(
            {
                "date": [date(2024, 1, 15), date(2024, 1, 16), date(2024, 1, 17)],
                "open": ["150.00", "151.00", "152.00"],
                "high": ["152.00", "153.00", "154.00"],
                "low": ["149.50", "150.50", "151.50"],
                "close": ["151.25", "152.50", "153.75"],
                "volume": [10_000_000, 11_000_000, 12_000_000],
            },
            schema={
                "date": pl.Date,
                "open": pl.Decimal(precision=18, scale=4),
                "high": pl.Decimal(precision=18, scale=4),
                "low": pl.Decimal(precision=18, scale=4),
                "close": pl.Decimal(precision=18, scale=4),
                "volume": pl.Int64,
            },
        )
        fake_obb.equity.price.historical.return_value = _FakeOBBject(df=df)

        bars = await equity.get_equity_price_history("AAPL", "1mo")

        assert len(bars) == 3
        assert all(isinstance(b, data_types.OHLCBar) for b in bars)
        # Decimal fields
        assert all(isinstance(b.close, Decimal) for b in bars)
        assert all(isinstance(b.open, Decimal) for b in bars)
        # First bar's close should match
        assert bars[0].close == Decimal("151.25")

    @pytest.mark.asyncio
    async def test_default_period_is_1y(self, fake_obb: MagicMock) -> None:
        """REQ: api/v1.md — default period='1y'."""
        import polars as pl

        from reflex_openbb.data import equity

        df = pl.DataFrame(
            {
                "date": ["2024-01-15"],
                "open": ["150.00"],
                "high": ["152.00"],
                "low": ["149.50"],
                "close": ["151.00"],
                "volume": [10_000_000],
            },
            schema={
                "date": pl.Date,
                "open": pl.Decimal(precision=18, scale=4),
                "high": pl.Decimal(precision=18, scale=4),
                "low": pl.Decimal(precision=18, scale=4),
                "close": pl.Decimal(precision=18, scale=4),
                "volume": pl.Int64,
            },
        )
        fake_obb.equity.price.historical.return_value = _FakeOBBject(df=df)

        await equity.get_equity_price_history("AAPL")

        # SDK was called with period='1y' (or similar — implementation detail)
        call_kwargs = fake_obb.equity.price.historical.call_args.kwargs
        assert call_kwargs.get("period") == "1y"

    @pytest.mark.asyncio
    async def test_sorted_ascending_by_date(self, fake_obb: MagicMock) -> None:
        """REQ: data-model — list is sorted ascending by date."""
        import polars as pl

        from reflex_openbb.data import equity

        # DataFrame in DESCENDING order — our code should sort it
        df = pl.DataFrame(
            {
                "date": ["2024-01-17", "2024-01-15", "2024-01-16"],
                "open": ["152.00", "150.00", "151.00"],
                "high": ["154.00", "152.00", "153.00"],
                "low": ["151.50", "149.50", "150.50"],
                "close": ["153.75", "151.25", "152.50"],
                "volume": [12_000_000, 10_000_000, 11_000_000],
            },
            schema={
                "date": pl.Date,
                "open": pl.Decimal(precision=18, scale=4),
                "high": pl.Decimal(precision=18, scale=4),
                "low": pl.Decimal(precision=18, scale=4),
                "close": pl.Decimal(precision=18, scale=4),
                "volume": pl.Int64,
            },
        )
        fake_obb.equity.price.historical.return_value = _FakeOBBject(df=df)

        bars = await equity.get_equity_price_history("AAPL", "1mo")

        dates = [b.date for b in bars]
        assert dates == sorted(dates)

    @pytest.mark.asyncio
    async def test_empty_dataframe_raises_provider_error(self, fake_obb: MagicMock) -> None:
        import polars as pl

        from reflex_openbb.data import equity

        fake_obb.equity.price.historical.return_value = _FakeOBBject(df=pl.DataFrame())

        with pytest.raises(data_errors.ProviderError):
            await equity.get_equity_price_history("AAPL", "1mo")

    @pytest.mark.asyncio
    async def test_schema_mismatch_raises_provider_error(self, fake_obb: MagicMock) -> None:
        """If the SDK returns a wrong column, pandera catches it.

        REQ: defensive validation at the data-layer boundary.

        We use a missing column (not a wrong type) because with `coerce=True`
        pandera happily converts int→Decimal and str→Date, so the most
        realistic schema break is "the provider dropped/renamed a column".
        """
        import polars as pl

        from reflex_openbb.data import equity

        # DataFrame with a column renamed — 'closing_price' instead of 'close'
        bad_df = pl.DataFrame(
            {
                "date": ["2024-01-15"],
                "open": ["150.00"],
                "high": ["152.00"],
                "low": ["149.50"],
                "closing_price": ["151.00"],  # wrong name!
                "volume": [10_000_000],
            }
        )
        fake_obb.equity.price.historical.return_value = _FakeOBBject(df=bad_df)

        with pytest.raises(data_errors.ProviderError, match="schema validation"):
            await equity.get_equity_price_history("AAPL", "1mo")

    @pytest.mark.asyncio
    async def test_negative_volume_raises_provider_error(self, fake_obb: MagicMock) -> None:
        """Pandera ge=0 check catches negative volume."""
        import polars as pl

        from reflex_openbb.data import equity

        df = pl.DataFrame(
            {
                "date": ["2024-01-15"],
                "open": ["150.00"],
                "high": ["152.00"],
                "low": ["149.50"],
                "close": ["151.00"],
                "volume": [-1],  # negative!
            },
            schema={
                "date": pl.Date,
                "open": pl.Decimal(precision=18, scale=4),
                "high": pl.Decimal(precision=18, scale=4),
                "low": pl.Decimal(precision=18, scale=4),
                "close": pl.Decimal(precision=18, scale=4),
                "volume": pl.Int64,
            },
        )
        fake_obb.equity.price.historical.return_value = _FakeOBBject(df=df)

        with pytest.raises(data_errors.ProviderError, match="schema validation"):
            await equity.get_equity_price_history("AAPL", "1mo")

    @pytest.mark.asyncio
    async def test_invalid_ticker_rejected(self) -> None:
        from reflex_openbb.data import equity

        with pytest.raises(data_errors.InvalidTickerError):
            await equity.get_equity_price_history("")


# ─── get_equity_fundamentals ────────────────────────────────────────────────


class TestGetEquityFundamentals:
    """REQ-003: get_equity_fundamentals(ticker) -> EquityFundamentals."""

    @pytest.mark.asyncio
    async def test_returns_equity_fundamentals(self, fake_obb: MagicMock) -> None:
        from reflex_openbb.data import equity

        fake_obb.equity.fundamental.metrics.return_value = _FakeOBBject(
            results=[
                {
                    "symbol": "AAPL",
                    "pe_ratio": 28.5,
                    "eps": 6.05,
                    "dividend_yield": 0.5,
                    "beta": 1.2,
                    "book_value_per_share": 4.25,
                    "price_to_book": 35.3,
                    "roe": 0.45,
                    "provider": "yfinance",
                }
            ]
        )

        f = await equity.get_equity_fundamentals("AAPL")

        assert isinstance(f, data_types.EquityFundamentals)
        assert f.ticker == "AAPL"
        # All monetary fields are Decimal
        assert isinstance(f.pe_ratio, Decimal)
        assert f.pe_ratio == Decimal("28.5")
        assert isinstance(f.eps, Decimal)
        assert f.eps == Decimal("6.05")

    @pytest.mark.asyncio
    async def test_handles_missing_metrics(self, fake_obb: MagicMock) -> None:
        """REQ: data-model — missing metrics are None (not omitted)."""
        from reflex_openbb.data import equity

        fake_obb.equity.fundamental.metrics.return_value = _FakeOBBject(
            results=[
                {
                    "symbol": "AAPL",
                    "pe_ratio": None,
                    "eps": None,
                    "dividend_yield": None,
                    "beta": None,
                    "book_value_per_share": None,
                    "price_to_book": None,
                    "roe": None,
                    "provider": "yfinance",
                }
            ]
        )

        f = await equity.get_equity_fundamentals("AAPL")

        assert f.pe_ratio is None
        assert f.eps is None

    @pytest.mark.asyncio
    async def test_caches_result(self, fake_obb: MagicMock) -> None:
        from reflex_openbb.data import equity

        fake_obb.equity.fundamental.metrics.return_value = _FakeOBBject(
            results=[
                {
                    "symbol": "AAPL",
                    "provider": "yfinance",
                }
            ]
        )

        await equity.get_equity_fundamentals("AAPL")
        await equity.get_equity_fundamentals("AAPL")

        # Second call should be a cache hit — SDK not called again
        assert fake_obb.equity.fundamental.metrics.call_count == 1


# ─── get_equity_news ────────────────────────────────────────────────────────


class TestGetEquityNews:
    """REQ-004: get_equity_news(ticker, limit=10) -> list[NewsItem]."""

    @pytest.mark.asyncio
    async def test_returns_list_of_news_items(self, fake_obb: MagicMock) -> None:
        from reflex_openbb.data import equity

        fake_obb.news.company.return_value = _FakeOBBject(
            results=[
                {
                    "id": "n1",
                    "title": "Apple launches new product",
                    "source": "Reuters",
                    "url": "https://reuters.com/article/1",
                    "published_at": "2024-01-15T10:30:00Z",
                },
                {
                    "id": "n2",
                    "title": "Apple Q4 earnings beat",
                    "source": "Bloomberg",
                    "url": "https://bloomberg.com/news/2",
                    "published_at": "2024-01-14T15:00:00Z",
                },
            ]
        )

        news = await equity.get_equity_news("AAPL", limit=2)

        assert len(news) == 2
        assert all(isinstance(n, data_types.NewsItem) for n in news)
        assert news[0].id == "n1"
        assert news[0].title == "Apple launches new product"

    @pytest.mark.asyncio
    async def test_sorted_descending_by_published_at(self, fake_obb: MagicMock) -> None:
        """REQ: data-model — sorted descending by published_at."""
        from reflex_openbb.data import equity

        # Return in ASCENDING order — our code should sort
        fake_obb.news.company.return_value = _FakeOBBject(
            results=[
                {
                    "id": "n1",
                    "title": "Older",
                    "source": "X",
                    "url": "https://x.com/1",
                    "published_at": "2024-01-10T00:00:00Z",
                },
                {
                    "id": "n2",
                    "title": "Newer",
                    "source": "X",
                    "url": "https://x.com/2",
                    "published_at": "2024-01-15T00:00:00Z",
                },
            ]
        )

        news = await equity.get_equity_news("AAPL")

        assert news[0].id == "n2"  # newer first
        assert news[1].id == "n1"

    @pytest.mark.asyncio
    async def test_default_limit_is_10(self, fake_obb: MagicMock) -> None:
        """REQ: api/v1.md — default limit=10."""
        from reflex_openbb.data import equity

        fake_obb.news.company.return_value = _FakeOBBject(results=[])

        await equity.get_equity_news("AAPL")

        call_kwargs = fake_obb.news.company.call_args.kwargs
        assert call_kwargs.get("limit") == 10

    @pytest.mark.asyncio
    async def test_empty_news_returns_empty_list(self, fake_obb: MagicMock) -> None:
        """REQ: api/v1.md — empty result is an empty list (NOT an error)."""
        from reflex_openbb.data import equity

        fake_obb.news.company.return_value = _FakeOBBject(results=[])

        news = await equity.get_equity_news("AAPL")
        assert news == []
