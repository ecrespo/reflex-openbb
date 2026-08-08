# Tasks — reflex-openbb v1.0

> Generated from `plans/v1-phase-plan.md`
> Each task cites the REQ it implements. **[P] = parallelizable with the previous task in the same phase.**

## Phase 0 — Repo scaffold

### T-001: Create the GitHub repo
- **REQ:** (none — infrastructure)
- **Acceptance:** `gh repo create ecrespo/reflex-openbb --public --description "Open-source OpenBB UI in pure Python (Reflex)"` succeeds
- **Files:** none
- **Verify:** `gh repo view ecrespo/reflex-openbb` returns the new repo
- **Estimate:** 5 min

### T-002: Write pyproject.toml
- **REQ:** Art. 9 (pre-commit gate), Art. 5 (Decimal type in deps if needed)
- **Acceptance:** `pyproject.toml` exists with `[project]` name=`reflex-openbb`, deps `reflex>=0.8,<0.9`, `openbb>=4.0,<5.0`, `cachetools>=5.0`, `pydantic>=2.0`, dev-deps `pytest`, `pytest-asyncio`, `ruff`, `ty`, `bandit`, `pre-commit`
- **Files:** `pyproject.toml`
- **Verify:** `pip install -e .` succeeds in a fresh venv
- **Estimate:** 15 min

### T-003: Create the module structure
- **REQ:** Art. 8 (component-first)
- **Acceptance:** `mkdir -p reflex_openbb/{data,state,components,pages,services,theme}`; `mkdir tests/{fixtures}`; `mkdir docs/screenshots`
- **Files:** directory tree
- **Verify:** `find reflex_openbb -type d` shows the expected tree
- **Estimate:** 5 min

### T-004: Configure pre-commit
- **REQ:** Art. 9
- **Acceptance:** `.pre-commit-config.yaml` includes Ruff, ty, Bandit, Gitleaks; `pre-commit install` runs
- **Files:** `.pre-commit-config.yaml`
- **Verify:** `pre-commit run --all-files` returns 0 (with stubs)
- **Estimate:** 20 min

### T-005: Stub app.py
- **REQ:** (none — placeholder)
- **Acceptance:** `reflex_openbb/app.py` defines `app = rx.App()` with a single page `index` showing "reflex-openbb v0.1.0"
- **Files:** `reflex_openbb/app.py`, `reflex_openbb/pages/__init__.py`, `reflex_openbb/pages/home.py`
- **Verify:** `python -m reflex_openbb` shows the stub page
- **Estimate:** 15 min

### T-006: Verify reflex run works
- **REQ:** (none — sanity check)
- **Acceptance:** `reflex run` starts a dev server on port 3000 and serves the stub page
- **Verify:** `curl http://localhost:3000` returns HTML
- **Estimate:** 5 min

### T-007: Add Apache-2.0 LICENSE
- **REQ:** (license requirement)
- **Files:** `LICENSE`
- **Estimate:** 2 min

### T-008: Add README.md skeleton
- **REQ:** (docs requirement)
- **Files:** `README.md`
- **Verify:** includes: title, one-paragraph description, "Status: WIP", "Install", "Quickstart", "Architecture" sections
- **Estimate:** 15 min

### T-009: GitHub Actions workflow
- **REQ:** Art. 9 (CI gate)
- **Files:** `.github/workflows/ci.yml`
- **Verify:** pushes to the repo trigger the workflow
- **Estimate:** 20 min

---

## Phase 1 — Data layer

### T-101: data/cache.py
- **REQ:** Art. 6
- **Acceptance:** `get_or_compute(key, cache_name, fn)` returns `(value, hit_bool)`; cache names match `data-model/v1-models.md` table
- **Files:** `reflex_openbb/data/cache.py`
- **Verify:** `pytest tests/test_data_cache.py::test_ttl_eviction` passes
- **Estimate:** 30 min

### T-102: data/rate_limiter.py
- **REQ:** (provider protection)
- **Acceptance:** `TokenBucket(rate=5, capacity=10).acquire()` is `async` and respects the rate
- **Files:** `reflex_openbb/data/rate_limiter.py`
- **Verify:** `pytest tests/test_data_rate_limiter.py::test_token_bucket_holds_under_burst` passes
- **Estimate:** 30 min

### T-103: data/circuit_breaker.py
- **REQ:** (provider protection)
- **Acceptance:** After 3 failures to provider X, the breaker is open for 60s
- **Files:** `reflex_openbb/data/circuit_breaker.py`
- **Verify:** `pytest tests/test_data_circuit_breaker.py::test_breaker_opens_after_threshold` passes
- **Estimate:** 30 min

### T-104: Pydantic models
- **REQ:** Art. 5 (Decimal), data-model/v1-models.md
- **Acceptance:** All models from `data-model/v1-models.md` exist; monetary fields are `Decimal`; validators coerce `float`/`int` to `Decimal` via `str(...)`
- **Files:** `reflex_openbb/data/types.py` (or split per module)
- **Verify:** `pytest tests/test_data_types.py::test_no_float_in_monetary_fields` passes
- **Estimate:** 1 h

### T-105: data/equity.py
- **REQ:** REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Acceptance:** `get_equity_quote`, `get_equity_price_history`, `get_equity_fundamentals`, `get_equity_news` exist and are async
- **Files:** `reflex_openbb/data/equity.py`
- **Verify:** `pytest tests/test_data_equity.py` passes; manual call to `get_equity_price_history("AAPL", "1y")` returns ≥ 200 bars
- **Estimate:** 2 h

### T-106: data/crypto.py
- **REQ:** REQ-006
- **Acceptance:** `get_crypto_price_history` exists; same shape as equity
- **Files:** `reflex_openbb/data/crypto.py`
- **Verify:** `pytest tests/test_data_crypto.py` passes
- **Estimate:** 30 min

### T-107: data/economy.py
- **REQ:** REQ-007
- **Acceptance:** `get_economy_indicator(indicator, country)` returns `list[MacroPoint]`
- **Files:** `reflex_openbb/data/economy.py`
- **Verify:** `pytest tests/test_data_economy.py` passes
- **Estimate:** 30 min

### T-108: data/search.py
- **REQ:** REQ-010
- **Acceptance:** `search(query)` returns `SearchResult`
- **Files:** `reflex_openbb/data/search.py`
- **Verify:** `pytest tests/test_data_search.py` passes
- **Estimate:** 30 min

### T-109: Unit tests for data
- **REQ:** Art. 4 (tests cite REQ)
- **Acceptance:** every data function has a unit test with a mocked OpenBB SDK; each test docstring cites the REQ
- **Files:** `tests/test_data_*.py`
- **Verify:** `pytest tests/ -k data` is green
- **Estimate:** 2 h

### T-110: Integration smoke test (manual)
- **REQ:** (not CI)
- **Acceptance:** a manual test that calls the data layer against a real OpenBB SDK, prints "ok"
- **Files:** `tests/manual_smoke.py` (not in CI)
- **Estimate:** 15 min

### T-111: Verify Decimal coercion (Art. 5)
- **REQ:** Art. 5
- **Acceptance:** a test that introspects every Pydantic model and asserts no monetary field is `float`
- **Files:** `tests/test_decimal_coercion.py`
- **Verify:** `pytest tests/test_decimal_coercion.py` passes
- **Estimate:** 30 min

### T-112: Rate limiter stress test
- **REQ:** (provider protection)
- **Acceptance:** a test that fires 100 calls in a tight loop and asserts the limiter delays them to ≤ 5/sec
- **Files:** `tests/test_rate_limiter_stress.py`
- **Verify:** passes
- **Estimate:** 30 min

---

## Phase 2 — State layer

### T-201: state/app_state.py
- **REQ:** REQ-010
- **Acceptance:** `AppState.global_search(query)` calls `data.search.search()` and navigates
- **Files:** `reflex_openbb/state/app_state.py`
- **Verify:** `pytest tests/test_app_state.py::test_global_search` passes
- **Estimate:** 1 h

### T-202: state/equity_state.py
- **REQ:** REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Acceptance:** `EquityState` has the fields, computed vars, and event handlers from `technical/v1-architecture.md` §4
- **Files:** `reflex_openbb/state/equity_state.py`
- **Verify:** `pytest tests/test_equity_state.py` passes
- **Estimate:** 2 h

### T-203: state/crypto_state.py
- **REQ:** REQ-006
- **Acceptance:** `CryptoState` has the required fields and event handlers
- **Files:** `reflex_openbb/state/crypto_state.py`
- **Verify:** `pytest tests/test_crypto_state.py` passes
- **Estimate:** 1 h

### T-204: state/economy_state.py
- **REQ:** REQ-007
- **Acceptance:** `EconomyState` has the required fields and event handlers
- **Files:** `reflex_openbb/state/economy_state.py`
- **Verify:** `pytest tests/test_economy_state.py` passes
- **Estimate:** 1 h

### T-205: Unit tests for state
- **REQ:** Art. 4
- **Acceptance:** every state event handler has a unit test; each test docstring cites the REQ
- **Files:** `tests/test_*_state.py`
- **Verify:** `pytest tests/ -k state` is green
- **Estimate:** 2 h

### T-206: Verify state-driven re-render
- **REQ:** (REACT pattern; ensure state changes propagate)
- **Acceptance:** a test that mutates a state field and asserts the computed var re-evaluates
- **Files:** `tests/test_state_rerender.py`
- **Verify:** passes
- **Estimate:** 30 min

---

## Phase 3 — Equity page

### T-301: components/price_chart.py
- **REQ:** REQ-001, REQ-002
- **Acceptance:** `price_chart(bars, comparison)` returns a `rx.Component` using `reflex-rosencharts.linechart`
- **Files:** `reflex_openbb/components/price_chart.py`
- **Verify:** renders in a smoke test
- **Estimate:** 1 h

### T-302: components/date_range.py
- **REQ:** REQ-002
- **Acceptance:** `date_range(state)` returns a row of 5 buttons
- **Files:** `reflex_openbb/components/date_range.py`
- **Verify:** clicking a button changes the state
- **Estimate:** 30 min

### T-303: components/kpi_grid.py
- **REQ:** REQ-005
- **Acceptance:** `kpi_grid(quote)` returns a 6-card grid
- **Files:** `reflex_openbb/components/kpi_grid.py`
- **Verify:** renders with a sample quote
- **Estimate:** 1 h

### T-304: components/fundamentals_table.py
- **REQ:** REQ-003
- **Acceptance:** `fundamentals_table(fundamentals)` returns an `rx.table`; "n/a" for None
- **Files:** `reflex_openbb/components/fundamentals_table.py`
- **Verify:** renders with a sample
- **Estimate:** 1 h

### T-305: components/news_feed.py
- **REQ:** REQ-004
- **Acceptance:** `news_feed(news)` returns a list of `rx.card`; "No recent news" if empty (REQ-004 O-where)
- **Files:** `reflex_openbb/components/news_feed.py`
- **Verify:** renders with a sample
- **Estimate:** 1 h

### T-306: pages/equity.py
- **REQ:** REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Acceptance:** composes all 5 components with `EquityState`
- **Files:** `reflex_openbb/pages/equity.py`
- **Verify:** manual QA passes
- **Estimate:** 2 h

### T-307: Wire dynamic route /equity/[ticker]
- **REQ:** (routing)
- **Files:** `reflex_openbb/app.py`
- **Verify:** `curl /equity/AAPL` returns HTML
- **Estimate:** 15 min

### T-308: Manual QA — multiple tickers
- **REQ:** REQ-001
- **Files:** none
- **Verify:** `/equity/AAPL`, `/equity/MSFT`, `/equity/TSLA` all render
- **Estimate:** 30 min

### T-309: Manual QA — date range
- **REQ:** REQ-002, NFR-001
- **Verify:** switching 1M/6M/1Y/5Y/Max updates the chart; cache hits < 500ms
- **Estimate:** 30 min

### T-310: Manual QA — stale data banner
- **REQ:** REQ-001 UW
- **Verify:** trigger 429 (or use a stale cache) and verify the banner
- **Estimate:** 30 min

---

## Phase 4 — Crypto and Economy pages

### T-401: components/crypto_chart.py
- **REQ:** REQ-006
- **Estimate:** 30 min (mostly a copy of T-301)

### T-402: pages/crypto.py
- **REQ:** REQ-006
- **Estimate:** 1 h

### T-403: Wire /crypto/[symbol]
- **Estimate:** 10 min

### T-404: Manual QA — /crypto/BTC, /crypto/ETH
- **Estimate:** 20 min

### T-405: components/economy_chart.py
- **REQ:** REQ-007
- **Estimate:** 1 h

### T-406: components/economy_selector.py
- **REQ:** REQ-007
- **Estimate:** 1 h

### T-407: pages/economy.py
- **REQ:** REQ-007
- **Estimate:** 1 h

### T-408: Wire /economy
- **Estimate:** 10 min

### T-409: Manual QA — /economy with multiple indicators and countries
- **REQ:** REQ-007
- **Estimate:** 30 min

### T-410: Take screenshots
- **REQ:** (docs)
- **Verify:** all three pages have at least one screenshot in `docs/screenshots/`
- **Estimate:** 30 min

---

## Phase 5 — Search, CSV export, multi-ticker

### T-501: components/search_box.py
- **REQ:** REQ-010
- **Estimate:** 1 h

### T-502: Wire global_search
- **REQ:** REQ-010
- **Estimate:** 30 min

### T-503: services/csv_export.py
- **REQ:** REQ-008
- **Estimate:** 30 min

### T-504: components/export_button.py
- **REQ:** REQ-008
- **Estimate:** 30 min

### T-505: Wire export on each page
- **REQ:** REQ-008
- **Estimate:** 30 min

### T-506: components/comparison_controls.py
- **REQ:** REQ-009
- **Estimate:** 1 h

### T-507: Wire comparison in price_chart
- **REQ:** REQ-009
- **Estimate:** 1 h

### T-508: Manual QA — multi-ticker overlay
- **REQ:** REQ-009
- **Estimate:** 30 min

### T-509: Manual QA — 6th ticker rejection
- **REQ:** REQ-009 UW
- **Estimate:** 15 min

### T-510: Manual QA — CSV export
- **REQ:** REQ-008
- **Estimate:** 30 min

---

## Phase 6 — Polish, docs, release

### T-601..T-605: docs
- **REQ:** (docs)
- **Estimate:** 4 h total

### T-606..T-608: PyPI release
- **REQ:** (release)
- **Estimate:** 2 h

### T-609: Release post
- **REQ:** (community)
- **Estimate:** 1 h

### T-610: dependabot
- **REQ:** (maintenance)
- **Estimate:** 15 min

---

## Execution order (first 3-5 tasks)

Per the SDD skill: **never start with 30 tasks unattended**. Start with:

1. **T-001** — create the repo
2. **T-002** — pyproject.toml
3. **T-003** — module structure
4. **T-007** — LICENSE
5. **T-008** — README skeleton

Then review, adjust the plan, and scale to the rest of Phase 0.

## Traceability summary

| REQ | Phase | Tasks |
|---|---|---|
| REQ-001 (Equity price chart) | 1, 3 | T-105, T-301, T-306, T-307, T-308 |
| REQ-002 (Date range) | 1, 3 | T-105, T-302, T-306, T-309 |
| REQ-003 (Fundamentals table) | 1, 3 | T-105, T-304, T-306 |
| REQ-004 (News feed) | 1, 3 | T-105, T-305, T-306 |
| REQ-005 (KPI cards) | 1, 3 | T-105, T-303, T-306 |
| REQ-006 (Crypto chart) | 1, 4 | T-106, T-401, T-402, T-404 |
| REQ-007 (Economy dashboard) | 1, 4 | T-107, T-405, T-406, T-407, T-409 |
| REQ-008 (CSV export) | 5 | T-503, T-504, T-505, T-510 |
| REQ-009 (Multi-ticker) | 3, 5 | T-301, T-506, T-507, T-508, T-509 |
| REQ-010 (Search) | 2, 5 | T-201, T-501, T-502 |
| Art. 5 (Decimal) | 1 | T-104, T-111 |
| Art. 6 (Cache) | 1 | T-101 |
| Art. 9 (Pre-commit) | 0 | T-004, T-009 |
