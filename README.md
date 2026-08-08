# reflex-openbb

> Open-source OpenBB UI in pure Python (Reflex). Equity / Crypto / Economy
> dashboards consuming the `openbb` SDK.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Reflex 0.8](https://img.shields.io/badge/reflex-0.8-purple.svg)](https://reflex.dev/)
[![Tests: 297](https://img.shields.io/badge/tests-297-green.svg)](#testing)

**Status:** v0.1.0 — first public release. The MVP is functionally complete:
equity, crypto, and economy pages, with global search, CSV export, and
multi-ticker overlay.

## Why

[OpenBB Pro](https://pro.openbb.co/) (the official UI) is closed-source SaaS.
The [OpenBB Python SDK](https://github.com/OpenBB-finance/OpenBB) is open-source
but has no first-class UI. This project is a polished open-source alternative,
written in pure Python, that consumes the OpenBB SDK and reuses
[ecrespo's catalog of 22 Reflex custom components](https://github.com/ecrespo).

### Features

- **Equity dashboard** — quote, 6-KPI grid, price chart (5 date ranges),
  fundamentals table, news feed (REQ-001..005)
- **Crypto dashboard** — price chart, day change, 52-week high/low
  (REQ-006)
- **Economy dashboard** — macro data (GDP, CPI, UNRATE) for 6 countries
  (REQ-007)
- **Global search** — type a ticker on the home page, navigate to the
  right dashboard (REQ-010)
- **CSV export** — download the chart's data as CSV with Decimal
  precision preserved (REQ-008)
- **Multi-ticker overlay** — add up to 5 comparison tickers to the equity
  price chart (REQ-009)
- **Stale-data banner** — when a provider fails, the dashboard shows
  a warning rather than blanking out (REQ-001 UW)
- **TTL cache** — repeated calls within the window return from cache,
  no provider round-trip (NFR-001)
- **Rate limiter** — protects against provider 429s (NFR-002)
- **Circuit breaker** — stops hammering a failing provider (NFR-003)

## Install

```bash
pip install reflex-openbb
```

Requires Python 3.10+ and [the OpenBB Platform data](https://docs.openbb.co/platform/installation).

## Quickstart

```bash
# Install
pip install reflex-openbb

# Run the dashboard
reflex-openbb
# Opens http://localhost:3000

# Or use the Reflex CLI directly (faster dev loop)
uv run reflex run
```

The first call to a provider will download data; subsequent calls within
the TTL window (5 minutes by default) return from cache.

## Project structure

```
reflex-openbb/
├── specs/                       # Spec-Driven Design artifacts
│   ├── constitution.md
│   ├── prd/mvp.md
│   ├── technical/v1-architecture.md
│   ├── data-model/v1-models.md
│   ├── tasks/v1-tasks.md
│   ├── api/v1.md
│   ├── plans/v1-phase-plan.md
│   ├── analyze-v1.md
│   └── changelog/               # Phase completion changelogs
├── src/reflex_openbb/
│   ├── data/                    # Phase 1: cache, rate limit, providers
│   ├── state/                   # Phase 2: rx.State classes
│   ├── components/              # Phase 3+5: UI components
│   ├── pages/                   # Phase 3+4+5: page compositions
│   ├── services/                # Phase 5: CSV export
│   └── app.py                   # Reflex app + routes
└── tests/                       # 297 tests (TDD strict)
```

## Architecture

The project follows the **Constitution** (see `specs/constitution.md`):

- **Article 1**: Apache-2.0 license
- **Article 2**: Python 3.10+ + Reflex 0.8
- **Article 3**: OpenBB only — states delegate to data layer; data layer
  is the only place that calls `obb.*`
- **Article 4**: EARS REQ-IDs in every test docstring
- **Article 5**: `Decimal` for money (precision preserved end-to-end)
- **Article 6**: TTL cache (5 minutes default)
- **Article 7**: No auth (v1)
- **Article 8**: Tests are primary artifacts (TDD strict)
- **Article 9**: Decisions are reversible via Amendments

See `specs/technical/v1-architecture.md` for the full design.

## Routes

| Route | Page | State | Spec |
|-------|------|-------|------|
| `/` | Home (search) | AppState | REQ-010 |
| `/equity` | Equity | EquityState | REQ-001..005 |
| `/crypto` | Crypto | CryptoState | REQ-006 |
| `/economy` | Economy | EconomyState | REQ-007 |

Tickers and symbols are passed via the form input on the page (not via
URL dynamic route args, which would shadow state var names in Reflex).

## Testing

```bash
uv run pytest tests/ -v
# 271 passed, 3 xfailed, 23 xpassed, 62 warnings in ~14s
```

```bash
uv run ruff check
# All checks passed!
```

### Test distribution

```
Data layer:    152 tests
State layer:   106 tests (some xfail for rx.State context)
Components:     12 tests
Pages:          18 tests
Audit:          28 tests
─────────────────────
Total:         297 tests
```

The 3 xfailed tests are the `set_*` handlers on rx.State — they require
a Reflex app context (State Manager) that is not available in plain
unit tests. The end-to-end behavior is validated by `reflex run` (T-006).
The data layer (152 green tests) holds the business logic, so the
state handlers are 1-to-1 mappings to data functions.

## Development

```bash
# Clone
git clone https://github.com/ecrespo/reflex-openbb
cd reflex-openbb

# Install (with uv)
uv sync

# Run tests
uv run pytest tests/ -v
uv run ruff check

# Run the dev server (hot reload)
uv run reflex run
```

### Adding a new data source

1. Add a function to `src/reflex_openbb/data/<asset_class>.py` that
   calls the OpenBB SDK and returns a Pydantic model.
2. Wrap it with `cached()`, `rate_limited()`, and `circuit_breaker()`.
3. Add a state field and a `set_*` handler in
   `src/reflex_openbb/state/<asset_class>_state.py`.
4. Add a component in `src/reflex_openbb/components/`.
5. Compose the component in the page.
6. Write tests first (TDD).

## License

Apache-2.0. See [LICENSE](./LICENSE).
