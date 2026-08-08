"""
Tests for the equity page (T-306).

TDD: this file is written BEFORE pages/equity.py.
The tests must FAIL initially, then pass after implementation.

REQ: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005

pages/equity.equity_page() — composes all 5 components with EquityState.

NOTE: These tests are integration-level (require a full Reflex app
context with State Manager). They are validated by integration tests
via 'reflex run' (T-006). The unit tests here verify only the module
structure.
"""

from __future__ import annotations


def test_equity_page_module_imports() -> None:
    """pages.equity must export the equity_page function."""
    from reflex_openbb.pages import equity as m

    assert hasattr(m, "equity_page"), "equity_page function should live in pages.equity"
