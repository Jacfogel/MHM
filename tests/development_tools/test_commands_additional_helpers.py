"""Additional helper coverage for development_tools/shared/service/commands.py."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_build_coverage_metadata_includes_changed_domains(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    output = "Domain(s) changed: ['core', 'ui']\nUsing cached coverage data only"

    metadata = service._build_coverage_metadata(output, source="main_coverage")

    assert metadata["cache_mode"] == "cache_only"
    assert metadata["source"] == "main_coverage"
    assert metadata["changed_domains"] == ["core", "ui"]
    assert isinstance(metadata["invalidation_reason"], str)


@pytest.mark.unit
def test_latest_mtime_for_patterns_respects_excludes(tmp_path: Path):
    project_root = tmp_path
    keep = project_root / "tests" / "development_tools" / "test_keep.py"
    skip_prefix = project_root / "tests" / "data" / "test_skip.py"
    skip_exact = project_root / "tests" / "development_tools" / "test_skip_exact.py"
    keep.parent.mkdir(parents=True, exist_ok=True)
    skip_prefix.parent.mkdir(parents=True, exist_ok=True)
    skip_exact.parent.mkdir(parents=True, exist_ok=True)

    keep.write_text("pass", encoding="utf-8")
    skip_prefix.write_text("pass", encoding="utf-8")
    skip_exact.write_text("pass", encoding="utf-8")

    service = AIToolsService(project_root=str(project_root))
    latest = service._latest_mtime_for_patterns(
        patterns=["tests/**/*.py"],
        exclude_prefixes=["tests/data/"],
        exclude_paths=["tests/development_tools/test_skip_exact.py"],
    )

    assert latest > 0
    assert latest == keep.stat().st_mtime


@pytest.mark.unit
def test_is_coverage_file_fresh_compares_source_and_config_mtimes(tmp_path: Path):
    service = AIToolsService(project_root=str(tmp_path))
    coverage_file = tmp_path / ".coverage"
    src_file = tmp_path / "tests" / "unit" / "test_x.py"
    cfg_file = tmp_path / "development_tools" / "config" / "development_tools_config.json"
    src_file.parent.mkdir(parents=True, exist_ok=True)
    cfg_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text("pass", encoding="utf-8")
    cfg_file.write_text("{}", encoding="utf-8")

    assert (
        service._is_coverage_file_fresh(
            coverage_file,
            source_patterns=["tests/**/*.py"],
            config_paths=["development_tools/config/development_tools_config.json"],
        )
        is False
    )

    coverage_file.write_text("data", encoding="utf-8")
    future_time = time.time() + 5
    Path(coverage_file).touch()
    import os

    os.utime(coverage_file, (future_time, future_time))
    assert (
        service._is_coverage_file_fresh(
            coverage_file,
            source_patterns=["tests/**/*.py"],
            config_paths=["development_tools/config/development_tools_config.json"],
        )
        is True
    )


@pytest.mark.unit
def test_to_standard_dev_tools_coverage_result_wraps_legacy_payload(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    raw = {"overall": {"total_missed": 42}, "modules": {}}

    normalized = service._to_standard_dev_tools_coverage_result(raw)

    assert normalized["summary"]["total_issues"] == 42
    assert normalized["summary"]["files_affected"] == 0
    assert normalized["details"] == raw


@pytest.mark.unit
def test_cached_state_extractors_and_failure_classification(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))

    main_cached = {
        "details": {
            "tier3_test_outcome": {
                "parallel": {"classification": "passed"},
                "no_parallel": {"classification": "failed"},
                "development_tools": {"classification": "passed"},
            }
        }
    }
    dev_cached = {
        "details": {"dev_tools_test_outcome": {"classification": "infra_cleanup_error"}}
    }

    assert service._extract_cached_main_coverage_state(main_cached) == "test_failures"
    assert (
        service._extract_cached_dev_tools_state(dev_cached) == "infra_cleanup_error"
    )
    assert service._extract_track_classification({"classification": "passed"}) == "passed"
    assert service._extract_track_classification({}) == "unknown"
    assert service._derive_tier3_state_from_classifications(main_cached["details"]["tier3_test_outcome"]) == "test_failures"
    assert service._is_failure_state("infra_cleanup_error") is True
    assert service._is_failure_state("clean") is False

    legacy_details_only = {
        "details": {
            "coverage_outcome": {
                "parallel": {"classification": "passed"},
                "no_parallel": {"classification": "passed"},
            }
        }
    }
    assert service._extract_cached_main_coverage_state(legacy_details_only) is None


@pytest.mark.unit
def test_is_interrupt_signature_detects_keyboard_interrupt_and_code(
    temp_project_copy: Path,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service._is_interrupt_signature("Traceback\nKeyboardInterrupt", None) is True
    assert service._is_interrupt_signature("", 130) is True
    assert service._is_interrupt_signature("ok", 0) is False


@pytest.mark.unit
def test_is_coverage_file_fresh_invalidates_when_runner_script_is_newer(tmp_path: Path):
    service = AIToolsService(project_root=str(tmp_path))
    coverage_file = tmp_path / ".coverage"
    test_file = tmp_path / "tests" / "unit" / "test_x.py"
    runner = tmp_path / "development_tools" / "tests" / "run_test_coverage.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    runner.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("pass", encoding="utf-8")
    runner.write_text("RUNNER = 'ok'\n", encoding="utf-8")
    coverage_file.write_text("data", encoding="utf-8")

    old_time = time.time() - 10
    Path(coverage_file).touch()
    import os

    os.utime(coverage_file, (old_time, old_time))

    with patch(
        "development_tools.shared.service.tool_wrappers.SCRIPT_REGISTRY",
        {"run_test_coverage": "development_tools/tests/run_test_coverage.py"},
    ):
        assert (
            service._is_coverage_file_fresh(
                coverage_file,
                source_patterns=["tests/**/*.py"],
                tool_names=["run_test_coverage"],
            )
            is False
        )

