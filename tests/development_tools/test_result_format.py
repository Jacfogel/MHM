"""Tests for development_tools/shared/result_format.py."""

import pytest

from tests.development_tools.conftest import load_development_tools_module

result_format = load_development_tools_module("shared.result_format")


@pytest.mark.unit
def test_normalize_to_standard_format_accepts_valid_dict():
    """Valid standard-format dict should be returned unchanged."""
    data = {
        "summary": {"total_issues": 5, "files_affected": 2},
        "details": {"foo": "bar"},
    }
    out = result_format.normalize_to_standard_format("test_tool", data)
    assert out is data
    assert out["summary"]["total_issues"] == 5
    assert out["summary"]["files_affected"] == 2


@pytest.mark.unit
def test_normalize_to_standard_format_rejects_non_dict():
    """Non-dict data should raise ValueError with type in message."""
    with pytest.raises(ValueError, match="must be a dict.*list"):
        result_format.normalize_to_standard_format("test_tool", [])
    with pytest.raises(ValueError, match="must be a dict.*str"):
        result_format.normalize_to_standard_format("test_tool", "x")


@pytest.mark.unit
def test_normalize_to_standard_format_requires_summary_dict():
    """Missing or non-dict summary should raise ValueError."""
    with pytest.raises(ValueError, match="missing 'summary' dict"):
        result_format.normalize_to_standard_format("test_tool", {})
    with pytest.raises(ValueError, match="missing 'summary' dict"):
        result_format.normalize_to_standard_format("test_tool", {"summary": None})
    with pytest.raises(ValueError, match="missing 'summary' dict"):
        result_format.normalize_to_standard_format("test_tool", {"summary": []})


@pytest.mark.unit
def test_normalize_to_standard_format_requires_total_issues_and_files_affected():
    """Summary must include total_issues and files_affected."""
    with pytest.raises(ValueError, match="total_issues and files_affected"):
        result_format.normalize_to_standard_format(
            "test_tool", {"summary": {}}
        )
    with pytest.raises(ValueError, match="total_issues and files_affected"):
        result_format.normalize_to_standard_format(
            "test_tool", {"summary": {"total_issues": 0}}
        )
    with pytest.raises(ValueError, match="total_issues and files_affected"):
        result_format.normalize_to_standard_format(
            "test_tool", {"summary": {"files_affected": 0}}
        )


@pytest.mark.unit
def test_normalize_to_standard_format_includes_tool_name_in_errors():
    """Error messages should include the tool name for diagnostics."""
    with pytest.raises(ValueError, match="test_tool"):
        result_format.normalize_to_standard_format("test_tool", [])
