"""fundamentals_table component (T-304).

REQ: REQ-003

Renders a fundamentals table for an EquityFundamentals object.
"n/a" for None values (REQ-003: gracefully handle missing data).

Two calling patterns are supported:
1. **Pre-extracted values (preferred)**: the page passes individual
   fields as strings. Used in production (with rx.State computed vars).
2. **Whole object (legacy / test)**: tests pass a Pydantic model
   and we extract the values ourselves.
"""

from __future__ import annotations

import reflex as rx

__all__ = ["fundamentals_table"]


def _row(label: str, value) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(label, weight="medium", color="gray.600")),
        rx.table.cell(rx.text(value)),
    )


def _table(pe_ratio, eps, dividend_yield, beta, book_value_per_share,
           price_to_book, roe) -> rx.Component:
    return rx.table.root(
        rx.table.body(
            _row("P/E ratio", pe_ratio),
            _row("EPS", eps),
            _row("Dividend yield", dividend_yield),
            _row("Beta", beta),
            _row("Book value / share", book_value_per_share),
            _row("Price / book", price_to_book),
            _row("ROE", roe),
        ),
        size="2",
        width="100%",
    )


def _empty_state() -> rx.Component:
    return rx.center(
        rx.text("No fundamentals data", color="gray.500", size="3"),
        padding="4",
    )


def _fmt(value) -> str:
    """Format a Decimal/None as a string."""
    return "n/a" if value is None else str(value)


def _from_obj(f) -> tuple:
    """Extract field values from an EquityFundamentals Pydantic model."""
    return (
        _fmt(f.pe_ratio),
        _fmt(f.eps),
        _fmt(f.dividend_yield),
        _fmt(f.beta),
        _fmt(f.book_value_per_share),
        _fmt(f.price_to_book),
        _fmt(f.roe),
    )


def fundamentals_table(
    fundamentals=None,
    pe_ratio: str = "n/a",
    eps: str = "n/a",
    dividend_yield: str = "n/a",
    beta: str = "n/a",
    book_value_per_share: str = "n/a",
    price_to_book: str = "n/a",
    roe: str = "n/a",
    has_data: bool = False,
) -> rx.Component:
    """Render a fundamentals table.

    Args:
        fundamentals: optional Pydantic model. If passed, its fields
            override the individual pe_ratio/eps/etc. (used in tests).
        pe_ratio, eps, ...: pre-formatted display strings (production).
        has_data: True to show the table, False for placeholder. May
            be a Var (in which case we use rx.cond).
    """
    if fundamentals is not None:
        pe_ratio, eps, dividend_yield, beta, book_value_per_share, price_to_book, roe = _from_obj(fundamentals)
        has_data = True
    if hasattr(has_data, "_var_type") or hasattr(has_data, "length"):
        return rx.cond(
            has_data,
            _table(pe_ratio, eps, dividend_yield, beta, book_value_per_share, price_to_book, roe),
            _empty_state(),
        )
    if not has_data:
        return _empty_state()
    return _table(pe_ratio, eps, dividend_yield, beta, book_value_per_share, price_to_book, roe)
