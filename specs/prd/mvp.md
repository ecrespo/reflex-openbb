# reflex-openbb — MVP (Equities, Crypto, Economy)

## Product Requirements Document (PRD)

| Field | Value |
|---|---|
| **Author** | Ernesto Crespo |
| **Status** | `DRAFT` |
| **Version** | 1.0 |
| **Date** | 2026-08-08 |
| **Reviewers** | Pending self-review |
| **Last updated** | 2026-08-08 |

---

## 1. Executive Summary

`reflex-openbb` is an open-source web app that lets an individual investor or analyst explore financial data (equities, crypto, economy) without paying for a Bloomberg terminal or OpenBB Pro subscription. It is built in pure Python on top of the **Reflex** web framework and the **OpenBB Python SDK**, reusing the existing `ecrespo/reflex-*` custom-component catalog for all visualizations.

The MVP scope is a local-first, single-user app with three working pages: **Equity** (price, fundamentals, news for any ticker), **Crypto** (price + on-chain stats), and **Economy** (indicator dashboards). Everything runs on the user's machine, uses only free OpenBB providers, and ships as a single `pip install reflex-openbb` command.

The strategic position is "an open-source OpenBB Workspace, written in pure Python" — a category that today is served only by OpenBB Pro (closed SaaS) and Streamlit (not Python-pure).

## 2. Context and Problem

### 2.1 Current Situation
- OpenBB Pro (the official UI) is closed-source SaaS at $50-300/month.
- The OpenBB Python SDK is open-source (AGPLv3) but has no first-class UI; users wire their own Streamlit / Jupyter.
- The author already maintains 22 Reflex custom components that cover ~80% of the chart/visualization needs for a financial app.
- A pure-Python alternative (Reflex) would let any Python analyst spin up a local dashboard without JavaScript, Streamlit, or a paid subscription.

### 2.2 Problem
- Individual analysts without enterprise budgets have no polished open-source UI to consume OpenBB data.
- Existing alternatives require either: (a) writing Streamlit code per analysis, (b) paying for OpenBB Pro, or (c) switching to a non-Python stack.

### 2.3 Opportunity
- The Reflex custom-component catalog (`reflex-rosencharts`, `reflex-tanstack-charts`, `reflex-xyflow`, etc.) is already production-grade.
- A focused MVP (3 pages) can be built in 1-2 weeks by composing existing components.
- Differentiation: pure-Python stack, Apache-2.0 license (vs AGPLv3 for OpenBB SDK), no auth/multi-tenancy complexity.

## 3. Target Users

### Persona 1: Solo Retail Investor (primary v1 user)
- **Description:** Self-directed investor in Venezuela / LATAM, USD-constrained, exploring equities and crypto in spare time.
- **Primary need:** Quickly check price, fundamentals, and recent news for a ticker without paying for a terminal.
- **Usage frequency:** Weekly to daily
- **Technical level:** Medium (can run `pip install`, comfortable with Python venv, no interest in writing JS)

### Persona 2: Quant Hobbyist (secondary)
- **Description:** Python developer who already uses Reflex for side projects.
- **Primary need:** Visual backtest results, correlation networks, factor dashboards.
- **Usage frequency:** Daily during strategy iteration
- **Technical level:** High (Reflex power user; will read source and contribute)

### Persona 3: Student (tertiary, aspirational)
- **Description:** Finance or CS student learning quantitative methods.
- **Primary need:** Free exploration of real financial data.
- **Usage frequency:** Occasional
- **Technical level:** Low to medium

## 4. Goals and Success Metrics

### 4.1 Project Goals

| Goal | Metric | Target | Timeframe |
|---|---|---|---|
| Ship a working v1 MVP | All 3 pages load and render data | 3/3 functional | 2 weeks from approval |
| Validate demand | GitHub stars | 50+ stars within 30 days of public release | 30 days post-release |
| Validate usability | "It just works" demo at 5-friends test | 4/5 say "I would use this" | Pre-release |
| Establish installable artifact | `pip install reflex-openbb-ui` | Latest version on PyPI | Release day |

### 4.2 User Goals

| User Goal | Indicator |
|---|---|
| Check a ticker's price history | Equity page renders line chart in < 2s after ticker entered |
| Compare two tickers | Multi-ticker comparison page (post-MVP) |
| See recent news for a holding | News feed on Equity page loads ≥ 5 items |
| Track macro indicators | Economy page shows GDP, inflation, unemployment for chosen country |

## 5. Scope

### 5.1 In Scope (Included in MVP)
- [ ] Single-user local app (no auth)
- [ ] Three pages: `/equity/{ticker}`, `/crypto/{symbol}`, `/economy/{country?}`
- [ ] Equity page: price chart, fundamentals table, news feed, KPI metrics
- [ ] Crypto page: price chart, market cap, 24h volume, recent news
- [ ] Economy page: indicator selector, multi-series line chart
- [ ] Multi-ticker comparison (overlay line charts)
- [ ] Date range picker
- [ ] CSV export of displayed data
- [ ] Caching layer with 5-min TTL on quotes
- [ ] `pip install reflex-openbb-ui` (the custom-components package)
- [ ] Documentation: README, quickstart, screenshots
- [ ] MIT/Apache-2.0 license

### 5.2 Out of Scope (Excluded from MVP)
- [ ] Authentication / multi-user (deferred to v2)
- [ ] Real-time WebSocket streaming (polling at 5-min cadence is sufficient for v1)
- [ ] Drag-and-drop dashboard builder (would need react-grid-layout wrapper)
- [ ] Excel add-in integration
- [ ] AI Copilot / NL-to-query (planned for v2)
- [ ] Backtesting engine (planned for v2)
- [ ] Mobile-first responsive design (desktop-only is acceptable for v1)
- [ ] Paid data provider integrations (free providers only in v1)
- [ ] Internationalization (English UI only)

### 5.3 Future Considerations (v2+)
- [ ] AI Copilot using OpenBB's `mcp_server` extension
- [ ] Drag-and-drop dashboard builder
- [ ] Auth + multi-tenant (only if there's a real need)
- [ ] Backtesting workspace
- [ ] Real-time WebSocket streaming
- [ ] Watchlist + alerts

## 6. Functional Requirements

### FR-001: Equity Price Chart
- **Description:** The system shall render a price line chart for any US-equity ticker.
- **Actor:** User enters a ticker in the URL `/equity/AAPL` or in the search box.
- **Preconditions:** The ticker is a valid symbol recognized by at least one configured OpenBB provider.
- **Main flow:**
  1. User navigates to `/equity/AAPL` (or types "AAPL" in the search box and submits).
  2. App calls `obb.equity.price.historical("AAPL", period="1y")` via cached SDK wrapper.
  3. The result DataFrame is converted to a chart payload.
  4. A line chart is rendered with date on x-axis, close price on y-axis.
- **Alternative flow:** If the provider returns 429, the cached value (if any) is used and a "stale data" banner is shown.
- **Postconditions:** A chart is visible in the browser.
- **Priority:** `MUST`

### FR-002: Date Range Selector
- **Description:** The system shall allow the user to change the date range of the price chart between 1M, 6M, 1Y, 5Y, and Max.
- **Actor:** User clicks a button in the date-range control.
- **Preconditions:** The Equity page is loaded with a valid ticker.
- **Main flow:**
  1. User clicks "1M" / "6M" / "1Y" / "5Y" / "Max".
  2. State updates; cache is checked; if miss, SDK is called.
  3. Chart re-renders with the new range.
- **Postconditions:** Chart re-renders within 500ms (cache hit) or 3s (cache miss).
- **Priority:** `MUST`

### FR-003: Equity Fundamentals Table
- **Description:** The system shall display a table of fundamental metrics (P/E, Market Cap, EPS, Dividend Yield, etc.) for the selected ticker.
- **Actor:** User navigates to the Equity page.
- **Preconditions:** Ticker is loaded.
- **Main flow:**
  1. App calls `obb.equity.fundamental.metrics("AAPL")`.
  2. The result is rendered as an `rx.table` with two columns: Metric / Value.
- **Postconditions:** A fundamentals table is visible.
- **Priority:** `MUST`

### FR-004: Equity News Feed
- **Description:** The system shall display the 10 most recent news articles for the selected ticker.
- **Actor:** User is on the Equity page.
- **Preconditions:** Ticker is loaded.
- **Main flow:**
  1. App calls `obb.news.company("AAPL", limit=10)`.
  2. The result is rendered as a list of `rx.card` with title, source, date, and link.
- **Postconditions:** A news feed is visible.
- **Priority:** `MUST`

### FR-005: Equity KPI Cards
- **Description:** The system shall display 4-6 KPI metrics (current price, day change %, market cap, volume, 52w high, 52w low) at the top of the Equity page.
- **Actor:** User is on the Equity page.
- **Preconditions:** Ticker is loaded.
- **Main flow:**
  1. App calls `obb.equity.quote("AAPL")` and `obb.equity.fundamental.metrics("AAPL")`.
  2. Six `rx.metric` cards are rendered in a grid.
- **Postconditions:** KPI grid is visible.
- **Priority:** `SHOULD`

### FR-006: Crypto Price Chart
- **Description:** The system shall render a price line chart for any crypto symbol (e.g., BTC, ETH).
- **Actor:** User navigates to `/crypto/BTC` or selects from a dropdown.
- **Preconditions:** The symbol is recognized.
- **Main flow:** Same shape as FR-001 but with `obb.crypto.price.historical(symbol, period)`.
- **Postconditions:** Chart is visible.
- **Priority:** `MUST`

### FR-007: Economy Indicator Dashboard
- **Description:** The system shall display a multi-series line chart for one or more macroeconomic indicators (GDP, CPI, Unemployment) for a chosen country.
- **Actor:** User navigates to `/economy/US` (default) and selects an indicator.
- **Preconditions:** Country is selected.
- **Main flow:**
  1. App calls `obb.economy.indicator(indicator="GDP", country="US")`.
  2. Result rendered as a line chart with year on x-axis.
- **Postconditions:** Chart is visible.
- **Priority:** `MUST`

### FR-008: CSV Export
- **Description:** The system shall allow the user to download the currently displayed chart data as a CSV file.
- **Actor:** User clicks an "Export CSV" button.
- **Preconditions:** Some data is loaded.
- **Main flow:**
  1. User clicks the button.
  2. A CSV file is generated in-memory and downloaded via `rx.download`.
- **Postconditions:** A `.csv` file is saved to the user's machine.
- **Priority:** `SHOULD`

### FR-009: Multi-Ticker Comparison
- **Description:** The system shall allow the user to overlay price charts for 2-5 tickers on the same axes.
- **Actor:** User adds additional tickers to the comparison.
- **Preconditions:** At least one ticker is loaded.
- **Main flow:**
  1. User types another ticker and clicks "Add to comparison".
  2. App fetches the data and overlays the line.
  3. A legend identifies each series.
- **Postconditions:** Multi-line chart is visible.
- **Priority:** `COULD`

### FR-010: Search
- **Description:** The system shall provide a global search box that resolves a ticker or crypto symbol to a page.
- **Actor:** User types in the search box and submits.
- **Preconditions:** None.
- **Main flow:**
  1. User types "AAPL" and presses Enter.
  2. The app routes to `/equity/AAPL` (or to the most likely match).
- **Postconditions:** User lands on the appropriate page.
- **Priority:** `MUST`

## 7. Non-Functional Requirements

### Performance
- NFR-001: The first render of a page with cached data SHALL complete in < 500ms.
- NFR-002: The first render with a cache miss SHALL complete in < 3s (typical home network).
- NFR-003: The app SHALL handle a 1M-row historical fetch by downsampling to 5K visible points before charting (chart responsiveness < 100ms).

### Security
- NFR-004: The system SHALL NOT log any user-entered ticker data in a way that persists across restarts.
- NFR-005: The system SHALL respect the `OPENBB_PAT` env var if set, but SHALL NOT require it.

### Availability
- NFR-006: The app is a local CLI process; no SLA is defined. If a provider is down, the cache is used.

### Scalability
- NFR-007: The app is single-user; horizontal scaling is out of scope.

### Observability
- NFR-008: The app SHALL print a one-line status to stdout on every OpenBB call: `[OpenBB] <provider>.<endpoint> <symbol> (<elapsed_ms>ms)`.

### License
- NFR-009: The project SHALL be released under Apache-2.0 (consistent with the author's other custom components).

## 8. Constraints and Dependencies

### Technical Constraints
- Reflex 0.8+ required (uses NoSSRComponent, typed state)
- Python 3.10+ (3.9 dropped by Reflex)
- OpenBB Python SDK 4.x
- Linux/macOS (Windows is best-effort)

### Business Constraints
- The author (Ernesto Crespo) is the sole maintainer
- Time budget: ~2 weeks of evenings/weekends for v1

### External Dependencies

| Dependency | Type | Owner | Status | Risk |
|---|---|---|---|---|
| OpenBB Python SDK | Library | OpenBB-finance | v4.x stable | High — API changes between minors |
| Free data providers (yfinance, FRED, etc.) | API | various | Working | Medium — free tier rate limits |
| `reflex-rosencharts` | Custom component | ecrespo | Active | Low — author controls it |
| `reflex-tanstack-charts` | Custom component | ecrespo | Active | Low |
| `reflex-xyflow` | Custom component | ecrespo | Active | Low |
| Reflex framework | Library | reflex-dev | Active | Low |

## 9. User Stories

### Epic: Equity Explorer

**US-001:** As a retail investor, I want to see a price chart for any ticker by typing the symbol in the URL, so that I can quickly check historical performance.
- Acceptance criteria: see FR-001 + REQ-001.

**US-002:** As a retail investor, I want to switch the date range between 1M/6M/1Y/5Y/Max with one click, so that I can zoom in on a period of interest.
- Acceptance criteria: see FR-002 + REQ-002.

**US-003:** As a retail investor, I want to see the current price, day change, and market cap as KPI cards, so that I can scan the most relevant numbers at a glance.
- Acceptance criteria: see FR-005 + REQ-005.

**US-004:** As a retail investor, I want to read recent news about a company, so that I can understand the context behind a price move.
- Acceptance criteria: see FR-004 + REQ-004.

**US-005:** As a retail investor, I want to see fundamental ratios (P/E, EPS, dividend yield), so that I can compare companies quickly.
- Acceptance criteria: see FR-003 + REQ-003.

### Epic: Crypto Explorer

**US-006:** As a crypto holder, I want a price chart for any coin, so that I can track my portfolio.
- Acceptance criteria: see FR-006 + REQ-006.

### Epic: Economy Dashboard

**US-007:** As a macro investor, I want to plot GDP/inflation/unemployment for a country, so that I can track economic trends.
- Acceptance criteria: see FR-007 + REQ-007.

### Epic: Power features

**US-008:** As an analyst, I want to export the chart data as CSV, so that I can paste it into my own spreadsheet.
- Acceptance criteria: see FR-008 + REQ-008.

**US-009:** As an analyst, I want to overlay 2-5 tickers on the same chart, so that I can visually compare them.
- Acceptance criteria: see FR-009 + REQ-009.

**US-010:** As any user, I want a global search box, so that I can navigate without typing URLs.
- Acceptance criteria: see FR-010 + REQ-010.

## 10. EARS Acceptance Criteria

The following criteria are machine-verifiable. Each is referenced by a test (see `tasks/`).

### REQ-001 — Equity price chart loads
- **U (ubiquitous):** THE SYSTEM SHALL render a line chart for `/equity/{ticker}` when the ticker is recognized by at least one configured provider.
- **E (event-driven):** WHEN the user types `{ticker}` in the search box and submits, THE SYSTEM SHALL navigate to `/equity/{ticker}` and render the chart.
- **U (state-driven):** WHILE the chart is loading, THE SYSTEM SHALL show a skeleton or "Loading..." placeholder.
- **O (optional):** WHERE the cache has a recent result (≤ 5 min old), THE SYSTEM SHALL render from the cache without calling the provider.
- **UW (unwanted):** IF the provider returns an error or 429, THE SYSTEM SHALL fall back to the cached value (if any) AND display a "stale data" banner.

### REQ-002 — Date range change
- **E:** WHEN the user selects a date range button, THE SYSTEM SHALL re-render the chart with the new range in < 500ms (cache hit) or < 3s (miss).

### REQ-003 — Fundamentals table
- **U:** THE SYSTEM SHALL display a fundamentals table with at least these rows: P/E Ratio, Market Cap, EPS, Dividend Yield, Beta, 52-Week High, 52-Week Low.
- **E:** WHEN the ticker changes, THE SYSTEM SHALL re-fetch and re-render the table.
- **O:** WHERE the provider doesn't return a metric, THE SYSTEM SHALL display "n/a" in that cell, NOT omit the row.

### REQ-004 — News feed
- **U:** THE SYSTEM SHALL display at least 5 news items, each with title, source, date, and a clickable link.
- **E:** WHEN the ticker changes, THE SYSTEM SHALL re-fetch the news.
- **O:** WHERE the provider returns 0 news, THE SYSTEM SHALL display "No recent news for this ticker" instead of an empty list.

### REQ-005 — KPI cards
- **U:** THE SYSTEM SHALL display 6 KPI cards: Current Price, Day Change %, Market Cap, Volume, 52-Week High, 52-Week Low.
- **E:** WHEN a KPI value updates, THE SYSTEM SHALL re-render only the affected card (not the whole page).

### REQ-006 — Crypto price chart
- **U:** THE SYSTEM SHALL render a line chart for `/crypto/{symbol}`.
- **E:** WHEN the user submits a crypto symbol in the search box, THE SYSTEM SHALL navigate to `/crypto/{symbol}`.

### REQ-007 — Economy indicator chart
- **U:** THE SYSTEM SHALL display a line chart of the selected indicator for the selected country.
- **E:** WHEN the user selects an indicator (GDP / CPI / Unemployment) or a country, THE SYSTEM SHALL re-render the chart.

### REQ-008 — CSV export
- **E:** WHEN the user clicks "Export CSV", THE SYSTEM SHALL download a CSV file containing the current chart data (date + value columns) within 1 second.

### REQ-009 — Multi-ticker overlay
- **E:** WHEN the user adds a ticker to the comparison, THE SYSTEM SHALL fetch its data and add a new line to the chart.
- **UW:** IF the user attempts to add a 6th ticker, THE SYSTEM SHALL display "Maximum 5 tickers in comparison" and reject the addition.

### REQ-010 — Search
- **E:** WHEN the user submits text in the global search box, THE SYSTEM SHALL resolve it to a route:
  - If the input matches a known ticker (e.g. `AAPL`) → `/equity/AAPL`
  - If the input matches a known crypto symbol (e.g. `BTC`) → `/crypto/BTC`
  - If no match → display a "Not found" inline message below the search box

## 11. Wireframes / Mockups

(To be added as Figma or text mockups during the Tech Design phase. Initial sketch in `research/mockups.md`.)

## 12. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| OpenBB SDK breaking change between minors | Medium | High | Pin exact version in `pyproject.toml`; subscribe to OpenBB GitHub releases; abstract all SDK calls behind a single `data/` module so a breaking change touches one file |
| Free provider rate-limited (429s) | High | Medium | TTL cache (5 min); graceful degradation with stale banner; support `OPENBB_PAT` for paid fallback |
| Reflex breaking change | Low | High | Pin `reflex>=0.8,<0.9`; subscribe to Reflex changelog |
| Custom component (`reflex-rosencharts`) regression | Low | Medium | Pin exact version; CI smoke-test against the demo app |
| Scope creep (tries to clone OpenBB Pro) | High | Medium | Re-read this PRD scope section weekly; defer everything in §5.2 to v2 |

## 13. Estimated Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| Spec & Design | 2 days (this PRD + Tech Design) | Approved specs |
| Repo scaffold | 1 day | Repo + CI + pre-commit + first deployable empty app |
| Equity MVP | 4 days | FR-001..005 working on `/equity/{ticker}` |
| Crypto + Economy pages | 3 days | FR-006 + FR-007 |
| Search + CSV export + multi-ticker | 2 days | FR-008..010 |
| Polish + docs + PyPI release | 2 days | `pip install reflex-openbb-ui` v0.1.0 |
| **Total MVP** | **~14 days** | v1.0 release |

---

## Constitution check

Articles satisfied by this PRD:
- **Art. 1** (open-source only): all dependencies MIT/Apache-2.0/Berkeley-compatible. ✅
- **Art. 3** (OpenBB SDK only): all data flows through `obb.`. ✅
- **Art. 4** (EARS): section 10 enumerates REQ-001..010 in EARS. ✅
- **Art. 5** (Decimal money): monetary KPIs from `obb.equity.fundamental.metrics` are coerced to `Decimal` in the data layer (Tech Design will detail this). ✅
- **Art. 7** (single-tenant, local-first): scope §5.2 excludes auth. ✅
- **Art. 8** (component-first): one component module per feature. ✅

Exceptions requested: **none.**

## Change History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-08 | Ernesto Crespo | Initial draft |

## Approvals

| Role | Name | Date | Status |
|---|---|---|---|
| Product Owner | Ernesto Crespo | 2026-08-08 | ☐ Pending |
| Tech Lead | Ernesto Crespo | 2026-08-08 | ☐ Pending |
