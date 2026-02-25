"""Focused tests for development_tools/shared/service/utilities.py."""

import pytest

from tests.development_tools.conftest import load_development_tools_module


utilities_module = load_development_tools_module("shared.service.utilities")
UtilitiesMixin = utilities_module.UtilitiesMixin


class _DummyUtilities(UtilitiesMixin):
    def __init__(self):
        self.results_cache = {}
        self.module_dependency_summary = {}


@pytest.mark.unit
def test_basic_formatting_and_parsing_helpers():
    """Top-level helper functions should handle normal and edge inputs."""
    assert utilities_module.format_list_for_display([]) == ""
    assert utilities_module.format_list_for_display(["a", "b"], limit=3) == "a, b"
    assert (
        utilities_module.format_list_for_display(["a", "b", "c"], limit=2)
        == "a, b, ... +1"
    )

    assert utilities_module.format_percentage(12.345, 1) == "12.3%"
    assert utilities_module.format_percentage("n/a") == "n/a"
    assert utilities_module.extract_first_int("abc -42 def") == -42
    assert utilities_module.extract_first_int(123) is None

    parsed = utilities_module.parse_function_entry(
        "foo (file: core/a.py, complexity: 77)"
    )
    assert parsed == {"function": "foo", "file": "core/a.py", "complexity": 77}
    assert utilities_module.parse_function_entry("not a function entry") is None


@pytest.mark.unit
def test_extract_function_and_documentation_metrics_paths():
    """Mixin extraction helpers should parse function and doc metrics payloads."""
    dummy = _DummyUtilities()
    dummy._extract_function_metrics(
        {
            "output": "\n".join(
                [
                    "Found 5 functions",
                    "HIGH COMPLEXITY (2):",
                    "- high_fn (file: core/a.py, complexity: 25)",
                    "CRITICAL COMPLEXITY (1):",
                    "- crit_fn (file: core/b.py, complexity: 300)",
                    "UNDOCUMENTED (1):",
                    "- doc_fn (file: core/c.py, complexity: 3)",
                ]
            )
        }
    )

    function_metrics = dummy.results_cache["analyze_functions"]
    assert function_metrics["total_functions"] == 5
    assert function_metrics["high_complexity"] == 2
    assert function_metrics["critical_complexity"] == 1
    assert function_metrics["undocumented"] == 1
    assert function_metrics["critical_complexity_examples"][0]["function"] == "crit_fn"

    dummy._extract_documentation_metrics(
        {
            "data": {
                "totals": {"functions_found": 5, "classes_found": 2, "files_scanned": 4},
                "missing": {"count": 1, "missing_files": ["core/c.py"]},
                "extra": {"count": 0},
            }
        }
    )
    registry_metrics = dummy.results_cache["analyze_function_registry"]
    assert registry_metrics["registry_functions_found"] == 5
    assert registry_metrics["missing_docs"] == 1


@pytest.mark.unit
def test_extract_decision_insights_builds_standard_result():
    """Decision support extraction should build standard-format cache output."""
    dummy = _DummyUtilities()
    dummy._extract_decision_insights(
        {
            "output": "\n".join(
                [
                    "[CRITICAL] critical complexity candidates",
                    "- critical_fn (file: core/x.py, complexity: 250)",
                    "[HIGH] high complexity candidates",
                    "- high_fn (file: core/y.py, complexity: 120)",
                    "Total functions: 10",
                    "Moderate complexity: 2",
                    "High complexity: 1",
                    "Critical complexity: 1",
                    "Undocumented functions: 3",
                ]
            )
        }
    )

    result = dummy.results_cache["decision_support"]
    assert result["summary"]["total_issues"] == 5
    assert result["details"]["total_functions"] == 10
    assert result["details"]["critical_complexity_examples"][0]["file"] == "core/x.py"
    assert dummy.results_cache["analyze_functions"]["critical_complexity_examples"]


@pytest.mark.unit
def test_extract_key_info_stores_standard_result_for_generic_tools():
    """_extract_key_info should preserve standard-format payloads for non-special tools."""
    dummy = _DummyUtilities()
    payload = {
        "data": {
            "summary": {"total_issues": 2, "files_affected": 1},
            "details": {"candidates": ["a.py"]},
        }
    }

    dummy._extract_key_info("module_refactor_candidates", payload)

    assert dummy.results_cache["module_refactor_candidates"]["summary"]["total_issues"] == 2
