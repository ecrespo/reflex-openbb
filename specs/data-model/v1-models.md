# Data Model — reflex-openbb v1.0

> Status: `DRAFT` · Date: 2026-08-08 · Owner: Ernesto Crespo
> Implements: API Spec `v1.md` + PRD REQ-001..010

All monetary values are `Decimal`, never `float` (Constitution Art. 5).
All timestamps are `datetime` in UTC.

## Pydantic models

### `EquityQuote`

| Field | Type | Required | Notes |
|---|---|---|---|
| `ticker` | str | yes | uppercase, validated against `^[A-Z][A-Z0-9.\-]{0,9}$` |
| `price` | Decimal | yes | current/latest price |
| `day_change_pct` | Decimal | yes | signed, e.g. -1.23 means -1.23% |
| `market_cap` | Decimal \| None | no | null if not provided by source |
| `volume` | int | yes | shares traded today |
| `fifty_two_week_high` | Decimal | yes | |
| `fifty_two_week_low` | Decimal | yes | |
| `fetched_at` | datetime | yes | UTC |
| `provider` | str | yes | e.g. "yfinance" |

### `OHLCBar`

| Field | Type | Required | Notes |
|---|---|---|---|
| `date` | date | yes | trading day (no time) |
| `open` | Decimal | yes | |
| `high` | Decimal | yes | |
| `low` | Decimal | yes | |
| `close` | Decimal | yes | used by the line chart |
| `volume` | int | yes | |

Indexes / constraints:
- `OHLCBar` lists are always sorted by `date` ascending
- The `date` field is unique within a ticker (no duplicate bars)

### `EquityFundamentals`

| Field | Type | Required | Notes |
|---|---|---|---|
| `ticker` | str | yes | |
| `pe_ratio` | Decimal \| None | no | n/a if provider doesn't return |
| `eps` | Decimal \| None | no | |
| `dividend_yield` | Decimal \| None | no | as a percentage, e.g. 1.23 = 1.23% |
| `beta` | Decimal \| None | no | |
| `book_value_per_share` | Decimal \| None | no | |
| `price_to_book` | Decimal \| None | no | |
| `roe` | Decimal \| None | no | return on equity, % |
| `fetched_at` | datetime | yes | UTC |
| `provider` | str | yes | |

Validation rule: any monetary field is `Decimal`; any "n/a" is `None` (NOT 0 or ""). The UI displays "n/a" for `None` (REQ-003 O-where).

### `NewsItem`

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | str | yes | provider-specific, may not be unique across providers |
| `title` | str | yes | |
| `source` | str | yes | e.g. "Reuters" |
| `url` | str | yes | must be a valid http(s) URL |
| `published_at` | datetime | yes | UTC |
| `summary` | str \| None | no | first paragraph or snippet |

Sorted descending by `published_at`.

### `MacroPoint`

| Field | Type | Required | Notes |
|---|---|---|---|
| `year` | int | yes | e.g. 2024 |
| `value` | Decimal | yes | the indicator value (e.g. GDP in trillions USD, CPI as index) |
| `country` | str | yes | ISO-3166 alpha-2 |
| `indicator` | str | yes | one of: GDP, CPI, UNRATE |

### `SearchResult`

| Field | Type | Required | Notes |
|---|---|---|---|
| `query` | str | yes | the original input |
| `equity_match` | str \| None | no | e.g. "AAPL" |
| `crypto_match` | str \| None | no | e.g. "BTC" |
| `confidence` | float | yes | 0.0..1.0 |

The search resolver tries equity first; if no match, tries crypto. If both, it picks the higher confidence.

## Error models

### `InvalidTickerError(ValueError)`
- `ticker: str`
- `reason: str` (e.g. "empty", "invalid_chars", "too_long")

### `ProviderError(RuntimeError)`
- `provider: str` (e.g. "yfinance", "fred")
- `status_code: int | None`
- `retry_after: int | None` (seconds, from 429 response)
- `original: str` (raw error message)

## Caching (in-process)

| Cache name | Key format | TTL | Max size |
|---|---|---|---|
| `quote` | `quote:{ticker}` | 300s (5 min) | 10,000 |
| `price` | `price:{ticker}:{period}` | 300s for 1mo/6mo/1y; 86400s for 5y/max | 5,000 |
| `fundamentals` | `fund:{ticker}` | 86400s (1 day) | 5,000 |
| `news` | `news:{ticker}` | 900s (15 min) | 2,000 |
| `macro` | `macro:{country}:{indicator}` | 604800s (7 days) | 500 |

Cache is in-memory only (no Redis, no SQLite). When the process exits, the cache is lost — this is acceptable for a single-user local app.

## Schema migrations

There is no persistent database in v1. The Pydantic models ARE the schema. Any breaking change to a model requires:
1. A new field with a default value (preferred — backward-compatible)
2. OR a major version bump on the `reflex-openbb-ui` package

## Constitution check

- **Art. 5 (Decimal):** every monetary / ratio / percentage field is `Decimal`. ✅
- **Art. 6 (cache):** TTL defined for every domain. ✅
- **Art. 8 (component-first):** each model lives in the data layer module for its feature (`data/equity.py`, etc.). ✅

No exceptions.
