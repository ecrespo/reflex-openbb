"""economy_chart component (T-405).

REQ: REQ-007
"""

from __future__ import annotations

import reflex as rx

__all__ = ["economy_chart"]


def _is_var(obj) -> bool:
    return hasattr(obj, "_var_type") or hasattr(obj, "length")


def _empty_state() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon("bar-chart-2", size=48, color="purple.500"),
            rx.text("No data", color="gray.500", size="4"),
            rx.text(
                "Select an indicator and country to see the chart",
                color="gray.400",
                size="2",
            ),
            spacing="2",
            align="center",
        ),
        height="400px",
        width="100%",
    )


def economy_chart(series) -> rx.Component:
    """Render a bar chart of macro points.

    Args:
        series: list of MacroPoint dicts (or Var).
    """
    if _is_var(series):
        return rx.cond(
            series.length() > 0,
            rx.recharts.bar_chart(
                rx.recharts.bar(
                    data_key="value",
                    fill="#8b5cf6",
                ),
                rx.recharts.x_axis(data_key="year"),
                rx.recharts.y_axis(),
                data=series,
                height=400,
                margin={"top": 20, "right": 20, "left": 20, "bottom": 20},
            ),
            _empty_state(),
        )
    if not series:
        return _empty_state()
    return rx.recharts.bar_chart(
        rx.recharts.bar(
            data_key="value",
            fill="#8b5cf6",
        ),
        rx.recharts.x_axis(data_key="year"),
        rx.recharts.y_axis(),
        data=series,
        height=400,
        margin={"top": 20, "right": 20, "left": 20, "bottom": 20},
    )
