"""kpi_grid component (T-303).

REQ: REQ-005

Renders a 6-card grid of KPIs for an EquityQuote (or any object
with the relevant fields):
  1. Price
  2. Day change %
  3. Market cap
  4. Volume
  5. 52-week high
  6. 52-week low

If quote is None, shows a placeholder (REQ-005 O-where: the system
shall display a placeholder if no data is available).
"""

from __future__ import annotations

import reflex as rx

__all__ = ["kpi_grid"]


def _format_market_cap(mc) -> str:
    """Format a market cap as a human-readable string (B / T)."""
    if mc is None:
        return "n/a"
    # mc is a Decimal or int (compatible with both)
    value = float(mc)
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.0f}"


def _format_volume(v) -> str:
    """Format a volume number as a human-readable string (K / M / B)."""
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


def _kpi_card(label: str, value: str, *, accent: str = "blue") -> rx.Component:
    """Render a single KPI card."""
    return rx.card(
        rx.vstack(
            rx.text(label, size="1", color="gray.500"),
            rx.heading(value, size="6", color=f"{accent}.9"),
            align="start",
            spacing="1",
        ),
        size="2",
    )


def _cards(quote) -> rx.Component:
    """Render the 6 KPI cards."""
    return rx.grid(
        _kpi_card("Price", f"${quote.price}"),
        _kpi_card(
            "Day change",
            f"{quote.day_change_pct}%",
            accent="green" if float(quote.day_change_pct) >= 0 else "red",
        ),
        _kpi_card("Market cap", _format_market_cap(quote.market_cap)),
        _kpi_card("Volume", _format_volume(quote.volume)),
        _kpi_card("52-wk high", f"${quote.fifty_two_week_high}"),
        _kpi_card("52-wk low", f"${quote.fifty_two_week_low}"),
        columns="3",
        spacing="3",
        width="100%",
    )


def _empty_state() -> rx.Component:
    """Placeholder when no quote is available."""
    return rx.center(
        rx.text(
            "No data — select a ticker to see the KPIs",
            color="gray.500",
            size="3",
        ),
        width="100%",
        padding="4",
    )


def kpi_grid(quote) -> rx.Component:
    """Render a 6-card KPI grid for a quote.

    Args:
        quote: an object with attributes: price, day_change_pct,
            market_cap, volume, fifty_two_week_high, fifty_two_week_low.
            Both EquityQuote and CryptoQuote satisfy this.

    Returns:
        A rx.Component (grid of 6 cards or placeholder).
    """
    if quote is None:
        return _empty_state()
    return _cards(quote)
