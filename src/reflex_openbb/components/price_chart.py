"""price_chart component (T-301).

REQ: REQ-001, REQ-002

Renders an equity/crypto price chart using rx.recharts.LineChart.

The component takes a list[dict] (the chart-ready output of
state.price_chart_data) and an optional list[dict] for comparison
(REQ-009 — multi-ticker overlay).

If bars is empty, shows a placeholder (REQ-001 O-where: "the system
shall display a placeholder chart if no data is available").
"""

from __future__ import annotations

import reflex as rx

__all__ = ["price_chart"]


def _empty_state() -> rx.Component:
    """Placeholder when no price data is available."""
    return rx.center(
        rx.vstack(
            rx.icon("line-chart", size=48, color="gray.500"),
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


def _chart(bars: list[dict], comparison: list[dict]) -> rx.Component:
    """The actual line chart with the data.

    For the main series, we use the bars as-is. For comparison (REQ-009),
    we add a second <Line> with a different stroke style. Note: with the
    current recharts integration, the comparison data is encoded in the
    same `data` array — its values appear in the rendered output.
    """
    # When comparison is provided, include it in the data so recharts
    # has both series to render.
    chart_data = bars
    if comparison:
        # Merge: for each main bar, append the matching comparison close.
        # recharts requires the data to be a flat list of dicts.
        # We tag the main as `close` and comparison as `close_compare`.
        merged: list[dict] = []
        comp_by_date = {c["date"]: c["close"] for c in comparison}
        for b in bars:
            row = {**b}
            if b["date"] in comp_by_date:
                row["close_compare"] = comp_by_date[b["date"]]
            merged.append(row)
        chart_data = merged

    children: list[rx.Component] = [
        rx.recharts.line(
            data_key="close",
            stroke="#3b82f6",  # blue
            dot=False,
            stroke_width=2,
        )
    ]
    if comparison:
        children.append(
            rx.recharts.line(
                data_key="close_compare",
                stroke="#ef4444",  # red
                dot=False,
                stroke_width=2,
                stroke_dasharray="5 5",
            )
        )

    return rx.recharts.line_chart(
        *children,
        data=chart_data,
        height=400,
        margin={"top": 20, "right": 20, "left": 20, "bottom": 20},
    )


def price_chart(bars: list[dict], comparison: list[dict] | None = None) -> rx.Component:
    """Render a price chart with optional comparison overlay.

    Args:
        bars: list of price bars as dicts (from state.price_chart_data).
            Each dict has keys: date, open, high, low, close, volume.
        comparison: optional list of comparison series dicts (REQ-009).
            Each dict has the same shape as a `bars` entry.

    Returns:
        A rx.Component (LineChart or placeholder).
    """
    if not bars:
        return _empty_state()
    return _chart(bars, comparison or [])
