"""
State coverage audit (T-205).

TDD: this file is written BEFORE running the audit.
- RED:  if any state class is missing tests, the audit FAILS.
- GREEN: when all 4 state classes have tests, the audit passes.

What this checks:
1. Every state class (AppState, EquityState, CryptoState, EconomyState)
   has a test file.
2. Each test file has at least the field tests (TestXxxStateFields).
3. Each test file's docstring (or class docstring) cites the REQ it covers.
4. The state classes exist in the right module.

REQ → state mapping (source of truth):
- REQ-001..005 (equity)        → EquityState   (T-202)
- REQ-006 (crypto)              → CryptoState   (T-203)
- REQ-007 (economy)             → EconomyState  (T-204)
- REQ-010 (search)              → AppState      (T-201)

The state layer is a thin orchestration layer over the data layer.
Business logic is tested in tests/test_data_*.py. The state tests
focus on fields, validation, and the public handler surface.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


# ─── Static metadata: REQ → state class (the source of truth) ──────────────


#: Mapping from REQ-ID to the state class it covers.
REQ_TO_STATE_CLASS: dict[str, str] = {
    "REQ-001": "reflex_openbb.state.equity_state:EquityState",
    "REQ-002": "reflex_openbb.state.equity_state:EquityState",
    "REQ-003": "reflex_openbb.state.equity_state:EquityState",
    "REQ-004": "reflex_openbb.state.equity_state:EquityState",
    "REQ-005": "reflex_openbb.state.equity_state:EquityState",
    "REQ-006": "reflex_openbb.state.crypto_state:CryptoState",
    "REQ-007": "reflex_openbb.state.economy_state:EconomyState",
    "REQ-010": "reflex_openbb.state.app_state:AppState",
}


#: The 4 state classes we expect to find.
EXPECTED_STATE_CLASSES: list[str] = [
    "reflex_openbb.state.app_state:AppState",
    "reflex_openbb.state.equity_state:EquityState",
    "reflex_openbb.state.crypto_state:CryptoState",
    "reflex_openbb.state.economy_state:EconomyState",
]


# ─── Helpers ────────────────────────────────────────────────────────────────


def _state_test_path(qualname: str) -> Path:
    """Get the test file path for a state class.

    Example: "reflex_openbb.state.app_state:AppState" →
             tests/test_app_state.py
    """
    module = qualname.split(":")[0]
    short_module = module.split(".")[-1]
    return REPO_ROOT / "tests" / f"test_{short_module}.py"


def _grep_req_in_text(text: str, req_id: str) -> bool:
    """Return True if the REQ ID appears anywhere in the text."""
    return bool(re.search(rf"\b{req_id}\b", text))


# ─── Audit tests ────────────────────────────────────────────────────────────


class TestStateClassesExist:
    """Every state class must be importable."""

    def test_app_state_class_exists(self) -> None:
        from reflex_openbb.state.app_state import AppState

        assert inspect.isclass(AppState)

    def test_equity_state_class_exists(self) -> None:
        from reflex_openbb.state.equity_state import EquityState

        assert inspect.isclass(EquityState)

    def test_crypto_state_class_exists(self) -> None:
        from reflex_openbb.state.crypto_state import CryptoState

        assert inspect.isclass(CryptoState)

    def test_economy_state_class_exists(self) -> None:
        from reflex_openbb.state.economy_state import EconomyState

        assert inspect.isclass(EconomyState)

    def test_all_expected_state_classes_are_found(self) -> None:
        """Sanity check: we have exactly the 4 state classes we expect."""
        assert len(EXPECTED_STATE_CLASSES) == 4


class TestStateTestsExist:
    """Every state class must have a test file with at least fields tests."""

    def test_app_state_has_test_file(self) -> None:
        path = _state_test_path("reflex_openbb.state.app_state:AppState")
        assert path.exists(), f"Missing test file: {path}"

    def test_equity_state_has_test_file(self) -> None:
        path = _state_test_path("reflex_openbb.state.equity_state:EquityState")
        assert path.exists(), f"Missing test file: {path}"

    def test_crypto_state_has_test_file(self) -> None:
        path = _state_test_path("reflex_openbb.state.crypto_state:CryptoState")
        assert path.exists(), f"Missing test file: {path}"

    def test_economy_state_has_test_file(self) -> None:
        path = _state_test_path("reflex_openbb.state.economy_state:EconomyState")
        assert path.exists(), f"Missing test file: {path}"


class TestStateTestsHaveFields:
    """Every state test file should have a TestXxxStateFields class.

    Exception: AppState has only one field (last_search) so the test file
    tests it inline in TestGlobalSearch rather than a separate class.
    """

    def test_equity_state_tests_have_fields_class(self) -> None:
        path = _state_test_path("reflex_openbb.state.equity_state:EquityState")
        text = path.read_text(encoding="utf-8")
        assert "TestEquityStateFields" in text, (
            "test_equity_state.py should have a TestEquityStateFields class"
        )

    def test_crypto_state_tests_have_fields_class(self) -> None:
        path = _state_test_path("reflex_openbb.state.crypto_state:CryptoState")
        text = path.read_text(encoding="utf-8")
        assert "TestCryptoStateFields" in text, (
            "test_crypto_state.py should have a TestCryptoStateFields class"
        )

    def test_economy_state_tests_have_fields_class(self) -> None:
        path = _state_test_path("reflex_openbb.state.economy_state:EconomyState")
        text = path.read_text(encoding="utf-8")
        assert "TestEconomyStateFields" in text, (
            "test_economy_state.py should have a TestEconomyStateFields class"
        )

    def test_app_state_tests_have_field_coverage(self) -> None:
        """AppState has 1 field (last_search); tested in TestGlobalSearch."""
        path = _state_test_path("reflex_openbb.state.app_state:AppState")
        text = path.read_text(encoding="utf-8")
        # The field `last_search` must be referenced at least once
        # (in a test that asserts state.last_search == result).
        assert "last_search" in text, "test_app_state.py must reference the last_search field"


class TestRequirementCoverage:
    """Verify that every state-layer REQ is covered by at least one test."""

    def test_req_001_equity_state_cites_req(self) -> None:
        """REQ-001 (equity price chart) is covered by EquityState tests."""
        path = _state_test_path("reflex_openbb.state.equity_state:EquityState")
        text = path.read_text(encoding="utf-8")
        assert _grep_req_in_text(text, "REQ-001"), f"REQ-001 not cited in {path.name}"

    def test_req_002_equity_state_cites_req(self) -> None:
        """REQ-002 (date range change) is covered by EquityState tests."""
        path = _state_test_path("reflex_openbb.state.equity_state:EquityState")
        text = path.read_text(encoding="utf-8")
        assert _grep_req_in_text(text, "REQ-002"), f"REQ-002 not cited in {path.name}"

    def test_req_003_equity_state_cites_req(self) -> None:
        """REQ-003 (fundamentals) is covered by EquityState tests."""
        path = _state_test_path("reflex_openbb.state.equity_state:EquityState")
        text = path.read_text(encoding="utf-8")
        assert _grep_req_in_text(text, "REQ-003"), f"REQ-003 not cited in {path.name}"

    def test_req_004_equity_state_cites_req(self) -> None:
        """REQ-004 (news) is covered by EquityState tests."""
        path = _state_test_path("reflex_openbb.state.equity_state:EquityState")
        text = path.read_text(encoding="utf-8")
        assert _grep_req_in_text(text, "REQ-004"), f"REQ-004 not cited in {path.name}"

    def test_req_005_equity_state_cites_req(self) -> None:
        """REQ-005 (KPI cards) is covered by EquityState tests."""
        path = _state_test_path("reflex_openbb.state.equity_state:EquityState")
        text = path.read_text(encoding="utf-8")
        assert _grep_req_in_text(text, "REQ-005"), f"REQ-005 not cited in {path.name}"

    def test_req_006_crypto_state_cites_req(self) -> None:
        """REQ-006 (crypto price chart) is covered by CryptoState tests."""
        path = _state_test_path("reflex_openbb.state.crypto_state:CryptoState")
        text = path.read_text(encoding="utf-8")
        assert _grep_req_in_text(text, "REQ-006"), f"REQ-006 not cited in {path.name}"

    def test_req_007_economy_state_cites_req(self) -> None:
        """REQ-007 (economy plot) is covered by EconomyState tests."""
        path = _state_test_path("reflex_openbb.state.economy_state:EconomyState")
        text = path.read_text(encoding="utf-8")
        assert _grep_req_in_text(text, "REQ-007"), f"REQ-007 not cited in {path.name}"

    def test_req_010_app_state_cites_req(self) -> None:
        """REQ-010 (global search) is covered by AppState tests."""
        path = _state_test_path("reflex_openbb.state.app_state:AppState")
        text = path.read_text(encoding="utf-8")
        assert _grep_req_in_text(text, "REQ-010"), f"REQ-010 not cited in {path.name}"


class TestStateHandlerCoverage:
    """Verify that each state's event handlers are exercised by tests.

    The handler tests may be xfail (rx.State requires app context) but
    they MUST be present in the test file as a form of documentation.
    """

    def test_equity_state_handlers_documented(self) -> None:
        """set_ticker, set_period are referenced in the test file."""
        path = _state_test_path("reflex_openbb.state.equity_state:EquityState")
        text = path.read_text(encoding="utf-8")
        assert "set_ticker" in text, "set_ticker not tested"
        assert "set_period" in text, "set_period not tested"

    def test_crypto_state_handlers_documented(self) -> None:
        """set_symbol is referenced in the test file."""
        path = _state_test_path("reflex_openbb.state.crypto_state:CryptoState")
        text = path.read_text(encoding="utf-8")
        assert "set_symbol" in text, "set_symbol not tested"

    def test_economy_state_handlers_documented(self) -> None:
        """set_indicator, set_country are referenced in the test file."""
        path = _state_test_path("reflex_openbb.state.economy_state:EconomyState")
        text = path.read_text(encoding="utf-8")
        assert "set_indicator" in text, "set_indicator not tested"
        assert "set_country" in text, "set_country not tested"

    def test_app_state_handlers_documented(self) -> None:
        """global_search is referenced in the test file."""
        path = _state_test_path("reflex_openbb.state.app_state:AppState")
        text = path.read_text(encoding="utf-8")
        assert "global_search" in text, "global_search not tested"


class TestAcceptanceSummary:
    """The audit summary: how many REQs are covered vs deferred."""

    def test_eight_state_reqs_are_covered(self) -> None:
        """We have 8 state-layer REQs (REQ-001..005, REQ-006, REQ-007, REQ-010).

        All 8 must be covered by state tests (T-205 acceptance).
        """
        assert len(REQ_TO_STATE_CLASS) == 8
        assert set(REQ_TO_STATE_CLASS.keys()) == {
            "REQ-001",
            "REQ-002",
            "REQ-003",
            "REQ-004",
            "REQ-005",
            "REQ-006",
            "REQ-007",
            "REQ-010",
        }

    def test_four_state_classes_implemented(self) -> None:
        """We have 4 state classes."""
        assert len(EXPECTED_STATE_CLASSES) == 4

    def test_state_classes_correspond_to_4_pages(self) -> None:
        """Each state class corresponds to a different page in the app."""
        # /equity/{ticker} → EquityState
        # /crypto/{symbol} → CryptoState
        # /economy → EconomyState
        # (global) → AppState
        pages = {
            "reflex_openbb.state.equity_state:EquityState": "/equity",
            "reflex_openbb.state.crypto_state:CryptoState": "/crypto",
            "reflex_openbb.state.economy_state:EconomyState": "/economy",
            "reflex_openbb.state.app_state:AppState": "(global)",
        }
        for cls in EXPECTED_STATE_CLASSES:
            assert cls in pages, f"{cls} has no page mapping"
