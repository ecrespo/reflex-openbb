"""
Tests for the crypto page (T-402).

REQ: REQ-006

pages/crypto.crypto_page() — composes crypto_chart with CryptoState.
"""

from __future__ import annotations


def test_crypto_page_module_imports() -> None:
    from reflex_openbb.pages import crypto as m

    assert hasattr(m, "crypto_page"), "crypto_page function should live in pages.crypto"
