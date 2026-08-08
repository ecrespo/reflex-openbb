"""AppState (T-201).

Global Reflex state. Currently exposes one event handler:
`AppState.global_search(query)` — the entry point for the global
search bar (REQ-010).

Architecture:
- This is a thin layer over `data.search.search`. The state class
  does NOT contain business logic; it just delegates to the data
  layer and remembers the most recent result.
- Validation is delegated to `data.search._validate_query`. The
  state propagates the ValueError unchanged.
- In a Reflex app, this class is a `rx.State` subclass. For tests
  we instantiate it directly (Reflex's pattern).

Constitution Art. 3 (OpenBB only): the data layer is the only
thing that calls the SDK. The state layer only orchestrates.
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.data.search import search
from reflex_openbb.data.types import SearchResult

__all__ = ["AppState", "search"]


class AppState(rx.State):
    """Global app state.

    The global search bar binds to `AppState.global_search`. The
    navigation after a successful search is handled by the page
    that owns the search bar — we just return the result and let
    the caller decide what to do (navigate to /equity/{ticker},
    /crypto/{symbol}, or show a "not found" message).
    """

    #: The most recent search result. None until the first search.
    last_search: SearchResult | None = None

    async def global_search(self, query: str) -> SearchResult:
        """Run a search and remember the result.

        REQ-010: global search bar entry point.

        Args:
            query: 1..20 chars, atomic symbol (no whitespace).

        Returns:
            SearchResult. equity_match is set for equity hits,
            crypto_match for crypto hits, both None with confidence=0
            on no match.

        Raises:
            ValueError: on validation failure (empty, too long, bad chars).
        """
        result = await search(query)
        self.last_search = result
        return result
