"""
Tests for the AppState (T-201).

TDD: this file is written BEFORE state/app_state.py.
The tests must FAIL initially, then pass after implementation.

REQ-010: AppState.global_search(query) calls data.search.search()
and navigates to the appropriate page or shows "not found".

Reflex state pattern:
- The state is a class with rx.State as base
- Event handlers are methods (sync or async)
- For testing, we instantiate the state directly and call its methods

Note: This test does NOT spin up a full Reflex app. It exercises
the state class in isolation, mocking the data layer when needed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from reflex_openbb.data.types import SearchResult

# ─── Module / smoke tests ───────────────────────────────────────────────────


def test_app_state_module_imports() -> None:
    """state.app_state must export the AppState class."""
    from reflex_openbb.state import app_state

    assert hasattr(app_state, "AppState"), "AppState class should live in state.app_state"


# ─── AppState.global_search ────────────────────────────────────────────────


class TestGlobalSearch:
    """REQ-010: AppState.global_search(query) → SearchResult + navigation."""

    @pytest.mark.asyncio
    async def test_equity_query_returns_search_result(self) -> None:
        """When the query matches an equity, AppState returns a SearchResult
        with equity_match set and confidence > 0.
        """
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        result = await state.global_search("AAPL")

        assert isinstance(result, SearchResult)
        assert result.equity_match == "AAPL"
        assert result.crypto_match is None
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_crypto_query_returns_search_result(self) -> None:
        """When the query matches a crypto, AppState returns a SearchResult
        with crypto_match set.
        """
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        result = await state.global_search("BTC")

        assert isinstance(result, SearchResult)
        assert result.crypto_match == "BTC"
        assert result.equity_match is None

    @pytest.mark.asyncio
    async def test_no_match_returns_zero_confidence(self) -> None:
        """When the query matches nothing, confidence is 0."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        result = await state.global_search("ZZZZNOTHING")

        assert result.confidence == 0.0
        assert result.equity_match is None
        assert result.crypto_match is None

    @pytest.mark.asyncio
    async def test_lowercase_query_normalized(self) -> None:
        """Lowercase input is normalized to uppercase."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        result = await state.global_search("aapl")

        assert result.query == "AAPL"
        assert result.equity_match == "AAPL"

    @pytest.mark.asyncio
    async def test_last_search_stored_in_state(self) -> None:
        """REQ: state pattern — last search result is stored on the state."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        result = await state.global_search("MSFT")

        # The state should remember the most recent search result.
        assert state.last_search == result

    @pytest.mark.asyncio
    async def test_query_raises_value_error_on_empty(self) -> None:
        """Validation: empty query raises ValueError."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        with pytest.raises(ValueError):
            await state.global_search("")

    @pytest.mark.asyncio
    async def test_query_raises_value_error_on_too_long(self) -> None:
        """Validation: query > 20 chars raises ValueError."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        with pytest.raises(ValueError):
            await state.global_search("A" * 21)

    @pytest.mark.asyncio
    async def test_invalid_chars_raise_value_error(self) -> None:
        """Validation: invalid characters raise ValueError."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        with pytest.raises(ValueError):
            await state.global_search("AA PL")  # whitespace

    @pytest.mark.asyncio
    async def test_calls_data_search_layer(self) -> None:
        """REQ: AppState delegates to data.search.search (no business logic in state)."""
        from reflex_openbb.state.app_state import AppState

        # Mock the underlying data.search.search to verify it's called.
        expected = SearchResult(
            query="TEST", equity_match="TEST", crypto_match=None, confidence=1.0
        )
        with patch(
            "reflex_openbb.state.app_state.search", new=AsyncMock(return_value=expected)
        ) as mock_search:
            state = AppState()
            result = await state.global_search("TEST")

        # The data layer was called with the original (un-normalized) query
        # — normalization happens inside data.search
        mock_search.assert_awaited_once()
        assert result == expected
