"""search_box component (T-501).

REQ: REQ-010

A global search bar that calls AppState.global_search(query) on submit.
The state navigates to the appropriate page (/equity, /crypto) or shows
a "not found" message.
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.state.app_state import AppState

__all__ = ["search_box"]


def search_box() -> rx.Component:
    """Render a search input that calls AppState.global_search.

    Returns:
        A rx.Component (form with input + button).
    """
    # Use rx.input's value binding via a local var. Reflex forms pass
    # the form values as a dict-like var. We use [] indexing (not .get)
    # because reflex form_data is an UntypedVar and .get() is unsupported.
    return rx.form(
        rx.hstack(
            rx.input(
                name="query",
                placeholder="Search AAPL, BTC, MSFT…",
                size="2",
                width="300px",
            ),
            rx.button(
                rx.icon("search", size=18),
                type="submit",
                size="2",
            ),
            spacing="2",
        ),
        on_submit=AppState.global_search,
        reset_on_submit=True,
    )
