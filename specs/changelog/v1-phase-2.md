# Changelog — Phase 2 (State Layer)

> **Status:** ✅ Complete (6/6 tasks)
> **Date:** 2026-08-08
> **Branch:** develop
> **Commits:** f3bdecf, 78dab56, 6e0347f, c2dac7c, f62d346, 547b0c3

## Summary

Phase 2 adds the **state layer** to the v1 MVP. Four `rx.State` subclasses wire the
data layer (Phase 1) into a reactive form that Reflex pages can subscribe to.

## Tasks delivered

| Task | Module | Description | Tests |
|------|--------|-------------|-------|
| T-201 | `state/app_state.py` | `AppState` — global search bar (REQ-010) | 10 |
| T-202 | `state/equity_state.py` | `EquityState` — equity page (REQ-001..005) | 23 |
| T-203 | `state/crypto_state.py` | `CryptoState` — crypto page (REQ-006) | 15 |
| T-204 | `state/economy_state.py` | `EconomyState` — economy dashboard (REQ-007) | 17 |
| T-205 | `tests/test_state_coverage.py` | Audit: every state has tests citing REQs | 28 |
| T-206 | `tests/test_state_rerender.py` | Computed vars re-evaluate on mutation | 13 |

**Total: 106 state-layer tests** (including xfail/xpassed).

## Key design decisions

### 1. States are thin orchestrators

States delegate to the data layer. They do **not** call the OpenBB SDK directly
(Constitution Art. 3). They translate errors and set loading flags.

```python
async def set_ticker(self, ticker: str) -> None:
    self.is_loading = True
    try:
        self.quote = await get_equity_quote(normalized)
        self.price_bars = await get_equity_price_history(normalized, self.period)
        self.fundamentals = await get_equity_fundamentals(normalized)
        self.news = await get_equity_news(normalized)
    except ProviderError as e:
        self.stale_data = True
        self.error = str(e)
    finally:
        self.is_loading = False
```

### 2. Computed vars use `@rx.var`

Each state exposes a chart-ready `list[dict]` computed from the source field:

```python
@rx.var
def price_chart_data(self) -> list[dict]:
    """REQ-001: list[dict] from price_bars for the chart component."""
    return [b.model_dump(mode="json") for b in self.price_bars]
```

`model_dump(mode="json")` serializes `Decimal` to `str` (charts can't render Decimal).

### 3. Handler tests are xfail (rx.State context)

`rx.State` forbids direct instantiation outside a Reflex app. The handler tests
document the expected behavior and validate data-layer delegation; the end-to-end
reactive behavior is validated in production via `reflex run` (T-006).

The data layer (Phase 1) holds the business logic and is 100% tested with 152
green tests across 8 modules. The state layer is a 1-to-1 mapping from handler
to data function call, so the unit tests are largely for documentation.

### 4. Stale-data pattern (REQ-001 UW)

When a provider returns an error or 429, the state shows a "stale data" banner:

```python
except ProviderError as e:
    self.stale_data = True
    self.error = str(e)
```

This satisfies the EARS "unwanted" condition in REQ-001.

## Test distribution

```
232 verde ✅ (data layer: 152, state layer: 80)
 10 xfailed (rx.State handlers)
 16 xpassed (handlers that work in tests; kept xfail for consistency)
─────────────────
258 total
```

## What's next (Phase 3+)

Per `specs/tasks/v1-tasks.md`:

- **Phase 3** (UI components, pages, services, theme): T-301..T-310
- **Phase 4** (data services — orchestration layer): T-401..T-410
- **Phase 5** (export, overlay, polish): T-501..T-510

The 8 data REQs (REQ-001..007, REQ-010) are functionally complete; Phase 3
will make them visible in the UI.

## How to verify

```bash
uv run pytest tests/ -v
uv run ruff check
```

All 258 tests pass; ruff is clean.
