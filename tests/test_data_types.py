"""
Tests for the Pydantic data models (T-104).

TDD: this file is written BEFORE data/data_types.py.
The tests must FAIL initially, then pass after implementation.

REQs:
- specs/data-model/v1-models.md: 6 Pydantic models
- Constitution Art. 5: monetary fields are Decimal, NEVER float
- Constitution Art. 4: tests cite the REQ
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from reflex_openbb.data import errors as data_errors
from reflex_openbb.data import types as data_types

# ─── Domain / smoke tests ───────────────────────────────────────────────────


def test_types_module_imports() -> None:
    """The data.types module must export the 6 Pydantic models."""
    expected = {
        "EquityQuote",
        "OHLCBar",
        "EquityFundamentals",
        "NewsItem",
        "MacroPoint",
        "SearchResult",
    }
    for name in expected:
        assert hasattr(data_types, name), f"Missing model: {name}"


def test_error_models_imported() -> None:
    """The data.types module must also export the 2 error models."""
    assert hasattr(data_errors, "InvalidTickerError")
    assert hasattr(data_errors, "ProviderError")


# ─── Art. 5: NO float in monetary fields ────────────────────────────────────


def test_no_float_in_monetary_fields() -> None:
    """Constitution Art. 5: monetary / ratio / percentage fields MUST be Decimal.

    REQ: Art. 5 ("THE SYSTEM SHALL represent monetary values as `Decimal`").
    This is a meta-test: introspect all Pydantic models and assert no
    monetary-named field is annotated as `float`.
    """
    from typing import get_type_hints

    # The fields that must be Decimal (or Optional[Decimal])
    monetary_field_names = {
        # EquityQuote
        "price",
        "day_change_pct",
        "market_cap",
        "fifty_two_week_high",
        "fifty_two_week_low",
        # EquityFundamentals
        "pe_ratio",
        "eps",
        "dividend_yield",
        "beta",
        "book_value_per_share",
        "price_to_book",
        "roe",
        # MacroPoint
        "value",
    }

    models = [
        data_types.EquityQuote,
        data_types.EquityFundamentals,
        data_types.NewsItem,
        data_types.OHLCBar,
        data_types.MacroPoint,
        data_types.SearchResult,
    ]

    for model in models:
        hints = get_type_hints(model)
        for field_name, field_type in hints.items():
            if field_name not in monetary_field_names:
                continue
            # The field type must be Decimal (or Optional/Union with Decimal)
            type_str = str(field_type)
            assert "Decimal" in type_str, (
                f"{model.__name__}.{field_name} is {field_type}, must be Decimal. "
                f"Constitution Art. 5 violation."
            )
            assert "float" not in type_str, (
                f"{model.__name__}.{field_name} contains 'float' in type: {field_type}. "
                f"Constitution Art. 5 violation."
            )


# ─── EquityQuote ────────────────────────────────────────────────────────────


class TestEquityQuote:
    """Tests for the EquityQuote model. REQ: REQ-005 (KPI cards)."""

    def test_minimal_quote(self) -> None:
        q = data_types.EquityQuote(
            ticker="AAPL",
            price=Decimal("150.25"),
            day_change_pct=Decimal("1.5"),
            market_cap=Decimal("2500000000000"),
            volume=50_000_000,
            fifty_two_week_high=Decimal("199.62"),
            fifty_two_week_low=Decimal("124.17"),
            fetched_at=datetime.now(timezone.utc),
            provider="yfinance",
        )
        assert q.ticker == "AAPL"
        assert q.price == Decimal("150.25")
        assert q.volume == 50_000_000

    def test_market_cap_can_be_none(self) -> None:
        """REQ: data-model §EquityQuote — `market_cap` is Optional."""
        q = data_types.EquityQuote(
            ticker="AAPL",
            price=Decimal("150.25"),
            day_change_pct=Decimal("1.5"),
            market_cap=None,
            volume=0,
            fifty_two_week_high=Decimal("199.62"),
            fifty_two_week_low=Decimal("124.17"),
            fetched_at=datetime.now(timezone.utc),
            provider="yfinance",
        )
        assert q.market_cap is None

    def test_price_coerces_from_int(self) -> None:
        """REQ: Art. 5 — even int inputs become Decimal (not float)."""
        q = data_types.EquityQuote(
            ticker="AAPL",
            price=150,  # int, not Decimal
            day_change_pct=2,  # int
            market_cap=2_500_000_000_000,
            volume=0,
            fifty_two_week_high=200,
            fifty_two_week_low=100,
            fetched_at=datetime.now(timezone.utc),
            provider="yfinance",
        )
        assert isinstance(q.price, Decimal)
        assert q.price == Decimal("150")

    def test_price_coerces_from_str(self) -> None:
        """REQ: Art. 5 — strings also coerce to Decimal (the safe path)."""
        q = data_types.EquityQuote(
            ticker="AAPL",
            price="150.25",
            day_change_pct="-1.5",
            market_cap="2500000000000",
            volume=0,
            fifty_two_week_high="199.62",
            fifty_two_week_low="124.17",
            fetched_at=datetime.now(timezone.utc),
            provider="yfinance",
        )
        assert isinstance(q.price, Decimal)
        assert q.price == Decimal("150.25")
        assert q.day_change_pct == Decimal("-1.5")

    def test_price_rejects_non_numeric(self) -> None:
        with pytest.raises(ValidationError):
            data_types.EquityQuote(
                ticker="AAPL",
                price="not-a-number",  # type: ignore[arg-type]
                day_change_pct=Decimal("1.5"),
                market_cap=None,
                volume=0,
                fifty_two_week_high=Decimal("199.62"),
                fifty_two_week_low=Decimal("124.17"),
                fetched_at=datetime.now(timezone.utc),
                provider="yfinance",
            )


# ─── OHLCBar ────────────────────────────────────────────────────────────────


class TestOHLCBar:
    """Tests for the OHLCBar model. REQ: REQ-001 (Equity price chart)."""

    def test_bar_minimal(self) -> None:
        bar = data_types.OHLCBar(
            date=date(2024, 1, 15),
            open=Decimal("150.00"),
            high=Decimal("152.00"),
            low=Decimal("149.50"),
            close=Decimal("151.25"),
            volume=10_000_000,
        )
        assert bar.date == date(2024, 1, 15)
        assert bar.close == Decimal("151.25")

    def test_bar_all_decimal(self) -> None:
        """REQ: Art. 5 — all price fields are Decimal."""
        bar = data_types.OHLCBar(
            date=date(2024, 1, 15),
            open="150.00",
            high="152.00",
            low="149.50",
            close="151.25",
            volume=10_000_000,
        )
        assert isinstance(bar.open, Decimal)
        assert isinstance(bar.high, Decimal)
        assert isinstance(bar.low, Decimal)
        assert isinstance(bar.close, Decimal)


# ─── EquityFundamentals ────────────────────────────────────────────────────


class TestEquityFundamentals:
    """Tests for EquityFundamentals. REQ: REQ-003 (Fundamentals table)."""

    def test_fundamentals_all_optional(self) -> None:
        """REQ: data-model §EquityFundamentals — every metric is Optional.

        Validators must handle n/a from the provider gracefully.
        """
        f = data_types.EquityFundamentals(
            ticker="AAPL",
            pe_ratio=None,
            eps=None,
            dividend_yield=None,
            beta=None,
            book_value_per_share=None,
            price_to_book=None,
            roe=None,
            fetched_at=datetime.now(timezone.utc),
            provider="yfinance",
        )
        assert f.pe_ratio is None
        assert f.eps is None

    def test_fundamentals_partial(self) -> None:
        f = data_types.EquityFundamentals(
            ticker="AAPL",
            pe_ratio=Decimal("28.5"),
            eps=Decimal("6.05"),
            dividend_yield=Decimal("0.5"),
            beta=None,  # missing
            book_value_per_share=None,
            price_to_book=None,
            roe=None,
            fetched_at=datetime.now(timezone.utc),
            provider="yfinance",
        )
        assert f.pe_ratio == Decimal("28.5")
        assert f.beta is None


# ─── NewsItem ───────────────────────────────────────────────────────────────


class TestNewsItem:
    """Tests for NewsItem. REQ: REQ-004 (News feed)."""

    def test_news_minimal(self) -> None:
        n = data_types.NewsItem(
            id="abc123",
            title="Apple announces new product",
            source="Reuters",
            url="https://reuters.com/article/123",
            published_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        )
        assert n.id == "abc123"
        assert n.title == "Apple announces new product"

    def test_news_summary_optional(self) -> None:
        n = data_types.NewsItem(
            id="x",
            title="Title",
            source="Source",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
            summary=None,
        )
        assert n.summary is None


# ─── MacroPoint ────────────────────────────────────────────────────────────


class TestMacroPoint:
    """Tests for MacroPoint. REQ: REQ-007 (Economy dashboard)."""

    def test_macro_point(self) -> None:
        m = data_types.MacroPoint(
            year=2024,
            value=Decimal("2.5"),
            country="US",
            indicator="GDP",
        )
        assert m.year == 2024
        assert m.value == Decimal("2.5")
        assert m.country == "US"


# ─── SearchResult ──────────────────────────────────────────────────────────


class TestSearchResult:
    """Tests for SearchResult. REQ: REQ-010 (Search)."""

    def test_search_equity_match(self) -> None:
        s = data_types.SearchResult(
            query="AAPL",
            equity_match="AAPL",
            crypto_match=None,
            confidence=0.95,
        )
        assert s.equity_match == "AAPL"
        assert s.confidence == 0.95

    def test_search_crypto_match(self) -> None:
        s = data_types.SearchResult(
            query="BTC",
            equity_match=None,
            crypto_match="BTC",
            confidence=0.98,
        )
        assert s.crypto_match == "BTC"

    def test_search_no_match(self) -> None:
        s = data_types.SearchResult(
            query="XYZNOTHING",
            equity_match=None,
            crypto_match=None,
            confidence=0.0,
        )
        assert s.equity_match is None
        assert s.crypto_match is None


# ─── Error models ──────────────────────────────────────────────────────────


class TestErrorModels:
    """Tests for the 2 error models. REQ: api/v1.md §Error model."""

    def test_invalid_ticker_error(self) -> None:
        from reflex_openbb.data.errors import InvalidTickerError

        e = InvalidTickerError("XYZ", "too_long")
        assert e.ticker == "XYZ"
        assert e.reason == "too_long"
        assert str(e)  # non-empty

    def test_provider_error(self) -> None:
        from reflex_openbb.data.errors import ProviderError

        e = ProviderError(
            provider="yfinance",
            status_code=429,
            retry_after=60,
            original="rate limited",
        )
        assert e.provider == "yfinance"
        assert e.status_code == 429
        assert e.retry_after == 60
        assert e.original == "rate limited"
