"""The home page of reflex-openbb.

This is the T-005 stub: a single page that shows the project name and version.
The real home page (with search, recent tickers, etc.) is part of Phase 3 / T-310.
"""

import reflex as rx

from reflex_openbb import __version__


def index() -> rx.Component:
    """The root page of the app.

    Returns a simple centered container with the project name and version.
    This is the minimum needed to satisfy the T-005 acceptance criterion:
    "a single page that prints 'reflex-openbb v0.1.0'".
    """
    return rx.center(
        rx.vstack(
            rx.heading("reflex-openbb", size="5"),
            rx.text(f"v{__version__}", color="gray"),
            spacing="2",
        ),
        height="100vh",
    )
