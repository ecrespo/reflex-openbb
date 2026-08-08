"""
Tests for the comparison_controls component (T-506).

REQ: REQ-009

comparison_controls(state) — input + button to add a ticker to
the comparison overlay.
"""

from __future__ import annotations


def test_comparison_controls_module_imports() -> None:
    from reflex_openbb.components import comparison_controls as m
    assert hasattr(m, "comparison_controls"), (
        "comparison_controls function should live in components.comparison_controls"
    )
