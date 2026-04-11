# TOOL_TIER: core

"""
Canonical definition of which tools run in each audit tier (1=quick, 2=standard, 3=full).

Used by measure_tool_timings.py and audit_orchestration.py so tier tool lists
are defined in one place and do not drift.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

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
    "analyze_dev_tools_import_boundaries",
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
# flaky_detector is manual/CLI-only: it spawns nested parallel pytest and must not run alongside
# run_test_coverage (resource contention, timeouts, empty capture). See flaky-detector command.
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
    "analyze_bandit",
    "analyze_pip_audit",
    "verify_process_cleanup",
]


def get_tier3_tool_names_full_repo() -> list[str]:
    """Tier 3 tools for a normal full audit (main/project coverage only; no dev-tools coverage subprocess)."""
    return [name for name in TIER3_TOOL_NAMES if name != "generate_dev_tools_coverage"]


def get_tier3_tool_names_dev_tools_only() -> list[str]:
    """Tier 3 tools for `audit --full --dev-tools-only` (dev-tools coverage only; no main TEST_COVERAGE_REPORT refresh)."""
    return [
        name
        for name in TIER3_TOOL_NAMES
        if name
        not in (
            "run_test_coverage",
            "generate_test_coverage_report",
            "generate_legacy_reference_report",
        )
    ]


def get_expected_tools_for_tier(tier: int, *, dev_tools_only: bool = False) -> list[str]:
    """Return expected tool names for a given audit tier (1, 2, or 3).

    When ``dev_tools_only`` is True, Tier 2/3 expectations omit markdown generators that
    write full-repo ``development_docs/*.md`` reports (V5 §7.19).
    """
    if tier <= 1:
        return list(TIER1_TOOL_NAMES)
    tier1_no_quick = [t for t in TIER1_TOOL_NAMES if t != "quick_status"]
    tier2_names = (
        [n for n in TIER2_TOOL_NAMES if n != "generate_unused_imports_report"]
        if dev_tools_only
        else list(TIER2_TOOL_NAMES)
    )
    if tier == 2:
        return tier1_no_quick + tier2_names
    tier3_names = (
        get_tier3_tool_names_dev_tools_only()
        if dev_tools_only
        else get_tier3_tool_names_full_repo()
    )
    return tier1_no_quick + tier2_names + tier3_names


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
    if tool_name == "verify_process_cleanup":
        return service.run_verify_process_cleanup
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
    independent_names = [
        "analyze_documentation",
        "analyze_config",
        "analyze_ai_work",
        "analyze_dev_tools_import_boundaries",
    ]
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
    dev_tools_only = bool(getattr(service, "dev_tools_only_mode", False))
    independent_names = [
        "analyze_functions",
        "analyze_error_handling",
        "analyze_package_exports",
        "analyze_duplicate_functions",
        "analyze_module_refactor_candidates",
    ]
    unused_imports_group = (
        ["analyze_unused_imports"]
        if dev_tools_only
        else ["analyze_unused_imports", "generate_unused_imports_report"]
    )
    if dev_tools_only:
        logger.info(
            "Skipping generate_unused_imports_report (dev-tools-only scope); "
            "development_docs/UNUSED_IMPORTS_REPORT.md left unchanged."
        )
    dependent_group_names = [
        ["analyze_module_imports", "analyze_dependency_patterns", "analyze_module_dependencies"],
        ["analyze_function_registry"],
        ["analyze_documentation_sync"],
        unused_imports_group,
    ]
    independent_tools = [(n, _get_runnable(service, n)) for n in independent_names]
    dependent_groups = [[(n, _get_runnable(service, n)) for n in group] for group in dependent_group_names]
    return independent_tools, dependent_groups


def get_tier3_groups(
    service: Any,
) -> tuple[list[tuple[str, Any]], list[tuple[str, Any]], list[tuple[str, Any]], list[tuple[str, Any]], list[tuple[str, Any]]]:
    """Return (coverage_main, coverage_dev_tools, coverage_dependent, legacy_group, static_analysis_group) for Tier 3.

    Coverage subprocesses are split by audit scope (V5 §1.9):
    - Full audit: main ``run_test_coverage`` only (no ``generate_dev_tools_coverage`` in the same pass).
    - ``--dev-tools-only``: ``generate_dev_tools_coverage`` only; ``generate_test_coverage_report`` is omitted
      because it consumes main-repo ``coverage.json``.
    """
    dev_tools_only = bool(getattr(service, "dev_tools_only_mode", False))
    if dev_tools_only:
        logger.info(
            "Skipping generate_test_coverage_report (dev-tools-only scope); "
            "development_docs/TEST_COVERAGE_REPORT.md left unchanged."
        )
        coverage_main = []
        coverage_dev_tools = [
            ("generate_dev_tools_coverage", _get_runnable(service, "generate_dev_tools_coverage")),
        ]
        coverage_dependent = [
            ("analyze_test_markers", _get_runnable(service, "analyze_test_markers")),
            ("analyze_backup_health", _get_runnable(service, "analyze_backup_health")),
        ]
    else:
        coverage_main = [("run_test_coverage", _get_runnable(service, "run_test_coverage"))]
        coverage_dev_tools = []
        coverage_dependent = [
            ("analyze_test_markers", _get_runnable(service, "analyze_test_markers")),
            ("generate_test_coverage_report", _get_runnable(service, "generate_test_coverage_report")),
            ("analyze_backup_health", _get_runnable(service, "analyze_backup_health")),
        ]
    if dev_tools_only:
        legacy_group = [
            ("analyze_legacy_references", _get_runnable(service, "analyze_legacy_references")),
        ]
        logger.info(
            "Skipping generate_legacy_reference_report (dev-tools-only scope); "
            "development_docs/LEGACY_REFERENCE_REPORT.md left unchanged."
        )
    else:
        legacy_group = [
            ("analyze_legacy_references", _get_runnable(service, "analyze_legacy_references")),
            ("generate_legacy_reference_report", _get_runnable(service, "generate_legacy_reference_report")),
        ]
    static_analysis_group = [
        ("analyze_ruff", _get_runnable(service, "analyze_ruff")),
        ("analyze_pyright", _get_runnable(service, "analyze_pyright")),
        ("analyze_bandit", _get_runnable(service, "analyze_bandit")),
        ("analyze_pip_audit", _get_runnable(service, "analyze_pip_audit")),
        ("verify_process_cleanup", _get_runnable(service, "verify_process_cleanup")),
    ]
    return coverage_main, coverage_dev_tools, coverage_dependent, legacy_group, static_analysis_group
