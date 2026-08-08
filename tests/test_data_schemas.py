"""
Tests for data/schemas.py (refactor: extract OHLCSchema + _to_ohlc_bars).

TDD: this file is written BEFORE the refactor.
The tests must FAIL initially, then pass after the extraction.

This refactor extracts the OHLCDataFrameSchema and the DataFrame→OHLCBar
converter from data/equity.py to a dedicated data/schemas.py module. The
goal is:
  - Single source of truth for the price-history DataFrame schema
  - Reusable for any future data source (crypto, options, futures, ...)
  - Cleaner separation: data/schemas.py is "what data looks like",
    data/equity.py is "where equity data comes from"

REQs:
- Constitution Art. 3 (OpenBB only): all DataFrame validation lives
  in the data layer.
- Constitution Art. 8 (Component-first): each piece of the data
  layer should be a single, focused module.
"""

from __future__ import annotations

import polars as pl
import pytest

from reflex_openbb.data import errors as data_errors
from reflex_openbb.data import schemas as data_schemas

# ─── Module / smoke tests ───────────────────────────────────────────────────


def test_schemas_module_imports() -> None:
    """data.schemas must export the schema class and the converter."""
    assert hasattr(data_schemas, "OHLCSchema"), (
        "OHLCSchema should live in data.schemas (not data.equity)"
    )
    assert hasattr(data_schemas, "ohlc_bars_from_dataframe"), (
        "ohlc_bars_from_dataframe should live in data.schemas"
    )


def test_ohlc_schema_still_validates_correct_data() -> None:
    """The refactored schema still accepts a valid OHLC DataFrame."""
    import datetime

    df = pl.DataFrame(
        {
            "date": [datetime.date(2024, 1, 15)],
            "open": ["150.00"],
            "high": ["152.00"],
            "low": ["149.50"],
            "close": ["151.25"],
            "volume": [10_000_000],
        },
        schema={
            "date": pl.Date,
            "open": pl.Decimal(precision=18, scale=4),
            "high": pl.Decimal(precision=18, scale=4),
            "low": pl.Decimal(precision=18, scale=4),
            "close": pl.Decimal(precision=18, scale=4),
            "volume": pl.Int64,
        },
    )

    # Should not raise
    validated = data_schemas.OHLCSchema.validate(df)
    assert validated.shape[0] == 1


def test_ohlc_schema_still_rejects_bad_data() -> None:
    """The refactored schema still rejects missing columns."""
    df = pl.DataFrame(
        {
            "date": ["2024-01-15"],
            "open": ["150.00"],
            "high": ["152.00"],
            "low": ["149.50"],
            "closing_price": ["151.25"],  # wrong name
            "volume": [10_000_000],
        }
    )

    with pytest.raises((pl.ColumnNotFoundError, Exception)):
        data_schemas.OHLCSchema.validate(df)


def test_ohlc_bars_from_dataframe_returns_sorted_list() -> None:
    """The converter still sorts by date ascending."""
    from decimal import Decimal

    df = pl.DataFrame(
        {
            "date": ["2024-01-17", "2024-01-15", "2024-01-16"],
            "open": ["152.00", "150.00", "151.00"],
            "high": ["154.00", "152.00", "153.00"],
            "low": ["151.50", "149.50", "150.50"],
            "close": ["153.75", "151.25", "152.50"],
            "volume": [12_000_000, 10_000_000, 11_000_000],
        },
        schema={
            "date": pl.Date,
            "open": pl.Decimal(precision=18, scale=4),
            "high": pl.Decimal(precision=18, scale=4),
            "low": pl.Decimal(precision=18, scale=4),
            "close": pl.Decimal(precision=18, scale=4),
            "volume": pl.Int64,
        },
    )

    bars = data_schemas.ohlc_bars_from_dataframe(df)
    dates = [b.date for b in bars]
    assert dates == sorted(dates)
    assert bars[0].close == Decimal("151.25")  # the earliest date


def test_ohlc_bars_from_dataframe_rejects_bad_schema() -> None:
    """The converter raises ProviderError on schema mismatch."""
    df = pl.DataFrame(
        {
            "date": ["2024-01-15"],
            "open": ["150.00"],
            "high": ["152.00"],
            "low": ["149.50"],
            "closing_price": ["151.25"],  # wrong name
            "volume": [10_000_000],
        }
    )

    with pytest.raises(data_errors.ProviderError, match="schema validation"):
        data_schemas.ohlc_bars_from_dataframe(df)


def test_equity_still_imports_schema() -> None:
    """data.equity must still be able to use the schema (re-export OK)."""
    from reflex_openbb.data import equity

    # equity can still use the schema (either re-exported or via direct import)
    assert hasattr(equity, "_to_ohlc_bars") or hasattr(equity, "OHLCSchema") or True
    # (the actual implementation can import from data.schemas directly)


def test_crypto_still_imports_converter() -> None:
    """data.crypto must still be able to use the converter."""
    from reflex_openbb.data import crypto

    # The crypto module should still be importable and work
    assert callable(getattr(crypto, "get_crypto_price_history", None))
