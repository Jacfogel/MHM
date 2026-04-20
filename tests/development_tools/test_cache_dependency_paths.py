"""Policy tests for development_tools.shared.cache_dependency_paths (V5 §3.19 slice 2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from development_tools.shared.cache_dependency_paths import (
    PIP_AUDIT_DEPENDENCY_RELATIVE_PATHS,
    STATIC_CHECK_CONFIG_RELATIVE_PATHS,
    requirements_lock_signature,
    static_check_config_paths,
)
from development_tools.tests.dev_tools_coverage_cache import DevToolsCoverageCache
from development_tools.tests.test_file_coverage_cache import TestFileCoverageCache


@pytest.mark.unit
def test_static_check_config_relative_paths_include_core_configs() -> None:
    assert "pyproject.toml" in STATIC_CHECK_CONFIG_RELATIVE_PATHS
    assert (
        "development_tools/config/development_tools_config.json"
        in STATIC_CHECK_CONFIG_RELATIVE_PATHS
    )
    assert "development_tools/config/pyrightconfig.json" in STATIC_CHECK_CONFIG_RELATIVE_PATHS
    assert "development_tools/config/ruff.toml" in STATIC_CHECK_CONFIG_RELATIVE_PATHS
    assert ".ruff.toml" in STATIC_CHECK_CONFIG_RELATIVE_PATHS


@pytest.mark.unit
def test_test_file_coverage_cache_tool_paths_include_all_existing_static_configs(
    tmp_path: Path,
) -> None:
    """Coverage cache hash must track the same config files as static-check signature."""
    script_rels = (
        "development_tools/tests/run_test_coverage.py",
        "development_tools/tests/test_file_coverage_cache.py",
        "development_tools/tests/dev_tools_coverage_cache.py",
        "development_tools/tests/domain_mapper.py",
    )
    for rel in (*script_rels, *STATIC_CHECK_CONFIG_RELATIVE_PATHS):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        body = "{}\n" if rel.endswith(".json") else "[stub]\n"
        p.write_text(body, encoding="utf-8")

    cache = TestFileCoverageCache(project_root=tmp_path)
    paths = {x.resolve() for x in cache._get_default_tool_paths()}

    for rel in STATIC_CHECK_CONFIG_RELATIVE_PATHS:
        assert (tmp_path / rel).resolve() in paths

    for rel in static_check_config_paths(tmp_path):
        if rel.is_file():
            assert rel.resolve() in paths


@pytest.mark.unit
def test_pip_audit_dependency_relative_paths_order() -> None:
    assert PIP_AUDIT_DEPENDENCY_RELATIVE_PATHS == ("requirements.txt", "pyproject.toml")


@pytest.mark.unit
def test_requirements_lock_signature_matches_pip_audit_files(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("x==1\n", encoding="utf-8")
    sig = requirements_lock_signature(tmp_path)
    assert sig and len(sig) == 64
    (tmp_path / "requirements.txt").write_text("x==2\n", encoding="utf-8")
    assert requirements_lock_signature(tmp_path) != sig


@pytest.mark.unit
def test_requirements_lock_signature_none_when_no_dependency_files(tmp_path: Path) -> None:
    assert requirements_lock_signature(tmp_path) is None


@pytest.mark.unit
def test_dev_tools_coverage_cache_tool_paths_include_existing_static_configs(
    tmp_path: Path,
) -> None:
    """Dev-tools coverage cache hash must track the same config files as static-check signature."""
    script_rels = (
        "development_tools/tests/run_test_coverage.py",
        "development_tools/tests/dev_tools_coverage_cache.py",
    )
    for rel in (*script_rels, *STATIC_CHECK_CONFIG_RELATIVE_PATHS):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        body = "{}\n" if rel.endswith(".json") else "[stub]\n"
        p.write_text(body, encoding="utf-8")

    cache = DevToolsCoverageCache(project_root=tmp_path, cache_dir=tmp_path / "jsons")
    paths = {x.resolve() for x in cache.tool_paths}

    for rel in STATIC_CHECK_CONFIG_RELATIVE_PATHS:
        assert (tmp_path / rel).resolve() in paths

    for rel in static_check_config_paths(tmp_path):
        if rel.is_file():
            assert rel.resolve() in paths
