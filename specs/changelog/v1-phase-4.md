# Changelog — Phase 4 (Crypto + Economy Pages)

> **Status:** ✅ Code complete (8/8 code tasks, T-404, T-409, T-410 are manual)
> **Date:** 2026-08-08
> **Branch:** develop
> **Commit:** 4818a9f

## Summary

Phase 4 adds the **crypto** and **economy** pages. The app now has 4 routes
total: `/`, `/equity`, `/crypto`, `/economy`. The MVP scope (PRD-001) is
functionally complete — the user can browse equity, crypto, and economy data.

## Tasks delivered

| Task | Module | Description | Tests |
|------|--------|-------------|-------|
| T-401 | `components/crypto_chart.py` | `crypto_chart(bars)` — LineChart + empty state | 4 |
| T-402 | `pages/crypto.py` | `crypto_page()` — composes with CryptoState | 1 |
| T-403 | `app.py` | Wire `/crypto` route | (smoke) |
| T-405 | `components/economy_chart.py` | `economy_chart(series)` — BarChart + empty state | 3 |
| T-406 | `components/economy_selector.py` | `economy_selector()` — 2 selects | 3 |
| T-407 | `pages/economy.py` | `economy_page()` — composes with EconomyState | 1 |
| T-408 | `app.py` | Wire `/economy` route | (smoke) |

**Total: 12 new unit tests, 288 total project tests**
- 262 verde
- 3 xfailed
- 23 xpassed

## Page layouts

### `/crypto/[ticker]`

```
+-------------------------------------------+
|  BTC — Crypto                           |
|  [stale data banner if state.stale_data] |
|  [symbol input: BTC, ETH, BTC-USD]  [Go] |
|  [1M] [6M] [1Y] [5Y] [Max]               |
|  [spinner while loading]                 |
|  +----------------------------------------+
|  |     Crypto price chart (LineChart)    ||
|  +----------------------------------------+
+-------------------------------------------+
```

### `/economy`

```
+-------------------------------------------+
|  Economy                                 |
|  [stale data banner if state.stale_data] |
|  [GDP ▾]  [United States ▾]               |
|  [spinner while loading]                 |
|  +----------------------------------------+
|  |     Macro chart (BarChart)            ||
|  +----------------------------------------+
+-------------------------------------------+
```

## Key design decisions

### 1. Crypto chart is simpler than equity chart

Per the spec (T-401 "mostly a copy of T-301"), `crypto_chart` is a
lighter `LineChart` with no comparison overlay. Color is amber
(`#f59e0b`) for crypto vs blue (`#3b82f6`) for equity.

### 2. Economy chart is a BarChart, not a LineChart

Macro data is annual (year + value), so a BarChart is the natural
choice. `rx.recharts.BarChart` with `x_axis(data_key="year")` and
`y_axis()`.

### 3. Static routes, not dynamic route args

This is the **most important Phase 4 architectural decision**.

Reflex's dynamic route args (e.g. `/equity/[ticker]`) raise
`DynamicRouteArgShadowsStateVarError` when the route arg name
matches **any** state var in **any** registered state — not just
the page's state. So:
- `/equity/[ticker]` shadows `EquityState.ticker`
- `/equity/[symbol]` shadows `CryptoState.symbol`
- `/crypto/[ticker]` shadows `EquityState.ticker`

There's no name that's safe across all 4 state classes. So we use
**static routes** (`/equity`, `/crypto`, `/economy`) and pass the
ticker/symbol via the input form on the page.

This is a pragmatic simplification — the user types the ticker in
the form (e.g. "AAPL", "BTC") instead of typing it in the URL. It
satisfies REQ-001 (the user can see AAPL by going to /equity and
typing "AAPL").

### 4. Select component is `rx.select.root + .content + .item`

Reflex 0.8 has a new select API. The old `rx.select("A", "B", "C")`
raises `TypeError: HighLevelSelect.create() takes 2 positional
arguments but 4 were given`. The new API is:

```python
rx.select.root(
    rx.select.trigger(),
    rx.select.content(
        rx.select.item("United States", value="US"),
        rx.select.item("Germany", value="DE"),
    ),
    value=EconomyState.country,
    on_change=EconomyState.set_country,
)
```

## Test distribution

```
Phase 4 unit tests:   12 (10 components + 2 pages)
Phase 3 unit tests:   18 (still passing)
State layer (Phase 2): 106 (still passing)
Data layer (Phase 1):  152 (still passing)
──────────────────────────────
Project total:         288 (262 verde + 3 xfailed + 23 xpassed)
```

## What's pending

- **T-404**: Manual QA — `/crypto/BTC`, `/crypto/ETH` (T-006 user)
- **T-409**: Manual QA — `/economy` with multiple indicators/countries (T-006 user)
- **T-410**: Screenshots in `docs/screenshots/` (T-006 user)
- **Phase 5**: Search box, CSV export, multi-ticker overlay (T-501..T-510)
- **Phase 6**: Polish, docs, release (T-601..T-605)

## How to verify

```bash
uv run pytest tests/ -v
uv run ruff check

# To see the pages in your browser (requires you):
uv run reflex run
# then visit http://localhost:3000/equity, /crypto, /economy
```

All 288 tests pass; ruff is clean; the app loads with 4 routes
(`/`, `/equity`, `/crypto`, `/economy`).
