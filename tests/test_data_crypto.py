"""
Tests for the crypto data functions (T-106).

TDD: this file is written BEFORE data/crypto.py.
The tests must FAIL initially, then pass after implementation.

REQs:
- api/v1.md §data.crypto:
  - get_crypto_price_history(symbol, period="1y") -> list[OHLCBar]
  - REQ: REQ-006 (crypto dashboard)
  - Cache: 5 min for 1mo/6mo/1y, 1 day for 5y/max
- data-model/v1-models.md: OHLCBar return type
- Constitution Art. 3: only OpenBB SDK is called
- Constitution Art. 5: monetary fields are Decimal
- Constitution Art. 6: cache via get_or_compute
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from reflex_openbb.data import errors as data_errors
from reflex_openbb.data import types as data_types

# ─── Fixtures: mock the OpenBB SDK ──────────────────────────────────────────


class _FakeOBBject:
    """Mimics the OpenBB SDK's OBBject: has `to_dataframe()` returning polars."""

    def __init__(self, df=None) -> None:
        self._df = df

    def to_dataframe(self):
        return self._df


@pytest.fixture
def fake_obb(monkeypatch: pytest.MonkeyPatch):
    """Inject a fake `openbb.obb` so the data layer can be tested offline."""
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


def test_crypto_module_imports() -> None:
    """data.crypto must export the public function from the API spec."""
    from reflex_openbb.data import crypto

    assert callable(getattr(crypto, "get_crypto_price_history", None))


# ─── get_crypto_price_history ───────────────────────────────────────────────


class TestGetCryptoPriceHistory:
    """REQ-006: get_crypto_price_history(symbol, period="1y") -> list[OHLCBar]."""

    @pytest.mark.asyncio
    async def test_returns_list_of_ohlc_bars(self, fake_obb: MagicMock) -> None:
        """Happy path: returns a list of OHLCBar built from the SDK DataFrame."""
        import polars as pl

        from reflex_openbb.data import crypto

        df = pl.DataFrame(
            {
                "date": ["2024-01-15", "2024-01-16", "2024-01-17"],
                "open": ["30000.00", "31000.00", "32000.00"],
                "high": ["31000.00", "32000.00", "33000.00"],
                "low": ["29500.00", "30500.00", "31500.00"],
                "close": ["30500.00", "31500.00", "32500.00"],
                "volume": [1_000_000, 1_100_000, 1_200_000],
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
        fake_obb.crypto.price.historical.return_value = _FakeOBBject(df=df)

        bars = await crypto.get_crypto_price_history("BTC", "1mo")

        assert len(bars) == 3
        assert all(isinstance(b, data_types.OHLCBar) for b in bars)
        # Decimal fields (Art. 5)
        assert all(isinstance(b.close, Decimal) for b in bars)
        assert all(isinstance(b.open, Decimal) for b in bars)
        assert bars[0].close == Decimal("30500.00")

    @pytest.mark.asyncio
    async def test_default_period_is_1y(self, fake_obb: MagicMock) -> None:
        """REQ: api/v1.md — default period='1y'."""
        import polars as pl

        from reflex_openbb.data import crypto

        df = pl.DataFrame(
            {
                "date": ["2024-01-15"],
                "open": ["30000.00"],
                "high": ["31000.00"],
                "low": ["29500.00"],
                "close": ["30500.00"],
                "volume": [1_000_000],
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
        fake_obb.crypto.price.historical.return_value = _FakeOBBject(df=df)

        await crypto.get_crypto_price_history("BTC")

        call_kwargs = fake_obb.crypto.price.historical.call_args.kwargs
        assert call_kwargs.get("period") == "1y"

    @pytest.mark.asyncio
    async def test_normalizes_symbol_to_uppercase(self, fake_obb: MagicMock) -> None:
        """REQ: api/v1.md — symbols are uppercase; e.g. BTC, ETH, BTC-USD."""
        import polars as pl

        from reflex_openbb.data import crypto

        df = pl.DataFrame(
            {
                "date": ["2024-01-15"],
                "open": ["30000.00"],
                "high": ["31000.00"],
                "low": ["29500.00"],
                "close": ["30500.00"],
                "volume": [1_000_000],
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
        fake_obb.crypto.price.historical.return_value = _FakeOBBject(df=df)

        await crypto.get_crypto_price_history("btc")

        # T-006: yfinance needs "BTC-USD" for USD-quoted pairs. Our
        # code adds the "-USD" suffix when the symbol is alphabetic
        # and has no dash.
        call_kwargs = fake_obb.crypto.price.historical.call_args.kwargs
        assert call_kwargs.get("symbol") == "BTC-USD"

    @pytest.mark.asyncio
    async def test_sorted_ascending_by_date(self, fake_obb: MagicMock) -> None:
        """REQ: data-model — list is sorted ascending by date."""
        import polars as pl

        from reflex_openbb.data import crypto

        # DataFrame in DESCENDING order — our code should sort it
        df = pl.DataFrame(
            {
                "date": ["2024-01-17", "2024-01-15", "2024-01-16"],
                "open": ["32000.00", "30000.00", "31000.00"],
                "high": ["33000.00", "31000.00", "32000.00"],
                "low": ["31500.00", "29500.00", "30500.00"],
                "close": ["32500.00", "30500.00", "31500.00"],
                "volume": [1_200_000, 1_000_000, 1_100_000],
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
        fake_obb.crypto.price.historical.return_value = _FakeOBBject(df=df)

        bars = await crypto.get_crypto_price_history("BTC", "1mo")

        dates = [b.date for b in bars]
        assert dates == sorted(dates)

    @pytest.mark.asyncio
    async def test_caches_result(self, fake_obb: MagicMock) -> None:
        """REQ: Art. 6 — second call with same symbol+period hits the cache."""
        import polars as pl

        from reflex_openbb.data import crypto

        df = pl.DataFrame(
            {
                "date": ["2024-01-15"],
                "open": ["30000.00"],
                "high": ["31000.00"],
                "low": ["29500.00"],
                "close": ["30500.00"],
                "volume": [1_000_000],
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
        fake_obb.crypto.price.historical.return_value = _FakeOBBject(df=df)

        b1 = await crypto.get_crypto_price_history("BTC", "1y")
        b2 = await crypto.get_crypto_price_history("BTC", "1y")

        assert b1 is b2  # cached
        # SDK was only called once
        assert fake_obb.crypto.price.historical.call_count == 1

    @pytest.mark.asyncio
    async def test_different_periods_cached_separately(self, fake_obb: MagicMock) -> None:
        """REQ: api/v1.md — different periods have different caches."""
        import polars as pl

        from reflex_openbb.data import crypto

        df = pl.DataFrame(
            {
                "date": ["2024-01-15"],
                "open": ["30000.00"],
                "high": ["31000.00"],
                "low": ["29500.00"],
                "close": ["30500.00"],
                "volume": [1_000_000],
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
        fake_obb.crypto.price.historical.return_value = _FakeOBBject(df=df)

        await crypto.get_crypto_price_history("BTC", "1mo")
        await crypto.get_crypto_price_history("BTC", "1y")

        # Different periods → SDK called twice
        assert fake_obb.crypto.price.historical.call_count == 2

    @pytest.mark.asyncio
    async def test_rejects_empty_symbol(self) -> None:
        from reflex_openbb.data import crypto

        with pytest.raises(data_errors.InvalidTickerError):
            await crypto.get_crypto_price_history("")

    @pytest.mark.asyncio
    async def test_rejects_invalid_chars(self) -> None:
        """Crypto symbols are stricter than equity — only [A-Z0-9\\-]."""
        from reflex_openbb.data import crypto

        with pytest.raises(data_errors.InvalidTickerError):
            await crypto.get_crypto_price_history("BTC USD")  # space

    @pytest.mark.asyncio
    async def test_rejects_too_long_symbol(self) -> None:
        from reflex_openbb.data import crypto

        with pytest.raises(data_errors.InvalidTickerError):
            await crypto.get_crypto_price_history("A" * 21)  # > 20 chars

    @pytest.mark.asyncio
    async def test_accepts_dash_in_symbol(self, fake_obb: MagicMock) -> None:
        """REQ: api/v1.md — symbols like 'BTC-USD' are valid (dash allowed)."""
        import polars as pl

        from reflex_openbb.data import crypto

        df = pl.DataFrame(
            {
                "date": ["2024-01-15"],
                "open": ["30000.00"],
                "high": ["31000.00"],
                "low": ["29500.00"],
                "close": ["30500.00"],
                "volume": [1_000_000],
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
        fake_obb.crypto.price.historical.return_value = _FakeOBBject(df=df)

        bars = await crypto.get_crypto_price_history("BTC-USD", "1y")

        assert len(bars) == 1
        assert bars[0].close == Decimal("30500.00")

    @pytest.mark.asyncio
    async def test_empty_dataframe_raises_provider_error(self, fake_obb: MagicMock) -> None:
        """If the SDK returns no data, raise ProviderError."""
        import polars as pl

        from reflex_openbb.data import crypto

        fake_obb.crypto.price.historical.return_value = _FakeOBBject(df=pl.DataFrame())

        with pytest.raises(data_errors.ProviderError):
            await crypto.get_crypto_price_history("BTC", "1mo")

    @pytest.mark.asyncio
    async def test_schema_mismatch_raises_provider_error(self, fake_obb: MagicMock) -> None:
        """If the SDK returns a wrong column, pandera catches it.

        REQ: defensive validation at the data-layer boundary.
        """
        import polars as pl

        from reflex_openbb.data import crypto

        # DataFrame with a column renamed — 'closing_price' instead of 'close'
        bad_df = pl.DataFrame(
            {
                "date": ["2024-01-15"],
                "open": ["30000.00"],
                "high": ["31000.00"],
                "low": ["29500.00"],
                "closing_price": ["30500.00"],
                "volume": [1_000_000],
            }
        )
        fake_obb.crypto.price.historical.return_value = _FakeOBBject(df=bad_df)

        with pytest.raises(data_errors.ProviderError, match="schema validation"):
            await crypto.get_crypto_price_history("BTC", "1mo")
