# Technical Design — reflex-openbb v1.0

> Status: `DRAFT` · Date: 2026-08-08 · Owner: Ernesto Crespo
> Implements: PRD `mvp.md` + API Spec `v1.md`

## 1. Architecture overview

```
┌──────────────────────────────────────────────────────────┐
│  Browser (Reflex-generated React app)                    │
│                                                          │
│  /equity/{ticker}   /crypto/{symbol}   /economy          │
└──────────────────────────┬───────────────────────────────┘
                           │ (Reflex state events)
                           ▼
┌──────────────────────────────────────────────────────────┐
│  Reflex app (Python, single process, local)              │
│                                                          │
│  pages/        — Reflex page components                  │
│  components/   — self-contained feature widgets         │
│  state/        — rx.State classes                        │
│  data/         — OpenBB SDK wrapper (cached, rate-limited)│
│  services/     — caching, rate limiting, error handling  │
└──────────────────────────┬───────────────────────────────┘
                           │ (HTTPS, in-process)
                           ▼
                   ┌───────────────────┐
                   │  OpenBB Python SDK │
                   │  (openbb package)  │
                   └────────┬──────────┘
                            │
                            ▼
              Free providers (yfinance, FRED, etc.)
```

Single-process, no external DB, no auth. The Reflex app is started with `reflex run` (or `python -m reflex_openbb`).

## 2. Module structure

```
reflex-openbb/
├── pyproject.toml
├── README.md
├── LICENSE                       (Apache-2.0)
├── custom_components/            (the wrapper package, reflex-openbb-ui)
│   └── reflex_openbb_ui/
│       ├── __init__.py
│       ├── candlestick.py
│       ├── heatmap.py
│       └── treemap.py
├── reflex_openbb/                (the app package)
│   ├── __init__.py
│   ├── app.py                    (entry point: rx.App + routes)
│   ├── data/                     (the data layer)
│   │   ├── __init__.py
│   │   ├── equity.py
│   │   ├── crypto.py
│   │   ├── economy.py
│   │   ├── search.py
│   │   ├── cache.py              (TTL cache)
│   │   ├── rate_limiter.py       (token bucket)
│   │   └── circuit_breaker.py    (per-provider)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── csv_export.py
│   │   └── format.py             (number/date formatting)
│   ├── state/
│   │   ├── __init__.py
│   │   ├── app_state.py
│   │   ├── equity_state.py
│   │   ├── crypto_state.py
│   │   └── economy_state.py
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── equity.py
│   │   ├── crypto.py
│   │   ├── economy.py
│   │   └── home.py
│   ├── components/               (the UI components)
│   │   ├── __init__.py
│   │   ├── search_box.py
│   │   ├── ticker_select.py
│   │   ├── date_range.py
│   │   ├── price_chart.py        (uses reflex-rosencharts.linechart)
│   │   ├── fundamentals_table.py (uses rx.table)
│   │   ├── news_feed.py          (uses rx.card)
│   │   ├── kpi_grid.py           (uses rx.metric)
│   │   └── export_button.py
│   └── theme/
│       └── colors.py             (palette tokens)
├── tests/
│   ├── test_data_equity.py
│   ├── test_data_crypto.py
│   ├── test_data_economy.py
│   ├── test_data_cache.py
│   ├── test_components.py
│   └── fixtures/
└── docs/
    ├── quickstart.md
    ├── architecture.md
    └── screenshots/
```

## 3. Component responsibilities

### `data/` — the data layer
- **Single owner of OpenBB SDK calls** (Art. 3)
- Implements TTL caching with `cachetools.TTLCache` (Art. 6)
- Implements token-bucket rate limiting (in-process, stdlib only)
- Implements per-provider circuit breaker
- All functions are `async def` and return Pydantic models
- **Never** imports Reflex (data layer is independent of the web layer)

### `state/` — Reflex state
- One `rx.State` subclass per page (e.g., `EquityState`)
- Computed properties (`@rx.var`) for derived data
- Event handlers call into `data/` (never directly into the SDK)

### `components/` — UI
- One Python file per feature widget
- Each component is a pure function that takes typed props (no global state)
- State is passed in from the page

### `pages/` — page composition
- Each page is a Reflex function that wires state to components
- Routing is set up in `app.py`

## 4. State model (high level)

```python
class EquityState(rx.State):
    ticker: str = "AAPL"
    period: str = "1y"
    quote: EquityQuote | None = None
    price_bars: list[OHLCBar] = []
    fundamentals: EquityFundamentals | None = None
    news: list[NewsItem] = []
    comparison_tickers: list[str] = []
    comparison_bars: dict[str, list[OHLCBar]] = {}
    is_loading: bool = False
    error: str | None = None
    stale_data: bool = False

    @rx.var
    def price_chart_data(self) -> list[dict]:
        return [b.model_dump() for b in self.price_bars]

    async def set_ticker(self, ticker: str):
        self.ticker = ticker.upper()
        self.is_loading = True
        try:
            self.quote = await get_equity_quote(self.ticker)
            self.price_bars = await get_equity_price_history(self.ticker, self.period)
            self.fundamentals = await get_equity_fundamentals(self.ticker)
            self.news = await get_equity_news(self.ticker)
            self.stale_data = False
        except ProviderError as e:
            self.stale_data = True
            self.error = str(e)
        finally:
            self.is_loading = False
```

## 5. Data layer deep dive

### 5.1 Caching (`data/cache.py`)

```python
from cachetools import TTLCache
from threading import Lock

_caches: dict[str, TTLCache] = {
    "quote": TTLCache(maxsize=10_000, ttl=300),       # 5 min
    "price": TTLCache(maxsize=5_000, ttl=300),        # 5 min
    "fundamentals": TTLCache(maxsize=5_000, ttl=86400), # 1 day
    "news": TTLCache(maxsize=2_000, ttl=900),         # 15 min
    "macro": TTLCache(maxsize=500, ttl=604800),       # 7 days
}
_lock = Lock()

def get_or_compute(key: str, cache_name: str, fn, *args, **kwargs):
    cache = _caches[cache_name]
    with _lock:
        if key in cache:
            return cache[key], True  # (value, hit)
    value = fn(*args, **kwargs)
    with _lock:
        cache[key] = value
    return value, False
```

### 5.2 Rate limiter (`data/rate_limiter.py`)

```python
import asyncio

class TokenBucket:
    def __init__(self, rate: float = 5.0, capacity: int = 10):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1
```

### 5.3 Circuit breaker (`data/circuit_breaker.py`)

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 60):
        self.failures: dict[str, int] = {}
        self.open_until: dict[str, float] = {}
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout

    def is_open(self, provider: str) -> bool:
        until = self.open_until.get(provider, 0)
        if until > time.time():
            return True
        return False

    def record_failure(self, provider: str):
        self.failures[provider] = self.failures.get(provider, 0) + 1
        if self.failures[provider] >= self.failure_threshold:
            self.open_until[provider] = time.time() + self.reset_timeout

    def record_success(self, provider: str):
        self.failures.pop(provider, None)
        self.open_until.pop(provider, None)
```

### 5.4 Decimal coercion (Art. 5)

```python
from decimal import Decimal
from pydantic import BaseModel, field_validator

class EquityQuote(BaseModel):
    ticker: str
    price: Decimal
    day_change_pct: Decimal
    market_cap: Decimal | None
    volume: int
    fifty_two_week_high: Decimal
    fifty_two_week_low: Decimal

    @field_validator("price", "day_change_pct", "market_cap", "fifty_two_week_high", "fifty_two_week_low", mode="before")
    @classmethod
    def to_decimal(cls, v):
        if v is None:
            return None
        return Decimal(str(v))  # NEVER Decimal(float) — go through str
```

## 6. UI component deep dives

### 6.1 `price_chart.py`

```python
import reflex as rx
from reflex_rosencharts import linechart
from data.types import OHLCBar

def price_chart(bars: list[dict], comparison: list[dict] | None = None) -> rx.Component:
    return rx.box(
        linechart(
            data=bars,
            x="date",
            y="close",
            comparison_data=comparison or [],
            height="400px",
        ),
        width="100%",
    )
```

Reuses `reflex-rosencharts` (Art. 2). The wrapper is a thin pass-through that converts Pydantic models to dicts.

### 6.2 `kpi_grid.py`

```python
import reflex as rx

def kpi_grid(quote) -> rx.Component:
    return rx.grid(
        kpi_card("Price",        f"${quote.price:,.2f}"),
        kpi_card("Day Change",   f"{quote.day_change_pct:+.2f}%"),
        kpi_card("Market Cap",   f"${quote.market_cap / 1e9:,.2f}B" if quote.market_cap else "n/a"),
        kpi_card("Volume",       f"{quote.volume / 1e6:,.1f}M"),
        kpi_card("52w High",     f"${quote.fifty_two_week_high:,.2f}"),
        kpi_card("52w Low",      f"${quote.fifty_two_week_low:,.2f}"),
        columns="3",
        spacing="4",
        width="100%",
    )

def kpi_card(label: str, value: str) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="sm", color="gray"),
        rx.heading(value, size="lg"),
        padding="4",
        border="1px solid",
        border_radius="md",
    )
```

Uses `rx.metric` indirectly via a custom card (since `rx.metric` styling is more limited).

### 6.3 `csv_export.py`

```python
import io
import csv
import reflex as rx

def csv_export(data: list[dict], filename: str) -> rx.Component:
    def _make_csv():
        buf = io.StringIO()
        if not data:
            return ""
        writer = csv.DictWriter(buf, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return buf.getvalue()

    csv_text = _make_csv()

    return rx.download(
        rx.button("Export CSV"),
        data=csv_text.encode("utf-8"),
        filename=filename,
    )
```

## 7. Routing

```python
# app.py
import reflex as rx
from pages import equity, crypto, economy, home

app = rx.App()
app.add_page(home.index, route="/")
app.add_page(equity.page, route="/equity/[ticker]")        # dynamic
app.add_page(crypto.page, route="/crypto/[symbol]")
app.add_page(economy.page, route="/economy")
```

Dynamic routes (e.g., `/equity/AAPL`) use Reflex's bracket syntax.

## 8. Concurrency model

- All `data/` functions are `async`
- The Reflex event handlers are also `async`
- The state object is mutated inside the event handler (Reflex serializes state automatically)
- No background tasks in v1; polling is triggered by state events only

## 9. Testing strategy

- **Unit tests** for `data/` functions with a mocked OpenBB SDK (using `unittest.mock`)
- **Component tests** verify that a given state renders a chart (using `rx.App().add_page()` in test mode)
- **E2E test** is a manual smoke test: `reflex run`, navigate to `/equity/AAPL`, see a chart
- **No** full Playwright suite in v1 (would be a v2 effort)

## 10. Performance budget

| Path | Budget | How |
|---|---|---|
| Cold start (no cache) | < 3s | Single SDK call + chart render |
| Warm cache hit | < 500ms | `TTLCache.get` + chart render |
| Date range change | < 500ms (hit) / < 3s (miss) | Same as above |
| Comparison add | < 3s | One new SDK call, then merge into existing chart data |

## 11. Deployment

The app is started locally:
```bash
pip install reflex-openbb-ui
reflex-openbb  # or: python -m reflex_openbb
```

This starts a Reflex dev server on `http://localhost:3000`.

A future v2 may add a Docker image or a hosted version (PaaS). v1 is local-only (Art. 7).

## 12. Constitution check

- **Art. 1 (open-source):** all dependencies MIT/Apache-2.0. ✅
- **Art. 2 (Reuse custom components):** `reflex-rosencharts` is used in `price_chart.py`; `reflex-tanstack-charts` for candlestick. ✅
- **Art. 3 (OpenBB only):** §3 / §5 — only `data/` calls `obb.`. ✅
- **Art. 4 (EARS):** PRD section 10 enumerates REQ-001..010; tests will cite these. ✅
- **Art. 5 (Decimal):** §5.4 — Pydantic model coerces to `Decimal` via `str()`. ✅
- **Art. 6 (cache):** §5.1 — TTL cache on every data function. ✅
- **Art. 7 (single-tenant, local):** §11 — no auth, no DB, local-only. ✅
- **Art. 8 (component-first):** §2 — module structure with one file per component. ✅
- **Art. 9 (pre-commit):** §9 — pre-commit will be configured in the repo scaffold task. ✅

No exceptions.
