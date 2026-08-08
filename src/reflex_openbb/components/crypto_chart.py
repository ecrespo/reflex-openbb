"""crypto_chart component (T-401).

REQ: REQ-006
"""

from __future__ import annotations

import reflex as rx

__all__ = ["crypto_chart"]


def _is_var(obj) -> bool:
    return hasattr(obj, "_var_type") or hasattr(obj, "length")


def _empty_state() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon("line-chart", size=48, color="orange.500"),
            rx.text("No price data", color="gray.500", size="4"),
            rx.text(
                "Select a crypto to see the price chart",
                color="gray.400",
                size="2",
            ),
            spacing="2",
            align="center",
        ),
        height="400px",
        width="100%",
    )


def crypto_chart(bars) -> rx.Component:
    """Render a crypto price chart.

    Args:
        bars: list of price bars (dict, Pydantic, or Var).
    """
    if _is_var(bars):
        return rx.cond(
            bars.length() > 0,
            rx.recharts.line_chart(
                rx.recharts.line(
                    data_key="close",
                    stroke="#f59e0b",
                    dot=False,
                    stroke_width=2,
                ),
                data=bars,
                height=400,
                margin={"top": 20, "right": 20, "left": 20, "bottom": 20},
            ),
            _empty_state(),
        )
    if not bars:
        return _empty_state()
    return rx.recharts.line_chart(
        rx.recharts.line(
            data_key="close",
            stroke="#f59e0b",
            dot=False,
            stroke_width=2,
        ),
        data=bars,
        height=400,
        margin={"top": 20, "right": 20, "left": 20, "bottom": 20},
    )
