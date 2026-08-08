"""fundamentals_table component (T-304).

REQ: REQ-003

Renders a fundamentals table for an EquityFundamentals object.
"n/a" for None values (REQ-003: gracefully handle missing data).
"""

from __future__ import annotations

import reflex as rx

__all__ = ["fundamentals_table"]


def _row(label: str, value) -> rx.Component:
    """One row of the fundamentals table."""
    display = str(value) if value is not None else "n/a"
    return rx.table.row(
        rx.table.cell(rx.text(label, weight="medium", color="gray.600")),
        rx.table.cell(rx.text(display, font_family="mono")),
    )


def _table(fundamentals) -> rx.Component:
    """The actual table."""
    return rx.table.root(
        rx.table.body(
            _row("P/E ratio", fundamentals.pe_ratio),
            _row("EPS", fundamentals.eps),
            _row("Dividend yield", fundamentals.dividend_yield),
            _row("Beta", fundamentals.beta),
            _row("Book value / share", fundamentals.book_value_per_share),
            _row("Price / book", fundamentals.price_to_book),
            _row("ROE", fundamentals.roe),
        ),
        size="2",
        width="100%",
    )


def _empty_state() -> rx.Component:
    return rx.center(
        rx.text("No fundamentals data", color="gray.500", size="3"),
        padding="4",
    )


def fundamentals_table(fundamentals) -> rx.Component:
    """Render a fundamentals table.

    Args:
        fundamentals: an EquityFundamentals object. None for placeholder.
    """
    if fundamentals is None:
        return _empty_state()
    return _table(fundamentals)
