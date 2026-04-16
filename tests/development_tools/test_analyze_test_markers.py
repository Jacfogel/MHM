"""Unit tests for development_tools.tests.analyze_test_markers."""

from pathlib import Path
import json
import shutil
from contextlib import contextmanager
from collections.abc import Callable
from typing import Any
from uuid import uuid4

import pytest

from tests.development_tools.conftest import load_development_tools_module


analyze_test_markers = load_development_tools_module("tests.analyze_test_markers")
TestMarkerAnalyzer = analyze_test_markers.TestMarkerAnalyzer
MissingMarkerFinder = analyze_test_markers.MissingMarkerFinder


class _FakeAnalyzer:
    """Minimal analyzer stub for main() tests; attributes set per test."""

    def __init__(self) -> None:
        self.find_missing_markers_ast: Callable[..., Any] = lambda: []
        self.analyze_markers: Callable[..., Any] = lambda: {}
        self.domain_markers: tuple[str, ...] = ()

    def get_last_domain_marker_gaps(self) -> list:
        return []

TMP_ROOT = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "data"
    / "devtools_unit"
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@contextmanager
def _workspace_temp_project():
    temp_dir = TMP_ROOT / f"project_{uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.unit
def test_find_test_files_filters_ai_and_pytest_temp_dirs():
    with _workspace_temp_project() as project_root:
        _write(project_root / "tests" / "unit" / "test_ok.py", "def test_ok():\n    pass\n")
        _write(project_root / "tests" / "ai" / "test_ai_flow.py", "def test_ai_flow():\n    pass\n")
        _write(project_root / "tests" / "unit" / "test_ai_helper.py", "def test_ai_helper():\n    pass\n")
        _write(
            project_root / "tests" / "data" / "pytest-tmp-1" / "test_tmp.py",
            "def test_tmp():\n    pass\n",
        )
        _write(
            project_root
            / "tests"
            / "data"
            / "tmp_pytest_runtime"
            / "pytest_runner"
            / "pytest_tmp_dev_tools_1234"
            / "test_runtime_tmp.py",
            "def test_runtime_tmp():\n    pass\n",
        )
        _write(
            project_root / "tests" / "data" / "custom" / "test_custom.py",
            "def test_custom():\n    pass\n",
        )

        analyzer = TestMarkerAnalyzer(project_root=project_root)
        files = [p.as_posix() for p in analyzer.find_test_files(exclude_ai=True)]

        assert str(project_root / "tests" / "unit" / "test_ok.py").replace("\\", "/") in files
        assert not any("tests/data/custom/test_custom.py" in f for f in files)
        assert not any("test_ai_flow.py" in f for f in files)
        assert not any("test_ai_helper.py" in f for f in files)
        assert not any("pytest-tmp-1" in f for f in files)
        assert not any("tmp_pytest_runtime" in f for f in files)


@pytest.mark.unit
def test_has_category_marker_and_expected_marker_path_resolution():
    with _workspace_temp_project() as project_root:
        analyzer = TestMarkerAnalyzer(project_root=project_root)

        assert analyzer.has_category_marker("@pytest.mark.unit\ndef test_x():\n    pass\n")
        assert not analyzer.has_category_marker("def test_x():\n    pass\n")
        assert analyzer.get_expected_marker(project_root / "tests" / "unit" / "test_file.py") == "unit"
        assert analyzer.get_expected_marker(project_root / "tests" / "integration" / "test_file.py") == "integration"
        assert analyzer.get_expected_marker(project_root / "tests" / "behavior" / "test_file.py") == "behavior"
        assert analyzer.get_expected_marker(project_root / "tests" / "ui" / "test_file.py") == "ui"
        assert analyzer.get_expected_marker(project_root / "tests" / "misc" / "test_file.py") is None


@pytest.mark.unit
def test_uses_configured_marker_categories_and_directory_map(monkeypatch):
    with _workspace_temp_project() as project_root:
        _write(
            project_root / "tests" / "suite" / "test_custom.py",
            "import pytest\n\n@pytest.mark.suite\ndef test_custom():\n    pass\n",
        )

        monkeypatch.setattr(
            analyze_test_markers.config,
            "get_test_markers_config",
            lambda: {
                "categories": ["suite", "integration"],
                "directory_to_marker": {
                    "suite": "suite",
                    "integration": "integration",
                },
                "transient_data_path_markers": [
                    "/tmp/",
                    "/tmp_pytest_runtime/",
                    "pytest-tmp-",
                    "pytest-of-",
                ],
                "ai_path_tokens": ["ai/test_ai", "test_ai"],
            },
        )

        analyzer = TestMarkerAnalyzer(project_root=project_root)
        content = (project_root / "tests" / "suite" / "test_custom.py").read_text(
            encoding="utf-8"
        )

        assert analyzer.has_category_marker(content)
        assert (
            analyzer.get_expected_marker(project_root / "tests" / "suite" / "test_file.py")
            == "suite"
        )


@pytest.mark.unit
def test_analyze_markers_reports_missing_and_file_groups():
    with _workspace_temp_project() as project_root:
        _write(
            project_root / "tests" / "unit" / "test_with_marker.py",
            "import pytest\n\n@pytest.mark.unit\ndef test_x():\n    pass\n",
        )
        _write(
            project_root / "tests" / "integration" / "test_without_marker.py",
            "def test_y():\n    pass\n",
        )
        _write(project_root / "tests" / "misc" / "test_misc.py", "def test_misc():\n    pass\n")

        analyzer = TestMarkerAnalyzer(project_root=project_root)
        result = analyzer.analyze_markers()

        assert result["total_files"] == 3
        assert result["files_needing_markers"] == 2
        assert result["files_by_dir"]["unit"] == 1
        assert result["files_by_dir"]["integration"] == 1
        assert result["files_by_dir"]["other"] == 1


@pytest.mark.unit
def test_missing_marker_finder_handles_fixtures_and_nested_tests():
    with _workspace_temp_project() as project_root:
        test_file = project_root / "tests" / "unit" / "test_nested.py"
        _write(
            test_file,
            (
                "import pytest\n\n"
                "@pytest.mark.unit\n"
                "def test_top_level_marked():\n    pass\n\n"
                "class TestOuter:\n"
                "    def test_missing(self):\n        pass\n\n"
                "    @pytest.fixture\n"
                "    def test_fixture_name(self):\n        return 1\n\n"
                "    @pytest.mark.unit\n"
                "    def test_marked(self):\n        pass\n\n"
                "    class TestInner:\n"
                "        def test_inner_missing(self):\n            pass\n"
            ),
        )

        finder = MissingMarkerFinder()
        finder.analyze_file(test_file)

        missing_names = {entry[2] for entry in finder.missing}
        assert "test_missing" in missing_names
        assert "test_inner_missing" in missing_names
        assert "test_fixture_name" not in missing_names
        assert "test_top_level_marked" not in missing_names
        assert "test_marked" not in missing_names


@pytest.mark.unit
def test_missing_marker_finder_skips_syntax_errors():
    with _workspace_temp_project() as project_root:
        bad_file = project_root / "tests" / "unit" / "test_bad.py"
        _write(bad_file, "def test_bad(:\n    pass\n")

        finder = MissingMarkerFinder()
        finder.analyze_file(bad_file)

        assert finder.missing == []


@pytest.mark.unit
def test_add_markers_inserts_import_and_class_markers():
    with _workspace_temp_project() as project_root:
        test_file = project_root / "tests" / "unit" / "test_add.py"
        _write(
            test_file,
            (
                "from pathlib import Path\n\n"
                "class TestFirst:\n"
                "    def test_one(self):\n        pass\n\n"
                "class TestSecond:\n"
                "    def test_two(self):\n        pass\n"
            ),
        )

        analyzer = TestMarkerAnalyzer(project_root=project_root)
        result = analyzer.add_markers(dry_run=False)

        updated_paths = [entry[0].replace("\\", "/") for entry in result["updated"]]
        assert str(test_file).replace("\\", "/") in updated_paths

        content = test_file.read_text(encoding="utf-8")
        assert "import pytest" in content
        assert content.count("@pytest.mark.unit") >= 2
        assert "class TestFirst" in content
        assert "class TestSecond" in content


@pytest.mark.unit
def test_add_markers_dry_run_does_not_modify_file():
    with _workspace_temp_project() as project_root:
        test_file = project_root / "tests" / "unit" / "test_dry_run.py"
        original = "class TestOnly:\n    def test_value(self):\n        pass\n"
        _write(test_file, original)

        analyzer = TestMarkerAnalyzer(project_root=project_root)
        result = analyzer.add_markers(dry_run=True)

        assert result["dry_run"] is True
        assert test_file.read_text(encoding="utf-8") == original


@pytest.mark.unit
def test_add_markers_skips_files_with_existing_marker_or_no_matching_class():
    with _workspace_temp_project() as project_root:
        with_marker = project_root / "tests" / "unit" / "test_with_marker.py"
        _write(
            with_marker,
            "import pytest\n\n@pytest.mark.unit\nclass TestUnit:\n    def test_x(self):\n        pass\n",
        )
        no_test_class = project_root / "tests" / "unit" / "test_no_class.py"
        _write(no_test_class, "def test_plain_function():\n    pass\n")

        analyzer = TestMarkerAnalyzer(project_root=project_root)
        result = analyzer.add_markers(dry_run=False)

        skipped = [s.replace("\\", "/") for s in result["skipped"]]
        assert str(with_marker).replace("\\", "/") in skipped
        assert str(no_test_class).replace("\\", "/") in skipped


@pytest.mark.unit
def test_main_check_json_output(monkeypatch, capsys):
    analyzer = _FakeAnalyzer()
    analyzer.find_missing_markers_ast = lambda: [("a.py", 10, "test_name", "function")]
    analyzer.analyze_markers = lambda: {}
    monkeypatch.setattr(analyze_test_markers, "TestMarkerAnalyzer", lambda: analyzer)
    monkeypatch.setattr(
        analyze_test_markers.sys,
        "argv",
        ["analyze_test_markers.py", "--check", "--json"],
    )

    rc = analyze_test_markers.main()
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["summary"]["total_issues"] == 1
    assert output["summary"]["files_affected"] == 1
    assert output["details"]["missing_count"] == 1
    assert output["details"]["missing_domain_count"] == 0
    assert output["details"]["missing_domain"] == []


@pytest.mark.unit
def test_main_check_returns_one_when_missing_without_json(monkeypatch, capsys):
    analyzer = _FakeAnalyzer()
    analyzer.find_missing_markers_ast = lambda: [("a.py", 2, "test_x", "function")]
    analyzer.analyze_markers = lambda: {}
    monkeypatch.setattr(analyze_test_markers, "TestMarkerAnalyzer", lambda: analyzer)
    monkeypatch.setattr(analyze_test_markers.sys, "argv", ["analyze_test_markers.py"])

    rc = analyze_test_markers.main()
    output = capsys.readouterr().out

    assert rc == 1
    assert "Total missing markers: 1" in output


@pytest.mark.unit
def test_main_analyze_json_output(monkeypatch, capsys):
    result = {
        "total_files": 2,
        "files_needing_markers": 1,
        "files_by_dir": {"unit": 1, "integration": 1, "behavior": 0, "ui": 0, "other": 0},
        "missing_markers": [("tests/unit/test_one.py", "unit")],
    }
    analyzer = _FakeAnalyzer()
    analyzer.find_missing_markers_ast = lambda: []
    analyzer.analyze_markers = lambda: result
    monkeypatch.setattr(analyze_test_markers, "TestMarkerAnalyzer", lambda: analyzer)
    monkeypatch.setattr(
        analyze_test_markers.sys,
        "argv",
        ["analyze_test_markers.py", "--analyze", "--json"],
    )

    rc = analyze_test_markers.main()
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["summary"]["total_issues"] == 1
    assert output["details"]["total_files"] == 2
