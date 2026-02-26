"""Tests for development_tools/shared/common.py helpers."""

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.development_tools.conftest import load_development_tools_module


common_module = load_development_tools_module("shared.common")


@pytest.mark.unit
def test_project_paths_uses_configured_paths(tmp_path, monkeypatch):
    """ProjectPaths should honor path overrides from config."""
    monkeypatch.setattr(
        common_module.config,
        "get_paths_config",
        lambda: {
            "ai_docs_dir": "docs_ai",
            "development_docs_dir": "docs_dev",
            "data_dir": "data_store",
            "tests_dir": "qa_tests",
            "tests_data_dir": "qa_tests/data_files",
        },
    )

    paths = common_module.ProjectPaths(root=tmp_path)
    assert paths.docs == tmp_path / "docs_ai"
    assert paths.dev_docs == tmp_path / "docs_dev"
    assert paths.tests == tmp_path / "qa_tests"
    assert paths.tests_data == tmp_path / "qa_tests" / "data_files"


@pytest.mark.unit
def test_ensure_ascii_write_and_load_helpers(tmp_path):
    """ASCII conversion and file helpers should preserve expected content."""
    assert common_module.ensure_ascii("cafe\u2019") == "cafe?"
    assert common_module.ensure_ascii("") == ""

    json_path = tmp_path / "out" / "data.json"
    txt_path = tmp_path / "out" / "note.txt"
    common_module.write_json(json_path, {"b": 2, "a": 1})
    common_module.write_text(txt_path, "hello")

    assert json_path.exists()
    assert txt_path.exists()
    assert common_module.load_text(txt_path) == "hello"


@pytest.mark.unit
def test_iter_python_sources_honors_exclusions(tmp_path, monkeypatch):
    """iter_python_sources should skip excluded files and missing directories."""
    src = tmp_path / "core"
    src.mkdir(parents=True, exist_ok=True)
    included = src / "service.py"
    excluded = src / "skip_me.py"
    included.write_text("x=1\n", encoding="utf-8")
    excluded.write_text("x=2\n", encoding="utf-8")

    monkeypatch.setattr(
        common_module,
        "should_exclude_file",
        lambda file_path, tool_type="analysis", context="development": str(file_path).endswith("skip_me.py"),
    )

    discovered = list(
        common_module.iter_python_sources(
            ["core", "missing_dir"], project_root=tmp_path
        )
    )

    rel = {p.relative_to(tmp_path).as_posix() for p in discovered}
    assert rel == {"core/service.py"}


@pytest.mark.unit
def test_run_cli_emits_text_or_json(monkeypatch):
    """run_cli should emit plain text by default and JSON when --json is set."""
    def execute(_ns):
        return 0, "Status cafe\u2019", {"status": "ok"}

    with (
        patch("sys.argv", ["tool.py"]),
        patch("builtins.print") as mock_print,
    ):
        exit_code = common_module.run_cli(execute, description="demo")
    assert exit_code == 0
    assert any("Status cafe?" in str(c.args[0]) for c in mock_print.call_args_list if c.args)

    with (
        patch("sys.argv", ["tool.py", "--json"]),
        patch("builtins.print") as mock_print_json,
    ):
        exit_code_json = common_module.run_cli(execute, description="demo")
    assert exit_code_json == 0
    assert '"status": "ok"' in str(mock_print_json.call_args.args[0])


@pytest.mark.unit
def test_summary_block_formats_title_and_body():
    """summary_block should render an underlined title and optional body."""
    with_body = common_module.summary_block("Title", ["a", "b"])
    assert with_body.startswith("Title\n-----\na\nb\n")

    no_body = common_module.summary_block("Only", [])
    assert no_body == "Only\n----\n"
