"""EconomyState (T-204).

The Reflex state for the /economy page. Wires the economy data
function into a single state class the page can subscribe to.

Fields:
  indicator, country, series, is_loading, error, stale_data

Event handlers:
  - set_indicator(indicator)  — REQ-007: stores; triggers load_indicator
  - set_country(country)      — REQ-007: stores; triggers load_indicator
  - load_indicator()          — internal: fetches data

Computed vars:
  - chart_data                — list[dict] from series (for the chart)

Constitution Art. 3 (OpenBB only): the state does NOT call obb.*.
It delegates to data.economy.* which is the only place that calls the SDK.
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.data.economy import get_economy_indicator
from reflex_openbb.data.errors import ProviderError
from reflex_openbb.data.types import MacroPoint

__all__ = ["EconomyState", "get_economy_indicator"]


_INDICATORS = ("GDP", "CPI", "UNRATE")


class EconomyState(rx.State):
    """State for the /economy page."""

    # ─── User-controlled fields ──────────────────────────────────────
    indicator: str = "GDP"
    country: str = "US"

    # ─── Loaded data ─────────────────────────────────────────────────
    series: list[MacroPoint] = []  # noqa: RUF012 (rx.State mutable defaults are safe)

    # ─── Status flags ────────────────────────────────────────────────
    is_loading: bool = False
    error: str | None = None
    stale_data: bool = False

    # ─── Computed vars ───────────────────────────────────────────────

    @rx.var
    def chart_data(self) -> list[dict]:
        """REQ-007: list[dict] from series for the chart component."""
        return [p.model_dump(mode="json") for p in self.series]

    # ─── Event handlers ──────────────────────────────────────────────

    async def set_indicator(self, indicator: str) -> None:
        """REQ-007: store the indicator and reload the series.

        Validation: must be one of GDP, CPI, UNRATE (the data layer
        enforces this — we re-raise ValueError for the form to surface).
        """
        normalized = indicator.upper()
        if normalized not in _INDICATORS:
            raise ValueError(f"indicator must be one of {_INDICATORS}, got {indicator!r}")
        self.indicator = normalized
        await self._load()

    async def set_country(self, country: str) -> None:
        """REQ-007: store the country and reload the series.

        Validation: must be 2-letter ISO-3166 (the data layer enforces
        this — we re-raise ValueError for the form to surface).
        """
        normalized = country.upper()
        self.country = normalized
        await self._load()

    async def _load(self) -> None:
        """Fetch the series for the current indicator+country.

        Translates ProviderError into stale_data=True + error=str(e).
        """
        self.is_loading = True
        self.error = None
        self.stale_data = False
        try:
            self.series = await get_economy_indicator(self.indicator, self.country)
        except ValueError:
            # Re-raise validation errors (bad indicator / bad country).
            self.is_loading = False
            raise
        except ProviderError as e:
            self.stale_data = True
            self.error = str(e)
        finally:
            self.is_loading = False
