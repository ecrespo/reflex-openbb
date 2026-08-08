"""equity page (T-306).

REQ: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005

Composes all 5 equity-page components with the EquityState.

Layout (top to bottom):
  1. Ticker input + period buttons
  2. KPI grid (6 cards)
  3. Price chart with comparison overlay slot
  4. Fundamentals table
  5. News feed
  6. Stale-data banner (if state.stale_data)
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.components.date_range import date_range
from reflex_openbb.components.fundamentals_table import fundamentals_table
from reflex_openbb.components.kpi_grid import kpi_grid
from reflex_openbb.components.news_feed import news_feed
from reflex_openbb.components.price_chart import price_chart
from reflex_openbb.state.equity_state import EquityState

__all__ = ["equity_page"]


def _ticker_input() -> rx.Component:
    """Ticker input form that calls EquityState.set_ticker."""
    return rx.form(
        rx.hstack(
            rx.input(
                name="ticker",
                placeholder="AAPL, MSFT, GOOG…",
                default_value=EquityState.ticker,
                size="2",
            ),
            rx.button("Go", type="submit", size="2"),
            spacing="2",
        ),
        on_submit=lambda form_data: EquityState.set_ticker(form_data.get("ticker", "AAPL")),
        reset_on_submit=False,
    )


def _stale_banner() -> rx.Component:
    """Show a warning banner when state.stale_data is True."""
    return rx.cond(
        EquityState.stale_data,
        rx.callout(
            rx.vstack(
                rx.text("Showing stale data — provider request failed."),
                rx.text(EquityState.error),
            ),
            icon="alert-triangle",
            color="amber",
            width="100%",
        ),
    )


def _loading_indicator() -> rx.Component:
    """Spinner shown while loading."""
    return rx.cond(
        EquityState.is_loading,
        rx.spinner(size="3"),
    )


def equity_page() -> rx.Component:
    """The /equity/{ticker} page.

    Composes the 5 components with EquityState. Reactive — when state
    fields change, the components re-render.
    """
    return rx.container(
        rx.vstack(
            rx.heading(f"{EquityState.ticker} — Equity", size="7"),
            _stale_banner(),
            _ticker_input(),
            date_range(EquityState),
            _loading_indicator(),
            kpi_grid(EquityState.quote),
            price_chart(EquityState.price_chart_data, comparison=[]),
            rx.grid(
                rx.box(fundamentals_table(EquityState.fundamentals)),
                rx.box(news_feed(EquityState.news)),
                columns="2",
                spacing="4",
                width="100%",
            ),
            spacing="4",
            width="100%",
            padding_y="4",
        ),
        size="4",
    )
