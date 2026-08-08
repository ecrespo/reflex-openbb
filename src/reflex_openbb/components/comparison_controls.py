"""comparison_controls component (T-506).

REQ: REQ-009

Provides a ticker input + Add button to add a ticker to the comparison
overlay. The state enforces a max of 5 (REQ-009 UW).
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.state.equity_state import EquityState

__all__ = ["comparison_controls"]


def _added_chips() -> rx.Component:
    """Render the chips for the tickers currently in the comparison overlay."""
    return rx.hstack(
        rx.foreach(
            EquityState.comparison_tickers,
            lambda t: rx.badge(
                t,
                rx.icon("x", size=12, margin_left="1"),
                variant="soft",
                color_scheme="blue",
                cursor="pointer",
                on_click=lambda t=t: EquityState.remove_from_comparison(t),
            ),
        ),
        spacing="2",
        wrap="wrap",
    )


def comparison_controls() -> rx.Component:
    """Render the comparison overlay controls.

    The user types a ticker and clicks Add to overlay it on the chart.
    Max 5 tickers (REQ-009 UW).
    """
    return rx.vstack(
        rx.form(
            rx.hstack(
                rx.input(
                    name="ticker",
                    placeholder="MSFT, GOOG, NVDA…",
                    size="2",
                    width="200px",
                ),
                rx.button(
                    rx.icon("plus", size=18),
                    "Add to comparison",
                    type="submit",
                    size="2",
                ),
                spacing="2",
            ),
            on_submit=EquityState.add_to_comparison,
            reset_on_submit=True,
        ),
        _added_chips(),
        spacing="3",
        width="100%",
    )
