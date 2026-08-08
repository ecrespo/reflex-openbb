"""economy_chart component (T-405).

REQ: REQ-007

Renders a BarChart of macro points. x=year, y=value.

If series is empty, shows a placeholder (REQ-007 O-where: the
system shall display a placeholder if no data is available).
"""

from __future__ import annotations

import reflex as rx

__all__ = ["economy_chart"]


def _empty_state() -> rx.Component:
    """Placeholder when no series is available."""
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


def economy_chart(series: list[dict]) -> rx.Component:
    """Render a bar chart of macro points.

    Args:
        series: list of MacroPoint as dicts (from state.chart_data).
            Each dict has keys: year, value, indicator, country.

    Returns:
        A rx.Component (BarChart or placeholder).
    """
    if not series:
        return _empty_state()
    return rx.recharts.bar_chart(
        rx.recharts.bar(
            data_key="value",
            fill="#8b5cf6",  # purple
        ),
        rx.recharts.x_axis(data_key="year"),
        rx.recharts.y_axis(),
        data=series,
        height=400,
        margin={"top": 20, "right": 20, "left": 20, "bottom": 20},
    )
