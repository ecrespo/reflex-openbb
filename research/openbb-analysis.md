# Research Notes — OpenBB and Reflex

> Compiled 2026-08-08 as background for the `reflex-openbb` spec kit.

## 1. What is OpenBB?

OpenBB is an open-source financial data platform with a Python SDK and a closed-source UI called OpenBB Workspace (or OpenBB Pro, the paid SaaS version).

| Stat | Value |
|---|---|
| GitHub stars | 71.3k |
| Forks | 7.3k |
| License (SDK) | AGPLv3 |
| License (Pro) | Closed |
| Repo | https://github.com/OpenBB-finance/OpenBB |
| Website | https://openbb.co/ |

The tagline: **"Open Data Platform for analysts, quants and AI agents"**.

## 2. Architecture

```
openbb_platform/
├── core/openbb/         # core API
└── extensions/          # 17+ data domains
    ├── commodity/
    ├── crypto/
    ├── currency/
    ├── derivatives/
    ├── econometrics/
    ├── economy/         ← macro data
    ├── equity/          ← stocks
    ├── etf/
    ├── famafrench/
    ├── fixedincome/
    ├── index/
    ├── mcp_server/      ← MCP server for AI agents
    ├── news/
    ├── quantitative/
    ├── regulators/
    └── technical/
```

The Python SDK returns a `OBBject` (their custom result type) that can be converted to a DataFrame with `.to_dataframe()`.

```python
from openbb import obb
output = obb.equity.price.historical("AAPL", period="1y")
df = output.to_dataframe()
```

## 3. OpenBB Workspace — the closed UI

The Workspace is a React app with these widget types:
- **Chart** (Plotly, TradingView, Vega-Lite)
- **Table**
- **Metric** (KPI)
- **Markdown**
- **Newsfeed**
- **Iframe** (embed any URL)
- **Note** (text widget)
- **PDF / Website** (viewer widgets)
- **YouTube** (video embed)
- **AI** (Copilot chat)

It is the gold standard for an open-source financial dashboard UI, but it is **closed source** and **requires a paid subscription** to use in any non-trivial way.

## 4. The opportunity

There is no polished open-source alternative to OpenBB Workspace written in pure Python. The closest options are:

| Option | Cost | Stack | Open source? |
|---|---|---|---|
| OpenBB Pro | $50-300/mo | React | ❌ |
| OpenBB CLI (`openbb-cli`) | Free | Python CLI | ✅ |
| Streamlit + OpenBB SDK | Free | Python | ✅ but per-analysis |
| Bokeh / Panel | Free | Python | ✅ but no financial domain knowledge |
| **Reflex + OpenBB SDK** | Free | Python | ✅ **and full app** |

The third row is the gap that `reflex-openbb` fills.

## 5. Reflex custom components available

The author already maintains 22 Reflex custom components, many of which directly map to OpenBB Workspace widgets:

| OpenBB widget | Reflex component (existing) | Coverage |
|---|---|---|
| Line chart | `reflex-rosencharts` (43 charts) | ✅ |
| Candlestick | `reflex-tanstack-charts` | ✅ |
| Bar chart | `reflex-rosencharts` | ✅ |
| Table | `rx.table` (Reflex native) | ✅ |
| Metric / KPI | `rx.metric` (Reflex native) | ✅ |
| Markdown | `rx.markdown` (Reflex native) | ✅ |
| Newsfeed card | `rx.card` (Reflex native) | ✅ |
| Heatmap | (no wrapper; use Plotly directly) | ⚠ |
| Tree map | (no wrapper; use Plotly directly) | ⚠ |
| Correlation network | `reflex-xyflow` or `reflex-gravityui-graph` | ✅ |
| Iframe | `rx.html` or embed | ✅ |
| AI Copilot chat | (no wrapper; would need `assistant-ui`) | ⚠ |

For v1, we use only ✅ rows. The ⚠ rows are deferred to v2.

## 6. Why this is "Option B" (the chosen path)

The user picked **Option B**: "Replicar la UI de OpenBB Workspace en Reflex" — but with a critical scope reduction. We are **not cloning the full OpenBB Workspace** (which would take 6-12 months). We are:

1. Consuming the **open OpenBB Python SDK** (the data layer)
2. Building a **3-page focused app** (Equity, Crypto, Economy) that exercises the most-used widgets
3. Reusing the **author's existing custom-component catalog** (no need to build from scratch)

This is the "**Strategy A from the feasibility analysis**" — what was originally called "OpenBB Reflex UI" and is now named `reflex-openbb`.

## 7. Why AGPLv3 is not a blocker

The OpenBB SDK is AGPLv3. The custom components in `ecrespo/reflex-*` are Apache-2.0. The combination is:

- Our app is Apache-2.0 (we set the license).
- The OpenBB SDK is a **runtime dependency**, not linked code. AGPLv3's "convey" clause applies to modifications of the SDK itself, not to programs that use it via `pip install openbb`. So we can ship a closed-or-open app that uses the SDK without AGPLv3 infecting our app.
- If we ever wanted to **modify** the OpenBB SDK, those modifications would be AGPLv3. We don't plan to.

This is the same pattern as using a BSD-licensed database: the application can be MIT/Apache, even if the database isn't.

## 8. Free data providers used by default

The `openbb` package, when installed with `openbb[all]`, pulls in adapters for many providers. The free ones relevant to v1:

- `yfinance` — equity prices, fundamentals, news
- `cboe` — equity quotes
- `fred` — macro data (CPI, GDP, UNRATE) — **requires `FRED_API_KEY`**
- `sec` — SEC filings
- `coinmarketcap` — crypto — **requires API key**

For v1, the default config uses `yfinance` for everything. If `FRED_API_KEY` is set, the economy page uses real FRED data. If not, the page is disabled with a friendly message.

## 9. References

- OpenBB repo: https://github.com/OpenBB-finance/OpenBB
- OpenBB docs: https://docs.openbb.co/
- OpenBB Workspace docs: https://docs.openbb.co/workspace/llms-full.txt
- Custom components: https://github.com/ecrespo (search "reflex-")
- AGPLv3 compatibility: https://www.gnu.org/licenses/agpl-3.0.html
