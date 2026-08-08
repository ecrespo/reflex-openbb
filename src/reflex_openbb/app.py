"""The Reflex app entry point.

T-005 + T-307 + T-403 + T-408: app with home + equity + crypto + economy.

Usage:
    uv run reflex-openbb           # uses `main()` as the console script
    uv run reflex run              # uses `app` directly via the reflex CLI

The console script declared in pyproject.toml points to `main()`.
"""

import reflex as rx

from reflex_openbb.pages import crypto, economy, equity, home
from reflex_openbb.state.crypto_state import CryptoState
from reflex_openbb.state.economy_state import EconomyState
from reflex_openbb.state.equity_state import EquityState


def index() -> rx.Component:
    """Wrapper around `home.index` for the console-script entry point.

    Keeping the page function here means the `reflex run` CLI (which expects
    a callable named `index` in the app module) finds it without further config.
    """
    return home.index()


def equity_route() -> rx.Component:
    """The /equity/[symbol] page (T-307)."""
    return equity.equity_page()


def crypto_route() -> rx.Component:
    """The /crypto/[symbol] page (T-403)."""
    return crypto.crypto_page()


def economy_route() -> rx.Component:
    """The /economy page (T-408)."""
    return economy.economy_page()


# Build the app. The `app` is a module-level `rx.App` so that `reflex run`
# (which introspects the module to find an `app` symbol) can find it.
app = rx.App()
app.add_page(index, route="/")
# /equity, /crypto, /economy — static routes (no dynamic route args).
# Reflex dynamic route args (e.g. /equity/[ticker]) conflict with state
# vars of the same name in other states (EquityState.ticker, CryptoState.symbol).
# We use a single static route per page and pass the ticker via URL query
# params (or via the ticker input form on the page itself).
app.add_page(equity_route, route="/equity", on_load=EquityState.load_initial)
app.add_page(crypto_route, route="/crypto", on_load=CryptoState.load_initial)
app.add_page(economy_route, route="/economy", on_load=EconomyState.load_initial)


def main() -> None:
    """Console-script entry point.

    Currently delegates to the `reflex` CLI. In Phase 6 this will be replaced
    with a `typer`-based CLI for the user-facing `reflex-openbb` commands.
    """
    # Lazy import keeps `app` importable without reflex's runtime deps
    # (e.g. for unit tests that import `app` but never run it).
    from reflex.reflex import cli

    cli()
