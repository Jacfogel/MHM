"""Tests for coverage-related helpers in CommandsMixin."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tests.development_tools.conftest import load_development_tools_module

# Patch at the module where config is imported from (development_tools.config)
CONFIG_PATCH = "development_tools.config.get_coverage_runtime_config"

commands_module = load_development_tools_module("shared.service.commands")
CommandsMixin = commands_module.CommandsMixin


class _DummyService(CommandsMixin):
    """Minimal service surface for testing coverage helpers."""

    def __init__(self, project_root: Path):
        self.project_root = project_root


@pytest.mark.unit
def test_resolve_coverage_workers_invalid_target_returns_none(tmp_path):
    """Invalid target returns None."""
    service = _DummyService(tmp_path)
    assert service._resolve_coverage_workers("invalid") is None
    assert service._resolve_coverage_workers("") is None
    assert service._resolve_coverage_workers("main_coverage") is None


@pytest.mark.unit
def test_resolve_coverage_workers_config_override_main(tmp_path):
    """Configured main_workers is returned when not concurrent."""
    service = _DummyService(tmp_path)
    with patch(CONFIG_PATCH, return_value={"main_workers": 4}):
        result = service._resolve_coverage_workers("main")
    assert result == "4"


@pytest.mark.unit
def test_resolve_coverage_workers_config_override_dev_tools(tmp_path):
    """Configured dev_tools_workers is returned when not concurrent."""
    service = _DummyService(tmp_path)
    with patch(CONFIG_PATCH, return_value={"dev_tools_workers": 2}):
        result = service._resolve_coverage_workers("dev_tools")
    assert result == "2"


@pytest.mark.unit
def test_resolve_coverage_workers_config_auto(tmp_path):
    """Configured 'auto' is returned as-is."""
    service = _DummyService(tmp_path)
    with patch(CONFIG_PATCH, return_value={"main_workers": "auto"}):
        result = service._resolve_coverage_workers("main")
    assert result == "auto"


@pytest.mark.unit
def test_resolve_coverage_workers_config_invalid_ignored(tmp_path):
    """Invalid configured value (non-numeric) is ignored; falls through to None."""
    service = _DummyService(tmp_path)
    with patch(CONFIG_PATCH, return_value={"main_workers": "nope"}):
        result = service._resolve_coverage_workers("main")
    assert result is None


@pytest.mark.unit
def test_resolve_coverage_workers_config_zero_ignored(tmp_path):
    """Configured 0 is ignored (must be > 0)."""
    service = _DummyService(tmp_path)
    with patch(CONFIG_PATCH, return_value={"main_workers": 0}):
        result = service._resolve_coverage_workers("main")
    assert result is None


@pytest.mark.unit
def test_resolve_coverage_workers_concurrent_fallback(tmp_path):
    """When concurrent and no config, returns CPU-based fallback."""
    service = _DummyService(tmp_path)
    service._tier3_coverage_concurrent = True
    with patch(CONFIG_PATCH, return_value={}):
        with patch("os.cpu_count", return_value=8):
            main_result = service._resolve_coverage_workers("main")
            dev_result = service._resolve_coverage_workers("dev_tools")
    assert main_result == "6"
    assert dev_result == "2"


@pytest.mark.unit
def test_resolve_coverage_workers_dev_tools_serialized_windows_path(tmp_path):
    """When coverage is serialized (Windows guardrail), dev-tools fallback matches main cap."""
    service = _DummyService(tmp_path)
    service._tier3_coverage_concurrent = True
    service._tier3_coverage_serialized = True
    with patch(CONFIG_PATCH, return_value={}):
        with patch("os.cpu_count", return_value=8):
            dev_result = service._resolve_coverage_workers("dev_tools")
    assert dev_result == "6"


@pytest.mark.unit
def test_resolve_coverage_workers_config_exception_uses_empty(tmp_path):
    """Config get_external_value exception uses empty dict; concurrent fallback used."""
    service = _DummyService(tmp_path)
    service._tier3_coverage_concurrent = True
    with patch(CONFIG_PATCH, side_effect=ValueError("simulated")):
        with patch("os.cpu_count", return_value=8):
            result = service._resolve_coverage_workers("main")
    assert result == "6"


@pytest.mark.unit
def test_infer_coverage_cache_mode_cache_only(tmp_path):
    """Infer cache_only from output text."""
    service = _DummyService(tmp_path)
    assert service._infer_coverage_cache_mode_from_output("Using cached coverage data only") == "cache_only"
    assert service._infer_coverage_cache_mode_from_output("using cached coverage data") == "cache_only"


@pytest.mark.unit
def test_infer_coverage_cache_mode_partial_cache(tmp_path):
    """Infer partial_cache from merge text."""
    service = _DummyService(tmp_path)
    assert service._infer_coverage_cache_mode_from_output("Merged cached and fresh coverage data") == "partial_cache"
    assert service._infer_coverage_cache_mode_from_output("cache merge complete") == "partial_cache"


@pytest.mark.unit
def test_infer_coverage_cache_mode_cold_scan(tmp_path):
    """Infer cold_scan from rerun markers."""
    service = _DummyService(tmp_path)
    assert service._infer_coverage_cache_mode_from_output("Running all tests") == "cold_scan"
    assert service._infer_coverage_cache_mode_from_output("source files changed") == "cold_scan"


@pytest.mark.unit
def test_infer_coverage_cache_mode_unknown(tmp_path):
    """Unknown text returns unknown."""
    service = _DummyService(tmp_path)
    assert service._infer_coverage_cache_mode_from_output("") == "unknown"
    assert service._infer_coverage_cache_mode_from_output("nothing relevant") == "unknown"


@pytest.mark.unit
def test_extract_coverage_invalidation_reason_empty(tmp_path):
    """Empty output returns unknown."""
    service = _DummyService(tmp_path)
    assert service._extract_coverage_invalidation_reason("") == "unknown"
    assert service._extract_coverage_invalidation_reason(None) == "unknown"


@pytest.mark.unit
def test_extract_coverage_invalidation_reason_found(tmp_path):
    """First matching line is returned."""
    service = _DummyService(tmp_path)
    out = "line1\n  Invalidating cache: source files changed\nline3"
    assert "invalidating" in service._extract_coverage_invalidation_reason(out).lower()
    out2 = "Using cached coverage data"
    assert "cached" in service._extract_coverage_invalidation_reason(out2).lower()


@pytest.mark.unit
def test_extract_coverage_invalidation_reason_no_match(tmp_path):
    """No matching markers returns unknown."""
    service = _DummyService(tmp_path)
    assert service._extract_coverage_invalidation_reason("foo\nbar") == "unknown"


@pytest.mark.unit
def test_extract_changed_domains_empty(tmp_path):
    """Empty output returns empty list."""
    service = _DummyService(tmp_path)
    assert service._extract_changed_domains("") == []
    assert service._extract_changed_domains(None) == []


@pytest.mark.unit
def test_extract_changed_domains_json_list(tmp_path):
    """JSON list in domain(s) changed: is parsed."""
    service = _DummyService(tmp_path)
    out = "Domain(s) changed: [\"core\", \"ui\"]"
    result = service._extract_changed_domains(out)
    assert result == ["core", "ui"]


@pytest.mark.unit
def test_extract_changed_domains_comma_separated(tmp_path):
    """Comma-separated values are parsed when not valid JSON."""
    service = _DummyService(tmp_path)
    out = "Domain(s) changed: core, ui, tasks"
    result = service._extract_changed_domains(out)
    assert "core" in result and "ui" in result


@pytest.mark.unit
def test_extract_changed_domains_single_quoted_json_list(tmp_path):
    """Bracket lists with single quotes are normalized to JSON for parsing."""
    service = _DummyService(tmp_path)
    out = "Domain(s) changed: ['core', 'ui']"
    result = service._extract_changed_domains(out)
    assert result == ["core", "ui"]


@pytest.mark.unit
def test_extract_changed_domains_malformed_json_bracket_falls_back_to_split(tmp_path):
    """Invalid JSON list content falls through to comma/bracket parsing."""
    service = _DummyService(tmp_path)
    out = "Domain(s) changed: [not-valid-json"
    result = service._extract_changed_domains(out)
    assert isinstance(result, list)
    assert len(result) >= 1


@pytest.mark.unit
def test_build_coverage_metadata_includes_cache_mode_and_reason(tmp_path):
    service = _DummyService(tmp_path)
    out = "Using cached coverage data only\nDomain(s) changed: [\"core\"]\n"
    meta = service._build_coverage_metadata(out, source="main")
    assert meta["cache_mode"] == "cache_only"
    assert meta["source"] == "main"
    assert "cached coverage" in str(meta["invalidation_reason"]).lower()
    assert meta["changed_domains"] == ["core"]


@pytest.mark.unit
def test_is_interrupt_signature_detects_keyboardinterrupt_and_sigint_code(tmp_path):
    service = _DummyService(tmp_path)
    assert service._is_interrupt_signature("KeyboardInterrupt in pytest", 1) is True
    assert service._is_interrupt_signature("", 130) is True
    assert service._is_interrupt_signature("regular failure", 1) is False


@pytest.mark.unit
def test_to_standard_dev_tools_coverage_result_preserves_standard_payload(tmp_path):
    service = _DummyService(tmp_path)
    payload = {"summary": {"total_issues": 3}, "details": {"overall": {}}}
    assert service._to_standard_dev_tools_coverage_result(payload) is payload


@pytest.mark.unit
def test_to_standard_dev_tools_coverage_result_wraps_raw_coverage_payload(tmp_path):
    service = _DummyService(tmp_path)
    raw = {"overall": {"total_missed": "12"}, "files": {"a.py": {}}}
    normalized = service._to_standard_dev_tools_coverage_result(raw)
    assert normalized["summary"]["total_issues"] == 12
    assert normalized["summary"]["files_affected"] == 0
    assert normalized["details"] == raw


@pytest.mark.unit
def test_extract_cached_main_coverage_state_uses_tier3_details(tmp_path):
    service = _DummyService(tmp_path)
    cached = {
        "details": {
            "tier3_test_outcome": {
                "parallel": {"classification": "passed"},
                "no_parallel": {"classification": "skipped"},
            }
        }
    }
    assert service._extract_cached_main_coverage_state(cached) == "clean"
    assert service._extract_cached_main_coverage_state({"details": {}}) is None
    assert service._extract_cached_main_coverage_state(None) is None


@pytest.mark.unit
def test_extract_cached_dev_tools_state_uses_structured_outcome(tmp_path):
    service = _DummyService(tmp_path)
    cached = {"details": {"dev_tools_test_outcome": {"classification": "failed"}}}
    assert service._extract_cached_dev_tools_state(cached) == "failed"
    assert service._extract_cached_dev_tools_state({"details": {"dev_tools_test_outcome": {}}}) == "unknown"
    assert service._extract_cached_dev_tools_state({"details": {}}) is None


@pytest.mark.unit
def test_extract_track_classification_strips_and_defaults_unknown(tmp_path):
    service = _DummyService(tmp_path)
    assert service._extract_track_classification({"classification": " passed "}) == "passed"
    assert service._extract_track_classification({"classification": ""}) == "unknown"
    assert service._extract_track_classification("not-a-dict") == "unknown"


@pytest.mark.unit
def test_latest_mtime_for_patterns_ignores_excluded_paths(tmp_path):
    service = _DummyService(tmp_path)
    (tmp_path / "keep").mkdir()
    (tmp_path / "skip").mkdir()
    older = tmp_path / "keep" / "a.py"
    newer = tmp_path / "skip" / "b.py"
    older.write_text("x", encoding="utf-8")
    newer.write_text("y", encoding="utf-8")

    # Exclude `skip/` so only `keep/a.py` counts.
    latest = service._latest_mtime_for_patterns(["**/*.py"], exclude_prefixes=["skip/"])
    assert latest == pytest.approx(older.stat().st_mtime)


@pytest.mark.unit
def test_get_existing_audit_related_locks_cleans_stale_lock(tmp_path):
    """Stale lock files are removed before returning active paths."""
    service = _DummyService(tmp_path)
    stale = tmp_path / ".audit_in_progress.lock"
    stale.write_text("not-json", encoding="utf-8")
    locks = service._get_existing_audit_related_locks()
    assert not stale.exists()
    assert locks == []


@pytest.mark.unit
def test_get_audit_related_lock_paths_returns_expected_paths(tmp_path):
    """_get_audit_related_lock_paths returns lock paths anchored at project root."""
    service = _DummyService(tmp_path)
    paths = service._get_audit_related_lock_paths()
    assert len(paths) == 3
    path_strs = [str(p) for p in paths]
    assert any(".audit_in_progress" in s for s in path_strs)
    assert any(".coverage" in s for s in path_strs)
    assert any("dev_tools" in s for s in path_strs)


@pytest.mark.unit
def test_get_existing_audit_related_locks_empty_project_returns_empty(tmp_path):
    """_get_existing_audit_related_locks returns [] when no lock files exist."""
    service = _DummyService(tmp_path)
    locks = service._get_existing_audit_related_locks()
    assert locks == []


@pytest.mark.unit
def test_get_audit_related_lock_paths_config_error_falls_back_to_defaults(tmp_path):
    """If config lookup fails, default lock basenames are still anchored at project root."""
    import development_tools as dt_pkg

    service = _DummyService(tmp_path)
    with patch.object(dt_pkg.config, "get_external_value", side_effect=RuntimeError("config unavailable")):
        paths = service._get_audit_related_lock_paths()
    assert len(paths) == 3
    names = {p.name for p in paths}
    assert ".audit_in_progress.lock" in names
    assert ".coverage_in_progress.lock" in names
    assert ".coverage_dev_tools_in_progress.lock" in names


@pytest.mark.unit
def test_derive_tier3_state_explicit_coverage_failed(tmp_path):
    """Explicit aggregate state short-circuits per-track classification."""
    service = _DummyService(tmp_path)
    assert (
        service._derive_tier3_state_from_classifications({"state": "coverage_failed"})
        == "coverage_failed"
    )


@pytest.mark.unit
def test_derive_tier3_state_infra_precedes_failed(tmp_path):
    service = _DummyService(tmp_path)
    outcome = {
        "parallel": {"classification": "failed"},
        "no_parallel": {"classification": "infra_cleanup_error"},
        "development_tools": {"classification": "passed"},
    }
    assert service._derive_tier3_state_from_classifications(outcome) == "infra_cleanup_error"


@pytest.mark.unit
def test_derive_tier3_state_clean_with_skipped_tracks(tmp_path):
    service = _DummyService(tmp_path)
    outcome = {
        "parallel": {"classification": "skipped"},
        "no_parallel": {"classification": "passed"},
        "development_tools": {"classification": "skipped"},
    }
    assert service._derive_tier3_state_from_classifications(outcome) == "clean"


@pytest.mark.unit
def test_derive_tier3_state_all_unknown_is_coverage_failed(tmp_path):
    service = _DummyService(tmp_path)
    outcome = {
        "parallel": {"classification": "unknown"},
        "no_parallel": {"classification": "unknown"},
        "development_tools": {"classification": "unknown"},
    }
    assert service._derive_tier3_state_from_classifications(outcome) == "coverage_failed"


@pytest.mark.unit
def test_is_coverage_file_fresh_false_when_coverage_stat_fails(tmp_path):
    service = _DummyService(tmp_path)
    coverage_file = MagicMock()
    coverage_file.exists.return_value = True
    coverage_file.stat.side_effect = OSError("no stat")
    assert (
        service._is_coverage_file_fresh(coverage_file, source_patterns=["**/*.py"])
        is False
    )


@pytest.mark.unit
def test_is_failure_state_recognizes_error_labels(tmp_path):
    service = _DummyService(tmp_path)
    assert service._is_failure_state("errors") is True
    assert service._is_failure_state("error") is True
    assert service._is_failure_state(None) is False


@pytest.mark.unit
def test_run_doc_subcheck_with_cache_uses_standard_data_payload(tmp_path, monkeypatch):
    service = _DummyService(tmp_path)
    service._tool_cache_metadata = {}
    service.results_cache = {}
    service._tools_run_in_current_tier = set()
    monkeypatch.setattr(service, "_is_doc_subcheck_cache_fresh", lambda _tool: False)

    payload = {"summary": {"total_issues": 1}, "details": {"files": ["x.md"]}}
    result = service._run_doc_subcheck_with_cache(
        "analyze_heading_numbering",
        "Headings",
        lambda _output: {},
        lambda: {"success": True, "data": payload},
    )

    assert result == payload
    assert "analyze_heading_numbering" in service._tools_run_in_current_tier
    assert service.results_cache["analyze_heading_numbering"] == payload
    assert (
        service._tool_cache_metadata["analyze_heading_numbering"]["source"]
        == "subcheck_direct_result"
    )


@pytest.mark.unit
def test_run_doc_subcheck_with_cache_parses_stdout_result(tmp_path, monkeypatch):
    service = _DummyService(tmp_path)
    service._tool_cache_metadata = {}
    service.results_cache = {}
    service._tools_run_in_current_tier = set()
    monkeypatch.setattr(service, "_is_doc_subcheck_cache_fresh", lambda _tool: False)

    parsed = {"summary": {"total_issues": 2}, "details": {"files": ["a.md", "b.md"]}}
    save_mock = MagicMock()
    monkeypatch.setattr(commands_module, "save_tool_result", save_mock)

    result = service._run_doc_subcheck_with_cache(
        "analyze_missing_addresses",
        "Missing addresses",
        lambda _output: parsed,
        lambda: {"success": True, "output": "tool text"},
    )

    assert result == parsed
    assert service.results_cache["analyze_missing_addresses"] == parsed
    save_mock.assert_called_once()
    assert (
        service._tool_cache_metadata["analyze_missing_addresses"]["source"]
        == "doc_subcheck_stdout"
    )


@pytest.mark.unit
def test_run_doc_subcheck_with_cache_fallback_parse_when_cached_loader_errors(
    tmp_path, monkeypatch
):
    service = _DummyService(tmp_path)
    service._tool_cache_metadata = {}
    service.results_cache = {}
    service._tools_run_in_current_tier = set()
    monkeypatch.setattr(service, "_is_doc_subcheck_cache_fresh", lambda _tool: False)
    monkeypatch.setattr(
        service,
        "_load_mtime_cached_tool_results",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("simulated")),
        raising=False,
    )
    monkeypatch.setattr(commands_module, "save_tool_result", MagicMock())

    parse_calls = {"count": 0}

    def _parser(_output):
        parse_calls["count"] += 1
        if parse_calls["count"] == 1:
            return {"summary": {}}  # Non-standard shape forces cached-loader path.
        return {"summary": {"total_issues": 0}, "details": {}}

    result = service._run_doc_subcheck_with_cache(
        "analyze_unconverted_links",
        "Unconverted links",
        _parser,
        lambda: {"success": True, "output": "fallback parse me"},
    )

    assert parse_calls["count"] == 2
    assert result == {"summary": {"total_issues": 0}, "details": {}}
    assert (
        service._tool_cache_metadata["analyze_unconverted_links"]["source"]
        == "doc_subcheck_fallback"
    )
