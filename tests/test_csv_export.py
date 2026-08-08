"""
Tests for the csv_export service (T-503).

REQ: REQ-008

services/csv_export.py
- to_csv_bars(bars) — convert list[OHLCBar] to CSV string
- to_csv_macro(points) — convert list[MacroPoint] to CSV string
"""

from __future__ import annotations

import csv
import io

from reflex_openbb.services.csv_export import to_csv_bars, to_csv_macro

# ─── to_csv_bars ────────────────────────────────────────────────────────────


def test_to_csv_bars_module_imports() -> None:
    from reflex_openbb.services import csv_export as m
    assert hasattr(m, "to_csv_bars"), (
        "to_csv_bars should live in services.csv_export"
    )


def test_to_csv_bars_with_empty_list() -> None:
    result = to_csv_bars([])
    # Even with empty list, should have the header
    reader = list(csv.reader(io.StringIO(result)))
    assert len(reader) == 1
    assert "date" in reader[0]


def test_to_csv_bars_includes_data() -> None:
    """REQ-008: CSV export contains the same bars as in the chart."""
    from datetime import date
    from decimal import Decimal

    from reflex_openbb.data.types import OHLCBar

    bars = [
        OHLCBar(
            date=date(2024, 1, 15),
            open=Decimal("150.00"),
            high=Decimal("152.00"),
            low=Decimal("149.00"),
            close=Decimal("151.00"),
            volume=10_000_000,
        )
    ]
    result = to_csv_bars(bars)
    reader = list(csv.reader(io.StringIO(result)))
    assert len(reader) == 2  # header + 1 row
    assert reader[0] == ["date", "open", "high", "low", "close", "volume"]
    assert reader[1][0] == "2024-01-15"
    assert reader[1][4] == "151.00"


# ─── to_csv_macro ──────────────────────────────────────────────────────────


def test_to_csv_macro_module_imports() -> None:
    from reflex_openbb.services import csv_export as m
    assert hasattr(m, "to_csv_macro"), (
        "to_csv_macro should live in services.csv_export"
    )


def test_to_csv_macro_with_empty_list() -> None:
    result = to_csv_macro([])
    reader = list(csv.reader(io.StringIO(result)))
    assert len(reader) == 1
    assert "year" in reader[0]


def test_to_csv_macro_includes_data() -> None:
    from decimal import Decimal

    from reflex_openbb.data.types import MacroPoint

    points = [
        MacroPoint(year=2020, value=Decimal("21.0"), country="US", indicator="GDP")
    ]
    result = to_csv_macro(points)
    reader = list(csv.reader(io.StringIO(result)))
    assert len(reader) == 2
    assert reader[0] == ["year", "value", "country", "indicator"]
    assert reader[1] == ["2020", "21.0", "US", "GDP"]
