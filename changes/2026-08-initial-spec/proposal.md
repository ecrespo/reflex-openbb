# Change Proposal — Initial spec for `reflex-openbb` v1.0

> **Status:** DRAFT · **Author:** Ernesto Crespo · **Date:** 2026-08-08
> **Affects:** new project `ecrespo/reflex-openbb` (greenfield; no existing specs to delta against)
> **Reviewers:** self-review pending

## Summary

This change introduces the **complete spec kit** for the new project `reflex-openbb` — an open-source web app that consumes the OpenBB Python SDK and presents equity / crypto / economy data through a Reflex UI built on the author's existing custom-component catalog.

This is a **greenfield** project: there is no pre-existing `specs/` to delta against. So this document plays two roles:

1. **As a Delta Spec** (per the SDD template): the formal proposal for kicking off the project.
2. **As a Project Brief**: the entry point any new contributor reads to understand "what is this and why".

## Motivation

- OpenBB Pro (the official UI) is closed SaaS at $50-300/month.
- The OpenBB Python SDK is open-source but has no first-class UI.
- Existing alternatives require either Streamlit code, paid subscription, or a non-Python stack.
- The author already maintains 22 Reflex custom components that cover ~80% of the chart needs.

## What is included

The full SDD spec kit is in `specs/`:

| Artifact | Path |
|---|---|
| Constitution | `specs/constitution.md` |
| PRD with EARS criteria | `specs/prd/mvp.md` |
| API Spec | `specs/api/v1.md` |
| Technical Design | `specs/technical/v1-architecture.md` |
| Data Model | `specs/data-model/v1-models.md` |
| Implementation Plan | `specs/plans/v1-phase-plan.md` |
| Tasks | `specs/tasks/v1-tasks.md` |
| Analyze gate | (next step — run after spec approval) |
| This Delta Spec | `changes/2026-08-initial-spec/proposal.md` |

The 10 functional requirements (REQ-001..010) are machine-verifiable and each has a test that cites it. Every Task in `tasks/v1-tasks.md` cites the REQ it implements.

## Open questions for review

These are decisions that the author wants a sanity check on before implementation. They are NOT blockers for starting Phase 0/1, but they shape Phase 3+.

1. **Multi-ticker comparison UX**: is overlay-on-same-axes the right v1 pattern, or should it be small-multiples (grid of charts)? The PRD currently picks overlay. See REQ-009.

2. **Crypto coverage**: should `crypto/` be limited to USD-priced top-100 by market cap, or accept any symbol? Currently the spec accepts any symbol; the data layer just forwards to `obb.crypto.price.historical`. This may hit rate limits on free providers for less common symbols.

3. **"Stale data" banner**: when the cache is stale AND the provider is down, do we show a "data may be stale" banner, or block the chart entirely? PRD says "show the cached value with a banner" (REQ-001 UW). Confirm this is acceptable UX.

4. **Naming of the PyPI package**: `reflex-openbb-ui` (the wrapper components) vs `reflex-openbb` (the app). Currently the convention is `reflex-openbb-ui` for the PyPI artifact, and the user runs `reflex-openbb` (a CLI script) to launch. Confirm the naming.

5. **Whether to add auth in v1.1**: the spec excludes auth (Art. 7) but a hosted version would need it. The roadmap hint is in `prd/mvp.md` §5.3. Confirm we want to keep v1 local-only.

## Acceptance criteria for this change

This proposal is **accepted** when:

- [x] Constitution exists and is ratified (9 articles)
- [x] PRD exists with at least 5 functional requirements and EARS-notation criteria
- [x] API Spec exists with module-level functions
- [x] Technical Design exists with module structure
- [x] Data Model exists with Pydantic schemas
- [x] Implementation Plan has phases and tasks
- [x] Tasks have unique IDs, REQ citations, and estimates
- [ ] Analyze gate has been run and no P0/P1 findings are open
- [ ] Constitution check sections appear in every artifact

## After acceptance

Once accepted:

1. The spec kit is moved from `changes/2026-08-initial-spec/` to `specs/` (already done in this proposal).
2. A git branch `feat/v1-scaffold` is created from the approved specs.
3. Phase 0 (T-001..T-009) is executed as a single PR.
4. Each subsequent phase becomes a separate PR.

## Out of scope (deferred to v2+)

- Auth, multi-tenant
- Real-time WebSocket streaming
- Drag-and-drop dashboard builder
- AI Copilot (will use OpenBB's `mcp_server` extension)
- Backtesting engine
- Mobile responsive design
- Paid data provider integrations

## Constitution check (this Delta Spec)

- **Art. 1 (open-source):** the project is Apache-2.0; no closed-source deps. ✅
- **Art. 4 (EARS for MUSTs):** REQ-001..010 are in EARS. ✅
- **Art. 7 (single-tenant, local):** v1 is local-only. ✅

No exceptions.
