"""
Tests for the export_button component (T-504).

REQ: REQ-008

export_button(state) — a button that triggers a CSV download.
"""

from __future__ import annotations


def test_export_button_module_imports() -> None:
    from reflex_openbb.components import export_button as m
    assert hasattr(m, "export_button"), (
        "export_button function should live in components.export_button"
    )
