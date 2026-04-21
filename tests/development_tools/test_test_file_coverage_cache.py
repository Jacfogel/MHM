"""Tests for test-file coverage cache invalidation behavior."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import time
import uuid
from pathlib import Path

# Ensure project root is on path so development_tools.tests is importable when run
# from tests/development_tools/ (e.g. serial no_parallel phase with rootdir elsewhere).
_proj = Path(__file__).resolve().parent.parent.parent
_proj_str = os.path.normpath(os.path.abspath(str(_proj)))
sys.path.insert(0, _proj_str)

import pytest

from development_tools.tests.domain_mapper import DomainMapper
from development_tools.tests.test_file_coverage_cache import TestFileCoverageCache
import contextlib


def _make_local_scratch_dir() -> Path:
    """Create a writable local scratch directory for cache tests under tests/data/tmp."""
    scratch_root = (
        Path("tests") / "data" / "tmp" / "test_file_coverage_cache_scratch"
    )
    scratch_root.mkdir(parents=True, exist_ok=True)
    scratch_dir = scratch_root / f"cache_{uuid.uuid4().hex[:10]}"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir.resolve()


def _cleanup_local_scratch_dir(path: Path) -> None:
    """Best-effort cleanup for scratch dirs with basic Windows retry/permission handling."""
    if not path.exists():
        return
    for _ in range(3):
        try:
            for item in path.rglob("*"):
                with contextlib.suppress(OSError):
                    os.chmod(item, stat.S_IWRITE | stat.S_IREAD)
            shutil.rmtree(path, ignore_errors=False)
            return
        except OSError:
            time.sleep(0.1)
    shutil.rmtree(path, ignore_errors=True)


@pytest.mark.unit
def test_domain_mapper_expands_cross_domain_dependencies() -> None:
    """Changed domains should include configured dependent domains."""
    temp_dir = _make_local_scratch_dir()
    try:
        mapper = DomainMapper(temp_dir)
        expanded = mapper.expand_domains_with_dependencies({"core"})

        assert "core" in expanded
        assert "communication" in expanded
        assert "ui" in expanded
        assert "tasks" in expanded
        assert "ai" in expanded
        assert "user" in expanded
        assert "notebook" in expanded
    finally:
        _cleanup_local_scratch_dir(temp_dir)


@pytest.mark.unit
def test_domain_mapper_get_test_files_for_source_includes_domain_tests() -> None:
    """Domain mapper should include relevant non-excluded test files."""
    temp_dir = _make_local_scratch_dir()
    try:
        core_dir = temp_dir / "core"
        tests_unit_dir = temp_dir / "tests" / "unit"
        core_dir.mkdir(parents=True, exist_ok=True)
        tests_unit_dir.mkdir(parents=True, exist_ok=True)

        (core_dir / "service.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        expected_test_file = tests_unit_dir / "test_service.py"
        expected_test_file.write_text(
            "import pytest\n\n@pytest.mark.unit\ndef test_service():\n    assert True\n",
            encoding="utf-8",
        )

        mapper = DomainMapper(temp_dir)
        test_files = mapper.get_test_files_for_source("core/service.py")

        assert expected_test_file in test_files
    finally:
        _cleanup_local_scratch_dir(temp_dir)


@pytest.mark.unit
def test_domain_mapper_get_test_files_for_source_excludes_tests_data() -> None:
    """Domain mapper should skip excluded paths like tests/data/** test files."""
    temp_dir = _make_local_scratch_dir()
    try:
        core_dir = temp_dir / "core"
        tests_unit_dir = temp_dir / "tests" / "unit"
        tests_data_dir = temp_dir / "tests" / "data" / "pytest-of-worker"
        core_dir.mkdir(parents=True, exist_ok=True)
        tests_unit_dir.mkdir(parents=True, exist_ok=True)
        tests_data_dir.mkdir(parents=True, exist_ok=True)

        (core_dir / "service.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        included_test_file = tests_unit_dir / "test_service.py"
        included_test_file.write_text(
            "import pytest\n\n@pytest.mark.unit\ndef test_service():\n    assert True\n",
            encoding="utf-8",
        )
        excluded_test_file = tests_data_dir / "test_transient.py"
        excluded_test_file.write_text(
            "import pytest\n\n@pytest.mark.unit\ndef test_transient():\n    assert True\n",
            encoding="utf-8",
        )

        mapper = DomainMapper(temp_dir)
        test_files = mapper.get_test_files_for_source("core/service.py")

        assert included_test_file in test_files
        assert excluded_test_file not in test_files
    finally:
        _cleanup_local_scratch_dir(temp_dir)


@pytest.mark.unit
def test_domain_mapper_domains_from_attribution_markers_exact_set() -> None:
    """Markers that match domain lists map to exactly those domains."""
    temp_dir = _make_local_scratch_dir()
    try:
        mapper = DomainMapper(temp_dir)
        assert mapper.domains_from_attribution_markers({"communication"}) == {
            "communication"
        }
        assert mapper.domains_from_attribution_markers({"communication", "ui"}) == {
            "communication",
            "ui",
        }
    finally:
        _cleanup_local_scratch_dir(temp_dir)


@pytest.mark.unit
def test_domain_mapper_domains_from_attribution_markers_none_without_domain_marks() -> None:
    """Non-attribution markers (or none) yield None so callers use directory/keyword fallback."""
    temp_dir = _make_local_scratch_dir()
    try:
        mapper = DomainMapper(temp_dir)
        assert mapper.domains_from_attribution_markers({"slow", "behavior"}) is None
        assert mapper.domains_from_attribution_markers(set()) is None
    finally:
        _cleanup_local_scratch_dir(temp_dir)


@pytest.mark.unit
def test_cache_invalidates_domains_when_test_file_changes() -> None:
    """Changing a test file should invalidate affected (and dependent) domains."""
    temp_path = _make_local_scratch_dir()
    try:
        (temp_path / "tests" / "unit").mkdir(parents=True, exist_ok=True)
        (temp_path / "core").mkdir(parents=True, exist_ok=True)

        source_file = temp_path / "core" / "demo_module.py"
        source_file.write_text("def f():\n    return 1\n", encoding="utf-8")

        test_file = temp_path / "tests" / "unit" / "test_demo_module.py"
        test_file.write_text(
            "import pytest\n\n@pytest.mark.unit\ndef test_demo():\n    assert True\n",
            encoding="utf-8",
        )

        cache = TestFileCoverageCache(temp_path)

        # Build initial mapping and a stable baseline cache snapshot.
        cache.update_test_file_mapping(test_file)
        for domain in cache.domain_mapper.SOURCE_TO_TEST_MAPPING:
            cache.cache_data.setdefault("source_files_mtime", {})[
                domain
            ] = cache.get_source_file_mtimes(domain)
        cache._save_cache()

        # First pass should use the saved baseline.
        cache._cached_changed_domains = None
        baseline_changes = cache.get_changed_domains()
        assert baseline_changes == set()

        # Modify the test file and bump mtime explicitly for deterministic detection.
        test_file.write_text(
            "import pytest\n\n@pytest.mark.unit\ndef test_demo():\n    assert 1 == 1\n",
            encoding="utf-8",
        )
        current_stat = test_file.stat()
        os.utime(test_file, (current_stat.st_atime + 2, current_stat.st_mtime + 2))

        cache._cached_changed_domains = None
        changed_domains = cache.get_changed_domains()

        assert "core" in changed_domains
        # Dependency expansion should pull in communication from core changes.
        assert "communication" in changed_domains
        assert cache.last_invalidation_reason == "test_file_content_or_mapping_changed"
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_cache_persists_tool_hash_and_mtimes() -> None:
    """Cache save should persist tool hash + tool mtimes metadata."""
    temp_path = _make_local_scratch_dir()
    try:
        project_root = Path.cwd().resolve()
        cache = TestFileCoverageCache(project_root, cache_dir=temp_path)

        cache._save_cache()

        cache_file = temp_path / "test_file_coverage_cache.json"
        assert cache_file.exists()
        cache_json = json.loads(cache_file.read_text(encoding="utf-8"))
        assert cache_json.get("tool_hash")
        tool_mtimes = cache_json.get("tool_mtimes")
        assert isinstance(tool_mtimes, dict)
        normalized_keys = {k.replace("\\", "/") for k in tool_mtimes}
        assert "development_tools/tests/run_test_coverage.py" in normalized_keys
        assert "development_tools/tests/test_file_coverage_cache.py" in normalized_keys
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_tool_hash_mismatch_invalidates_all_domains() -> None:
    """Tool hash mismatch should invalidate all domains with explicit reason."""
    temp_path = _make_local_scratch_dir()
    try:
        project_root = Path.cwd().resolve()
        cache = TestFileCoverageCache(project_root, cache_dir=temp_path)
        cache._save_cache()

        # Force mismatch without touching tool files.
        cache.cache_data["tool_hash"] = "stale_hash_value"
        cache._cached_changed_domains = None
        changed_domains = cache.get_changed_domains()

        expected_domains = set(cache.domain_mapper.SOURCE_TO_TEST_MAPPING.keys())
        assert changed_domains == expected_domains
        assert cache.last_invalidation_reason is not None
        assert cache.last_invalidation_reason.startswith("tool_change:")
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_cache_backfills_missing_tool_hash_on_load() -> None:
    """Legacy cache payloads missing tool hash should be backfilled on load."""
    temp_path = _make_local_scratch_dir()
    try:
        project_root = Path.cwd().resolve()
        cache_file = temp_path / "test_file_coverage_cache.json"
        cache_file.write_text(
            json.dumps(
                {
                    "cache_version": "1.0",
                    "source_files_mtime": {},
                    "test_files": {},
                    "test_files_mtime": {},
                }
            ),
            encoding="utf-8",
        )

        cache = TestFileCoverageCache(project_root, cache_dir=temp_path)
        assert isinstance(cache.cache_data.get("tool_hash"), str)
        assert cache._get_tool_change_reason() is None

        persisted = json.loads(cache_file.read_text(encoding="utf-8"))
        assert isinstance(persisted.get("tool_hash"), str)
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_save_cache_backfills_missing_excluded_test_dirs() -> None:
    """Saving cache should tolerate legacy instances missing excluded dirs state."""
    temp_path = _make_local_scratch_dir()
    try:
        project_root = Path.cwd().resolve()
        cache = TestFileCoverageCache(project_root, cache_dir=temp_path)

        # Simulate a legacy/partial instance state that may appear in old caches.
        if hasattr(cache, "excluded_test_dirs"):
            delattr(cache, "excluded_test_dirs")

        cache._save_cache()

        assert cache.cache_file.exists()
        assert isinstance(cache.excluded_test_dirs, list)
        assert cache.excluded_test_dirs
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_failed_run_without_failed_domains_invalidates_last_run_domains() -> None:
    """Failed run fallback should invalidate previously-run domains before global fallback."""
    temp_path = _make_local_scratch_dir()
    try:
        project_root = Path.cwd().resolve()
        cache = TestFileCoverageCache(project_root, cache_dir=temp_path)
        cache._save_cache()

        cache.cache_data["last_run_ok"] = False
        cache.cache_data["last_no_parallel_ok"] = False
        cache.cache_data["last_failed_domains"] = []
        cache.cache_data["last_run_domains"] = ["core", "communication"]
        cache._cached_changed_domains = None

        changed_domains = cache.get_changed_domains()

        assert changed_domains == {"core", "communication"}
        assert (
            cache.last_invalidation_reason
            == "previous_run_failed: run domains from previous run"
        )
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_is_valid_test_file_uses_shared_exclusions() -> None:
    """Shared exclusions should mark tests/coverage_html test files as invalid."""
    temp_path = _make_local_scratch_dir()
    try:
        (temp_path / "tests" / "unit").mkdir(parents=True, exist_ok=True)
        (temp_path / "tests" / "coverage_html").mkdir(parents=True, exist_ok=True)

        valid_file = temp_path / "tests" / "unit" / "test_ok.py"
        excluded_file = temp_path / "tests" / "coverage_html" / "test_skip.py"
        valid_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        excluded_file.write_text(
            "def test_skip():\n    assert True\n", encoding="utf-8"
        )

        cache = TestFileCoverageCache(temp_path, cache_dir=temp_path / "cache")

        assert cache.is_valid_test_file(valid_file)
        assert not cache.is_valid_test_file(excluded_file)
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_get_source_file_mtimes_respects_shared_exclusions() -> None:
    """Source mtimes should skip files under excluded paths like domain/scripts/*."""
    temp_path = _make_local_scratch_dir()
    try:
        core_dir = temp_path / "core"
        keep_file = core_dir / "module.py"
        skip_file = core_dir / "scripts" / "helper.py"
        keep_file.parent.mkdir(parents=True, exist_ok=True)
        skip_file.parent.mkdir(parents=True, exist_ok=True)
        keep_file.write_text("def f():\n    return 1\n", encoding="utf-8")
        skip_file.write_text("def s():\n    return 1\n", encoding="utf-8")

        cache = TestFileCoverageCache(temp_path, cache_dir=temp_path / "cache")
        mtimes = cache.get_source_file_mtimes("core")
        normalized_keys = {k.replace("\\", "/") for k in mtimes}

        assert "core/module.py" in normalized_keys
        assert "core/scripts/helper.py" not in normalized_keys
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_test_file_set_removal_selective_invalidates_subset() -> None:
    """Removing a tracked test file should bust only implied domains when mapping is known."""
    temp_path = _make_local_scratch_dir()
    try:
        ui_dir = temp_path / "tests" / "ui"
        ui_dir.mkdir(parents=True, exist_ok=True)
        keep = ui_dir / "test_keep.py"
        removed = ui_dir / "test_removed.py"
        content = (
            "import pytest\n\n@pytest.mark.ui\ndef test_x():\n    assert True\n"
        )
        keep.write_text(content, encoding="utf-8")
        removed.write_text(content, encoding="utf-8")

        cache = TestFileCoverageCache(temp_path)
        cache.update_test_file_mapping(keep)
        cache.update_test_file_mapping(removed)
        for domain in cache.domain_mapper.SOURCE_TO_TEST_MAPPING:
            cache.cache_data.setdefault("source_files_mtime", {})[
                domain
            ] = cache.get_source_file_mtimes(domain)
        cache._save_cache()

        removed.unlink()
        cache._cached_changed_domains = None
        changed = cache.get_changed_domains()
        all_d = set(cache.domain_mapper.SOURCE_TO_TEST_MAPPING.keys())

        assert cache.last_invalidation_reason == "test_file_set_changed_selective"
        assert cache.last_invalidation_detail is not None
        assert cache.last_invalidation_detail.get("branch") == "test_file_set_changed_selective"
        assert cache.invalidation_counters.get("full_bust") is False
        assert cache.invalidation_counters.get("removed_test_files") == 1
        assert len(changed) < len(all_d)
        assert "ui" in changed
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_get_test_files_domains_explicit_markers_exclude_directory_fallback() -> None:
    """With domain attribution markers, do not also tag legacy directory domains (e.g. core for tests/unit)."""
    temp_path = _make_local_scratch_dir()
    try:
        unit_dir = temp_path / "tests" / "unit"
        unit_dir.mkdir(parents=True)
        f = unit_dir / "test_explicit_communication.py"
        f.write_text(
            "import pytest\n\n@pytest.mark.communication\ndef test_x():\n    assert True\n",
            encoding="utf-8",
        )
        cache = TestFileCoverageCache(temp_path, cache_dir=temp_path / "cache")
        doms = cache.get_test_files_domains(f, force_refresh=True)
        assert doms == {"communication"}
    finally:
        _cleanup_local_scratch_dir(temp_path)


@pytest.mark.unit
def test_get_test_files_domains_fallback_uses_directory_when_no_attribution_markers() -> None:
    """No domain-attribution markers → legacy directory / keyword mapping."""
    temp_path = _make_local_scratch_dir()
    try:
        unit_dir = temp_path / "tests" / "unit"
        unit_dir.mkdir(parents=True)
        f = unit_dir / "test_no_marks.py"
        f.write_text("def test_x():\n    assert True\n", encoding="utf-8")
        cache = TestFileCoverageCache(temp_path, cache_dir=temp_path / "cache")
        doms = cache.get_test_files_domains(f, force_refresh=True)
        assert "core" in doms
    finally:
        _cleanup_local_scratch_dir(temp_path)
