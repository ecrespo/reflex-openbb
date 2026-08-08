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

    async def global_search(self, form_data: dict) -> None:
        """Run a search and remember the result.

        REQ-010: global search bar entry point.

        Reflex forms pass the form data as a dict-like var. The form
        has a single 'query' input, so we extract it from the dict.
        The result is stored on the state and the page reads
        `state.last_search` reactively (we don't return anything).

        Args:
            form_data: dict with 'query' key (or empty dict if no input).

        Raises:
            ValueError: on validation failure (empty, too long, bad chars).
        """
        query = form_data.get("query", "") if isinstance(form_data, dict) else ""
        # Validation: search() will raise ValueError for empty/too-long/invalid
        # queries. We just delegate to it (let exceptions propagate).
        result = await search(query)
        self.last_search = result
