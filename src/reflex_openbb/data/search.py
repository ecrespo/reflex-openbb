"""Search data function (T-108).

The single public function `search(query)` is the cheapest way to resolve
a user query ("AAPL", "BTC", "msft") into a known equity or crypto ticker.

Implementation note (v1):
- We do NOT call the OpenBB SDK for this. The SDK requires a backend
  round-trip and credentials, and the spec says 'no cache — cheap'.
- Instead, we use small in-memory lookup tables (EQUITY_TICKERS and
  CRYPTO_TICKERS) that the app populates at startup. v2 may swap this
  for the SDK's `obb.equity.search` / `obb.crypto.search` endpoints.
- The function always returns a SearchResult, even on no-match
  (REQ-010: "always returns a result, even if no match"). On no-match,
  confidence is 0 and both match fields are None.

Constitution Art. 3: this is the only place in the app that resolves
a user query to a ticker. (For v1 the resolver is local, not via
`obb.*` — but the public API is identical to what the SDK version
would expose.)
Constitution Art. 6: no cache (the spec is explicit: "Cache: none").

Reference:
- api/v1.md §data.search
- data-model/v1-models.md §SearchResult
"""

from __future__ import annotations

import re

from reflex_openbb.data.types import SearchResult

__all__ = ["search"]


# ─── Lookup tables (v1) ─────────────────────────────────────────────────────
#
# These are the tickers the search resolver knows about. In v1 we only
# support a small set; v2 will wire this to obb.equity.search / obb.crypto.search.
# Adding a ticker here is intentionally manual — v1 is about getting the
# plumbing right, not about being a complete ticker database.


EQUITY_TICKERS: frozenset[str] = frozenset(
    {
        # Mega caps
        "AAPL",
        "MSFT",
        "GOOGL",
        "GOOG",
        "AMZN",
        "META",
        "NVDA",
        "TSLA",
        "BRK.B",
        "JPM",
        "V",
        "JNJ",
        "WMT",
        "PG",
        "MA",
        "HD",
        "DIS",
        # ETFs
        "SPY",
        "QQQ",
        "IWM",
        "VOO",
        "VTI",
        # Other common
        "NFLX",
        "AMD",
        "INTC",
        "ORCL",
        "CRM",
        "ADBE",
        "PYPL",
        "SBUX",
        "KO",
        "PEP",
        "MCD",
        "NKE",
        "BA",
        "GS",
        "MS",
        "C",
        "BAC",
    }
)


CRYPTO_TICKERS: frozenset[str] = frozenset(
    {
        "BTC",
        "ETH",
        "SOL",
        "BNB",
        "XRP",
        "ADA",
        "DOGE",
        "AVAX",
        "MATIC",
        "DOT",
        "LINK",
        "UNI",
        "LTC",
        "BCH",
        "NEAR",
        "ATOM",
        # Stablecoins (less common as "search" targets but possible)
        "USDT",
        "USDC",
        "DAI",
    }
)


# Crypto tickers that are also valid as `<TICKER>-USD` pairs
CRYPTO_WITH_USD_PAIR: frozenset[str] = frozenset(
    {
        "BTC",
        "ETH",
        "SOL",
        "BNB",
        "XRP",
        "ADA",
        "DOGE",
        "AVAX",
        "MATIC",
        "DOT",
        "LINK",
        "UNI",
        "LTC",
        "BCH",
    }
)


# ─── Validation ─────────────────────────────────────────────────────────────


_QUERY_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,19}$")


def _validate_query(query: str) -> str:
    """Validate and normalize a search query. REQ: api/v1.md §search.

    - 1..20 chars
    - Atomic symbol (no whitespace)
    - Starts with a letter
    - May contain [A-Z0-9.\\-]
    - Returns the uppercase version
    """
    if not query:
        raise ValueError("query cannot be empty")
    normalized = query.upper()
    if len(normalized) > 20:
        raise ValueError(f"query must be <= 20 chars, got {len(normalized)}")
    if not _QUERY_RE.match(normalized):
        raise ValueError(f"query must match [A-Z][A-Z0-9.\\-]{{0,19}}, got {query!r}")
    return normalized


# ─── Public API ─────────────────────────────────────────────────────────────


async def search(query: str) -> SearchResult:
    """Resolve a user query to an equity or crypto ticker.

    REQ: REQ-010 (search bar).

    Returns a SearchResult. Always returns a result, even on no-match
    (in which case confidence is 0 and both match fields are None).

    Resolution order:
    1. Exact match in EQUITY_TICKERS → equity_match set, confidence 1.0
    2. Exact match in CRYPTO_TICKERS → crypto_match set, confidence 1.0
    3. `<CRYPTO>-USD` pattern → crypto_match = the base ticker, confidence 0.95
    4. Case-insensitive prefix match (e.g. 'AA' → 'AAPL') → confidence 0.5
    5. No match → both None, confidence 0.0
    """
    normalized = _validate_query(query)

    # 1. Exact equity match
    if normalized in EQUITY_TICKERS:
        return SearchResult(
            query=normalized,
            equity_match=normalized,
            crypto_match=None,
            confidence=1.0,
        )

    # 2. Exact crypto match
    if normalized in CRYPTO_TICKERS:
        return SearchResult(
            query=normalized,
            equity_match=None,
            crypto_match=normalized,
            confidence=1.0,
        )

    # 3. `<CRYPTO>-USD` pattern (e.g. "BTC-USD" → crypto_match = "BTC")
    if normalized.endswith("-USD"):
        base = normalized[: -len("-USD")]
        if base in CRYPTO_WITH_USD_PAIR:
            return SearchResult(
                query=normalized,
                equity_match=None,
                crypto_match=base,
                confidence=0.95,
            )

    # 4. Case-insensitive prefix match — a fallback for partial queries
    #    e.g. "AA" → "AAPL" (equity), "BT" → "BTC" (crypto)
    #    Prefer the longest match.
    candidates: list[tuple[float, str, str | None, str | None]] = []

    for t in EQUITY_TICKERS:
        if t.startswith(normalized) and t != normalized:
            # Confidence drops with each extra character needed
            conf = 0.5 * (len(normalized) / len(t))
            candidates.append((conf, t, t, None))
    for t in CRYPTO_TICKERS:
        if t.startswith(normalized) and t != normalized:
            conf = 0.5 * (len(normalized) / len(t))
            candidates.append((conf, t, None, t))

    if candidates:
        # Pick the highest-confidence match
        best = max(candidates, key=lambda c: c[0])
        confidence, _ticker, equity, crypto = best
        return SearchResult(
            query=normalized,
            equity_match=equity,
            crypto_match=crypto,
            confidence=confidence,
        )

    # 5. No match
    return SearchResult(
        query=normalized,
        equity_match=None,
        crypto_match=None,
        confidence=0.0,
    )
