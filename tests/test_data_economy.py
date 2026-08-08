"""
Tests for the economy data functions (T-107).

TDD: this file is written BEFORE data/economy.py.
The tests must FAIL initially, then pass after implementation.

REQs:
- api/v1.md §data.economy:
  - get_economy_indicator(indicator, country="US") -> list[MacroPoint]
  - REQ: REQ-007 (economy dashboard)
  - Cache: 7 days TTL (key = 'macro:{country}:{indicator}')
- data-model/v1-models.md §MacroPoint:
  - year (int), value (Decimal), country (ISO-3166 alpha-2),
    indicator (one of GDP/CPI/UNRATE)
- Constitution Art. 5: value is Decimal
- Constitution Art. 6: cache via get_or_compute
- Constitution Art. 3: only OpenBB SDK is called
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


def test_economy_module_imports() -> None:
    """data.economy must export the public function from the API spec."""
    from reflex_openbb.data import economy

    assert callable(getattr(economy, "get_economy_indicator", None))


# ─── get_economy_indicator ──────────────────────────────────────────────────


class TestGetEconomyIndicator:
    """REQ-007: get_economy_indicator(indicator, country='US') -> list[MacroPoint]."""

    @pytest.mark.asyncio
    async def test_gdp_returns_list_of_macro_points(self, fake_obb: MagicMock) -> None:
        """GDP: list of MacroPoint with year + Decimal value."""
        import polars as pl

        from reflex_openbb.data import economy

        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022, 2023],
                "value": ["21.0", "23.0", "25.5", "27.4"],
            },
            schema={"year": pl.Int64, "value": pl.Decimal(precision=18, scale=4)},
        )
        fake_obb.economy.indicators.return_value = _FakeOBBject(df=df)

        points = await economy.get_economy_indicator("GDP", "US")

        assert len(points) == 4
        assert all(isinstance(p, data_types.MacroPoint) for p in points)
        assert all(isinstance(p.value, Decimal) for p in points)
        assert points[0].year == 2020
        assert points[0].value == Decimal("21.0")
        assert points[0].country == "US"
        assert points[0].indicator == "GDP"

    @pytest.mark.asyncio
    async def test_cpi_routes_to_cpi_endpoint(self, fake_obb: MagicMock) -> None:
        """REQ: 'CPI' indicator calls obb.economy.cpi."""
        import polars as pl

        from reflex_openbb.data import economy

        df = pl.DataFrame(
            {"year": [2024], "value": ["300.0"]},
            schema={"year": pl.Int64, "value": pl.Decimal(precision=18, scale=4)},
        )
        fake_obb.economy.indicators.return_value = _FakeOBBject(df=df)

        await economy.get_economy_indicator("CPI", "US")

        call_kwargs = fake_obb.economy.indicators.call_args.kwargs
        assert call_kwargs.get("country") == "US"

    @pytest.mark.asyncio
    async def test_unrate_routes_to_unrate_endpoint(self, fake_obb: MagicMock) -> None:
        """REQ: 'UNRATE' indicator calls obb.economy.indicators.

        T-006: OpenBB v4 unified the macro endpoints into
        `obb.economy.indicators(symbol=..., country=...)`. UNRATE is
        not available in the econdb catalog; we return [] for it.
        """
        import polars as pl

        from reflex_openbb.data import economy

        df = pl.DataFrame(
            {"year": [2024], "value": ["3.7"]},
            schema={"year": pl.Int64, "value": pl.Decimal(precision=18, scale=4)},
        )
        fake_obb.economy.indicators.return_value = _FakeOBBject(df=df)

        points = await economy.get_economy_indicator("UNRATE", "US")

        # T-006: UNRATE returns [] because econdb doesn't have it.
        assert points == []
        # The SDK should NOT be called for UNRATE (early return).
        assert fake_obb.economy.indicators.call_count == 0

    @pytest.mark.asyncio
    async def test_default_country_is_us(self, fake_obb: MagicMock) -> None:
        """REQ: api/v1.md — default country='US'."""
        import polars as pl

        from reflex_openbb.data import economy

        df = pl.DataFrame(
            {"year": [2024], "value": ["27.4"]},
            schema={"year": pl.Int64, "value": pl.Decimal(precision=18, scale=4)},
        )
        fake_obb.economy.indicators.return_value = _FakeOBBject(df=df)

        await economy.get_economy_indicator("GDP")

        call_kwargs = fake_obb.economy.indicators.call_args.kwargs
        assert call_kwargs.get("country") == "US"

    @pytest.mark.asyncio
    async def test_country_normalized_to_uppercase(self, fake_obb: MagicMock) -> None:
        """REQ: data-model — country is uppercase ISO-3166."""
        import polars as pl

        from reflex_openbb.data import economy

        df = pl.DataFrame(
            {"year": [2024], "value": ["27.4"]},
            schema={"year": pl.Int64, "value": pl.Decimal(precision=18, scale=4)},
        )
        fake_obb.economy.indicators.return_value = _FakeOBBject(df=df)

        await economy.get_economy_indicator("GDP", "us")

        call_kwargs = fake_obb.economy.indicators.call_args.kwargs
        assert call_kwargs.get("country") == "US"

    @pytest.mark.asyncio
    async def test_sorted_ascending_by_year(self, fake_obb: MagicMock) -> None:
        """REQ: data-model — list is sorted ascending by year."""
        import polars as pl

        from reflex_openbb.data import economy

        # DataFrame in DESCENDING order — our code should sort
        df = pl.DataFrame(
            {
                "year": [2023, 2021, 2022, 2020],
                "value": ["27.4", "23.0", "25.5", "21.0"],
            },
            schema={"year": pl.Int64, "value": pl.Decimal(precision=18, scale=4)},
        )
        fake_obb.economy.indicators.return_value = _FakeOBBject(df=df)

        points = await economy.get_economy_indicator("GDP", "US")

        years = [p.year for p in points]
        assert years == sorted(years)

    @pytest.mark.asyncio
    async def test_caches_result(self, fake_obb: MagicMock) -> None:
        """REQ: Art. 6 — second call with same indicator+country hits cache."""
        import polars as pl

        from reflex_openbb.data import economy

        df = pl.DataFrame(
            {"year": [2024], "value": ["27.4"]},
            schema={"year": pl.Int64, "value": pl.Decimal(precision=18, scale=4)},
        )
        fake_obb.economy.indicators.return_value = _FakeOBBject(df=df)

        p1 = await economy.get_economy_indicator("GDP", "US")
        p2 = await economy.get_economy_indicator("GDP", "US")

        assert p1 is p2
        assert fake_obb.economy.indicators.call_count == 1

    @pytest.mark.asyncio
    async def test_different_indicators_cached_separately(self, fake_obb: MagicMock) -> None:
        """REQ: different indicators → different cache keys."""
        import polars as pl

        from reflex_openbb.data import economy

        df = pl.DataFrame(
            {"year": [2024], "value": ["27.4"]},
            schema={"year": pl.Int64, "value": pl.Decimal(precision=18, scale=4)},
        )
        fake_obb.economy.indicators.return_value = _FakeOBBject(df=df)
        fake_obb.economy.indicators.return_value = _FakeOBBject(df=df)

        await economy.get_economy_indicator("GDP", "US")
        await economy.get_economy_indicator("CPI", "US")

        # T-006: OpenBB v4 uses one endpoint with `symbol=` arg, so
        # each indicator makes a separate SDK call.
        assert fake_obb.economy.indicators.call_count == 2
        # Verify both symbols were called
        symbols_called = [
            c.kwargs.get("symbol") for c in fake_obb.economy.indicators.call_args_list
        ]
        assert "GDP" in symbols_called
        assert "CPI" in symbols_called

    @pytest.mark.asyncio
    async def test_different_countries_cached_separately(self, fake_obb: MagicMock) -> None:
        """REQ: different countries → different cache keys."""
        import polars as pl

        from reflex_openbb.data import economy

        df = pl.DataFrame(
            {"year": [2024], "value": ["27.4"]},
            schema={"year": pl.Int64, "value": pl.Decimal(precision=18, scale=4)},
        )
        fake_obb.economy.indicators.return_value = _FakeOBBject(df=df)

        await economy.get_economy_indicator("GDP", "US")
        await economy.get_economy_indicator("GDP", "DE")

        # Each country triggers a separate SDK call
        assert fake_obb.economy.indicators.call_count == 2

    @pytest.mark.asyncio
    async def test_rejects_invalid_indicator(self) -> None:
        """REQ: only GDP, CPI, UNRATE are allowed."""
        from reflex_openbb.data import economy

        with pytest.raises(ValueError):
            await economy.get_economy_indicator("INVALID", "US")

    @pytest.mark.asyncio
    async def test_rejects_invalid_country(self) -> None:
        """REQ: country must be 2-letter ISO-3166."""
        from reflex_openbb.data import economy

        with pytest.raises(ValueError):
            await economy.get_economy_indicator("GDP", "USA")  # 3 letters

        with pytest.raises(ValueError):
            await economy.get_economy_indicator("GDP", "U")

        with pytest.raises(ValueError):
            await economy.get_economy_indicator("GDP", "12")

    @pytest.mark.asyncio
    async def test_empty_dataframe_returns_empty_list(self, fake_obb: MagicMock) -> None:
        """REQ: empty result is an empty list (NOT an error)."""
        import polars as pl

        from reflex_openbb.data import economy

        fake_obb.economy.indicators.return_value = _FakeOBBject(df=pl.DataFrame())

        points = await economy.get_economy_indicator("GDP", "US")
        assert points == []

    @pytest.mark.asyncio
    async def test_schema_mismatch_raises_provider_error(self, fake_obb: MagicMock) -> None:
        """Pandera catches wrong column."""
        import polars as pl

        from reflex_openbb.data import economy

        bad_df = pl.DataFrame(
            {
                "year": [2024],
                "indicator_value": ["27.4"],  # wrong name
            }
        )
        fake_obb.economy.indicators.return_value = _FakeOBBject(df=bad_df)

        with pytest.raises(data_errors.ProviderError, match="schema validation"):
            await economy.get_economy_indicator("GDP", "US")
