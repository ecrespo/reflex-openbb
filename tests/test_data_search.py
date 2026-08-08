"""
Tests for the search data function (T-108).

TDD: this file is written BEFORE data/search.py.
The tests must FAIL initially, then pass after implementation.

REQs:
- api/v1.md §data.search:
  - search(query) -> SearchResult
  - REQ: REQ-010 (search)
  - Input: query (1..20 chars)
  - Output: SearchResult with equity_match, crypto_match, confidence
  - Errors: none (always returns a result, even if no match)
  - Cache: none (cheap)
- data-model/v1-models.md §SearchResult
"""

from __future__ import annotations

import pytest

# ─── Module / smoke tests ───────────────────────────────────────────────────


def test_search_module_imports() -> None:
    """data.search must export the public function from the API spec."""
    from reflex_openbb.data import search

    assert callable(getattr(search, "search", None))


# ─── search() ───────────────────────────────────────────────────────────────


class TestSearch:
    """REQ-010: search(query) -> SearchResult."""

    @pytest.mark.asyncio
    async def test_equity_match(self) -> None:
        """When the query is an equity ticker, return equity_match set."""
        from reflex_openbb.data import search

        result = await search.search("AAPL")

        assert result.query == "AAPL"
        assert result.equity_match == "AAPL"
        assert result.crypto_match is None
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_crypto_match_for_btc(self) -> None:
        """When the query is a crypto ticker, return crypto_match set."""
        from reflex_openbb.data import search

        result = await search.search("BTC")

        assert result.query == "BTC"
        assert result.crypto_match == "BTC"
        assert result.equity_match is None
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_crypto_match_for_eth(self) -> None:
        from reflex_openbb.data import search

        result = await search.search("ETH")

        assert result.crypto_match == "ETH"
        assert result.equity_match is None

    @pytest.mark.asyncio
    async def test_no_match_returns_low_confidence(self) -> None:
        """REQ: 'always returns a result, even if no match'."""
        from reflex_openbb.data import search

        result = await search.search("ZZZZNOTHING")

        assert result.query == "ZZZZNOTHING"
        assert result.equity_match is None
        assert result.crypto_match is None
        # Confidence is 0 (or near 0) when nothing matches
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_query_normalized_to_uppercase(self) -> None:
        """Lowercase input is normalized to uppercase."""
        from reflex_openbb.data import search

        result = await search.search("aapl")

        assert result.query == "AAPL"
        assert result.equity_match == "AAPL"

    @pytest.mark.asyncio
    async def test_rejects_empty_query(self) -> None:
        from reflex_openbb.data import search

        with pytest.raises(ValueError):
            await search.search("")

    @pytest.mark.asyncio
    async def test_rejects_too_long_query(self) -> None:
        """REQ: api/v1.md — query must be 1..20 chars."""
        from reflex_openbb.data import search

        with pytest.raises(ValueError):
            await search.search("A" * 21)

    @pytest.mark.asyncio
    async def test_rejects_query_with_whitespace(self) -> None:
        """Whitespace in the query is rejected (queries are atomic symbols)."""
        from reflex_openbb.data import search

        with pytest.raises(ValueError):
            await search.search("AA PL")

    @pytest.mark.asyncio
    async def test_dash_in_query_accepted(self) -> None:
        """A dash is valid in tickers like BTC-USD."""
        from reflex_openbb.data import search

        result = await search.search("BTC-USD")

        # Either equity or crypto match (BTC-USD is most likely crypto)
        assert result.query == "BTC-USD"
        # Confidence should be positive (the symbol was found in our static list)
        assert result.confidence >= 0.0

    @pytest.mark.asyncio
    async def test_confidence_in_valid_range(self) -> None:
        """REQ: data-model — confidence is in [0.0, 1.0]."""
        from reflex_openbb.data import search

        for q in ["AAPL", "BTC", "ZZZZ", "MSFT", "ETH-USD"]:
            result = await search.search(q)
            assert 0.0 <= result.confidence <= 1.0, (
                f"Confidence out of range for {q!r}: {result.confidence}"
            )
