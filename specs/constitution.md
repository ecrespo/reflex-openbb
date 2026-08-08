# Constitution — reflex-openbb

> Version 1.0 · Ratified: 2026-08-08 · Last amended: 2026-08-08
> Scope: ecrespo/reflex-openbb and the `reflex-openbb-ui` PyPI package

## Articles

### Art. 1 — Open-source stack only
THE SYSTEM SHALL be built entirely with open-source dependencies (MIT, BSD, Apache-2.0);
no closed-source SDKs and no paid data providers in the default config.
*Rationale: The project is a public open-source alternative to OpenBB Pro (closed SaaS). Closed deps in the default path defeat the mission.*

### Art. 2 — Reflex + the existing custom-component catalog
THE SYSTEM SHALL use Reflex 0.8+ as the only web framework and SHALL prefer the existing 22 custom components in `ecrespo/reflex-*` over new wrappers whenever a feature maps to one of them.
*Rationale: The author already maintains a curated custom-component catalog; reusing it reduces duplication and ships features faster.*

### Art. 3 — Data layer via OpenBB Python SDK
THE SYSTEM SHALL obtain all financial data exclusively through the `openbb` Python SDK (`obb`); the app SHALL NOT scrape provider sites directly.
*Rationale: The OpenBB SDK is the legal, supported integration point. Direct scraping is fragile and likely to violate provider ToS.*

### Art. 4 — EARS criteria for every MUST requirement
THE TEAM SHALL express every MUST functional requirement as EARS-notation criteria (REQ-NNN) before the implementation task is generated, and every test SHALL cite the REQ it verifies.
*Rationale: EARS makes acceptance criteria machine-verifiable; traceability prevents "shipped but unmeasurable" features.*

### Art. 5 — Money is Decimal, never float
THE SYSTEM SHALL represent monetary values as `Decimal`; floats SHALL NOT appear in any financial computation, serialization, or display path.
*Rationale: Binary float cannot represent 0.10 exactly. Aggregations across thousands of quotes accumulate error. Decimal is non-negotiable for finance.*

### Art. 6 — Cache every external call
THE SYSTEM SHALL cache every OpenBB SDK call with a configurable TTL (default 5 min for quotes, 1 day for fundamentals, 7 days for reference data) keyed by `provider + symbol + params + date`.
*Rationale: OpenBB free providers have rate limits. Aggressive caching keeps the demo responsive and prevents 429s.*

### Art. 7 — App is single-tenant, local-first
THE SYSTEM SHALL run as a single-user, local-first app (no auth, no multi-tenancy in v1) and SHALL expose an optional `OPENBB_PAT` env var for users who configure paid providers.
*Rationale: The v1 use case is the author (and other individual analysts) running it on their own machine. Premature multi-tenancy adds complexity without a real user.*

### Art. 8 — Component-first architecture
THE SYSTEM SHALL organize code as self-contained components: each feature is one Reflex state class plus one component module; cross-cutting concerns (caching, error handling) live in shared services.
*Rationale: The app has many small features (ticker chart, fundamentals, news, KPIs). Component-first keeps each one shippable and testable in isolation.*

### Art. 9 — Pre-commit gate is non-negotiable
THE TEAM SHALL keep the pre-commit gate (Ruff, ty, Bandit, Gitleaks) green; no merge with hooks disabled.
*Rationale: The repo is intended to be read by other Reflex developers. A high signal-to-noise codebase builds trust.*

## Stack constraints

| Concern | Decision | Version (min) |
|---|---|---|
| Language | Python | 3.10+ |
| Web framework | Reflex | 0.8+ |
| Data SDK | openbb | 4.x (latest) |
| Charts (primary) | `reflex-rosencharts` | latest |
| Charts (specialty) | `reflex-tanstack-charts` | latest |
| Graph viz | `reflex-xyflow` | latest |
| Tables | `rx.table` (Reflex native, Radix) | bundled |
| Markdown | `rx.markdown` (Reflex native) | bundled |
| KPIs / metrics | `rx.metric` (Reflex native, Radix) | bundled |
| State | `rx.State` + `rx.Var` | bundled |
| Caching | `cachetools.TTLCache` (stdlib-only) | 5.x |
| Tests | `pytest` + `pytest-asyncio` | latest |
| Type-check | `ty` (Astral) or `mypy --strict` | latest |
| Lint | `ruff` | latest |
| Security | `bandit` + `gitleaks` | latest |
| Build | `reflex component build` for custom components | bundled |

## Amendments

| Date | Article | Change | Reason | Approved by |
|---|---|---|---|---|
| 2026-08-08 | — | Initial ratification | Project kickoff | Ernesto Crespo |

## Constitution check (use in every artifact)

A 3-5 line section at the end of every PRD / Tech Design / Plan listing which articles apply and how they are satisfied — or which exception is requested and why. An exception without written justification is a violation.
