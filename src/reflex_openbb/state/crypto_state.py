"""CryptoState (T-203).

The Reflex state for the /crypto/{symbol} page. Wires the crypto data
function into a single state class the page can subscribe to.

Fields:
  symbol, price_bars, is_loading, error, stale_data

Event handlers:
  - set_symbol(symbol)  — REQ-006: validates, stores, and loads price history

Computed vars:
  - price_chart_data    — list[dict] from price_bars (for the chart)

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
    """State for the /crypto/{symbol} page."""

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
        """REQ-006: validate symbol and load its price history.

        The data layer's get_crypto_price_history already validates the
        symbol (raises InvalidTickerError) and raises ProviderError on
        SDK failure. We translate those into the state's error flags.

        Args:
            symbol: crypto symbol (e.g. "BTC", "ETH", "BTC-USD").
        """
        self.is_loading = True
        self.error = None
        self.stale_data = False
        try:
            self.price_bars = await get_crypto_price_history(symbol)
            self.symbol = symbol.upper()
        except InvalidTickerError:
            # Re-raise — the form should surface the validation error.
            self.is_loading = False
            raise
        except ProviderError as e:
            self.stale_data = True
            self.error = str(e)
        finally:
            self.is_loading = False
