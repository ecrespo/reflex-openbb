"""
Tests for the search_box component (T-501).

REQ: REQ-010

search_box() — a global search bar that calls AppState.global_search.
"""

from __future__ import annotations


def test_search_box_module_imports() -> None:
    from reflex_openbb.components import search_box as m
    assert hasattr(m, "search_box"), (
        "search_box function should live in components.search_box"
    )
