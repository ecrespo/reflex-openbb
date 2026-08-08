# Release v0.1.0 — 2026-08-08

## 🎉 First public release of reflex-openbb

**reflex-openbb** is the open-source OpenBB UI in pure Python (Reflex).
Equity / Crypto / Economy dashboards consuming the `openbb` SDK.

This is v0.1.0 — the MVP is functionally complete.

## What's in the box

- **Equity dashboard** — quote, 6-KPI grid, price chart (5 date
  ranges), fundamentals table, news feed
- **Crypto dashboard** — price chart for any symbol (BTC, ETH, etc.)
- **Economy dashboard** — macro data (GDP, CPI, UNRATE) for 6 countries
- **Global search** — type a ticker on the home page, navigate to the
  right dashboard
- **CSV export** — download the chart's data with Decimal precision
  preserved
- **Multi-ticker overlay** — compare up to 5 tickers on the same chart
- **Stale-data banner** — graceful degradation when a provider fails
- **TTL cache + rate limiter + circuit breaker** — robust against
  provider issues

## By the numbers

- 297 tests (271 verde, 3 xfailed, 23 xpassed)
- Ruff clean
- 5 PRs merged (#1..#5)
- 6 phases delivered (scaffold → data → state → pages → features → docs)
- 9 components, 4 pages, 4 state classes, 8 data functions

## Install

```bash
pip install reflex-openbb
```

## Run

```bash
reflex-openbb
# Opens http://localhost:3000
```

## Links

- **Repository**: https://github.com/ecrespo/reflex-openbb
- **Documentation**: https://github.com/ecrespo/reflex-openbb/tree/main/docs
- **Issues**: https://github.com/ecrespo/reflex-openbb/issues
- **Spec kit**: https://github.com/ecrespo/reflex-openbb/tree/main/specs

## What's next

v0.2.0 (next minor):
- T-006: manual `reflex run` smoke (user task)
- T-009: GitHub Actions CI
- T-410: screenshots
- More providers (FMP, Polygon, Alpha Vantage) — depends on user feedback

## License

Apache-2.0

## Contributors

- Ernesto Crespo (@ecrespo) — author, maintainer
- Hermes Agent — TDD co-pilot, generated 60% of test code

---

If you find this useful, ⭐ the repo and share it with your
finance/data friends. If you find a bug, please open an issue.
