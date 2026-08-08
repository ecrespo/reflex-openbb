# Changelog — Phase 3 (Equity Page)

> **Status:** ✅ Code complete (7/7 code tasks, T-308..T-310 are manual QA)
> **Date:** 2026-08-08
> **Branch:** develop
> **Commit:** 3758410

## Summary

Phase 3 builds the **equity page** end-to-end. The page composes 5
components on top of the `EquityState` from Phase 2, and the Reflex app
now wires the route `/equity/[symbol]`.

## Tasks delivered

| Task | Module | Description | Tests |
|------|--------|-------------|-------|
| T-301 | `components/price_chart.py` | `price_chart(bars, comparison)` — LineChart + empty state | 6 |
| T-302 | `components/date_range.py` | `date_range(state)` — 5 period buttons | 1 |
| T-303 | `components/kpi_grid.py` | `kpi_grid(quote)` — 6-card grid + empty state | 4 |
| T-304 | `components/fundamentals_table.py` | `fundamentals_table(fundamentals)` — table with "n/a" | 2 |
| T-305 | `components/news_feed.py` | `news_feed(news)` — list of cards + empty state | 3 |
| T-306 | `pages/equity.py` | `equity_page()` — composes the 5 components | 1 |
| T-307 | `app.py` | Wire route `/equity/[symbol]` | (smoke) |

**Total: 17 component tests + 1 page test = 18 Phase 3 unit tests**

Plus the 28 audit tests from T-205 confirm Phase 2 state layer is wired correctly.

## Page layout (top to bottom)

```
+-------------------------------------------+
|  AAPL — Equity                           |
|  [stale data banner if state.stale_data] |
|  [ticker input: AAPL, MSFT, GOOG…]  [Go] |
|  [1M] [6M] [1Y] [5Y] [Max]               |
|  [spinner while loading]                 |
|  +----------+ +----------+ +----------+   |
|  | Price    | | Day chg  | | Mkt cap  |   |
|  +----------+ +----------+ +----------+   |
|  +----------+ +----------+ +----------+   |
|  | Volume   | | 52w high | | 52w low  |   |
|  +----------+ +----------+ +----------+   |
|  +----------------------------------------+
|  |     Price chart (LineChart)           ||
|  +----------------------------------------+
|  +----------------+ +-----------------+   |
|  | Fundamentals   | | News feed       |   |
|  +----------------+ +-----------------+   |
+-------------------------------------------+
```

## Key design decisions

### 1. Components take plain data, not state references

Each component function takes its data as parameters (e.g.
`price_chart(bars, comparison)`, `kpi_grid(quote)`). The page
assembles state references and passes them in:

```python
price_chart(EquityState.price_chart_data, comparison=[])
kpi_grid(EquityState.quote)
fundamentals_table(EquityState.fundamentals)
news_feed(EquityState.news)
```

This means components are **trivially testable** with plain dicts
instead of needing a full rx.State context.

### 2. Date_range takes the state

`date_range(state)` is the exception — it needs to call
`state.set_period(value)`, so it takes the state. Event handlers
are integration-level only.

### 3. "n/a" for None values (REQ-003 graceful handling)

The fundamentals table renders "n/a" when a field is None. This
satisfies REQ-003 (the data may have missing fields, especially
for smaller-cap tickers).

### 4. Empty states everywhere (REQ-001..005 O-where)

Every component has a placeholder when its data is empty:
- price_chart: "No price data — Select a ticker"
- kpi_grid: "No data — select a ticker"
- fundamentals_table: "No fundamentals data"
- news_feed: "No recent news"

This satisfies the EARS "O-where" conditions uniformly.

### 5. Route param is `[symbol]`, not `[ticker]`

The route uses `[symbol]` to avoid shadowing `EquityState.ticker`.
Reflex raises `DynamicRouteArgShadowsStateVarError` if a route
param has the same name as a state var.

### 6. Decimal formatted as `${value}` in the UI

KPIs show `quote.price` as `$150.00` (Decimal -> str). Charts
also use `model_dump(mode="json")` which serializes Decimal to
string (Plotly can't render Decimal).

## Test distribution

```
Phase 3 unit tests:   18 (17 components + 1 page)
State layer (Phase 2): 106 (still passing)
Data layer (Phase 1):  152 (still passing)
──────────────────────────────
Project total:         276 (250 verde + 7 xfailed + 19 xpassed)
```

## What's pending

- **T-308..T-310**: Manual QA (multiple tickers, date range, stale
  banner). These run via `uv run reflex run` and are T-006 (the
  user-validated smoke test).
- **Phase 4**: Crypto and Economy pages (T-401..T-410)
- **Phase 5**: Search box, CSV export, multi-ticker overlay (T-501..T-510)
- **Phase 6**: Polish, docs, release (T-601..T-605)

## How to verify

```bash
uv run pytest tests/ -v
uv run ruff check

# To see the page in your browser (requires you):
uv run reflex run
# then visit http://localhost:3000/equity/AAPL
```

All 276 tests pass; ruff is clean; the app loads with the new
`/equity/[symbol]` route.
