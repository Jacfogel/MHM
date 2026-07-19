"""Policy: Pyright and Ruff config files exist and are readable (portability baseline).

V6 B-004: single Pyright source of truth is ``pyproject.toml`` ``[tool.pyright]``.
Root ``pyrightconfig.json`` and nested ``development_tools/config/pyrightconfig.json``
must not be reintroduced. Owned Ruff remains ``development_tools/config/ruff.toml``
with root ``.ruff.toml`` as a compatibility mirror.
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

_REMOVED_OWNED_PYRIGHT_PATH = (
    project_root / "development_tools" / "config" / "pyrightconfig.json"
)


def _root_tool_pyright() -> dict:
    data = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    sec = data.get("tool", {}).get("pyright")
    assert isinstance(sec, dict), "pyproject.toml must define [tool.pyright]"
    return sec


@pytest.mark.unit
def test_root_pyright_in_pyproject_exists() -> None:
    """Root Pyright config is [tool.pyright] in pyproject.toml."""
    root = _root_tool_pyright()
    assert root.get("typeCheckingMode")
    assert root.get("venv") == ".venv"
    assert root.get("venvPath") == "."


@pytest.mark.unit
def test_root_pyright_excludes_tests_data_and_temp() -> None:
    """Pyright SSOT must keep test fixtures and temp trees out of analysis scope."""
    ex = _root_tool_pyright().get("exclude", [])
    assert isinstance(ex, list)
    flat = " ".join(str(x) for x in ex)
    assert "tests/data" in flat or "tests\\data" in flat
    assert "tests/temp" in flat or "tests\\temp" in flat


@pytest.mark.unit
def test_pyrightconfig_json_files_are_not_reintroduced() -> None:
    """Pyright policy is pyproject.toml only; JSON configs stay removed."""
    assert not (project_root / "pyrightconfig.json").exists()
    assert not _REMOVED_OWNED_PYRIGHT_PATH.exists()


@pytest.mark.unit
def test_dev_tools_ruff_toml_exists_and_parses() -> None:
    path = project_root / "development_tools" / "config" / "ruff.toml"
    assert path.is_file(), f"Missing {path}"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "line-length" in data or "exclude" in data


@pytest.mark.unit
def test_root_ruff_toml_exists_for_direct_ruff_workflows() -> None:
    """Compatibility mirror for `ruff check .` (see DEVELOPMENT_TOOLS_GUIDE §7.6)."""
    path = project_root / ".ruff.toml"
    assert path.is_file(), f"Missing {path}"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "line-length" in data or "exclude" in data


@pytest.mark.unit
def test_root_and_owned_ruff_configs_share_core_policy_keys() -> None:
    """Portability: keep direct-workflow Ruff mirror aligned with owned dev-tools Ruff config."""
    root = tomllib.loads((project_root / ".ruff.toml").read_text(encoding="utf-8"))
    owned = tomllib.loads(
        (project_root / "development_tools" / "config" / "ruff.toml").read_text(
            encoding="utf-8"
        )
    )
    for key in ("line-length", "target-version", "exclude"):
        assert root.get(key) == owned.get(key), f"ruff mirror drift for key: {key}"
    assert root.get("lint", {}).get("select") == owned.get("lint", {}).get("select")
    assert root.get("lint", {}).get("ignore") == owned.get("lint", {}).get("ignore")


@pytest.mark.unit
def test_static_check_cache_dependencies_cover_pyright_and_ruff_configs() -> None:
    """Static-check cache invalidation must include Pyright SSOT and Ruff configs."""
    from development_tools.shared.cache_dependency_paths import (
        STATIC_CHECK_CONFIG_RELATIVE_PATHS,
        static_check_config_paths,
    )

    expected = {
        "pyproject.toml",
        "development_tools/config/ruff.toml",
        ".ruff.toml",
    }
    assert expected.issubset(set(STATIC_CHECK_CONFIG_RELATIVE_PATHS))
    assert "development_tools/config/pyrightconfig.json" not in STATIC_CHECK_CONFIG_RELATIVE_PATHS
    resolved = {
        str(p.relative_to(project_root)).replace("\\", "/")
        for p in static_check_config_paths(project_root)
    }
    assert expected.issubset(resolved)


@pytest.mark.integration
@pytest.mark.e2e
def test_e2e_pyright_outputjson_parses_for_pyproject() -> None:
    """Optional smoke: ``pyright --project pyproject.toml`` emits a JSON summary.

    Excluded from default runs (`-m "not e2e"`). Requires `python -m pyright` in PATH/venv.
    """
    import subprocess

    check = subprocess.run(
        [sys.executable, "-m", "pyright", "--version"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if check.returncode != 0:
        pytest.skip("pyright CLI not available")

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            "--outputjson",
            "--project",
            str(project_root / "pyproject.toml"),
        ],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        timeout=600,
    )
    raw = (proc.stdout or "").strip()
    assert raw, f"pyright produced no stdout (stderr={proc.stderr!r})"
    payload = json.loads(raw)
    assert "summary" in payload
    summary = payload["summary"]
    assert isinstance(summary, dict)
    assert int(summary.get("filesAnalyzed") or 0) >= 1
