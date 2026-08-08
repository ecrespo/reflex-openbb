"""
Tests for the economy_chart component (T-405).

REQ: REQ-007

economy_chart(series) — renders a BarChart of the macro points.
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.components.economy_chart import economy_chart


def _series() -> list[dict]:
    return [
        {"year": 2020, "value": "21.0", "indicator": "GDP", "country": "US"},
        {"year": 2021, "value": "23.0", "indicator": "GDP", "country": "US"},
    ]


def test_economy_chart_module_imports() -> None:
    from reflex_openbb.components import economy_chart as m

    assert hasattr(m, "economy_chart"), (
        "economy_chart function should live in components.economy_chart"
    )


def test_economy_chart_returns_component_with_data() -> None:
    result = economy_chart(_series())
    assert isinstance(result, rx.Component)


def test_economy_chart_returns_component_when_empty() -> None:
    """REQ-007 O-where: placeholder if no data."""
    result = economy_chart([])
    assert isinstance(result, rx.Component)
