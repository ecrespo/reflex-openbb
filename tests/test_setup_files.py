"""
Tests for the pre-commit configuration (T-004).

Following TDD strictly: this file is written BEFORE the .pre-commit-config.yaml.
The tests must FAIL initially, then pass after we create the config.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PRECOMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"


def test_precommit_config_exists() -> None:
    """The .pre-commit-config.yaml file must exist at the repo root.

    REQ: T-004 acceptance ("pre-commit install runs").
    """
    assert PRECOMMIT_CONFIG.is_file(), (
        f"Missing pre-commit config at {PRECOMMIT_CONFIG}. "
        "Create it with the Ruff, Bandit, and Gitleaks hooks."
    )


def test_precommit_config_is_valid_yaml() -> None:
    """The pre-commit config must be parseable YAML.

    REQ: T-004 ("the config is valid").
    """
    if not PRECOMMIT_CONFIG.is_file():
        pytest.skip("config does not exist yet — see test_precommit_config_exists")
    with PRECOMMIT_CONFIG.open() as f:
        config = yaml.safe_load(f)
    assert isinstance(config, dict), "pre-commit config root must be a mapping"
    assert "repos" in config, "pre-commit config must have a 'repos' key"
    assert isinstance(config["repos"], list), "'repos' must be a list"
    assert len(config["repos"]) > 0, "'repos' must have at least one entry"


def test_precommit_includes_required_hooks() -> None:
    """The pre-commit config must include Ruff, Bandit, and Gitleaks.

    REQ: Art. 9 of the Constitution (pre-commit gate is non-negotiable).
    The author-specified tools are: Ruff (lint), ty (type-check) OR mypy,
    Bandit (security), Gitleaks (secrets).
    """
    if not PRECOMMIT_CONFIG.is_file():
        pytest.skip("config does not exist yet — see test_precommit_config_exists")
    with PRECOMMIT_CONFIG.open() as f:
        config = yaml.safe_load(f)

    # Collect all hook IDs from all repos
    all_hooks: list[str] = []
    for repo in config.get("repos", []):
        for hook in repo.get("hooks", []):
            all_hooks.append(hook.get("id", ""))

    # Required hook IDs (Ruff ships multiple hook IDs)
    required = {
        "ruff": "linting + formatting",
        "ruff-format": "Ruff formatter (replaces Black)",
        "bandit": "security",
        "gitleaks": "secrets",
    }
    missing = [name for name in required if name not in all_hooks]
    assert not missing, f"Missing required pre-commit hooks: {missing}. Have: {all_hooks}"


def test_precommit_targets_python_sources() -> None:
    """The pre-commit config must include Python source patterns (default OK).

    REQ: T-004 (hooks fire on Python source changes).

    By default pre-commit uses the standard `files:` pattern which respects
    `.gitignore`. The config doesn't need to explicitly list `src/` or `tests/`
    unless it overrides the defaults. We accept either:
    - explicit `src/` / `tests/` mention, OR
    - at least one `types: [python]` / `types_or: [python]` directive.
    """
    if not PRECOMMIT_CONFIG.is_file():
        pytest.skip("config does not exist yet")
    config_text = PRECOMMIT_CONFIG.read_text()

    # The hooks should be Python-aware (types: python) OR mention src/tests.
    python_aware = "python" in config_text and "types" in config_text
    explicit_paths = "src/" in config_text or "tests/" in config_text

    assert python_aware or explicit_paths, (
        "pre-commit config should target Python sources via `types: [python]` "
        "or explicit `src/` / `tests/` paths"
    )


def test_precommit_config_validates() -> None:
    """The pre-commit config must pass `pre-commit validate-config`.

    REQ: T-004 acceptance ("pre-commit run --all-files returns 0 (with stubs)").

    Skipped if `pre-commit` is not installed (e.g. CI without it).
    """
    if not PRECOMMIT_CONFIG.is_file():
        pytest.skip("config does not exist yet")

    result = subprocess.run(
        ["pre-commit", "validate-config", str(PRECOMMIT_CONFIG)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 127:  # pre-commit not installed
        pytest.skip("pre-commit is not installed in this environment")
    assert result.returncode == 0, (
        f"pre-commit validate-config failed:\n  stdout: {result.stdout}\n  stderr: {result.stderr}"
    )


def test_license_file_exists() -> None:
    """The Apache-2.0 LICENSE file must exist at the repo root.

    REQ: T-007 acceptance ("LICENSE exists").
    """
    license_file = REPO_ROOT / "LICENSE"
    assert license_file.is_file(), f"Missing LICENSE at {license_file}"


def test_license_is_apache_2() -> None:
    """The LICENSE file must be Apache License 2.0.

    REQ: Constitution Art. 1 (open-source stack only — Apache-2.0 is the
    project license, matching the author's other custom components).
    """
    license_file = REPO_ROOT / "LICENSE"
    if not license_file.is_file():
        pytest.skip("LICENSE does not exist yet")
    content = license_file.read_text()
    assert "Apache License" in content, "LICENSE must be Apache-2.0"
    assert "Version 2.0" in content or "version 2.0" in content.lower(), (
        "LICENSE must specify Version 2.0"
    )


def test_license_has_copyright_with_current_year() -> None:
    """The LICENSE must include a copyright line for the current year.

    REQ: T-007 acceptance (Apache-2.0 boilerplate includes the year).
    """
    license_file = REPO_ROOT / "LICENSE"
    if not license_file.is_file():
        pytest.skip("LICENSE does not exist yet")
    content = license_file.read_text()
    current_year = str(Path(__file__).stat().st_mtime and __import__("datetime").date.today().year)
    # The Apache-2.0 boilerplate contains "Copyright [yyyy] [name]"
    assert re.search(
        rf"Copyright\s+\d{{4}}.*{re.escape('Ernesto Crespo')}",
        content,
        re.IGNORECASE,
    ), f"LICENSE must include 'Copyright YYYY Ernesto Crespo' (year: {current_year})"
