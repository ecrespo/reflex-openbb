"""The Reflex app entry point.

T-005 stub: a minimal app with the home page.

Usage:
    uv run reflex-openbb           # uses `main()` as the console script
    uv run reflex run              # uses `app` directly via the reflex CLI

The console script declared in pyproject.toml points to `main()`.
"""

import reflex as rx

from reflex_openbb.pages import home


def index() -> rx.Component:
    """Wrapper around `home.index` for the console-script entry point.

    Keeping the page function here means the `reflex run` CLI (which expects
    a callable named `index` in the app module) finds it without further config.
    """
    return home.index()


# Build the app. The `app` is a module-level `rx.App` so that `reflex run`
# (which introspects the module to find an `app` symbol) can find it.
app = rx.App()
app.add_page(index, route="/")
# Placeholder route for Phase 3 (T-307). Removed once the equity page exists.
app.add_page(index, route="/equity/[ticker]")


def main() -> None:
    """Console-script entry point.

    Currently delegates to the `reflex` CLI. In Phase 6 this will be replaced
    with a `typer`-based CLI for the user-facing `reflex-openbb` commands.
    """
    # Lazy import keeps `app` importable without reflex's runtime deps
    # (e.g. for unit tests that import `app` but never run it).
    from reflex.reflex import cli

    cli()
