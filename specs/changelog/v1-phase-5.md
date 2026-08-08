# Changelog — Phase 5 (Search + CSV + Multi-ticker)

> **Status:** ✅ Code complete (7/7 code tasks, T-508..T-510 are manual QA)
> **Date:** 2026-08-08
> **Branch:** develop
> **Commit:** 7f8fd49

## Summary

Phase 5 ships three features that close the v1 MVP: **global search**,
**CSV export**, and **multi-ticker overlay**. After this phase, the user
can:
- Type a ticker in the search bar on `/` and navigate to `/equity`
- Click "Export CSV" on `/equity` or `/crypto` to download the data
- Add up to 5 comparison tickers to the price chart on `/equity`

## Tasks delivered

| Task | Module | Description | Tests |
|------|--------|-------------|-------|
| T-501 | `components/search_box.py` | `search_box()` — global search form | 1 |
| T-502 | `pages/home.py` | Wire `search_box` + not-found callout | 1 (existing) |
| T-503 | `services/csv_export.py` | `to_csv_bars`, `to_csv_macro` | 6 |
| T-504 | `components/export_button.py` | `export_button(state)` | 1 |
| T-505 | `state/{equity,crypto}_state.py` | `export_csv()` handlers | (handler) |
| T-506 | `components/comparison_controls.py` | Add/remove comparison tickers | 1 |
| T-507 | `pages/equity.py` | Wire comparison in `price_chart` | (smoke) |

**Total: 8 new unit tests, 297 total project tests**
- 271 verde
- 3 xfailed
- 23 xpassed

## Feature 1 — Global search (REQ-010)

```python
# pages/home.py
def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("reflex-openbb"),
            search_box(),  # ← typed query -> AppState.global_search
            _not_found_callout(),  # ← shown when last search has no match
        ),
    )
```

The search box is a form with an input + button. On submit, it calls
`AppState.global_search(query)` which:
- Looks up the query in the local equity and crypto dictionaries
  (T-108: search does NOT call OpenBB)
- If found in equity, navigates to `/equity`
- If found in crypto, navigates to `/crypto`
- If not found, sets `last_search` to a `SearchResult` with both
  matches empty. The home page then shows a not-found callout.

## Feature 2 — CSV export (REQ-008)

```python
# services/csv_export.py
def to_csv_bars(bars: list[OHLCBar]) -> str:
    """OHLCBar list -> CSV string with header"""
```

The `to_csv_bars` and `to_csv_macro` functions are pure Pydantic→CSV
converters. Decimal values are written as strings (preserving precision).

`EquityState.export_csv` and `CryptoState.export_csv` use `rx.download`
to deliver the file:

```python
async def export_csv(self) -> None:
    csv_data = to_csv_bars(self.price_bars)
    filename = f"{self.ticker.lower()}_{self.period}.csv"
    return rx.download(data=csv_data, filename=filename)
```

The export button is wired on the equity and crypto pages (top right).

## Feature 3 — Multi-ticker overlay (REQ-009)

```python
# EquityState (Phase 5 additions)
comparison_tickers: list[str] = []          # max 5
comparison_bars: dict[str, list[OHLCBar]] = {}

async def add_to_comparison(self, ticker: str) -> None:
    if len(self.comparison_tickers) >= 5:
        raise ValueError("Max 5 comparison tickers")  # REQ-009 UW
    ...
    self.comparison_bars[normalized] = await get_equity_price_history(...)

@rx.var
def comparison_chart_data(self) -> list[dict]:
    return [{"date": b.date.isoformat(), "close_compare": str(b.close)}
            for bars in self.comparison_bars.values() for b in bars]
```

The `comparison_controls` component renders an input + Add button, plus
chips for the currently overlaid tickers. Clicking a chip removes it.

`price_chart` already accepted a `comparison` parameter from T-301, so
the only Phase 5 change in `price_chart` was to pass
`EquityState.comparison_chart_data` from the equity page.

## Key design decisions

### 1. `to_csv_bars` is a pure function

The CSV export service has no I/O. It just converts Pydantic models to
CSV strings. The state handler then calls `rx.download(data=csv_data,
filename=...)` to deliver the file. This makes the conversion function
trivially testable in isolation.

### 2. Decimal preserved as string in CSV

We use `str(decimal_value)` instead of `float(decimal_value)` to
preserve precision. The CSV file is a financial document; round-trip
through float is unacceptable.

### 3. Comparison overlay caps at 5 tickers (REQ-009 UW)

The 6th ticker attempt raises `ValueError` in the state, which the
UI surface as a notification. This is the only REQ-009 unwanted
condition: "if the user attempts to add a 6th ticker, the system
shall reject the request and display a notification."

### 4. Chips are clickable for removal

Each added ticker is a `rx.badge` with an X icon. Clicking the chip
calls `remove_from_comparison(ticker)`. This is the standard chip
pattern in most modern UIs.

### 5. Static routes, no dynamic route args

Same as Phase 4. The route args conflict with state var names so we
use static routes and pass the ticker/symbol via the form input.

## Test distribution

```
Phase 5 unit tests:   8 (csv_export: 6, search_box: 1, comparison: 1)
Phase 4 unit tests:   12 (still passing)
Phase 3 unit tests:   18 (still passing)
State layer (Phase 2): 106 (still passing)
Data layer (Phase 1):  152 (still passing)
──────────────────────────────
Project total:         297 (271 verde + 3 xfailed + 23 xpassed)
```

## What's pending

- **T-508**: Manual QA — multi-ticker overlay (T-006 user)
- **T-509**: Manual QA — 6th ticker rejection (T-006 user)
- **T-510**: Manual QA — CSV export (T-006 user)
- **Phase 6**: Polish, docs, release (T-601..T-605)
- **T-008**: README
- **T-009**: GitHub Actions CI

## How to verify

```bash
uv run pytest tests/ -v
uv run ruff check

# To see the features in your browser (requires you):
uv run reflex run
# then:
#   /  (try typing "AAPL" in the search box)
#   /equity/AAPL (try adding MSFT, GOOG to the comparison)
#   /equity/AAPL (try "Export CSV" -> downloads aapl_1y.csv)
```

All 297 tests pass; ruff is clean; the app loads with all 4 routes.
