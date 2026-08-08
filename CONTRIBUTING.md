# Contributing

Thank you for your interest in contributing to reflex-openbb! This
document covers the development workflow, coding standards, and how
to submit changes.

## Development setup

```bash
# Clone the repo
git clone https://github.com/ecrespo/reflex-openbb
cd reflex-openbb

# Install with uv (recommended)
uv sync

# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check

# Run the dev server
uv run reflex run
```

## TDD is mandatory

This project follows strict TDD (Test-Driven Development). Every new
feature, bug fix, or refactor must follow the red-green-refactor cycle:

1. **RED**: Write a failing test that captures the desired behavior.
2. **GREEN**: Write the minimum code to make the test pass.
3. **REFACTOR**: Clean up the code while keeping tests green.

The Constitution (Article 8) says: "Tests are primary artifacts". This
means tests are not optional. A PR without tests for new behavior
will be rejected.

### Test placement

| Layer | Test file | Coverage |
|-------|-----------|----------|
| Data | `tests/test_data_*.py` | All 8 data functions |
| State | `tests/test_*_state.py` | 4 state classes + 2 audit files |
| Components | `tests/test_<component>.py` | 9 components |
| Pages | `tests/test_<page>.py` | 4 page compositions |
| Service | `tests/test_<service>.py` | CSV export |

### REQ-IDs in test docstrings

Every test must cite the REQ it covers in its docstring:

```python
def test_get_equity_quote_returns_pydantic_model() -> None:
    """REQ-001: get_equity_quote returns an EquityQuote pydantic model."""
    ...
```

This is Constitution Article 4 and is enforced by
`tests/test_req_coverage.py`.

## Coding standards

- **Python 3.10+** — use type hints everywhere
- **Ruff** — `uv run ruff check` must pass
- **No mocking of OpenBB SDK in tests** — import with `import openbb as _openbb`
  inside the function and patch the import
- **State handlers use xfail** — `rx.State` requires an app context
  (State Manager) that is not available in plain unit tests. Mark
  handler tests with `@pytest.mark.xfail(strict=False, reason="...")`.

## Submitting a PR

1. Fork the repo
2. Create a feature branch from `develop`:
   `git checkout -b feat/your-feature develop`
3. Make your changes (with tests)
4. Verify `uv run pytest tests/ -v` and `uv run ruff check` pass
5. Push to your fork
6. Open a PR against `develop`

We use **squash merges** with `--delete-branch` to keep the history
clean.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(state): add EquityState (T-202)
fix(cache): invalidate TTL on data mutation
docs(readme): add install instructions
test(state): add state re-render tests (T-206)
```

## Architecture

See [`specs/`](./specs/) for the full design. Key documents:

- [Constitution](./specs/constitution.md) — 9 articles that govern
  every decision
- [PRD](./specs/prd/mvp.md) — 10 user requirements (REQ-001..010)
- [Architecture](./specs/technical/v1-architecture.md) — system design
- [Tasks](./specs/tasks/v1-tasks.md) — task breakdown by phase
- [API](./specs/api/v1.md) — function signatures and contracts

## Code of conduct

Be kind. Disagree on ideas, not people. We're all here to build
something useful together.
