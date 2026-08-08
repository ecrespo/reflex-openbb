"""
Tests for the economy_selector component (T-406).

REQ: REQ-007

economy_selector(state) — provides dropdowns / inputs for
indicator (GDP, CPI, UNRATE) and country (US, DE, etc.).
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.components.economy_selector import economy_selector


def test_economy_selector_module_imports() -> None:
    from reflex_openbb.components import economy_selector as m

    assert hasattr(m, "economy_selector"), (
        "economy_selector function should live in components.economy_selector"
    )


def test_economy_selector_returns_component() -> None:
    result = economy_selector()
    assert isinstance(result, rx.Component)


def test_economy_selector_includes_all_indicators() -> None:
    """REQ-007: the selector must offer GDP, CPI, UNRATE."""
    result = economy_selector()
    rendered = str(result)
    for indicator in ("GDP", "CPI", "UNRATE"):
        assert indicator in rendered, f"Missing indicator: {indicator}"
