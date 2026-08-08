"""
Tests for fundamentals_table and news_feed (T-304, T-305).
"""

from __future__ import annotations

import reflex as rx

from reflex_openbb.components.fundamentals_table import fundamentals_table
from reflex_openbb.components.news_feed import news_feed

# ─── fundamentals_table (T-304) ────────────────────────────────────────────


def test_fundamentals_table_module_imports() -> None:
    from reflex_openbb.components import fundamentals_table as m

    assert hasattr(m, "fundamentals_table")


def test_fundamentals_table_returns_component_with_data() -> None:
    from datetime import datetime, timezone
    from decimal import Decimal

    from reflex_openbb.data.types import EquityFundamentals

    fund = EquityFundamentals(
        ticker="AAPL",
        pe_ratio=Decimal("28.5"),
        eps=Decimal("6.05"),
        dividend_yield=Decimal("0.5"),
        beta=Decimal("1.2"),
        book_value_per_share=None,
        price_to_book=None,
        roe=None,
        fetched_at=datetime.now(timezone.utc),
        provider="yfinance",
    )
    result = fundamentals_table(fund)
    assert isinstance(result, rx.Component)


def test_fundamentals_table_returns_component_when_none() -> None:
    result = fundamentals_table(None)
    assert isinstance(result, rx.Component)


# ─── news_feed (T-305) ─────────────────────────────────────────────────────


def test_news_feed_module_imports() -> None:
    from reflex_openbb.components import news_feed as m

    assert hasattr(m, "news_feed")


def test_news_feed_returns_component_with_data() -> None:
    from datetime import datetime, timezone

    from reflex_openbb.data.types import NewsItem

    news = [
        NewsItem(
            id="n1",
            title="Apple beats Q4",
            source="Reuters",
            url="https://x.com/1",
            published_at=datetime.now(timezone.utc),
        )
    ]
    result = news_feed(news)
    assert isinstance(result, rx.Component)


def test_news_feed_shows_placeholder_when_empty() -> None:
    """REQ-004 O-where: 'No recent news' if empty."""
    result = news_feed([])
    rendered = str(result)
    assert "no recent news" in rendered.lower() or "no news" in rendered.lower()
