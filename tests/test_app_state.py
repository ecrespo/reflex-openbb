"""
Tests for the AppState (T-201).

TDD: this file is written BEFORE state/app_state.py.
The tests must FAIL initially, then pass after implementation.

REQ-010: AppState.global_search(form_data) calls data.search.search()
and navigates to the appropriate page or shows "not found".

Reflex state pattern:
- The state is a class with rx.State as base
- Event handlers are methods (sync or async)
- For testing, we instantiate the state directly and call its methods

Note: This test does NOT spin up a full Reflex app. It exercises
the state class in isolation, mocking the data layer when needed.

T-006 update: The handler now takes `form_data: dict` (not `query: str`)
because it's bound to a `rx.form` which passes the form values as a
dict. The handler extracts the 'query' key.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from reflex_openbb.data.types import SearchResult


def test_app_state_module_imports() -> None:
    """state.app_state must export the AppState class."""
    from reflex_openbb.state import app_state

    assert hasattr(app_state, "AppState"), "AppState class should live in state.app_state"


class TestGlobalSearch:
    """REQ-010: AppState.global_search(form_data) → SearchResult + navigation."""

    @pytest.mark.asyncio
    async def test_equity_query_returns_search_result(self) -> None:
        """When the query matches an equity, AppState returns a SearchResult."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        await state.global_search({"query": "AAPL"})

        # The state remembers the most recent search result.
        assert state.last_search is not None
        assert state.last_search.equity_match == "AAPL"
        assert state.last_search.crypto_match is None
        assert state.last_search.confidence > 0

    @pytest.mark.asyncio
    async def test_crypto_query_returns_search_result(self) -> None:
        """When the query matches a crypto, AppState returns a SearchResult."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        await state.global_search({"query": "BTC"})

        assert state.last_search is not None
        assert state.last_search.crypto_match == "BTC"
        assert state.last_search.equity_match is None

    @pytest.mark.asyncio
    async def test_no_match_returns_zero_confidence(self) -> None:
        """When the query matches nothing, confidence is 0."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        await state.global_search({"query": "ZZZZNOTHING"})

        assert state.last_search is not None
        assert state.last_search.confidence == 0.0
        assert state.last_search.equity_match is None
        assert state.last_search.crypto_match is None

    @pytest.mark.asyncio
    async def test_lowercase_query_normalized(self) -> None:
        """Lowercase input is normalized to uppercase."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        await state.global_search({"query": "aapl"})

        assert state.last_search is not None
        assert state.last_search.query == "AAPL"
        assert state.last_search.equity_match == "AAPL"

    @pytest.mark.asyncio
    async def test_last_search_stored_in_state(self) -> None:
        """REQ: state pattern — last search result is stored on the state."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        await state.global_search({"query": "MSFT"})

        assert state.last_search is not None
        assert state.last_search.query == "MSFT"

    @pytest.mark.asyncio
    async def test_query_raises_value_error_on_empty(self) -> None:
        """Validation: empty query raises ValueError."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        with pytest.raises(ValueError):
            await state.global_search({"query": ""})

    @pytest.mark.asyncio
    async def test_query_raises_value_error_on_too_long(self) -> None:
        """Validation: query > 20 chars raises ValueError."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        with pytest.raises(ValueError):
            await state.global_search({"query": "A" * 21})

    @pytest.mark.asyncio
    async def test_invalid_chars_raise_value_error(self) -> None:
        """Validation: invalid characters raise ValueError."""
        from reflex_openbb.state.app_state import AppState

        state = AppState()
        with pytest.raises(ValueError):
            await state.global_search({"query": "AA PL"})  # whitespace

    @pytest.mark.asyncio
    async def test_calls_data_search_layer(self) -> None:
        """REQ: AppState delegates to data.search.search (no business logic in state)."""
        from reflex_openbb.state.app_state import AppState

        expected = SearchResult(
            query="TEST", equity_match="TEST", crypto_match=None, confidence=1.0
        )
        with patch(
            "reflex_openbb.state.app_state.search", new=AsyncMock(return_value=expected)
        ) as mock_search:
            state = AppState()
            await state.global_search({"query": "TEST"})

        mock_search.assert_awaited_once()
        # The state stored the expected result.
        assert state.last_search == expected
