"""crypto_chart component (T-401).

REQ: REQ-006

A lighter version of price_chart. Renders a LineChart for crypto
price bars (no comparison overlay — that was an equity-only feature
in T-301).

If bars is empty, shows a placeholder (REQ-006 O-where: the system
shall display a placeholder if no data is available).
"""

from __future__ import annotations

import reflex as rx

__all__ = ["crypto_chart"]


def _empty_state() -> rx.Component:
    """Placeholder when no price data is available."""
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


def crypto_chart(bars: list[dict]) -> rx.Component:
    """Render a crypto price chart.

    Args:
        bars: list of price bars as dicts (from state.price_chart_data).
            Each dict has keys: date, open, high, low, close, volume.

    Returns:
        A rx.Component (LineChart or placeholder).
    """
    if not bars:
        return _empty_state()
    return rx.recharts.line_chart(
        rx.recharts.line(
            data_key="close",
            stroke="#f59e0b",  # amber/orange — crypto color
            dot=False,
            stroke_width=2,
        ),
        data=bars,
        height=400,
        margin={"top": 20, "right": 20, "left": 20, "bottom": 20},
    )
