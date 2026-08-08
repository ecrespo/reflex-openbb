"""price_chart component (T-301).

REQ: REQ-001, REQ-009

Renders a price LineChart with optional comparison overlay.
Accepts either a plain Python list (for unit tests) or a Reflex Var
list[dict] (for the page). Uses is_var detection to pick the right
API.
"""

from __future__ import annotations

import reflex as rx

__all__ = ["price_chart"]


def _is_var(obj) -> bool:
    """True if obj is a Reflex Var (not a plain Python value)."""
    return hasattr(obj, "_var_type") or hasattr(obj, "length")


def _empty_state() -> rx.Component:
    """Placeholder when no price data is available."""
    return rx.center(
        rx.vstack(
            rx.icon("line-chart", size=48, color="blue.500"),
            rx.text("No price data", color="gray.500", size="4"),
            rx.text(
                "Select a ticker to see the price chart",
                color="gray.400",
                size="2",
            ),
            spacing="2",
            align="center",
        ),
        height="400px",
        width="100%",
    )


def _chart(bars, comparison) -> rx.Component:
    """The actual line chart with optional comparison overlay.

    `comparison` may be a list (test) or a Var (production).
    """
    if _is_var(comparison):
        return rx.cond(
            comparison.length() > 0,
            rx.recharts.line_chart(
                rx.recharts.line(
                    data_key="close",
                    stroke="#3b82f6",
                    dot=False,
                    stroke_width=2,
                ),
                rx.recharts.line(
                    data_key="close_compare",
                    stroke="#f97316",
                    dot=False,
                    stroke_width=2,
                    stroke_dasharray="5 5",
                ),
                data=bars,
                height=400,
                margin={"top": 20, "right": 20, "left": 20, "bottom": 20},
            ),
            rx.recharts.line_chart(
                rx.recharts.line(
                    data_key="close",
                    stroke="#3b82f6",
                    dot=False,
                    stroke_width=2,
                ),
                data=bars,
                height=400,
                margin={"top": 20, "right": 20, "left": 20, "bottom": 20},
            ),
        )
    # Plain Python comparison
    if comparison:
        return rx.recharts.line_chart(
            rx.recharts.line(
                data_key="close",
                stroke="#3b82f6",
                dot=False,
                stroke_width=2,
            ),
            rx.recharts.line(
                data_key="close_compare",
                stroke="#f97316",
                dot=False,
                stroke_width=2,
                stroke_dasharray="5 5",
            ),
            data=bars,
            height=400,
            margin={"top": 20, "right": 20, "left": 20, "bottom": 20},
        )
    return rx.recharts.line_chart(
        rx.recharts.line(
            data_key="close",
            stroke="#3b82f6",
            dot=False,
            stroke_width=2,
        ),
        data=bars,
        height=400,
        margin={"top": 20, "right": 20, "left": 20, "bottom": 20},
    )


def price_chart(bars, comparison=None) -> rx.Component:
    """Render a price chart.

    Args:
        bars: list of price bars (dict, Pydantic, or Var).
        comparison: optional list of comparison bars (for REQ-009).
    """
    if comparison is None:
        comparison = []
    if _is_var(bars):
        return rx.cond(
            bars.length() > 0,
            _chart(bars, comparison),
            _empty_state(),
        )
    # Plain Python list (test path)
    if not bars:
        return _empty_state()
    return _chart(bars, comparison)
