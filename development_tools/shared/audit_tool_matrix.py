# TOOL_TIER: core

"""Audit tier participation and report-surface hints (V5 §7.21).

Single source for JSON under ``development_tools/config/audit_tool_matrix.json``.
Regenerate after changing ``audit_tiers`` or report wiring expectations.
"""

from __future__ import annotations

from development_tools.shared.audit_tiers import get_expected_tools_for_tier
from development_tools.shared.tool_metadata import get_script_registry, get_tool_metadata

# Narrow, explicit exceptions only; everything else is derived from canonical sources.
_NON_AUDIT_REASON_OVERRIDES: dict[str, str] = {
    "flaky_detector": "manual_cli_nested_pytest",
    "fix_version_sync": "manual_docs_cli",
    "measure_tool_timings": "manual_benchmark",
}

_REPORT_HINT_OVERRIDES: dict[str, list[str]] = {
    "analyze_system_signals": ["AI_STATUS System Signals", "CONSOLIDATED_REPORT"],
    "analyze_test_markers": ["AI_STATUS Test Markers"],
    "verify_process_cleanup": ["AI_STATUS Pytest process cleanup"],
    "run_test_coverage": ["AI_STATUS Test Coverage", "TEST_COVERAGE_REPORT", "coverage.json"],
    "generate_dev_tools_coverage": ["AI_STATUS Development Tools Coverage", "coverage_dev_tools.json"],
    "generate_unused_imports_report": ["development_docs/UNUSED_IMPORTS_REPORT.md"],
    "generate_test_coverage_report": ["development_docs/TEST_COVERAGE_REPORT.md"],
    "generate_legacy_reference_report": ["development_docs/LEGACY_REFERENCE_REPORT.md"],
}


def _tool_domain_from_registry(script_registry: dict[str, str], tool_name: str) -> str | None:
    rel = script_registry.get(tool_name, "").replace("\\", "/").strip()
    if not rel:
        return None
    parts = rel.split("/")
    return parts[0] if len(parts) >= 2 else None


def _default_report_surface_hints(tool_name: str, domain: str | None) -> list[str]:
    if tool_name in _REPORT_HINT_OVERRIDES:
        return _REPORT_HINT_OVERRIDES[tool_name]
    hints: list[str] = []
    if domain:
        hints.append(f"jsons/{domain}")
    if domain == "static_checks":
        hints.insert(0, "AI_STATUS Static Analysis")
    elif tool_name.startswith("analyze_") and domain in {"reports", "docs"}:
        hints.insert(0, "CONSOLIDATED_REPORT")
    if tool_name in {"decision_support", "analyze_duplicate_functions", "analyze_module_refactor_candidates"}:
        hints.append("AI_PRIORITIES")
    return hints or ["jsons or generated markdown"]


def _non_audit_reason(tool_name: str) -> str:
    if tool_name in _NON_AUDIT_REASON_OVERRIDES:
        return _NON_AUDIT_REASON_OVERRIDES[tool_name]
    try:
        info = get_tool_metadata(tool_name)
    except KeyError:
        return "script_not_in_tier_lists_review_if_new"
    if info.trust in {"experimental", "advisory"}:
        return "not_in_tier_lists_review_if_new"
    return "core_script_not_in_tier_lists"


def build_audit_tool_matrix() -> dict:
    """Return serializable matrix: tier membership + catalog cross-check."""
    t1 = set(get_expected_tools_for_tier(1))
    t2 = set(get_expected_tools_for_tier(2))
    t3_full = set(get_expected_tools_for_tier(3, dev_tools_only=False))
    t3_dev = set(get_expected_tools_for_tier(3, dev_tools_only=True))
    audit_names = sorted(t1 | t2 | t3_full | t3_dev)

    script_registry = get_script_registry()
    tools_out: dict[str, dict] = {}
    for name in audit_names:
        domain = _tool_domain_from_registry(script_registry, name)
        tools_out[name] = {
            "in_tier1_quick": name in t1,
            "in_tier2_standard_expanded": name in t2,
            "in_tier3_full_repo_audit": name in t3_full,
            "in_tier3_dev_tools_only_audit": name in t3_dev,
            "report_surface_hints": _default_report_surface_hints(name, domain),
        }

    script_names = set(script_registry.keys())
    scripts_not_in_audit = sorted(script_names - set(audit_names))
    manual_other = [
        {
            "tool": n,
            "reason": _non_audit_reason(n),
        }
        for n in scripts_not_in_audit
    ]

    return {
        "schema_version": 1,
        "description": "Tier membership from audit_tiers.get_expected_tools_for_tier; "
        "non-audit entries are script-registry keys missing from tier unions.",
        "audit_tools": tools_out,
        "script_registry_tools_not_in_audit_matrix": manual_other,
    }
