"""
Tests for the crypto_chart component (T-401).

TDD: this file is written BEFORE components/crypto_chart.py.
The tests must FAIL initially, then pass after implementation.

REQ: REQ-006

crypto_chart(bars) — returns a rx.Component using rx.recharts.LineChart.
Lighter version of price_chart (no comparison overlay for crypto).
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.components.crypto_chart import crypto_chart


def _bars() -> list[dict]:
    return [
        {"date": "2024-01-15", "close": "30000.00"},
        {"date": "2024-01-16", "close": "30500.00"},
        {"date": "2024-01-17", "close": "30250.00"},
    ]


def test_crypto_chart_module_imports() -> None:
    from reflex_openbb.components import crypto_chart as m

    assert hasattr(m, "crypto_chart"), (
        "crypto_chart function should live in components.crypto_chart"
    )


def test_crypto_chart_returns_component_with_data() -> None:
    result = crypto_chart(_bars())
    assert isinstance(result, rx.Component)


def test_crypto_chart_returns_component_when_empty() -> None:
    """REQ-006 O-where: placeholder if no data."""
    result = crypto_chart([])
    assert isinstance(result, rx.Component)


def test_crypto_chart_includes_bars_in_output() -> None:
    result = crypto_chart(_bars())
    rendered = str(result)
    for bar in _bars():
        assert bar["date"] in rendered
