# Analyze Gate — reflex-openbb v1.0

> **Status:** DRAFT · **Date:** 2026-08-08 · **Reviewer:** (self)
> **Inputs:** constitution, PRD, API Spec, Tech Design, Data Model, Implementation Plan, Tasks
> **Method:** walk through `references/11-ANALYZE-CHECKLIST.md` (from the SDD skill).

This is a read-only cross-artifact validation. It does NOT modify the spec kit; it produces a findings list with severity. The human decides what to fix.

## Checklist results

### 1. Coverage

> Every PRD requirement must be covered by the API Spec; every API field in the Data Model; every API call in the Tech Design; every phase in the Plan; every REQ in a Task.

| REQ | In API Spec? | In Data Model? | In Tech Design? | In Plan? | In Tasks? |
|---|---|---|---|---|---|
| REQ-001 | ✅ get_equity_price_history | ✅ OHLCBar | ✅ §6.1 price_chart | ✅ Phase 3 | ✅ T-105, T-301..T-306, T-308 |
| REQ-002 | ✅ get_equity_price_history(period) | ✅ OHLCBar | ✅ §6.1 | ✅ Phase 3 | ✅ T-105, T-302, T-309 |
| REQ-003 | ✅ get_equity_fundamentals | ✅ EquityFundamentals | ✅ §6.2 | ✅ Phase 3 | ✅ T-105, T-304, T-306 |
| REQ-004 | ✅ get_equity_news | ✅ NewsItem | ✅ (omitted in deep dive; see Finding F-001) | ✅ Phase 3 | ✅ T-105, T-305, T-306 |
| REQ-005 | ✅ get_equity_quote | ✅ EquityQuote | ✅ §6.2 kpi_grid | ✅ Phase 3 | ✅ T-105, T-303, T-306 |
| REQ-006 | ✅ get_crypto_price_history | ✅ OHLCBar (reused) | ✅ §6.1 (reused) | ✅ Phase 4 | ✅ T-106, T-401..T-404 |
| REQ-007 | ✅ get_economy_indicator | ✅ MacroPoint | ✅ (omitted in deep dive; see F-001) | ✅ Phase 4 | ✅ T-107, T-405..T-409 |
| REQ-008 | ✅ (UI-only) | n/a | ✅ §6.3 | ✅ Phase 5 | ✅ T-503..T-505, T-510 |
| REQ-009 | ✅ (state-level) | n/a | ✅ (mentioned, see F-001) | ✅ Phase 5 | ✅ T-506..T-509 |
| REQ-010 | ✅ search | ✅ SearchResult | ✅ (mentioned, see F-001) | ✅ Phase 5 | ✅ T-201, T-501, T-502 |

✅ **All 10 REQs are covered** end-to-end.

### 2. Constitution compliance

> Every artifact's "Constitution check" section must reference the articles that apply and assert satisfaction.

| Article | Satisfied in | Notes |
|---|---|---|
| Art. 1 (open-source) | PRD, Tech Design, Tasks | All deps MIT/Apache-2.0. ✅ |
| Art. 2 (Reuse custom components) | Tech Design, Tasks | T-301 explicitly uses reflex-rosencharts. ✅ |
| Art. 3 (OpenBB only) | Tech Design, API Spec | data/ is the single owner. ✅ |
| Art. 4 (EARS) | PRD, Tasks | REQ-001..010 in EARS; tasks cite REQs. ✅ |
| Art. 5 (Decimal) | Data Model, Tech Design, Tasks | Pydantic validators + T-111 verification test. ✅ |
| Art. 6 (Cache) | Data Model, Tech Design, Tasks | TTL defined for every data function. ✅ |
| Art. 7 (Single-tenant) | PRD, Tech Design | Scope §5.2 excludes auth. ✅ |
| Art. 8 (Component-first) | Tech Design, Tasks | Module structure enforces it. ✅ |
| Art. 9 (Pre-commit) | Tech Design, Tasks | T-004, T-009 configure it. ✅ |

✅ **No constitution violations.**

### 3. Ambiguity

> Acceptance criteria that no test can verify.

Spot-check:

- REQ-001 U ("render a line chart for `/equity/{ticker}` when the ticker is recognized") — testable: a `test_equity_state.py::test_set_ticker_triggers_quote_load` calls the event handler with "AAPL" and asserts `state.quote` is populated. ✅
- REQ-003 O ("WHERE the provider doesn't return a metric, THE SYSTEM SHALL display 'n/a'") — testable: a component test renders `fundamentals_table(EquityFundamentals(ticker="AAPL", pe_ratio=None, ...))` and asserts the cell shows "n/a". ✅
- REQ-005 U ("display 6 KPI cards") — testable: a component test asserts 6 `kpi_card` instances are rendered. ✅
- REQ-009 UW ("IF the user attempts to add a 6th ticker, THE SYSTEM SHALL display 'Maximum 5 tickers' and reject the addition") — testable: a state test calls `add_to_comparison` 6 times and asserts the 6th call is rejected. ✅
- REQ-008 E ("WHEN the user clicks 'Export CSV', THE SYSTEM SHALL download a CSV file") — testable: a state test mocks `rx.download` and asserts it's called with the expected CSV bytes. ✅

✅ **No ambiguous criteria.**

### 4. Terminology drift

> The same concept must use the same name across documents.

Spot-check (the top 5 concepts):

| Concept | PRD | API Spec | Tech Design | Data Model | Consistent? |
|---|---|---|---|---|---|
| "ticker" | "ticker" | "ticker" | "ticker" | "ticker" | ✅ |
| "OHLC bar" / "price bar" | "OHLC bar" | "OHLCBar" | "OHLCBar" | "OHLCBar" | ⚠ See F-002 |
| "EquityQuote" (the model) | "equity quote" | "EquityQuote" | "EquityQuote" | "EquityQuote" | ✅ |
| "fundamentals" | "fundamentals" | "EquityFundamentals" | "EquityFundamentals" | "EquityFundamentals" | ✅ |
| "KPI card" | "KPI card" / "KPI metric" | n/a | "kpi_grid" / "kpi_card" | n/a | ⚠ See F-003 |

### 5. Orphan tasks

> Tasks that don't trace back to a REQ or a phase.

Spot-check: every Task in `tasks/v1-tasks.md` has either:
- A REQ citation in its `Acceptance` line, OR
- An "infrastructure" tag (e.g., T-001, T-007, T-008, T-009)

✅ **No orphan tasks** (with the exception of pure infra tasks, which are tagged).

### 6. Phase dependencies

> Later phases must depend on earlier phases.

```
Phase 0 (scaffold) → Phase 1 (data) → Phase 2 (state) → Phase 3 (equity UI) → Phase 4 (crypto/economy) → Phase 5 (power) → Phase 6 (release)
```

✅ **No circular dependencies.** Each phase builds on the previous.

### 7. Estimates

> Each task should have a sane estimate (5 min to 4 h).

All tasks are in the 5 min – 4 h range. The largest (T-105, T-205) are 2 h; T-306 is 2 h. No 8 h monsters. ✅

### 8. Test coverage

> Every MUST REQ must have at least one automated test.

| REQ | Test |
|---|---|
| REQ-001 | T-105 (unit), T-308 (manual) |
| REQ-002 | T-105, T-309 (manual) |
| REQ-003 | T-105, T-304 (component), T-310 (manual) |
| REQ-004 | T-105, T-305 (component) |
| REQ-005 | T-105, T-303 (component) |
| REQ-006 | T-106, T-404 (manual) |
| REQ-007 | T-107, T-409 (manual) |
| REQ-008 | T-503, T-510 (manual) |
| REQ-009 | T-506, T-508, T-509 (manual) |
| REQ-010 | T-201, T-501, T-502 |

⚠ Most tests are manual in v1; the plan explicitly defers a full Playwright suite to v2 (Section 9 of Tech Design). This is acceptable for v1 because the manual tests are in a checklist that the author will execute before each release.

## Findings

| ID | Severity | Finding | Recommendation |
|---|---|---|---|
| F-001 | P2 (low) | Tech Design §6 is missing deep-dive code samples for the news feed, economy chart, search box, and multi-ticker components. These are covered in Tasks but not in the Tech Design. | Add 2-3 lines of code per missing component to Tech Design §6 before starting Phase 3. |
| F-002 | P3 (cosmetic) | PRD uses "OHLC bar" and "price bar" interchangeably; the rest of the kit uses "OHLCBar". | Standardize on "OHLC bar" in the PRD; update on first edit. |
| F-003 | P3 (cosmetic) | PRD says "KPI card" or "KPI metric"; Tech Design says "kpi_grid" / "kpi_card". | Standardize on "KPI card" everywhere. |
| F-004 | P2 (low) | The `circle_breaker` recovery time is hard-coded at 60s; the spec doesn't say how to configure it. | Add a config block to Tech Design §5.3 (a `CircuitBreakerConfig` Pydantic model). |
| F-005 | P2 (low) | The rate-limiter's `rate=5` and `capacity=10` are also hard-coded. | Same — make them configurable via env vars (`OPENBB_RATE_RPS`, `OPENBB_BURST`). |
| F-006 | P3 (info) | The plan does not include a "smoke test" CI job that runs the dev server. | Add a smoke-test CI job in Phase 6 (T-606 or new T-611). |
| F-007 | P2 (low) | The data layer doesn't have a "force refresh" path — once cached, you can't bypass the cache from the UI. | Add an `?fresh=1` query param or a button in the UI to bust the cache. |

## Verdict

**Acceptable to start Phase 0.** All P0/P1 checks pass. The P2/P3 findings are non-blocking and can be fixed during the first 2-3 phases.

## Sign-off

| Reviewer | Date | Status |
|---|---|---|
| Ernesto Crespo (self) | 2026-08-08 | ☐ Pending |

## Next step

Either:
- (A) Approve the proposal and start Phase 0 with the first 3-5 tasks (T-001..T-005), OR
- (B) Fix the P2 findings (F-001, F-004, F-005, F-007) before starting.
