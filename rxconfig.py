"""Reflex configuration for reflex-openbb.

This file is required by `reflex run` to find the app entry point.
It points to src/reflex_openbb/app.py where the rx.App lives.

The `config` symbol must be an instance of `reflex.config.Config`.
"""

import os
import sys

# Add src/ to sys.path so `reflex_openbb` is importable without installing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import reflex as rx

# The Reflex config is a module-level `config = rx.Config(...)` instance.
# Reflex auto-discovers it when run from the project root.
config = rx.Config(
    app_name="reflex_openbb",
    # The module that defines the rx.App (as `app`).
    app_module_import="reflex_openbb.app",
)
