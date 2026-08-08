# Implementation Plan — reflex-openbb v1.0

> Status: `DRAFT` · Date: 2026-08-08 · Owner: Ernesto Crespo
> Implements: PRD + Tech Design + Data Model for v1.0
> Estimated total: 14 days

This plan is split into **phases**. Each phase ends with a working, demoable artifact. The plan is **dependency-ordered**: later phases depend on earlier ones.

## Phase 0 — Repo scaffold (1 day)

**Goal:** An empty Reflex app that starts and shows a "Hello, reflex-openbb" page.

**Tasks:**
- T-001: Create repo `ecrespo/reflex-openbb` (GitHub)
- T-002: Write `pyproject.toml` with deps (reflex, openbb, cachetools, pydantic)
- T-003: Create the module structure from `technical/v1-architecture.md` §2
- T-004: Configure pre-commit (Ruff, ty, Bandit, Gitleaks)
- T-005: Write a stub `app.py` with a single page that prints "reflex-openbb"
- T-006: Verify `reflex run` works locally
- T-007: Add `LICENSE` (Apache-2.0)
- T-008: Add `README.md` skeleton
- T-009: First GitHub Actions workflow (lint + type-check on push)

**Done when:** `git clone ... && pip install -e . && reflex run` shows the stub page.

## Phase 1 — Data layer (2 days)

**Goal:** The `data/` module is fully implemented and unit-tested, but no UI consumes it yet.

**Tasks:**
- T-101: Implement `data/cache.py` (TTLCache wrapper)
- T-102: Implement `data/rate_limiter.py` (TokenBucket)
- T-103: Implement `data/circuit_breaker.py` (per-provider)
- T-104: Define Pydantic models in `data/types.py` (or split by module)
- T-105: Implement `data/equity.py`: `get_equity_quote`, `get_equity_price_history`, `get_equity_fundamentals`, `get_equity_news`
- T-106: Implement `data/crypto.py`: `get_crypto_price_history`
- T-107: Implement `data/economy.py`: `get_economy_indicator`
- T-108: Implement `data/search.py`: `search`
- T-109: Unit tests for each function (with mocked OpenBB SDK)
- T-110: Integration test: real OpenBB SDK call to `/equity/AAPL` (recorded as a `pytest` fixture, not a CI test)
- T-111: Verify Decimal coercion works (Art. 5): no `float` in any output
- T-112: Verify the rate limiter holds under load (artificial 100-call burst)

**Done when:** `pytest tests/test_data_*.py` passes; manual call to `get_equity_price_history("AAPL", "1y")` returns ≥ 200 bars as `list[OHLCBar]`.

## Phase 2 — State layer (1 day)

**Goal:** The state classes exist and are wired to the data layer.

**Tasks:**
- T-201: `state/app_state.py` with `AppState` and `global_search` event handler
- T-202: `state/equity_state.py` with `EquityState` (REQ-001..005)
- T-203: `state/crypto_state.py` with `CryptoState` (REQ-006)
- T-204: `state/economy_state.py` with `EconomyState` (REQ-007)
- T-205: Unit tests for state event handlers (with mocked data layer)
- T-206: Verify that state changes trigger re-render of computed vars

**Done when:** A state class can be instantiated, an event handler can be called, and the state updates are reflected in `@rx.var` properties.

## Phase 3 — Equity page (3 days)

**Goal:** The `/equity/{ticker}` page is fully functional and looks good.

**Tasks:**
- T-301: `components/price_chart.py` (uses `reflex-rosencharts`)
- T-302: `components/date_range.py` (1M/6M/1Y/5Y/Max buttons)
- T-303: `components/kpi_grid.py` (6 KPI cards)
- T-304: `components/fundamentals_table.py` (uses `rx.table`)
- T-305: `components/news_feed.py` (uses `rx.card`)
- T-306: `pages/equity.py` — composes the components with `EquityState`
- T-307: Wire dynamic route `/equity/[ticker]` in `app.py`
- T-308: Manual QA: navigate to `/equity/AAPL`, `/equity/MSFT`, `/equity/TSLA` — all render correctly
- T-309: Manual QA: switch date ranges — chart updates within budget (NFR-001)
- T-310: Manual QA: trigger a 429 from the provider (use `OPENBB_PAT` override or a low-rate-limit config) and verify the stale-data banner appears (REQ-001 UW)

**Done when:** All REQ-001..005 are manually verified. Screenshots saved to `docs/screenshots/`.

## Phase 4 — Crypto and Economy pages (2 days)

**Goal:** Two more pages, same pattern as Phase 3.

**Tasks:**
- T-401: `components/crypto_chart.py` (line chart, same as price chart)
- T-402: `pages/crypto.py`
- T-403: Wire `/crypto/[symbol]`
- T-404: Manual QA: `/crypto/BTC`, `/crypto/ETH`
- T-405: `components/economy_chart.py` (multi-series line chart for indicator)
- T-406: `components/economy_selector.py` (country + indicator dropdowns)
- T-407: `pages/economy.py`
- T-408: Wire `/economy`
- T-409: Manual QA: `/economy`, switch between GDP / CPI / UNRATE, switch between US / VE / AR
- T-410: Take screenshots for all three pages

**Done when:** All three pages render correctly. REQ-006 and REQ-007 verified.

## Phase 5 — Search, CSV export, multi-ticker (2 days)

**Goal:** The power features work.

**Tasks:**
- T-501: `components/search_box.py` (global search)
- T-502: Wire `global_search` from `AppState` to navigate (REQ-010)
- T-503: `services/csv_export.py`
- T-504: `components/export_button.py` (uses `rx.download`)
- T-505: Wire export button on each page (REQ-008)
- T-506: `components/comparison_controls.py` (add/remove tickers)
- T-507: Wire comparison into `price_chart.py` (multiple series)
- T-508: Manual QA: add 2-5 tickers to comparison, verify overlay works (REQ-009)
- T-509: Manual QA: attempt to add 6th ticker, verify rejection (REQ-009 UW)
- T-510: Manual QA: download CSV from each page, open in spreadsheet, verify columns

**Done when:** All of REQ-008, REQ-009, REQ-010 verified.

## Phase 6 — Polish, docs, release (2 days)

**Goal:** A release-quality v1.0.0.

**Tasks:**
- T-601: README.md with install, quickstart, screenshots, and the "Why this exists" section
- T-602: docs/quickstart.md
- T-603: docs/architecture.md (a stripped-down version of the Tech Design)
- T-604: docs/screenshots/ for all three pages
- T-605: Add `CHANGELOG.md`
- T-606: Set up the `reflex-openbb-ui` wrapper package (the custom components — see Phase 6a below)
- T-607: Tag v0.1.0
- T-608: Publish to PyPI
- T-609: Write a release post (Reddit r/Python, HackerNews, etc.)
- T-610: Set up `dependabot` to track OpenBB and Reflex versions

### Phase 6a — `reflex-openbb-ui` custom components (parallel, optional for v1)

**Goal:** If the three pages need any custom component not in the existing catalog (e.g., a specific candlestick variant), create them as standalone packages.

**Tasks:**
- T-6a-001: Decide which new components are needed (probably none in v1; reuse `reflex-rosencharts` and `reflex-tanstack-charts`)
- T-6a-002: If needed, scaffold new components with the `ecrespo-reflex-custom-components` skill
- T-6a-003: Publish as `reflex-openbb-ui` v0.1.0

## Dependency graph

```
Phase 0  →  Phase 1  →  Phase 2  →  Phase 3  →  Phase 5
                          │         │
                          └→  Phase 4  →  ┘
                                              │
                                              ↓
                                           Phase 6
                                              ↓
                                           Phase 6a (parallel)
```

## Risks specific to implementation

| Risk | Mitigation |
|---|---|
| OpenBB SDK call signature changes mid-implementation | Pin exact version in pyproject; subscribe to OpenBB releases during the 14 days |
| Custom component is incompatible with the latest Reflex | Run `reflex run` after every dep upgrade; pin Reflex in pyproject |
| A free provider goes down | The data layer falls back to cache; the circuit breaker kicks in; users can configure `OPENBB_PAT` for a paid alternative |

## Rollback plan

Each phase is in a separate git branch and PR. If a phase fails acceptance, the previous phase's main is still shippable. There is no "all or nothing" release.

## Constitution check

- **Art. 9 (pre-commit):** pre-commit is configured in Phase 0 and gates every commit. ✅
- **Art. 6 (cache):** Phase 1 includes cache implementation. ✅
- **Art. 5 (Decimal):** Phase 1 includes a verification test (T-111). ✅
- **Art. 8 (component-first):** every Phase 3/4 task is one component file. ✅
- **Art. 2 (Reuse catalog):** Phase 3 task T-301 explicitly uses `reflex-rosencharts`; Phase 6a is only for new components, not duplicates. ✅

No exceptions.
