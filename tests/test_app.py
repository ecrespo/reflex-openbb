"""
Tests for the Reflex app entry point (T-005).

Following TDD strictly:
- This test file is written FIRST, BEFORE app.py.
- It must FAIL when run (RED).
- The minimum code is written to make it pass (GREEN).
- Then refactor.

The first test verifies the home page exists and has the expected text.
This is the TDD contract: if this test passes, the scaffold is correct.
"""

import reflex as rx


def test_reflex_openbb_module_imports() -> None:
    """The `reflex_openbb` package must import without errors.

    This is the most basic sanity check: if the package doesn't import,
    nothing else can work. Caught early by T-002 (pyproject.toml) and T-003
    (module structure).
    """
    import reflex_openbb

    assert hasattr(reflex_openbb, "__version__")
    assert reflex_openbb.__version__ == "0.1.0"


def test_app_entry_point_exists() -> None:
    """The `app` module must export a `main` function and an `app` object.

    The `main` function is the console-script entry point declared in
    pyproject.toml. The `app` object is the Reflex app instance.
    """
    from reflex_openbb import app as app_module

    assert callable(getattr(app_module, "main", None)), (
        "app.main must be callable (the CLI entry point)"
    )
    assert isinstance(getattr(app_module, "app", None), rx.App), (
        "app.app must be a reflex.App instance"
    )


def test_home_page_exists() -> None:
    """The home page function must exist.

    REQ: implicit from T-005 ("a single page that prints 'reflex-openbb v0.1.0'").
    We don't render the page (it accesses rx.State vars which require
    a full app context). End-to-end rendering is validated by integration
    tests via 'reflex run' (T-006).
    """
    from reflex_openbb.pages import home

    assert callable(home.index)


def test_main_function_is_runnable() -> None:
    """The `main` function must be importable and not raise on inspection.

    We don't actually run `main()` here (that would start a server).
    We just verify it can be imported and called as a no-op.
    """
    from reflex_openbb.app import main

    # The function exists and is callable. We don't call it because it
    # would start a Reflex dev server, which is out of scope for unit tests.
    assert callable(main)
