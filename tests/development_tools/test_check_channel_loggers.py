"""Unit tests for development_tools/static_checks/check_channel_loggers.py."""

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module


check_channel_loggers = load_development_tools_module(
    "static_checks.check_channel_loggers"
)


@pytest.mark.unit
def test_iter_python_files_respects_standard_exclusions(tmp_path: Path):
    """iter_python_files should skip paths excluded by shared standard exclusions."""
    include_file = tmp_path / "core" / "service.py"
    excluded_script_file = tmp_path / "scripts" / "helper.py"
    excluded_tests_data_file = tmp_path / "tests" / "data" / "test_tmp.py"
    excluded_cache_file = tmp_path / ".ruff_cache" / "cache_mod.py"

    include_file.parent.mkdir(parents=True, exist_ok=True)
    excluded_script_file.parent.mkdir(parents=True, exist_ok=True)
    excluded_tests_data_file.parent.mkdir(parents=True, exist_ok=True)
    excluded_cache_file.parent.mkdir(parents=True, exist_ok=True)

    include_file.write_text("def ok():\n    return True\n", encoding="utf-8")
    excluded_script_file.write_text("def s():\n    return True\n", encoding="utf-8")
    excluded_tests_data_file.write_text(
        "def transient():\n    return True\n", encoding="utf-8"
    )
    excluded_cache_file.write_text("def c():\n    return True\n", encoding="utf-8")

    files = list(check_channel_loggers.iter_python_files(tmp_path))
    as_posix = {p.relative_to(tmp_path).as_posix() for p in files}

    assert "core/service.py" in as_posix
    assert "scripts/helper.py" not in as_posix
    assert "tests/data/test_tmp.py" not in as_posix
    assert ".ruff_cache/cache_mod.py" not in as_posix
