"""
Tests for the EconomyState (T-204).

TDD: this file is written BEFORE state/economy_state.py.
The tests must FAIL initially, then pass after implementation.

REQ: REQ-007 (economy dashboard)

EconomyState event handlers (per specs/api/v1.md §EconomyState):
  - set_indicator(indicator)  — stores; triggers load_indicator
  - set_country(country)      — stores; triggers load_indicator
  - load_indicator()          — internal handler: fetches data

EconomyState fields (minimal):
  indicator: str
  country: str
  series: list[MacroPoint]
  is_loading: bool
  error: str | None
  stale_data: bool
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from reflex_openbb.data.errors import ProviderError
from reflex_openbb.data.types import MacroPoint

# ─── Shared fixtures ────────────────────────────────────────────────────────


def _make_points(indicator: str = "GDP", country: str = "US") -> list[MacroPoint]:
    """Build a minimal valid MacroPoint list for mocking."""
    return [
        MacroPoint(
            year=2020,
            value=Decimal("21.0"),
            country=country,
            indicator=indicator,
        ),
        MacroPoint(
            year=2021,
            value=Decimal("23.0"),
            country=country,
            indicator=indicator,
        ),
    ]


@pytest.fixture
def mock_data_layer():
    """Patch the only data function (get_economy_indicator)."""
    series_mock = AsyncMock(return_value=_make_points())

    with patch(
        "reflex_openbb.state.economy_state.get_economy_indicator",
        new=series_mock,
    ):
        yield {"series": series_mock}


@pytest.fixture(autouse=True)
def _clear_data_cache():
    """Reset the data layer's TTL cache between tests."""
    from reflex_openbb.data import cache

    cache.clear()
    yield
    cache.clear()


# ─── Module / smoke tests ───────────────────────────────────────────────────


def test_economy_state_module_imports() -> None:
    """state.economy_state must export the EconomyState class."""
    from reflex_openbb.state import economy_state

    assert hasattr(economy_state, "EconomyState"), (
        "EconomyState class should live in state.economy_state"
    )


# ─── EconomyState fields ────────────────────────────────────────────────────


class TestEconomyStateFields:
    """REQ-007: EconomyState has the fields defined in the spec."""

    def test_default_indicator_is_gdp(self) -> None:
        """Per the spec, the default indicator is GDP."""
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        assert state.indicator == "GDP"

    def test_default_country_is_us(self) -> None:
        """Per the spec, the default country is US."""
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        assert state.country == "US"

    def test_initial_series_is_empty(self) -> None:
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        assert state.series == []

    def test_initial_is_loading_is_false(self) -> None:
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        assert state.is_loading is False

    def test_initial_error_is_none(self) -> None:
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        assert state.error is None

    def test_initial_stale_data_is_false(self) -> None:
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        assert state.stale_data is False


# ─── EconomyState event handlers ────────────────────────────────────────────


class TestEventHandlers:
    """REQ-007: set_indicator, set_country, load_indicator."""

    @pytest.mark.asyncio
    async def test_set_indicator_loads_series(self, mock_data_layer) -> None:
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        custom_points = _make_points("CPI")
        mock_data_layer["series"].return_value = custom_points

        await state.set_indicator("CPI")

        assert state.series == custom_points
        assert state.indicator == "CPI"

    @pytest.mark.asyncio
    async def test_set_country_loads_series(self, mock_data_layer) -> None:
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        custom_points = _make_points(country="DE")
        mock_data_layer["series"].return_value = custom_points

        await state.set_country("DE")

        assert state.series == custom_points
        assert state.country == "DE"

    @pytest.mark.asyncio
    async def test_set_indicator_normalizes_to_uppercase(self, mock_data_layer) -> None:
        """Lowercase input is normalized to uppercase."""
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        await state.set_indicator("gdp")

        assert state.indicator == "GDP"

    @pytest.mark.asyncio
    async def test_set_country_normalizes_to_uppercase(self, mock_data_layer) -> None:
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        await state.set_country("de")

        assert state.country == "DE"

    @pytest.mark.asyncio
    async def test_set_indicator_rejects_invalid_indicator(self, mock_data_layer) -> None:
        """Validation: only GDP, CPI, UNRATE are allowed."""
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        with pytest.raises(ValueError):
            await state.set_indicator("INVALID")

    @pytest.mark.asyncio
    async def test_set_country_rejects_invalid_country(self, mock_data_layer) -> None:
        """Validation: country must be 2-letter ISO-3166."""
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        with pytest.raises(ValueError):
            await state.set_country("USA")  # 3 letters

    @pytest.mark.asyncio
    async def test_set_indicator_sets_stale_data_on_provider_error(self, mock_data_layer) -> None:
        """REQ-007 (UW): on provider error, stale_data=True."""
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        mock_data_layer["series"].side_effect = ProviderError("fred", 500, None, "boom")

        await state.set_indicator("CPI")

        assert state.stale_data is True
        assert "boom" in (state.error or "")

    @pytest.mark.asyncio
    async def test_set_indicator_resets_loading_flag(self, mock_data_layer) -> None:
        """REQ: while loading, is_loading=True; after, is_loading=False."""
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        captured: dict = {}

        async def fake_series(*args, **kwargs):
            captured["loading_during"] = state.is_loading
            return _make_points()

        mock_data_layer["series"].side_effect = fake_series

        await state.set_indicator("GDP")

        assert captured["loading_during"] is True
        assert state.is_loading is False


# ─── EconomyState computed var ──────────────────────────────────────────────


class TestChartData:
    """REQ-007: chart_data is a list[dict] from series for the chart."""

    def test_chart_data_is_empty_when_no_series(self) -> None:
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        assert state.chart_data == []

    def test_chart_data_converts_points_to_dicts(self) -> None:
        from reflex_openbb.state.economy_state import EconomyState

        state = EconomyState()
        state.series = [
            MacroPoint(
                year=2024,
                value=Decimal("27.4"),
                country="US",
                indicator="GDP",
            )
        ]

        data = state.chart_data

        assert len(data) == 1
        assert data[0]["year"] == 2024
        # model_dump(mode="json") serializes Decimal to string for the chart
        assert data[0]["value"] == "27.4"
        assert data[0]["indicator"] == "GDP"
        assert data[0]["country"] == "US"
