"""Unit tests for development_tools/static_checks/check_channel_loggers.py."""

from pathlib import Path
from unittest.mock import patch

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


@pytest.mark.unit
def test_check_file_flags_forbidden_logging_import(tmp_path: Path):
    """check_file should report direct logging import violations."""
    target = tmp_path / "core" / "bad_logging.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "import logging\nlogger = logging.getLogger(__name__)\n",
        encoding="utf-8",
    )

    with patch.object(check_channel_loggers, "REPO_ROOT", tmp_path):
        issues = list(check_channel_loggers.check_file(target))

    assert any("Direct logging import is forbidden" in issue for issue in issues)
    assert any("core.logger.get_component_logger" in issue for issue in issues)


@pytest.mark.unit
def test_check_file_flags_multi_arg_logger_calls(tmp_path: Path):
    """check_file should require a single positional arg for logger methods."""
    target = tmp_path / "core" / "bad_logger_call.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "from core.logger import get_component_logger\n"
        "app_logger = get_component_logger('x')\n"
        "app_logger.info('value=%s', 3)\n",
        encoding="utf-8",
    )

    with patch.object(check_channel_loggers, "REPO_ROOT", tmp_path):
        issues = list(check_channel_loggers.check_file(target))

    assert any("single positional argument" in issue for issue in issues)


@pytest.mark.unit
def test_check_file_allows_logging_import_for_allowlisted_path(tmp_path: Path):
    """Allowlisted files should not fail direct logging import checks."""
    target = tmp_path / "core" / "logger.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("import logging\n", encoding="utf-8")

    with (
        patch.object(check_channel_loggers, "REPO_ROOT", tmp_path),
        patch.object(
            check_channel_loggers,
            "_get_allowed_logging_import_paths",
            return_value={Path("core/logger.py")},
        ),
    ):
        issues = list(check_channel_loggers.check_file(target))

    assert issues == []


@pytest.mark.unit
def test_main_returns_failure_when_violations_found(tmp_path: Path):
    """main should return 1 and print violations when issues are present."""
    violation_file = tmp_path / "core" / "bad.py"
    violation_file.parent.mkdir(parents=True, exist_ok=True)
    violation_file.write_text("import logging\n", encoding="utf-8")

    with (
        patch.object(check_channel_loggers, "REPO_ROOT", tmp_path),
        patch("builtins.print") as mock_print,
    ):
        result = check_channel_loggers.main()

    assert result == 1
    printed = [str(c.args[0]) for c in mock_print.call_args_list if c.args]
    assert any("Static logging check failed" in line for line in printed)


@pytest.mark.unit
def test_main_returns_success_when_no_violations(tmp_path: Path):
    """main should return 0 when no files violate static logging rules."""
    clean_file = tmp_path / "core" / "good.py"
    clean_file.parent.mkdir(parents=True, exist_ok=True)
    clean_file.write_text(
        "from core.logger import get_component_logger\n"
        "app_logger = get_component_logger('x')\n"
        "app_logger.info(f'value={3}')\n",
        encoding="utf-8",
    )

    with (
        patch.object(check_channel_loggers, "REPO_ROOT", tmp_path),
        patch("builtins.print") as mock_print,
    ):
        result = check_channel_loggers.main()

    assert result == 0
    printed = [str(c.args[0]) for c in mock_print.call_args_list if c.args]
    assert any("Static check passed" in line for line in printed)
