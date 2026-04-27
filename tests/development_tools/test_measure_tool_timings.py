"""Unit tests for development_tools/shared/measure_tool_timings.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from development_tools.shared.measure_tool_timings import (
    generate_timing_report,
    measure_tool_execution,
    run_timing_analysis,
)


@pytest.mark.unit
def test_measure_tool_execution_dict_success():
    service = MagicMock()

    def tool():
        return {"success": True, "error": ""}

    ok, elapsed, err = measure_tool_execution(service, "x", tool)
    assert ok is True
    assert err == ""
    assert elapsed >= 0.0


@pytest.mark.unit
def test_measure_tool_execution_dict_failure():
    service = MagicMock()

    def tool():
        return {"success": False, "error": "boom"}

    ok, elapsed, err = measure_tool_execution(service, "x", tool)
    assert ok is False
    assert err == "boom"
    assert elapsed >= 0.0


@pytest.mark.unit
def test_measure_tool_execution_non_dict_truthy():
    service = MagicMock()

    def tool():
        return "ok"

    ok, elapsed, err = measure_tool_execution(service, "x", tool)
    assert ok is True
    assert err == ""
    assert elapsed >= 0.0


@pytest.mark.unit
def test_measure_tool_execution_exception():
    service = MagicMock()

    def tool():
        raise ValueError("bad")

    ok, elapsed, err = measure_tool_execution(service, "x", tool)
    assert ok is False
    assert "bad" in err
    assert elapsed >= 0.0


@pytest.mark.unit
def test_generate_timing_report_writes_md_and_json(tmp_path: Path):
    out = tmp_path / "TIMING_ANALYSIS.md"
    results = {
        "tier1": {
            "a": {"success": True, "time": 5.0, "error": ""},
            "slow": {"success": True, "time": 45.0, "error": ""},
        },
        "tier2": {
            "b": {"success": True, "time": 20.0, "error": ""},
        },
        "tier3": {
            "c": {"success": False, "time": 200.0, "error": "x"},
        },
        "summary": {
            "total_tools": 4,
            "successful": 3,
            "failed": 1,
            "total_time": 270.0,
        },
    }
    generate_timing_report(results, out)

    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "Tool Execution Timing Analysis" in text
    assert "Total Tools Measured" in text
    assert "| slow |" in text

    js = out.with_suffix(".json")
    assert js.is_file()
    assert '"tier1"' in js.read_text(encoding="utf-8")


@pytest.mark.unit
def test_run_timing_analysis_uses_tier_lists(tmp_path: Path):
    """Smoke run_timing_analysis with mocked tiers (no real tool execution)."""

    def t_ok():
        return {"success": True}

    calls: list[int] = []

    def fake_get_tier_runnables(_service, tier: int, **_kwargs):
        calls.append(tier)
        return [("only_t1", t_ok)] if tier == 1 else []

    mock_gen_report = MagicMock()
    out = tmp_path / "out.md"

    # Patch the function globals directly because this suite can load dev-tools modules
    # through alternate import paths during coverage runs.
    with patch.dict(
        run_timing_analysis.__globals__,
        {
            "AIToolsService": MagicMock(return_value=MagicMock()),
            "get_tier_runnables": fake_get_tier_runnables,
            "generate_timing_report": mock_gen_report,
        },
    ):
        run_timing_analysis(out)

    assert calls == [1, 2, 3]
    mock_gen_report.assert_called_once()
    args, _ = mock_gen_report.call_args
    assert args[1] == out
    payload = args[0]
    assert "tier1" in payload and "only_t1" in payload["tier1"]
    assert payload["summary"]["total_tools"] == 1
    assert payload["summary"]["successful"] == 1
