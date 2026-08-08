"""
T-006 integration tests: verify the data layer against the real OpenBB SDK.

These tests use the live SDK (yfinance + econdb) — they are slow
(several seconds per test) and require network. They were added in
T-006 to catch bugs that the mock-based unit tests miss.

Run with: uv run pytest tests/test_data_integration.py -v
or:        uv run pytest tests/ -m integration -v
"""

from __future__ import annotations

import asyncio

import pytest

# ─── Equity ────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_get_equity_quote_msft() -> None:
    """REQ-005: equity.price.quote should return an EquityQuote with a price."""
    from reflex_openbb.data.equity import get_equity_quote

    q = asyncio.run(get_equity_quote("MSFT"))
    assert q.ticker == "MSFT"
    assert q.price > 0
    assert q.day_change_pct is not None


@pytest.mark.integration
def test_get_equity_price_history_msft() -> None:
    """REQ-001, REQ-002: equity.price.historical returns a list of OHLCBars."""
    from reflex_openbb.data.equity import get_equity_price_history

    bars = asyncio.run(get_equity_price_history("MSFT", "1mo"))
    assert len(bars) > 0
    assert all(b.close > 0 for b in bars)
    assert all(b.volume >= 0 for b in bars)


@pytest.mark.integration
def test_get_equity_fundamentals_msft() -> None:
    """REQ-003: equity.fundamental.metrics returns EquityFundamentals."""
    from reflex_openbb.data.equity import get_equity_fundamentals

    f = asyncio.run(get_equity_fundamentals("MSFT"))
    assert f.ticker == "MSFT"
    # beta should be present for yfinance
    assert f.beta is not None


@pytest.mark.integration
def test_get_equity_news_msft() -> None:
    """REQ-004: news.company returns a list of NewsItem."""
    from reflex_openbb.data.equity import get_equity_news

    news = asyncio.run(get_equity_news("MSFT"))
    assert isinstance(news, list)
    if news:  # May be empty
        assert news[0].title
        assert news[0].url
        assert news[0].published_at


# ─── Crypto ────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_get_crypto_price_history_btc() -> None:
    """REQ-006: crypto.price.historical returns OHLCBars for BTC."""
    from reflex_openbb.data.crypto import get_crypto_price_history

    bars = asyncio.run(get_crypto_price_history("BTC"))
    assert len(bars) > 0
    assert all(b.close > 0 for b in bars)


# ─── Economy ───────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_get_economy_indicator_gdp_us() -> None:
    """REQ-007: economy.indicators returns MacroPoints for GDP/US."""
    from reflex_openbb.data.economy import get_economy_indicator

    points = asyncio.run(get_economy_indicator("GDP", "US"))
    assert len(points) > 0
    assert all(p.value is not None for p in points)
    assert points[0].country == "US"


@pytest.mark.integration
def test_get_economy_indicator_cpi_us() -> None:
    """REQ-007: CPI for US should return MacroPoints."""
    from reflex_openbb.data.economy import get_economy_indicator

    points = asyncio.run(get_economy_indicator("CPI", "US"))
    assert isinstance(points, list)
