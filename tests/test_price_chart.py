"""
Tests for the price_chart component (T-301).

TDD: this file is written BEFORE components/price_chart.py.
The tests must FAIL initially, then pass after implementation.

REQ: REQ-001, REQ-002

price_chart(bars, comparison) — returns a rx.Component using
rx.recharts.LineChart. Renders the main series (ticker) and optional
comparison series (REQ-009 — future; for now comparison is empty).

The component:
- Takes a list[dict] (already serialized) and a comparison list[dict]
- Returns a LineChart with x=date, y=close
- Shows a placeholder if bars is empty
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.components.price_chart import price_chart


def _bars() -> list[dict]:
    """Sample price bars for testing."""
    return [
        {"date": "2024-01-15", "close": "150.00"},
        {"date": "2024-01-16", "close": "152.00"},
        {"date": "2024-01-17", "close": "151.00"},
    ]


class TestPriceChartExists:
    """The component must be importable."""

    def test_price_chart_is_callable(self) -> None:
        assert callable(price_chart)


class TestPriceChartReturnsComponent:
    """price_chart must return a rx.Component instance."""

    def test_price_chart_returns_rx_component(self) -> None:
        result = price_chart(_bars(), comparison=[])
        assert isinstance(result, rx.Component), (
            f"price_chart must return rx.Component, got {type(result)}"
        )

    def test_price_chart_returns_component_when_empty(self) -> None:
        """Empty bars → still a Component (placeholder)."""
        result = price_chart([], comparison=[])
        assert isinstance(result, rx.Component)


class TestPriceChartData:
    """The chart's data attribute must contain the input bars."""

    def test_chart_includes_all_bars(self) -> None:
        bars = _bars()
        result = price_chart(bars, comparison=[])
        # The LineChart has a `data` prop that we can inspect
        assert hasattr(result, "data") or "data" in str(result)
        # At minimum, the result should encode the bar count
        rendered = str(result)
        assert "2024-01-15" in rendered
        assert "2024-01-16" in rendered
        assert "2024-01-17" in rendered

    def test_chart_includes_comparison_data(self) -> None:
        """REQ-009: comparison data shows up in the chart."""
        bars = _bars()
        comparison = [
            {"date": "2024-01-15", "close": "300.00"},
            {"date": "2024-01-16", "close": "305.00"},
        ]
        result = price_chart(bars, comparison=comparison)
        rendered = str(result)
        # The comparison data_key should be in the rendered output.
        # Note: actual data values are passed to recharts and serialized
        # at runtime; what we can check is the data_key="close_compare"
        # line in the rendered JSX.
        assert "close_compare" in rendered


class TestPriceChartEmptyState:
    """When no data, the chart shows a placeholder (REQ-001 O-where)."""

    def test_empty_bars_shows_placeholder(self) -> None:
        result = price_chart([], comparison=[])
        rendered = str(result)
        # Should mention "no data" or have a placeholder
        # (we don't constrain the exact wording, just that there's a message)
        assert (
            "no data" in rendered.lower()
            or "no chart" in rendered.lower()
            or "no price" in rendered.lower()
            or "select a" in rendered.lower()
            or "loading" in rendered.lower()
            or "placeholder" in rendered.lower()
        ), f"Empty chart should show a placeholder, got: {rendered[:200]}"
