# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-08-08

### Added

**Phase 0 — Repo scaffold**
- T-001..T-005: project structure, pyproject.toml, README stub, Reflex app

**Phase 1 — Data layer (T-101..T-108)**
- T-101: TTL cache (`data/cache.py`)
- T-102: Rate limiter (`data/rate_limiter.py`)
- T-103: Circuit breaker (`data/circuit_breaker.py`)
- T-104: Pydantic types (`data/types.py`) — EquityQuote, OHLCBar,
  EquityFundamentals, NewsItem, MacroPoint
- T-105: Equity data functions (`data/equity.py`) — get_equity_quote,
  get_equity_price_history, get_equity_fundamentals, get_equity_news
- T-106: Crypto data functions (`data/crypto.py`) — get_crypto_price_history
- T-107: Economy data functions (`data/economy.py`) — get_macro_series
- T-108: Local search (`data/search.py`) — equity + crypto dictionaries

**Phase 2 — State layer (T-201..T-206)**
- T-201: `AppState` (global_search) — REQ-010
- T-202: `EquityState` (set_ticker, set_period) — REQ-001..005
- T-203: `CryptoState` (set_symbol) — REQ-006
- T-204: `EconomyState` (set_indicator, set_country) — REQ-007
- T-205: State coverage audit (28 tests)
- T-206: State re-render tests (13 tests)

**Phase 3 — Equity page (T-301..T-307)**
- T-301: `price_chart` component (rx.recharts.LineChart + comparison)
- T-302: `date_range` component (5 period buttons)
- T-303: `kpi_grid` component (6 KPI cards)
- T-304: `fundamentals_table` component
- T-305: `news_feed` component
- T-306: `equity_page` composition
- T-307: Wire `/equity` route

**Phase 4 — Crypto + Economy pages (T-401..T-408)**
- T-401: `crypto_chart` component
- T-402: `crypto_page` composition
- T-403: Wire `/crypto` route
- T-405: `economy_chart` component (rx.recharts.BarChart)
- T-406: `economy_selector` component (2 selects)
- T-407: `economy_page` composition
- T-408: Wire `/economy` route

**Phase 5 — Search + CSV + Multi-ticker (T-501..T-507)**
- T-501: `search_box` component
- T-502: Wire global_search in home page
- T-503: `csv_export` service (to_csv_bars, to_csv_macro)
- T-504: `export_button` component
- T-505: `export_csv` handler in EquityState + CryptoState
- T-506: `comparison_controls` component
- T-507: Wire comparison in price_chart

**Phase 6 — Polish + docs (T-601..T-605)**
- T-601: Full README with install, quickstart, features
- T-602: CHANGELOG.md (this file)
- T-603: LICENSE (Apache-2.0)
- T-604: CONTRIBUTING.md
- T-605: docs/ directory with spec index

### Test results

```
297 tests total:
  271 verde (passing)
  3 xfailed (rx.State handlers — validated via 'reflex run')
  23 xpassed (handlers that work in tests; kept xfail for consistency)

Ruff: clean
```

### Notes

- Routes are static (`/equity`, `/crypto`, `/economy`). Dynamic route
  args would conflict with state var names.
- Tickers/symbols are passed via the form input on the page, not via
  the URL.

[0.1.0]: https://github.com/ecrespo/reflex-openbb/releases/tag/v0.1.0
