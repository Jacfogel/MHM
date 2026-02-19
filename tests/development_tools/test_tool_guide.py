"""Unit tests for development_tools.shared.tool_guide."""

from types import SimpleNamespace

import pytest

from tests.development_tools.conftest import load_development_tools_module


tool_guide = load_development_tools_module("shared.tool_guide")


@pytest.mark.unit
def test_print_tier_overview_uses_tool_metadata(monkeypatch, capsys):
    fake_map = {
        "core": [SimpleNamespace(name="core_tool.py", trust="stable", description="Core tool")],
        "supporting": [SimpleNamespace(name="support_tool.py", trust="advisory", description="Support tool")],
        "experimental": [],
    }

    monkeypatch.setattr(tool_guide, "get_tools_by_tier", lambda tier: fake_map.get(tier, []))
    tool_guide._print_tier_overview()
    output = capsys.readouterr().out

    assert "Tier Overview" in output
    assert "Core (stable):" in output
    assert "core_tool.py [stable]: Core tool" in output
    assert "Supporting (advisory):" in output
    assert "support_tool.py [advisory]: Support tool" in output


@pytest.mark.unit
def test_show_tool_guide_specific_and_unknown(capsys):
    tool_guide.show_tool_guide("analyze_functions.py")
    known_output = capsys.readouterr().out
    assert "Tool Guide: analyze_functions.py" in known_output
    assert "When to Use:" in known_output

    tool_guide.show_tool_guide("missing_tool.py")
    unknown_output = capsys.readouterr().out
    assert "Available tools:" in unknown_output


@pytest.mark.unit
def test_get_tool_recommendation_returns_matches():
    recs = tool_guide.get_tool_recommendation("Need documentation and refactoring help")
    assert len(recs) > 0
    assert all("tool" in rec and "reason" in rec and "priority" in rec for rec in recs)


@pytest.mark.unit
def test_show_recommendations_with_and_without_results(monkeypatch, capsys):
    monkeypatch.setattr(
        tool_guide,
        "get_tool_recommendation",
        lambda scenario: [{"tool": "analyze_functions.py", "reason": "Need structure", "priority": "medium"}],
    )
    tool_guide.show_recommendations("code organization")
    has_output = capsys.readouterr().out
    assert "[MED] 1. analyze_functions.py" in has_output

    monkeypatch.setattr(tool_guide, "get_tool_recommendation", lambda scenario: [])
    tool_guide.show_recommendations("totally unrelated term")
    no_output = capsys.readouterr().out
    assert "Try running the general audit first" in no_output


@pytest.mark.unit
def test_run_tool_with_guidance_invalid_tool_logs_error(monkeypatch):
    calls = []
    monkeypatch.setattr(tool_guide.logger, "error", lambda msg: calls.append(msg))

    tool_guide.run_tool_with_guidance("missing_tool.py")

    assert calls
    assert "not found" in calls[0]


@pytest.mark.unit
def test_run_tool_with_guidance_success_and_stderr(monkeypatch, capsys):
    result = SimpleNamespace(stdout="ok output", stderr="warning output")

    monkeypatch.setattr(
        tool_guide.subprocess,
        "run",
        lambda *args, **kwargs: result,
    )

    tool_guide.run_tool_with_guidance("analyze_functions.py")
    output = capsys.readouterr().out

    assert "Running analyze_functions.py with guidance..." in output
    assert "Tool Output:" in output
    assert "ok output" in output
    assert "Errors:" in output
    assert "warning output" in output
    assert "Success Criteria Check:" in output


@pytest.mark.unit
def test_run_tool_with_guidance_handles_timeout(monkeypatch, capsys):
    def _raise_timeout(*args, **kwargs):
        raise tool_guide.subprocess.TimeoutExpired(cmd="x", timeout=60)

    monkeypatch.setattr(tool_guide.subprocess, "run", _raise_timeout)

    tool_guide.run_tool_with_guidance("analyze_functions.py")
    output = capsys.readouterr().out

    assert "Tool timed out after 60 seconds" in output


@pytest.mark.unit
def test_show_tool_guide_default_lists_overview(monkeypatch, capsys):
    monkeypatch.setattr(tool_guide, "_print_tier_overview", lambda: None)

    tool_guide.show_tool_guide()
    output = capsys.readouterr().out

    assert "AI Tools Guide - When to Use Each Tool" in output
    assert "run_development_tools.py" in output
