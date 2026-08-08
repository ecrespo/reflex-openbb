"""CryptoState (T-203 + T-505).

The Reflex state for the /crypto page. Wires the crypto data
function into a single state class the page can subscribe to.

Fields:
  symbol, price_bars, is_loading, error, stale_data

Event handlers:
  - set_symbol(symbol)   — REQ-006: validates, stores, and loads price history
  - export_csv()         — REQ-008: trigger CSV download

Computed vars:
  - price_chart_data     — list[dict] from price_bars (for the chart)

Constitution Art. 3 (OpenBB only): the state does NOT call obb.*.
It delegates to data.crypto.* which is the only place that calls the SDK.
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.data.crypto import get_crypto_price_history
from reflex_openbb.data.errors import InvalidTickerError, ProviderError
from reflex_openbb.data.types import OHLCBar

__all__ = ["CryptoState", "get_crypto_price_history"]


class CryptoState(rx.State):
    """State for the /crypto page."""

    # ─── User-controlled field ───────────────────────────────────────
    symbol: str = "BTC"

    # ─── Loaded data ─────────────────────────────────────────────────
    price_bars: list[OHLCBar] = []  # noqa: RUF012 (rx.State mutable defaults are safe)

    # ─── Status flags ────────────────────────────────────────────────
    is_loading: bool = False
    error: str | None = None
    stale_data: bool = False

    # ─── Computed vars ───────────────────────────────────────────────

    @rx.var
    def price_chart_data(self) -> list[dict]:
        """REQ-006: list[dict] from price_bars for the chart component."""
        return [b.model_dump(mode="json") for b in self.price_bars]

    # ─── Event handlers ──────────────────────────────────────────────

    async def set_symbol(self, symbol: str) -> None:
        """REQ-006: validate symbol and load its price history."""
        self.is_loading = True
        self.error = None
        self.stale_data = False
        try:
            self.price_bars = await get_crypto_price_history(symbol)
            self.symbol = symbol.upper()
        except InvalidTickerError:
            self.is_loading = False
            raise
        except ProviderError as e:
            self.stale_data = True
            self.error = str(e)
        finally:
            self.is_loading = False

    async def export_csv(self) -> None:
        """REQ-008: trigger a CSV download of the current price_bars."""
        from reflex_openbb.services.csv_export import to_csv_bars

        csv_data = to_csv_bars(self.price_bars)
        filename = f"{self.symbol.lower()}.csv"
        return rx.download(
            data=csv_data,
            filename=filename,
        )
