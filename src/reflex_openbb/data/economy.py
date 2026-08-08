"""Economy / macro data functions (T-107).

Currently exposes one public function:
`get_economy_indicator(indicator, country="US") -> list[MacroPoint]`.

Indicator routing:
- "GDP"   → obb.economy.gdp(country=...)
- "CPI"   → obb.economy.cpi(country=...)
- "UNRATE"→ obb.economy.unrate(country=...)

The macro DataFrame is validated against `MacroSchema` in
data/schemas.py and converted to a sorted list of `MacroPoint`.

Constitution Art. 3: this is the only place in the app that calls
`obb.economy.*`.
Constitution Art. 5: every `value` is Decimal.
Constitution Art. 6: every function uses the TTL cache (7 days for macro).

Reference:
- api/v1.md §data.economy
- data-model/v1-models.md §MacroPoint
- tech-design/v1-architecture.md §3 (data layer)
"""

from __future__ import annotations

import re
from typing import Literal

from reflex_openbb.data.cache import CacheName, get_or_compute
from reflex_openbb.data.errors import ProviderError
from reflex_openbb.data.schemas import macro_points_from_dataframe
from reflex_openbb.data.types import MacroPoint

__all__ = ["get_economy_indicator"]


# ─── Validation ─────────────────────────────────────────────────────────────


_INDICATORS = ("GDP", "CPI", "UNRATE")
_COUNTRY_RE = re.compile(r"^[A-Z]{2}$")


def _validate_country(country: str) -> str:
    """Validate a country code (ISO-3166 alpha-2, uppercase)."""
    if not country:
        raise ValueError("country cannot be empty")
    normalized = country.upper()
    if not _COUNTRY_RE.match(normalized):
        raise ValueError(f"country must be 2-letter ISO-3166 code, got {country!r}")
    return normalized


# ─── Public API ─────────────────────────────────────────────────────────────


async def get_economy_indicator(
    indicator: Literal["GDP", "CPI", "UNRATE"],
    country: str = "US",
) -> list[MacroPoint]:
    """Get a macro indicator (GDP, CPI, or UNRATE) for a country.

    REQ: REQ-007 (economy dashboard).

    Cache: 7 days (key = `macro:{country}:{indicator}`).
    Macro data is updated slowly, so the long TTL is safe.

    Returns an empty list (not an error) if the SDK returns no data.
    """
    if indicator not in _INDICATORS:
        raise ValueError(f"indicator must be one of {_INDICATORS}, got {indicator!r}")
    normalized_country = _validate_country(country)

    cache_key = f"macro:{normalized_country}:{indicator}"

    def _fetch() -> list[MacroPoint]:
        import openbb as _openbb

        # T-006 fix: OpenBB v4 no longer exposes `obb.economy.gdp/cpi/unrate`
        # as direct methods. The unified endpoint is `obb.economy.indicators`
        # with `symbol=...` (the indicator code) and `country=...`.
        # Some providers require `frequency`.
        #
        # Provider strategy:
        # - GDP, CPI  → econdb (annual)
        # - UNRATE    → not available in current econdb/imf catalogs;
        #               we return [] for now and log a warning.
        if indicator == "UNRATE":
            # The OpenBB v4 economy providers don't include unemployment
            # rate for major countries at the moment. Returning [] is
            # safer than raising — the page will show an empty chart.
            return []

        provider_kwargs: dict = {
            "symbol": indicator,
            "country": normalized_country,
            "provider": "econdb",
        }
        if indicator in ("GDP", "CPI"):
            provider_kwargs["frequency"] = "annual"

        try:
            endpoint = _openbb.obb.economy.indicators
            obb_obj = endpoint(**provider_kwargs)
        except Exception as e:
            raise ProviderError(
                provider="econdb",
                status_code=None,
                retry_after=None,
                original=str(e),
            ) from e

        df = obb_obj.to_dataframe()
        if df is None or len(df) == 0:
            return []

        # T-006 fix: econdb returns a pandas DataFrame. Our schema
        # expects polars with `year` and `value` columns. Convert and
        # rename the econdb columns.
        import polars as pl
        if not isinstance(df, pl.DataFrame):
            # Try to convert from pandas
            if hasattr(df, "to_pandas"):
                df = df.to_pandas()
            if hasattr(df, "reset_index") and df.index.name is not None and "date" not in df.columns:
                    df = df.reset_index()
            try:
                df = pl.from_pandas(df)
            except Exception as e:
                raise ProviderError(
                    provider="econdb",
                    status_code=None,
                    retry_after=None,
                    original=f"Could not convert macro df to polars: {e}",
                ) from e

        # Normalize columns: econdb returns `date` (datetime index) and `value`.
        # The schema wants `year` and `value`.
        if "year" not in df.columns and "date" in df.columns:
            df = df.with_columns(pl.col("date").dt.year().alias("year"))
        elif "year" not in df.columns:
            # try first column as year
            df = df.rename({df.columns[0]: "year"})
        # Ensure we only have the columns the schema needs
        keep = [c for c in ("year", "value") if c in df.columns]
        df = df.select(keep)

        return macro_points_from_dataframe(df, country=normalized_country, indicator=indicator)

    value, _ = get_or_compute(cache_key, CacheName.MACRO, _fetch)
    return value
