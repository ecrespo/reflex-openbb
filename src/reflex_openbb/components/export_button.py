"""export_button component (T-504).

REQ: REQ-008

A button that triggers a CSV download of the current chart's data.
The button calls the state's export_csv handler, which uses rx.download
to deliver the file to the user.
"""

from __future__ import annotations

import reflex as rx

__all__ = ["export_button"]


def export_button(state) -> rx.Component:
    """Render an "Export CSV" button.

    Args:
        state: A Reflex state with an `export_csv()` async handler.
            Both EquityState and CryptoState satisfy this in Phase 5+.
    """
    return rx.button(
        rx.icon("download", size=18),
        rx.text("Export CSV"),
        on_click=lambda: state.export_csv(),
        size="2",
        variant="outline",
    )
