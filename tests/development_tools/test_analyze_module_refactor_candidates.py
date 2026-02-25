"""Tests for analyze_module_refactor_candidates supporting tool."""

import pytest

from tests.development_tools.conftest import load_development_tools_module


@pytest.fixture
def module_refactor_module():
    """Load analyze_module_refactor_candidates module with dev tools loader."""
    return load_development_tools_module("functions.analyze_module_refactor_candidates")


@pytest.mark.unit
def test_module_metrics_collects_expected_fields(tmp_path, module_refactor_module):
    """_module_metrics should return stable metrics for valid Python files."""
    module_path = tmp_path / "sample.py"
    module_path.write_text(
        "class A:\n"
        "    def m(self):\n"
        "        return 1\n"
        "\n"
        "def f(x):\n"
        "    if x:\n"
        "        return x\n"
        "    return 0\n",
        encoding="utf-8",
    )

    metrics = module_refactor_module._module_metrics(module_path)

    assert metrics is not None
    assert metrics["lines"] >= 7
    assert metrics["function_count"] == 2
    assert metrics["class_count"] == 1
    assert metrics["total_function_complexity"] > 0
    assert metrics["high_complexity_count"] >= 0
    assert metrics["critical_complexity_count"] >= 0


@pytest.mark.unit
def test_reasons_flags_when_any_threshold_is_exceeded(module_refactor_module):
    """_reasons should emit a candidate reason when thresholds are exceeded."""
    metrics = {
        "lines": 10,
        "function_count": 1,
        "total_function_complexity": 5,
        "high_complexity_count": 0,
        "critical_complexity_count": 0,
    }

    reason = module_refactor_module._reasons(
        {"max_lines_per_module": 10},
        metrics,
        "sample.py",
    )
    assert reason == ["exceeds size/complexity thresholds"]

    no_reason = module_refactor_module._reasons(
        {
            "max_lines_per_module": 11,
            "max_functions_per_module": 2,
            "max_total_complexity_per_module": 99,
            "high_plus_critical_threshold": 1,
        },
        metrics,
        "sample.py",
    )
    assert no_reason == []


@pytest.mark.unit
def test_scan_in_production_keeps_top_level_tests_only(
    tmp_path, module_refactor_module, monkeypatch
):
    """Production scan keeps top-level tests files even when excluded."""
    tests_root = tmp_path / "tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    (tests_root / "conftest.py").write_text("def top_level():\n    return 1\n", encoding="utf-8")
    (tests_root / "unit").mkdir(parents=True, exist_ok=True)
    (tests_root / "unit" / "test_x.py").write_text("def nested_test():\n    return 2\n", encoding="utf-8")

    monkeypatch.setattr(
        module_refactor_module.config,
        "get_project_root",
        lambda: str(tmp_path),
        raising=False,
    )
    monkeypatch.setattr(
        module_refactor_module.config,
        "get_scan_directories",
        lambda: ["tests"],
        raising=False,
    )
    monkeypatch.setattr(
        module_refactor_module,
        "_get_config",
        lambda: {"max_lines_per_module": 1},
        raising=False,
    )
    monkeypatch.setattr(
        module_refactor_module,
        "should_exclude_file",
        lambda *_args, **_kwargs: True,
        raising=False,
    )

    result = module_refactor_module._scan_and_evaluate()
    files = [entry["file"] for entry in result["details"]["refactor_candidates"]]

    assert "tests/conftest.py" in files
    assert "tests/unit/test_x.py" not in files


@pytest.mark.unit
def test_scan_context_switches_for_include_flags(
    tmp_path, module_refactor_module, monkeypatch
):
    """Scan context should be testing/development depending on include flags."""
    scan_dir = tmp_path / "core"
    scan_dir.mkdir(parents=True, exist_ok=True)
    (scan_dir / "sample.py").write_text("def x():\n    return 1\n", encoding="utf-8")

    monkeypatch.setattr(
        module_refactor_module.config,
        "get_project_root",
        lambda: str(tmp_path),
        raising=False,
    )
    monkeypatch.setattr(
        module_refactor_module.config,
        "get_scan_directories",
        lambda: ["core"],
        raising=False,
    )
    monkeypatch.setattr(
        module_refactor_module,
        "_get_config",
        lambda: {"max_lines_per_module": 1},
        raising=False,
    )

    seen_contexts = []

    def _capture_context(_path: str, context: str, _default: str) -> bool:
        seen_contexts.append(context)
        return False

    monkeypatch.setattr(
        module_refactor_module,
        "should_exclude_file",
        _capture_context,
        raising=False,
    )

    module_refactor_module._scan_and_evaluate(include_tests=True)
    module_refactor_module._scan_and_evaluate(include_dev_tools=True)

    assert "testing" in seen_contexts
    assert "development" in seen_contexts


@pytest.mark.unit
def test_scan_sorts_candidates_by_lines_then_complexity(
    tmp_path, module_refactor_module, monkeypatch
):
    """Candidates should be sorted by line count, then total complexity."""
    scan_dir = tmp_path / "core"
    scan_dir.mkdir(parents=True, exist_ok=True)
    small = scan_dir / "small.py"
    large = scan_dir / "large.py"
    small.write_text("def a():\n    return 1\n", encoding="utf-8")
    large.write_text(
        "def b():\n"
        "    x = 0\n"
        "    x += 1\n"
        "    x += 2\n"
        "    x += 3\n"
        "    return x\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module_refactor_module.config,
        "get_project_root",
        lambda: str(tmp_path),
        raising=False,
    )
    monkeypatch.setattr(
        module_refactor_module.config,
        "get_scan_directories",
        lambda: ["core"],
        raising=False,
    )
    monkeypatch.setattr(
        module_refactor_module,
        "_get_config",
        lambda: {"max_lines_per_module": 1},
        raising=False,
    )
    monkeypatch.setattr(
        module_refactor_module,
        "should_exclude_file",
        lambda *_args, **_kwargs: False,
        raising=False,
    )

    result = module_refactor_module._scan_and_evaluate()
    files = [entry["file"] for entry in result["details"]["refactor_candidates"]]

    assert files[0] == "core/large.py"
    assert "core/small.py" in files
