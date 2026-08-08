"""economy_selector component (T-406).

REQ: REQ-007

Provides dropdowns / inputs for indicator (GDP, CPI, UNRATE) and
country (US, DE, etc.). Each one calls the corresponding state handler
on change.
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.state.economy_state import EconomyState

__all__ = ["economy_selector"]


#: Indicator definitions: (label, value).
_INDICATORS: list[tuple[str, str]] = [
    ("GDP", "GDP"),
    ("CPI", "CPI"),
    ("Unemployment rate", "UNRATE"),
]

#: Country definitions: (label, value).
_COUNTRIES: list[tuple[str, str]] = [
    ("United States", "US"),
    ("Germany", "DE"),
    ("Japan", "JP"),
    ("United Kingdom", "GB"),
    ("France", "FR"),
    ("Canada", "CA"),
]


def economy_selector() -> rx.Component:
    """Render indicator + country selectors.

    Returns:
        A rx.Component with two select inputs.
    """
    return rx.hstack(
        rx.select.root(
            rx.select.trigger(placeholder=EconomyState.indicator),
            rx.select.content(
                *[rx.select.item(label, value=value) for label, value in _INDICATORS],
            ),
            value=EconomyState.indicator,
            on_change=EconomyState.set_indicator,
            size="2",
        ),
        rx.select.root(
            rx.select.trigger(placeholder=EconomyState.country),
            rx.select.content(
                *[rx.select.item(label, value=value) for label, value in _COUNTRIES],
            ),
            value=EconomyState.country,
            on_change=EconomyState.set_country,
            size="2",
        ),
        spacing="3",
    )
