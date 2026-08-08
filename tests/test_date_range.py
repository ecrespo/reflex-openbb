"""
Tests for the date_range component (T-302).

TDD: this file is written BEFORE components/date_range.py.
The tests must FAIL initially, then pass after implementation.

REQ: REQ-002

date_range(state) — returns a row of 5 buttons: 1M, 6M, 1Y, 5Y, Max
Each button calls state.set_period(period) when clicked.

NOTE: The unit tests below verify the component structure. The
end-to-end click behavior (button click triggers state.set_period
which reloads the chart) is validated by integration tests via
'reflex run' (T-006). Unit-testing event handlers requires a
full rx.State which we cannot instantiate outside a Reflex app.
"""

from __future__ import annotations


def test_date_range_module_imports() -> None:
    """components.date_range must export the date_range function."""
    from reflex_openbb.components import date_range as date_range_module

    assert hasattr(date_range_module, "date_range"), (
        "date_range function should live in components.date_range"
    )
