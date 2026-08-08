"""kpi_grid component (T-303).

REQ: REQ-005

Renders a 6-card grid of KPIs.

Two calling patterns:
1. **Production**: page passes pre-formatted strings (display vars
   from EquityState) + `has_data: bool`. Used in the page.
2. **Test**: page passes a Pydantic quote (EquityQuote or None) and
   we extract + format the values ourselves.
"""

from __future__ import annotations

import reflex as rx

__all__ = ["kpi_grid"]


def _format_market_cap(mc) -> str:
    if mc is None:
        return "n/a"
    value = float(mc)
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.0f}"


def _format_volume(v) -> str:
    if v is None:
        return "n/a"
    value = float(v)
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:,.0f}"


def _kpi_card(label: str, value) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(label, size="1", color="gray.500"),
            rx.heading(value, size="6"),
            align="start",
            spacing="1",
        ),
        size="2",
    )


def _cards(price, day_change_pct, market_cap, volume, high_52w, low_52w) -> rx.Component:
    return rx.grid(
        _kpi_card("Price", price),
        _kpi_card("Day change", f"{day_change_pct}%"),
        _kpi_card("Market cap", market_cap),
        _kpi_card("Volume", volume),
        _kpi_card("52-wk high", high_52w),
        _kpi_card("52-wk low", low_52w),
        columns="3",
        spacing="3",
        width="100%",
    )


def _empty_state() -> rx.Component:
    return rx.center(
        rx.text(
            "No data — select a ticker to see the KPIs",
            color="gray.500",
            size="3",
        ),
        width="100%",
        padding="4",
    )


def _from_quote(q) -> tuple:
    """Extract field values from an EquityQuote Pydantic model."""
    return (
        f"${q.price}",
        f"{q.day_change_pct}",
        _format_market_cap(q.market_cap),
        _format_volume(q.volume),
        f"${q.fifty_two_week_high}",
        f"${q.fifty_two_week_low}",
    )


def kpi_grid(
    quote=None,
    price: str = "n/a",
    day_change_pct: str = "n/a",
    market_cap: str = "n/a",
    volume: str = "n/a",
    high_52w: str = "n/a",
    low_52w: str = "n/a",
    has_data: bool = False,
) -> rx.Component:
    """Render a 6-card KPI grid.

    Args:
        quote: optional Pydantic quote (test path). If passed, its
            fields override the individual strings.
        price, day_change_pct, ...: pre-formatted display strings.
        has_data: True to show the grid, False for placeholder. May be
            a Var (in which case we use rx.cond).
    """
    if quote is not None:
        price, day_change_pct, market_cap, volume, high_52w, low_52w = _from_quote(quote)
        has_data = True
    # Detect Var: has_data is a Reflex Var when used in pages
    if hasattr(has_data, "_var_type") or hasattr(has_data, "length"):
        return rx.cond(
            has_data,
            _cards(price, day_change_pct, market_cap, volume, high_52w, low_52w),
            _empty_state(),
        )
    if not has_data:
        return _empty_state()
    return _cards(price, day_change_pct, market_cap, volume, high_52w, low_52w)
