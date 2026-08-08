"""economy page (T-407).

REQ: REQ-007

Composes the economy selector + chart with EconomyState. Layout:
  1. Indicator + country selectors
  2. Economy chart (BarChart)
  3. Stale-data banner
  4. Loading spinner
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.components.economy_chart import economy_chart
from reflex_openbb.components.economy_selector import economy_selector
from reflex_openbb.state.economy_state import EconomyState

__all__ = ["economy_page"]


def _stale_banner() -> rx.Component:
    """Show a warning banner when state.stale_data is True."""
    return rx.cond(
        EconomyState.stale_data,
        rx.callout(
            rx.vstack(
                rx.text("Showing stale data — provider request failed."),
                rx.text(EconomyState.error),
            ),
            icon="alert-triangle",
            color="amber",
            width="100%",
        ),
    )


def _loading_indicator() -> rx.Component:
    return rx.cond(
        EconomyState.is_loading,
        rx.spinner(size="3"),
    )


def economy_page() -> rx.Component:
    """The /economy page (T-407)."""
    return rx.container(
        rx.vstack(
            rx.heading("Economy", size="7"),
            _stale_banner(),
            economy_selector(),
            _loading_indicator(),
            economy_chart(EconomyState.chart_data),
            spacing="4",
            width="100%",
            padding_y="4",
        ),
        size="4",
    )
