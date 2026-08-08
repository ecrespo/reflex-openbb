"""Crypto data functions (T-106).

Like `data/equity.py`, but for crypto. Currently exposes a single function:
`get_crypto_price_history(symbol, period="1y") -> list[OHLCBar]`.

The implementation reuses the OHLCSchema validation from `equity.py` — the
price-history schema is identical (date, open, high, low, close, volume)
regardless of whether the source is equity or crypto. This avoids
duplication and keeps a single source of truth for the schema.

Constitution Art. 3: this is the only place in the app that calls
`obb.crypto.*`.
Constitution Art. 5: every monetary field is Decimal.
Constitution Art. 6: every function uses the TTL cache.

Reference:
- api/v1.md §data.crypto
- data-model/v1-models.md
- tech-design/v1-architecture.md §3 (data layer)
"""

from __future__ import annotations

import re
from typing import Literal

from reflex_openbb.data.cache import CacheName, get_or_compute
from reflex_openbb.data.errors import InvalidTickerError, ProviderError
from reflex_openbb.data.schemas import ohlc_bars_from_dataframe  # reuse
from reflex_openbb.data.types import OHLCBar

__all__ = ["get_crypto_price_history"]


# ─── Symbol validation ─────────────────────────────────────────────────────


_CRYPTO_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,19}$")


def _validate_symbol(symbol: str) -> str:
    """Validate and normalize a crypto symbol. REQ: api/v1.md §crypto.

    Crypto symbols are up to 20 chars and may include dashes
    (e.g. `BTC-USD` for Coinbase tickers). Unlike equity, they do NOT
    include a period suffix.

    Returns the uppercase version.
    """
    if not symbol:
        raise InvalidTickerError(symbol or "", "empty")
    normalized = symbol.upper()
    if len(normalized) > 20:
        raise InvalidTickerError(symbol, "too_long")
    if not _CRYPTO_RE.match(normalized):
        raise InvalidTickerError(symbol, "invalid_chars")
    return normalized


# ─── Public API ─────────────────────────────────────────────────────────────


async def get_crypto_price_history(
    symbol: str,
    period: Literal["1mo", "6mo", "1y", "5y", "max"] = "1y",
) -> list[OHLCBar]:
    """Get OHLC price history for a crypto symbol. REQ: REQ-006.

    Cache: 5 min for 1mo/6mo/1y, 1 day for 5y/max.
    """
    normalized = _validate_symbol(symbol)
    cache_key = f"crypto:{normalized}:{period}"

    def _fetch() -> list[OHLCBar]:
        import openbb as _openbb

        # yfinance requires the "-USD" suffix (e.g. "BTC-USD", "ETH-USD").
        # If the user passed just "BTC" or "ETH", add it. Otherwise pass
        # the symbol as-is (e.g. "BTC-USD" already, or "BTCUSDT" for
        # binance provider).
        provider_symbol = normalized
        if "-" not in provider_symbol and provider_symbol.isalpha():
            # Heuristic: 3-5 letter alphabetic symbol → yfinance crypto
            provider_symbol = f"{provider_symbol}-USD"

        try:
            obb_obj = _openbb.obb.crypto.price.historical(
                symbol=provider_symbol, period=period, provider="yfinance"
            )
        except Exception as e:
            raise ProviderError(
                provider="yfinance",
                status_code=None,
                retry_after=None,
                original=str(e),
            ) from e

        df = obb_obj.to_dataframe()
        if df is None or len(df) == 0:
            raise ProviderError(
                provider="yfinance",
                status_code=None,
                retry_after=None,
                original=f"No price history for {normalized} ({period})",
            )

        # T-006 fix: yfinance returns pandas; convert to polars
        import polars as pl
        if not isinstance(df, pl.DataFrame):
            if hasattr(df, "to_pandas"):  # polars → pandas (shouldn't happen)
                df = df.to_pandas()
            if hasattr(df, "reset_index") and df.index.name is not None and "date" not in df.columns:
                    df = df.reset_index()
            try:
                df = pl.from_pandas(df)
            except Exception as e:
                raise ProviderError(
                    provider="yfinance",
                    status_code=None,
                    retry_after=None,
                    original=f"Could not convert crypto df to polars: {e}",
                ) from e
        if "date" not in df.columns and df.columns[0] not in ("date",):
            df = df.rename({df.columns[0]: "date"})

        return ohlc_bars_from_dataframe(df)

    value, _ = get_or_compute(cache_key, CacheName.PRICE, _fetch)
    return value
