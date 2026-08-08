"""crypto page (T-402).

REQ: REQ-006

Composes the crypto chart with CryptoState. Layout:
  1. Symbol input (BTC, ETH, BTC-USD)
  2. Date range buttons
  3. Crypto chart
  4. Stale-data banner (if state.stale_data)
  5. Loading spinner
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.components.crypto_chart import crypto_chart
from reflex_openbb.components.date_range import date_range
from reflex_openbb.components.export_button import export_button
from reflex_openbb.state.crypto_state import CryptoState

__all__ = ["crypto_page"]


def _symbol_input() -> rx.Component:
    """Symbol input form that calls CryptoState.set_symbol."""
    return rx.form(
        rx.hstack(
            rx.input(
                name="symbol",
                placeholder="BTC, ETH, BTC-USD…",
                default_value=CryptoState.symbol,
                size="2",
            ),
            rx.button("Go", type="submit", size="2"),
            spacing="2",
        ),
        on_submit=lambda form_data: CryptoState.set_symbol(form_data.get("symbol", "BTC")),
        reset_on_submit=False,
    )


def _stale_banner() -> rx.Component:
    """Show a warning banner when state.stale_data is True."""
    return rx.cond(
        CryptoState.stale_data,
        rx.callout(
            rx.vstack(
                rx.text("Showing stale data — provider request failed."),
                rx.text(CryptoState.error),
            ),
            icon="alert-triangle",
            color="amber",
            width="100%",
        ),
    )


def _loading_indicator() -> rx.Component:
    """Spinner shown while loading."""
    return rx.cond(
        CryptoState.is_loading,
        rx.spinner(size="3"),
    )


def crypto_page() -> rx.Component:
    """The /crypto page (T-402)."""
    return rx.container(
        rx.vstack(
            rx.hstack(
                rx.heading(f"{CryptoState.symbol} — Crypto", size="7"),
                rx.spacer(),
                export_button(CryptoState),
                align="center",
                width="100%",
            ),
            _stale_banner(),
            _symbol_input(),
            date_range(CryptoState),
            _loading_indicator(),
            crypto_chart(CryptoState.price_chart_data),
            spacing="4",
            width="100%",
            padding_y="4",
        ),
        size="4",
    )
