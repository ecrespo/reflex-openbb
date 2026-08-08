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

        # Route to the correct endpoint based on indicator.
        endpoint = getattr(_openbb.obb.economy, indicator.lower())

        try:
            obb_obj = endpoint(country=normalized_country)
        except Exception as e:
            raise ProviderError(
                provider="unknown",
                status_code=None,
                retry_after=None,
                original=str(e),
            ) from e

        df = obb_obj.to_dataframe()
        if df is None or df.is_empty():
            return []

        return macro_points_from_dataframe(df, country=normalized_country, indicator=indicator)

    value, _ = get_or_compute(cache_key, CacheName.MACRO, _fetch)
    return value
