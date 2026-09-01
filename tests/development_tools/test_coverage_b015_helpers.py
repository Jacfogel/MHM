"""Direct unit tests for V6 B-015 coverage helper modules."""

from __future__ import annotations

from pathlib import Path
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from development_tools.tests.coverage_domain_cache import (
    check_dev_tools_changed,
    get_dev_tools_source_mtimes,
    get_dev_tools_test_mtimes,
)
from development_tools.shared.mtime_cache import hash_file_sha256
from development_tools.tests.coverage_pytest_argv import (
    build_dev_tools_coverage_pytest_cmd,
    build_main_coverage_pytest_cmd,
    build_no_parallel_coverage_pytest_cmd,
    build_no_parallel_test_args,
)
from development_tools.tests.coverage_shard_merge import (
    domains_with_collapsed_coverage,
    is_full_coverage_run,
    load_coverage_json_dict,
    merge_coverage_json,
)
from development_tools.shared.service.report_generation_scope_helpers import (
    count_duplicate_affected_files,
    path_is_under_development_tools_dir,
)


@pytest.mark.unit
def test_build_no_parallel_test_args_filter_and_fallback() -> None:
    assert build_no_parallel_test_args(["a.py"], "tests/") == ["a.py"]
    assert build_no_parallel_test_args([], "tests/") == ["tests/"]


@pytest.mark.unit
def test_build_main_coverage_pytest_cmd_parallel_and_serial(tmp_path: Path) -> None:
    cov_cfg = tmp_path / "coverage.ini"
    cov_cfg.write_text("[run]\n", encoding="utf-8")
    json_out = tmp_path / "coverage.json"

    parallel_cmd = build_main_coverage_pytest_cmd(
        executable="python",
        parallel=True,
        num_workers="4",
        cov_args=["--cov=core"],
        coverage_config_path=cov_cfg,
        maxfail=3,
        test_filter_args=["tests/unit"],
        coverage_json_output=None,
    )
    assert "-n" in parallel_cmd
    assert "4" in parallel_cmd
    assert "--dist=loadscope" in parallel_cmd
    assert "--cov-append" in parallel_cmd
    assert not any(a.startswith("--cov-report=json:") for a in parallel_cmd)
    assert "tests/unit" in parallel_cmd

    serial_cmd = build_main_coverage_pytest_cmd(
        executable="python",
        parallel=False,
        num_workers="auto",
        cov_args=["--cov=core"],
        coverage_config_path=cov_cfg,
        maxfail=10,
        test_filter_args=[],
        coverage_json_output=json_out,
    )
    assert "-n" not in serial_cmd
    assert any(a.startswith("--cov-report=json:") for a in serial_cmd)
    assert "tests/" in serial_cmd


@pytest.mark.unit
def test_build_no_parallel_and_dev_tools_pytest_cmds(tmp_path: Path) -> None:
    cov_cfg = tmp_path / "coverage.ini"
    cov_cfg.write_text("[run]\n", encoding="utf-8")
    json_out = tmp_path / "coverage_dev_tools.json"

    no_par = build_no_parallel_coverage_pytest_cmd(
        executable="python",
        cov_args=["--cov=core"],
        coverage_config_path=cov_cfg,
        maxfail=5,
        test_filter_args=[],
        test_directory="tests/",
    )
    assert "no_parallel and not e2e" in no_par
    assert "tests/" in no_par

    dev = build_dev_tools_coverage_pytest_cmd(
        executable="python",
        parallel=True,
        num_workers="2",
        coverage_json_output=json_out,
        coverage_config_path=cov_cfg,
    )
    assert "--cov=development_tools" in dev
    assert "-n" in dev
    assert "2" in dev
    assert "tests/development_tools/" in dev


@pytest.mark.unit
def test_merge_coverage_json_unions_executed_lines() -> None:
    a = {
        "files": {
            "mod.py": {
                "executed_lines": [1, 2],
                "missing_lines": [3, 4],
                "excluded_lines": [],
                "summary": {
                    "num_statements": 4,
                    "covered_lines": 2,
                    "missing_lines": 2,
                },
            }
        }
    }
    b = {
        "files": {
            "mod.py": {
                "executed_lines": [2, 3],
                "missing_lines": [1, 4],
                "excluded_lines": [],
                "summary": {
                    "num_statements": 4,
                    "covered_lines": 2,
                    "missing_lines": 2,
                },
            }
        }
    }
    merged = merge_coverage_json(a, b)
    assert merged["files"]["mod.py"]["executed_lines"] == [1, 2, 3]
    assert merged["files"]["mod.py"]["missing_lines"] == [4]
    assert merged["totals"]["covered_lines"] == 3


@pytest.mark.unit
@pytest.mark.development_tools
def test_is_full_coverage_run_rejects_missing_cache_plus_subset() -> None:
    """A selective file list with no cache is not a full suite measurement."""
    assert (
        is_full_coverage_run(
            test_files_to_run=["tests/unit/test_a.py"],
            total_test_files=100,
            changed_domains={"integrations"},
            all_domains={"integrations", "development_tools"},
            ran_entire_test_tree=False,
        )
        is False
    )
    assert (
        is_full_coverage_run(
            test_files_to_run=[],
            total_test_files=100,
            ran_entire_test_tree=True,
        )
        is True
    )
    assert (
        is_full_coverage_run(
            test_files_to_run=["a.py", "b.py"],
            total_test_files=2,
            changed_domains={"integrations", "development_tools"},
            all_domains={"integrations", "development_tools"},
        )
        is True
    )


@pytest.mark.unit
@pytest.mark.development_tools
def test_merge_keeps_unchanged_domain_when_fresh_is_zero() -> None:
    """Selective product-domain runs must not publish 0% for skipped domains."""
    mapper = SimpleNamespace(
        get_source_domain=lambda path: (
            "development_tools"
            if path.replace("\\", "/").startswith("development_tools/")
            else "integrations"
        )
    )
    cached = {
        "files": {
            "development_tools/cmd.py": {
                "executed_lines": [1, 2, 3],
                "missing_lines": [4],
                "excluded_lines": [],
                "summary": {
                    "num_statements": 4,
                    "covered_lines": 3,
                    "missing_lines": 1,
                },
            }
        }
    }
    fresh = {
        "files": {
            "development_tools/cmd.py": {
                "executed_lines": [],
                "missing_lines": [1, 2, 3, 4],
                "excluded_lines": [],
                "summary": {
                    "num_statements": 4,
                    "covered_lines": 0,
                    "missing_lines": 4,
                },
            },
            "integrations/client.py": {
                "executed_lines": [1, 2],
                "missing_lines": [],
                "excluded_lines": [],
                "summary": {
                    "num_statements": 2,
                    "covered_lines": 2,
                    "missing_lines": 0,
                },
            },
        }
    }
    merged = merge_coverage_json(
        cached,
        fresh,
        domain_mapper=mapper,
        changed_domains={"integrations"},
    )
    dt = merged["files"]["development_tools/cmd.py"]
    assert dt["executed_lines"] == [1, 2, 3]
    assert dt["summary"]["covered_lines"] == 3
    assert merged["files"]["integrations/client.py"]["summary"]["covered_lines"] == 2


@pytest.mark.unit
@pytest.mark.development_tools
def test_domains_with_collapsed_coverage_detects_drop(tmp_path: Path) -> None:
    mapper = SimpleNamespace(
        get_source_domain=lambda path: (
            "development_tools"
            if "development_tools" in path.replace("\\", "/")
            else "integrations"
        )
    )
    previous = {
        "files": {
            "development_tools/a.py": {
                "summary": {"num_statements": 100, "covered_lines": 70}
            }
        }
    }
    fresh = {
        "files": {
            "development_tools/a.py": {
                "summary": {"num_statements": 100, "covered_lines": 3}
            }
        }
    }
    assert domains_with_collapsed_coverage(
        fresh, previous, domain_mapper=mapper
    ) == ["development_tools"]

    json_path = tmp_path / "coverage.json"
    json_path.write_text(
        '{"files": {"core/mod.py": {"summary": {"num_statements": 1}}}}',
        encoding="utf-8",
    )
    loaded = load_coverage_json_dict(json_path)
    assert loaded is not None
    assert "core/mod.py" in loaded["files"]
    assert load_coverage_json_dict(tmp_path / "missing.json") is None


@pytest.mark.unit
def test_check_dev_tools_changed_disabled_or_missing_cache(tmp_path: Path) -> None:
    assert (
        check_dev_tools_changed(
            use_domain_cache=False,
            dev_tools_cache=None,
            project_root=tmp_path,
        )
        is True
    )
    assert (
        check_dev_tools_changed(
            use_domain_cache=True,
            dev_tools_cache=None,
            project_root=tmp_path,
        )
        is True
    )


@pytest.mark.unit
def test_check_dev_tools_changed_tool_reason_and_mtimes(tmp_path: Path) -> None:
    cache = MagicMock()
    cache.get_tool_change_reason.return_value = "tool hash changed"
    assert (
        check_dev_tools_changed(
            use_domain_cache=True,
            dev_tools_cache=cache,
            project_root=tmp_path,
        )
        is True
    )

    # Unchanged: matching source/test/config mtimes and last_run_ok
    src = tmp_path / "development_tools" / "pkg"
    src.mkdir(parents=True)
    py = src / "mod.py"
    py.write_text("x = 1\n", encoding="utf-8")
    tests = tmp_path / "tests" / "development_tools"
    tests.mkdir(parents=True)
    test_py = tests / "test_mod.py"
    test_py.write_text("def test_x():\n    assert True\n", encoding="utf-8")
    cfg = tmp_path / "development_tools" / "config" / "development_tools_config.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("{}", encoding="utf-8")

    # Nightly --basetemp lives under tests/data/tmp/pytest_runner/. Keep exclusion
    # checks from treating this scratch tree as test-data so mtime scans see files.
    with patch(
        "development_tools.tests.coverage_domain_cache.should_exclude_file",
        return_value=False,
    ), patch(
        "development_tools.tests.coverage_domain_cache.get_config_file_path",
        return_value=cfg,
    ):
        source_mtimes = get_dev_tools_source_mtimes(tmp_path)
        test_mtimes = get_dev_tools_test_mtimes(tmp_path)
        assert source_mtimes
        assert test_mtimes
        config_mtime = cfg.stat().st_mtime
        config_hash = hash_file_sha256(cfg)
        cache2 = SimpleNamespace(
            get_tool_change_reason=lambda: None,
            get_cached_config_mtime=lambda: config_mtime,
            get_cached_config_hash=lambda: config_hash,
            get_last_run_ok=lambda: True,
            get_cached_mtimes=lambda: dict(source_mtimes),
            get_cached_test_mtimes=lambda: dict(test_mtimes),
        )
        assert (
            check_dev_tools_changed(
                use_domain_cache=True,
                dev_tools_cache=cache2,
                project_root=tmp_path,
            )
            is False
        )

        os.utime(cfg, None)
        cache_touched = SimpleNamespace(
            get_tool_change_reason=lambda: None,
            get_cached_config_mtime=lambda: config_mtime,
            get_cached_config_hash=lambda: config_hash,
            get_last_run_ok=lambda: True,
            get_cached_mtimes=lambda: dict(source_mtimes),
            get_cached_test_mtimes=lambda: dict(test_mtimes),
        )
        assert (
            check_dev_tools_changed(
                use_domain_cache=True,
                dev_tools_cache=cache_touched,
                project_root=tmp_path,
            )
            is False
        )


@pytest.mark.unit
def test_scope_helpers_path_and_duplicate_count(tmp_path: Path) -> None:
    (tmp_path / "development_tools").mkdir()
    assert path_is_under_development_tools_dir("development_tools/a.py", tmp_path)
    assert not path_is_under_development_tools_dir("ui/a.py", tmp_path)
    groups = [
        {
            "functions": [
                {"file": "a.py"},
                {"file": "b.py"},
            ]
        }
    ]
    assert count_duplicate_affected_files(groups) == 2
