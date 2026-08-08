"""date_range component (T-302).

REQ: REQ-002

Renders a row of 5 period buttons: 1M, 6M, 1Y, 5Y, Max.
Each button calls state.set_period(period) when clicked.
The current period is highlighted (variant=solid).
"""

from __future__ import annotations

import reflex as rx

__all__ = ["date_range"]


#: Period definitions: (label, value).
#: Value matches the EquityState.period Literal type.
_PERIODS: list[tuple[str, str]] = [
    ("1M", "1mo"),
    ("6M", "6mo"),
    ("1Y", "1y"),
    ("5Y", "5y"),
    ("Max", "max"),
]


def _period_button(label: str, value: str, state) -> rx.Component:
    """A single period button.

    Uses rx.cond for the variant comparison. The on_click is a lambda
    that calls state.set_period(value) — we cannot pass the handler
    directly because on_click passes a PointerEventInfo, not a string.
    """
    return rx.button(
        label,
        on_click=lambda v=value: state.set_period(v),
        variant=rx.cond(state.period == value, "solid", "outline"),
        size="2",
    )


def date_range(state) -> rx.Component:
    """Render a row of 5 period buttons.

    Args:
        state: A Reflex state with a `period` field and a
            `set_period(period: str)` async handler.
            Both EquityState and CryptoState satisfy this.

    Returns:
        A rx.Component containing the 5 buttons.
    """
    return rx.hstack(
        *[_period_button(label, value, state) for label, value in _PERIODS],
        spacing="2",
        wrap="wrap",
    )
