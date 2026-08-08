"""DataFrame schemas and converters for the data layer.

This module is the single source of truth for:
- Pandera schemas (DataFrame validation at the data-layer boundary)
- DataFrame → Pydantic model converters

When the OpenBB SDK returns a DataFrame, it MUST be validated against
the appropriate schema here BEFORE being converted to Pydantic models.
This catches provider-schema drift (renamed columns, changed types) at
the boundary instead of corrupting downstream state with KeyError.

Constitution Art. 3 (OpenBB only): all DataFrame validation lives here.
Constitution Art. 8 (Component-first): each schema is a single, focused
class — easy to find, easy to test, easy to extend.
"""

from __future__ import annotations

from datetime import date

import pandera.polars as pa
import polars as pl
from pandera.errors import SchemaError, SchemaErrors

from reflex_openbb.data.errors import ProviderError
from reflex_openbb.data.types import OHLCBar

# ─── Schemas ────────────────────────────────────────────────────────────────


class OHLCSchema(pa.DataFrameModel):
    """Schema for any OHLC price history DataFrame returned by the SDK.

    Used by:
    - data.equity.get_equity_price_history
    - data.crypto.get_crypto_price_history
    - any future price-history function (options, futures, etc.)

    Strict by design: every column is required, types are explicit,
    and we check `volume >= 0`. If the provider changes its schema,
    we fail loudly here, NOT later in Pydantic construction.
    """

    # NOTE: in pandera.polars, precision/scale for Decimal columns are
    # defined on the polars type itself (`pl.Decimal(precision, scale)`),
    # not on `pa.Field`. The `ge=0` check on volume is a built-in.
    date: pl.Date
    open: pl.Decimal(precision=18, scale=4)
    high: pl.Decimal(precision=18, scale=4)
    low: pl.Decimal(precision=18, scale=4)
    close: pl.Decimal(precision=18, scale=4)
    volume: int = pa.Field(ge=0)

    class Config:
        coerce = True  # coerce string → Decimal, etc.


class MacroSchema(pa.DataFrameModel):
    """Schema for macro indicator DataFrames (GDP, CPI, UNRATE).

    Used by data.economy.get_economy_indicator.

    The SDK returns a DataFrame with `year` and `value` columns
    (one row per year of data). The `country` and `indicator` are
    passed as arguments to the SDK call, so they don't appear in
    the DataFrame — they're added to each MacroPoint by the converter.
    """

    year: int = pa.Field(ge=1900, le=2200)
    value: pl.Decimal(precision=18, scale=4)

    class Config:
        coerce = True


# ─── Converters ─────────────────────────────────────────────────────────────


def ohlc_bars_from_dataframe(df: pl.DataFrame) -> list[OHLCBar]:
    """Validate `df` against OHLCSchema and convert to a sorted list of OHLCBar.

    REQ: REQ-001, REQ-002 + data-model §OHLCBar.
    Returns a list sorted ascending by date.

    Raises:
        ProviderError: if the DataFrame fails schema validation
            (wrong columns, wrong types, negative volume, etc.).
    """
    # 1. Validate schema. If it doesn't match, raise ProviderError.
    #    We catch BOTH pandera's SchemaError/SchemaErrors AND polars'
    #    ColumnNotFoundError — the latter happens when the provider
    #    drops/renames a column, which pandera doesn't wrap.
    try:
        validated = OHLCSchema.validate(df, lazy=True)
    except (SchemaError, SchemaErrors) as e:
        raise ProviderError(
            provider="unknown",
            status_code=None,
            retry_after=None,
            original=f"OHLC data failed schema validation: {e}",
        ) from e
    except pl.exceptions.ColumnNotFoundError as e:
        raise ProviderError(
            provider="unknown",
            status_code=None,
            retry_after=None,
            original=f"OHLC data failed schema validation: missing column: {e}",
        ) from e

    # 2. Convert to a sorted list of OHLCBar.
    sorted_df = validated.sort("date")

    bars: list[OHLCBar] = []
    for row in sorted_df.iter_rows(named=True):
        d = row["date"]
        # `pl.Date` always returns a `date` object, but be defensive.
        if isinstance(d, str):
            d = date.fromisoformat(d)

        bars.append(
            OHLCBar(
                date=d,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=int(row["volume"]),
            )
        )
    return bars


def macro_points_from_dataframe(
    df: pl.DataFrame, *, country: str, indicator: str
) -> list[MacroPoint]:
    """Validate `df` against MacroSchema and convert to a sorted list of MacroPoint.

    REQ: REQ-007 + data-model §MacroPoint.
    Returns a list sorted ascending by year.

    The `country` and `indicator` are passed in by the caller (they were
    arguments to the SDK call, not columns in the DataFrame). They're
    added to each MacroPoint.

    Raises:
        ProviderError: if the DataFrame fails schema validation.
    """
    from reflex_openbb.data.types import MacroPoint  # avoid circular import

    # 1. Validate schema. Catch BOTH pandera errors and polars'
    #    ColumnNotFoundError.
    try:
        validated = MacroSchema.validate(df, lazy=True)
    except (SchemaError, SchemaErrors) as e:
        raise ProviderError(
            provider="unknown",
            status_code=None,
            retry_after=None,
            original=f"Macro data failed schema validation: {e}",
        ) from e
    except pl.exceptions.ColumnNotFoundError as e:
        raise ProviderError(
            provider="unknown",
            status_code=None,
            retry_after=None,
            original=f"Macro data failed schema validation: missing column: {e}",
        ) from e

    # 2. Sort by year ascending and convert to MacroPoint.
    sorted_df = validated.sort("year")

    return [
        MacroPoint(
            year=int(row["year"]),
            value=row["value"],
            country=country,
            indicator=indicator,
        )
        for row in sorted_df.iter_rows(named=True)
    ]


__all__ = ["MacroSchema", "OHLCSchema", "macro_points_from_dataframe", "ohlc_bars_from_dataframe"]
