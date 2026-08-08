"""
Tests for the economy page (T-407).
"""

from __future__ import annotations


def test_economy_page_module_imports() -> None:
    from reflex_openbb.pages import economy as m

    assert hasattr(m, "economy_page"), "economy_page function should live in pages.economy"
