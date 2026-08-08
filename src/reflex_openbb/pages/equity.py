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

from reflex_openbb.components.comparison_controls import comparison_controls
from reflex_openbb.components.date_range import date_range
from reflex_openbb.components.export_button import export_button
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
        on_submit=EquityState.set_ticker,
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
    """The /equity page (T-307).

    Composes the 5 components with EquityState. Reactive — when state
    fields change, the components re-render.
    """
    return rx.container(
        rx.vstack(
            rx.hstack(
                rx.heading(f"{EquityState.ticker} — Equity", size="7"),
                rx.spacer(),
                export_button(EquityState),
                align="center",
                width="100%",
            ),
            _stale_banner(),
            _ticker_input(),
            date_range(EquityState),
            comparison_controls(),
            _loading_indicator(),
            kpi_grid(
                price=EquityState.price_display,
                day_change_pct=EquityState.day_change_pct_display,
                market_cap=EquityState.market_cap_display,
                volume=EquityState.volume_display,
                high_52w=EquityState.high_52w_display,
                low_52w=EquityState.low_52w_display,
                has_data=EquityState.has_quote,
            ),
            price_chart(
                EquityState.price_chart_data,
                comparison=EquityState.comparison_chart_data,
            ),
            rx.grid(
                rx.box(
                    fundamentals_table(
                        pe_ratio=EquityState.fund_pe_ratio_display,
                        eps=EquityState.fund_eps_display,
                        dividend_yield=EquityState.fund_dividend_yield_display,
                        beta=EquityState.fund_beta_display,
                        book_value_per_share=EquityState.fund_book_value_display,
                        price_to_book=EquityState.fund_price_to_book_display,
                        roe=EquityState.fund_roe_display,
                        has_data=EquityState.has_fundamentals,
                    ),
                ),
                rx.box(
                    news_feed(
                        EquityState.news_display,
                        has_data=EquityState.has_news,
                    ),
                ),
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
