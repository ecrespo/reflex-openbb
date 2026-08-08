"""The Reflex app entry point.

T-005 + T-307: minimal app with home + equity routes.

Usage:
    uv run reflex-openbb           # uses `main()` as the console script
    uv run reflex run              # uses `app` directly via the reflex CLI

The console script declared in pyproject.toml points to `main()`.
"""

import reflex as rx

from reflex_openbb.pages import equity, home


def index() -> rx.Component:
    """Wrapper around `home.index` for the console-script entry point.

    Keeping the page function here means the `reflex run` CLI (which expects
    a callable named `index` in the app module) finds it without further config.
    """
    return home.index()


def equity_route() -> rx.Component:
    """The /equity/[ticker] page (T-307)."""
    return equity.equity_page()


# Build the app. The `app` is a module-level `rx.App` so that `reflex run`
# (which introspects the module to find an `app` symbol) can find it.
app = rx.App()
app.add_page(index, route="/")
# The route param is `[symbol]` to avoid shadowing EquityState.ticker
# (reflex raises DynamicRouteArgShadowsStateVarError otherwise).
app.add_page(equity_route, route="/equity/[symbol]")


def main() -> None:
    """Console-script entry point.

    Currently delegates to the `reflex` CLI. In Phase 6 this will be replaced
    with a `typer`-based CLI for the user-facing `reflex-openbb` commands.
    """
    # Lazy import keeps `app` importable without reflex's runtime deps
    # (e.g. for unit tests that import `app` but never run it).
    from reflex.reflex import cli

    cli()
