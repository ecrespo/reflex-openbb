"""The home page of reflex-openbb.

T-005 + T-502: home with the global search box and a not-found message
when the last search has no match.
"""

import reflex as rx

from reflex_openbb import __version__
from reflex_openbb.components.search_box import search_box
from reflex_openbb.state.app_state import AppState


def _not_found_callout() -> rx.Component:
    """Show a not-found message when the last search yielded no result.

    We use a simple boolean expression: equity_match OR crypto_match
    set means "found"; both empty means "not found".
    """
    return rx.cond(
        AppState.last_search,
        rx.cond(
            AppState.last_search.equity_match,
            rx.fragment(),
            rx.cond(
                AppState.last_search.crypto_match,
                rx.fragment(),
                rx.callout(
                    rx.text(f"No match for {AppState.last_search.query}"),
                    icon="search-x",
                    color="orange",
                    width="400px",
                ),
            ),
        ),
    )


def index() -> rx.Component:
    """The root page of the app.

    Returns a centered container with the project name, version, and
    the global search box. Below the search box, shows a not-found
    message if the last search had no match.
    """
    return rx.center(
        rx.vstack(
            rx.heading("reflex-openbb", size="5"),
            rx.text(f"v{__version__}", color="gray"),
            rx.spacer(),
            search_box(),
            _not_found_callout(),
            spacing="4",
            align="center",
        ),
        height="100vh",
    )
