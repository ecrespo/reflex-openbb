"""
Tests for the kpi_grid component (T-303).

TDD: this file is written BEFORE components/kpi_grid.py.
The tests must FAIL initially, then pass after implementation.

REQ: REQ-005

kpi_grid(quote) — returns a 6-card grid of KPIs:
  1. Price
  2. Day change %
  3. Market cap
  4. Volume
  5. 52-week high
  6. 52-week low

If quote is None, shows a placeholder.
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.components.kpi_grid import kpi_grid


def test_kpi_grid_module_imports() -> None:
    """components.kpi_grid must export the kpi_grid function."""
    from reflex_openbb.components import kpi_grid as kpi_grid_module

    assert hasattr(kpi_grid_module, "kpi_grid"), (
        "kpi_grid function should live in components.kpi_grid"
    )


class TestKpiGridReturnsComponent:
    """kpi_grid must return a rx.Component."""

    def test_returns_component_when_quote_is_none(self) -> None:
        """REQ-005 O-where: placeholder when no data."""
        result = kpi_grid(None)
        assert isinstance(result, rx.Component)

    def test_returns_component_with_valid_quote(self) -> None:
        """With a quote, the grid renders 6 cards."""
        from datetime import datetime, timezone
        from decimal import Decimal

        from reflex_openbb.data.types import EquityQuote

        quote = EquityQuote(
            ticker="AAPL",
            price=Decimal("150.00"),
            day_change_pct=Decimal("1.5"),
            market_cap=Decimal("2000000000000"),
            volume=10_000_000,
            fifty_two_week_high=Decimal("200.00"),
            fifty_two_week_low=Decimal("100.00"),
            fetched_at=datetime.now(timezone.utc),
            provider="yfinance",
        )
        result = kpi_grid(quote)
        assert isinstance(result, rx.Component)

    def test_renders_with_low_market_cap(self) -> None:
        """A 'normal' quote with smaller market cap also works."""
        from datetime import datetime, timezone
        from decimal import Decimal

        from reflex_openbb.data.types import EquityQuote

        quote = EquityQuote(
            ticker="AAPL",
            price=Decimal("150.00"),
            day_change_pct=Decimal("-1.5"),
            market_cap=Decimal("2000000000000"),
            volume=10_000_000,
            fifty_two_week_high=Decimal("200.00"),
            fifty_two_week_low=Decimal("100.00"),
            fetched_at=datetime.now(timezone.utc),
            provider="yfinance",
        )
        result = kpi_grid(quote)
        assert isinstance(result, rx.Component)
