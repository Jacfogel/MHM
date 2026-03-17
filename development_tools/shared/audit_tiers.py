# TOOL_TIER: core

"""
Canonical definition of which tools run in each audit tier (1=quick, 2=standard, 3=full).

Used by measure_tool_timings.py and audit_orchestration.py so tier tool lists
are defined in one place and do not drift.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

# -----------------------------------------------------------------------------
# Flat tool name lists (for reporting, timing, _get_expected_tools_for_tier)
# -----------------------------------------------------------------------------

# Tier 1: Quick audit (<=2s target per tool). quick_status only in explicit Tier 1 runs.
TIER1_TOOL_NAMES = [
    "analyze_system_signals",
    "analyze_documentation",
    "analyze_config",
    "analyze_ai_work",
    "analyze_function_patterns",
    "decision_support",
    "quick_status",
]

# Tier 2: Standard audit (>2s but <=10s per tool).
TIER2_TOOL_NAMES = [
    "analyze_functions",
    "analyze_error_handling",
    "analyze_package_exports",
    "analyze_duplicate_functions",
    "analyze_module_refactor_candidates",
    "analyze_module_imports",
    "analyze_dependency_patterns",
    "analyze_module_dependencies",
    "analyze_function_registry",
    "analyze_documentation_sync",
    "analyze_unused_imports",
    "generate_unused_imports_report",
]

# Tier 3: Full audit (>10s acceptable).
TIER3_TOOL_NAMES = [
    "run_test_coverage",
    "generate_dev_tools_coverage",
    "analyze_test_markers",
    "generate_test_coverage_report",
    "analyze_backup_health",
    "analyze_legacy_references",
    "generate_legacy_reference_report",
    "analyze_ruff",
    "analyze_pyright",
]


def get_expected_tools_for_tier(tier: int) -> list[str]:
    """Return expected tool names for a given audit tier (1, 2, or 3)."""
    if tier <= 1:
        return list(TIER1_TOOL_NAMES)
    tier1_no_quick = [t for t in TIER1_TOOL_NAMES if t != "quick_status"]
    if tier == 2:
        return tier1_no_quick + list(TIER2_TOOL_NAMES)
    return tier1_no_quick + list(TIER2_TOOL_NAMES) + list(TIER3_TOOL_NAMES)


# -----------------------------------------------------------------------------
# Runnables: resolve (service, tool_name) -> callable that returns result
# -----------------------------------------------------------------------------


def _get_runnable(service: Any, tool_name: str) -> Callable[[], Any]:
    """Return a no-arg callable that runs the tool on the given service."""
    if tool_name == "analyze_documentation":
        include_overlap = getattr(service, "_include_overlap", False)
        return lambda: service.run_analyze_documentation(include_overlap=include_overlap)
    if tool_name == "analyze_ai_work":
        return service.run_validate
    if tool_name == "quick_status":
        return lambda: service.run_script("quick_status", "json")
    if tool_name == "analyze_duplicate_functions":
        return lambda: service._run_analyze_duplicate_functions_for_audit()
    if tool_name == "analyze_test_markers":
        return lambda: service.run_test_markers("check")
    if tool_name == "analyze_backup_health":
        return lambda: service.run_backup_health_check(run_drill=True)
    if tool_name == "run_test_coverage":
        return service.run_coverage_regeneration
    if tool_name == "generate_dev_tools_coverage":
        return service.run_dev_tools_coverage
    # Default: service.run_<tool_name> (e.g. run_analyze_functions)
    method_name = "run_" + tool_name
    method = getattr(service, method_name, None)
    if method is None:
        raise AttributeError(f"Service has no method {method_name!r} for tool {tool_name!r}")
    return method


def get_tier_runnables(service: Any, tier: int, include_quick_status: bool = True) -> list[tuple[str, Callable[[], Any]]]:
    """
    Return a flat list of (tool_name, runnable) for the given tier.
    Used by measure_tool_timings.py.
    """
    if tier == 1:
        names = list(TIER1_TOOL_NAMES)
        if not include_quick_status:
            names = [n for n in names if n != "quick_status"]
    elif tier == 2:
        names = list(TIER2_TOOL_NAMES)
    elif tier == 3:
        names = list(TIER3_TOOL_NAMES)
    else:
        raise ValueError(f"tier must be 1, 2, or 3; got {tier!r}")
    return [(name, _get_runnable(service, name)) for name in names]


# -----------------------------------------------------------------------------
# Grouped structure for audit_orchestration (Tier 1: core, independent, dependent)
# -----------------------------------------------------------------------------


def get_tier1_groups(service: Any) -> tuple[list[tuple[str, Any]], list[tuple[str, Any]], list[list[tuple[str, Any]]]]:
    """Return (core_tools, independent_tools, dependent_groups) for Tier 1."""
    core_names = ["analyze_system_signals"]
    independent_names = ["analyze_documentation", "analyze_config", "analyze_ai_work"]
    dependent_group_names = [
        ["analyze_function_patterns"],
        ["decision_support"],
    ]
    core_tools = [(n, _get_runnable(service, n)) for n in core_names]
    independent_tools = [(n, _get_runnable(service, n)) for n in independent_names]
    dependent_groups = [[(n, _get_runnable(service, n)) for n in group] for group in dependent_group_names]
    return core_tools, independent_tools, dependent_groups


def get_tier2_groups(service: Any) -> tuple[list[tuple[str, Any]], list[list[tuple[str, Any]]]]:
    """Return (independent_tools, dependent_groups) for Tier 2."""
    independent_names = [
        "analyze_functions",
        "analyze_error_handling",
        "analyze_package_exports",
        "analyze_duplicate_functions",
        "analyze_module_refactor_candidates",
    ]
    dependent_group_names = [
        ["analyze_module_imports", "analyze_dependency_patterns", "analyze_module_dependencies"],
        ["analyze_function_registry"],
        ["analyze_documentation_sync"],
        ["analyze_unused_imports", "generate_unused_imports_report"],
    ]
    independent_tools = [(n, _get_runnable(service, n)) for n in independent_names]
    dependent_groups = [[(n, _get_runnable(service, n)) for n in group] for group in dependent_group_names]
    return independent_tools, dependent_groups


def get_tier3_groups(
    service: Any,
) -> tuple[list[tuple[str, Any]], list[tuple[str, Any]], list[tuple[str, Any]], list[tuple[str, Any]], list[tuple[str, Any]]]:
    """Return (coverage_main, coverage_dev_tools, coverage_dependent, legacy_group, static_analysis_group) for Tier 3."""
    coverage_main = [("run_test_coverage", _get_runnable(service, "run_test_coverage"))]
    coverage_dev_tools = [("generate_dev_tools_coverage", _get_runnable(service, "generate_dev_tools_coverage"))]
    coverage_dependent = [
        ("analyze_test_markers", _get_runnable(service, "analyze_test_markers")),
        ("generate_test_coverage_report", _get_runnable(service, "generate_test_coverage_report")),
        ("analyze_backup_health", _get_runnable(service, "analyze_backup_health")),
    ]
    legacy_group = [
        ("analyze_legacy_references", _get_runnable(service, "analyze_legacy_references")),
        ("generate_legacy_reference_report", _get_runnable(service, "generate_legacy_reference_report")),
    ]
    static_analysis_group = [
        ("analyze_ruff", _get_runnable(service, "analyze_ruff")),
        ("analyze_pyright", _get_runnable(service, "analyze_pyright")),
    ]
    return coverage_main, coverage_dev_tools, coverage_dependent, legacy_group, static_analysis_group
