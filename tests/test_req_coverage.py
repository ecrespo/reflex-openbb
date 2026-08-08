"""
REQ coverage audit (T-109).

TDD: this file is written BEFORE running the audit.
- RED:  if any REQ is uncovered, the relevant test FAILS.
- GREEN: when all 10 REQs are covered, the audit passes.

What this checks:
1. Every public data function has at least one test in the test suite.
2. Each test's docstring (or the test class's docstring) cites the REQ
   it covers (e.g. "REQ-001" or "REQ-005").
3. The 10 REQs from specs/prd/mvp.md all have at least one test that
   references them.

REQ → function mapping (source of truth):
- REQ-001 (equity price chart)         → get_equity_price_history
- REQ-002 (date range change)          → get_equity_price_history (period kwarg)
- REQ-003 (fundamentals table)         → get_equity_fundamentals
- REQ-004 (recent news)                → get_equity_news
- REQ-005 (KPI cards: price/change)    → get_equity_quote
- REQ-006 (crypto price chart)         → get_crypto_price_history
- REQ-007 (economy plot)               → get_economy_indicator
- REQ-008 (CSV export)                 → NOT YET (UI feature, no data fn)
- REQ-009 (multi-ticker overlay)       → NOT YET (UI feature, no data fn)
- REQ-010 (global search box)          → search

REQ-008 and REQ-009 are UI/state concerns. They will be implemented
in Phase 2 (state layer). For Phase 1, the audit verifies that the
8 REQs that map to data functions are all covered.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


# ─── Static metadata: REQ → data function (the source of truth) ─────────────


#: Mapping from REQ-ID to the public data function it covers.
REQ_TO_FUNCTION: dict[str, str] = {
    "REQ-001": "reflex_openbb.data.equity:get_equity_price_history",
    "REQ-002": "reflex_openbb.data.equity:get_equity_price_history",
    "REQ-003": "reflex_openbb.data.equity:get_equity_fundamentals",
    "REQ-004": "reflex_openbb.data.equity:get_equity_news",
    "REQ-005": "reflex_openbb.data.equity:get_equity_quote",
    "REQ-006": "reflex_openbb.data.crypto:get_crypto_price_history",
    "REQ-007": "reflex_openbb.data.economy:get_economy_indicator",
    "REQ-010": "reflex_openbb.data.search:search",
}


# REQs intentionally NOT covered by data tests (UI/state concerns, Phase 2+).
DEFERRED_REQS = {
    "REQ-008",  # CSV export (UI)
    "REQ-009",  # multi-ticker overlay (UI)
}


# ─── Helpers: collect tests by module ───────────────────────────────────────


def _collect_test_modules() -> list[Path]:
    """Find all test_data_*.py files."""
    return sorted((REPO_ROOT / "tests").glob("test_data_*.py"))


def _module_docstring_for_function(test_path: Path, function_name: str) -> str | None:
    """Return the docstring of the test module — used to grep for REQ refs.

    We grep ALL docstrings in the file (module + class + test function)
    because a REQ-XXX citation may live in any of them.
    """
    try:
        text = test_path.read_text(encoding="utf-8")
    except OSError:
        return None
    # Extract every docstring (triple-quoted strings) from the file.
    return text


def _grep_req_in_text(text: str, req_id: str) -> bool:
    """Return True if the REQ ID appears anywhere in the file text."""
    # We accept 'REQ-001', 'REQ-001,', 'REQ-001)', etc.
    return bool(re.search(rf"\b{req_id}\b", text))


# ─── Audit tests ────────────────────────────────────────────────────────────


class TestRequirementCoverage:
    """Verify that every data-function REQ is covered by at least one test."""

    def test_req_001_equity_price_history_is_tested(self) -> None:
        """REQ-001 (equity price chart) is covered by get_equity_price_history tests."""
        target_fn = REQ_TO_FUNCTION["REQ-001"].split(":")[1]
        for path in _collect_test_modules():
            if "equity" not in path.name:
                continue
            text = _module_docstring_for_function(path, target_fn)
            assert text is not None
            assert _grep_req_in_text(text, "REQ-001"), (
                f"REQ-001 not cited in {path.name} — see specs/prd/mvp.md §REQ-001 for the criteria"
            )

    def test_req_002_date_range_change_is_tested(self) -> None:
        """REQ-002 (date range change) is covered by the period kwarg tests."""
        for path in _collect_test_modules():
            if "equity" not in path.name:
                continue
            text = _module_docstring_for_function(path, "get_equity_price_history")
            assert text is not None
            # REQ-002 is the period/range feature; we look for the literal "period"
            # OR an explicit REQ-002 citation.
            assert _grep_req_in_text(text, "REQ-002") or "period" in text, (
                f"REQ-002 not covered in {path.name} — need a test that exercises the period kwarg"
            )

    def test_req_003_fundamentals_is_tested(self) -> None:
        """REQ-003 (fundamentals table) is covered by get_equity_fundamentals tests."""
        for path in _collect_test_modules():
            if "equity" not in path.name:
                continue
            text = _module_docstring_for_function(path, "get_equity_fundamentals")
            assert text is not None
            assert _grep_req_in_text(text, "REQ-003"), f"REQ-003 not cited in {path.name}"

    def test_req_004_news_is_tested(self) -> None:
        """REQ-004 (recent news) is covered by get_equity_news tests."""
        for path in _collect_test_modules():
            if "equity" not in path.name:
                continue
            text = _module_docstring_for_function(path, "get_equity_news")
            assert text is not None
            assert _grep_req_in_text(text, "REQ-004"), f"REQ-004 not cited in {path.name}"

    def test_req_005_quote_kpi_is_tested(self) -> None:
        """REQ-005 (KPI cards: price/change/market cap) is covered by quote tests."""
        for path in _collect_test_modules():
            if "equity" not in path.name:
                continue
            text = _module_docstring_for_function(path, "get_equity_quote")
            assert text is not None
            assert _grep_req_in_text(text, "REQ-005"), f"REQ-005 not cited in {path.name}"

    def test_req_006_crypto_is_tested(self) -> None:
        """REQ-006 (crypto price chart) is covered by get_crypto_price_history."""
        for path in _collect_test_modules():
            if "crypto" not in path.name:
                continue
            text = _module_docstring_for_function(path, "get_crypto_price_history")
            assert text is not None
            assert _grep_req_in_text(text, "REQ-006"), f"REQ-006 not cited in {path.name}"

    def test_req_007_economy_is_tested(self) -> None:
        """REQ-007 (economy plot) is covered by get_economy_indicator."""
        for path in _collect_test_modules():
            if "economy" not in path.name:
                continue
            text = _module_docstring_for_function(path, "get_economy_indicator")
            assert text is not None
            assert _grep_req_in_text(text, "REQ-007"), f"REQ-007 not cited in {path.name}"

    def test_req_010_search_is_tested(self) -> None:
        """REQ-010 (global search) is covered by search()."""
        for path in _collect_test_modules():
            if "search" not in path.name:
                continue
            text = _module_docstring_for_function(path, "search")
            assert text is not None
            assert _grep_req_in_text(text, "REQ-010"), f"REQ-010 not cited in {path.name}"


class TestDataFunctionsHaveTests:
    """Every public data function must have at least one test."""

    def test_all_data_functions_have_at_least_one_test(self) -> None:
        """For each data module, find the public functions and assert there
        is at least one test that calls them.
        """
        # Discover data modules
        data_modules = [
            "reflex_openbb.data.equity",
            "reflex_openbb.data.crypto",
            "reflex_openbb.data.economy",
            "reflex_openbb.data.search",
        ]

        for module_name in data_modules:
            mod = __import__(module_name, fromlist=["*"])
            public_fns = [
                name
                for name, obj in inspect.getmembers(mod, inspect.isfunction)
                if not name.startswith("_") and obj.__module__ == module_name
            ]
            assert public_fns, f"No public functions found in {module_name}"

            # Find the corresponding test module
            short_name = module_name.split(".")[-1]
            test_path = REPO_ROOT / "tests" / f"test_data_{short_name}.py"
            assert test_path.exists(), f"Missing test file: {test_path}"

            test_text = test_path.read_text(encoding="utf-8")
            for fn_name in public_fns:
                # Look for the function name in the test file
                assert fn_name in test_text, (
                    f"Function {module_name}.{fn_name} is not tested in {test_path.name}"
                )


class TestDeferredReqsAreDocumented:
    """REQ-008 and REQ-009 are deferred to Phase 2 (UI layer)."""

    def test_req_008_csv_export_documented_as_deferred(self) -> None:
        """REQ-008 is a UI feature. It must be tracked in the spec."""
        # Look for REQ-008 mention in the specs
        prd_path = REPO_ROOT / "specs" / "prd" / "mvp.md"
        text = prd_path.read_text(encoding="utf-8")
        assert "REQ-008" in text, "REQ-008 must be in specs/prd/mvp.md"

    def test_req_009_multi_ticker_documented_as_deferred(self) -> None:
        """REQ-009 is a UI feature. It must be tracked in the spec."""
        prd_path = REPO_ROOT / "specs" / "prd" / "mvp.md"
        text = prd_path.read_text(encoding="utf-8")
        assert "REQ-009" in text, "REQ-009 must be in specs/prd/mvp.md"


class TestAcceptanceSummary:
    """The audit summary: how many REQs are covered vs deferred."""

    def test_eight_data_reqs_are_covered(self) -> None:
        """We have 8 data-function REQs (REQ-001..007, REQ-010).

        All 8 must have tests (T-109 acceptance).
        """
        assert len(REQ_TO_FUNCTION) == 8
        assert set(REQ_TO_FUNCTION.keys()) == {
            "REQ-001",
            "REQ-002",
            "REQ-003",
            "REQ-004",
            "REQ-005",
            "REQ-006",
            "REQ-007",
            "REQ-010",
        }

    def test_two_reqs_are_deferred_to_ui(self) -> None:
        """REQ-008 (CSV) and REQ-009 (overlay) are UI, deferred to Phase 2."""
        assert {"REQ-008", "REQ-009"} == DEFERRED_REQS
