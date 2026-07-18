# TOOL_TIER: core

"""
Canonical definition of which tools run in each audit tier (1=quick, 2=standard, 3=full).

Used by measure_tool_timings.py and audit_orchestration.py so tier tool lists
are defined in one place and do not drift.

Flat ``TIER*_TOOL_NAMES`` are the membership source for reporting / expected-tools.
Orchestration group maps below must cover every flat name except documented
``TIER*_ORCHESTRATION_OMIT`` exclusions (validated at import time).
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, TypedDict

from development_tools.shared.logging import get_dev_tools_logger

logger = get_dev_tools_logger("development_tools")


class _Tier1GroupMap(TypedDict):
    core: list[str]
    independent: list[str]
    dependent: list[list[str]]


class _Tier2GroupMap(TypedDict):
    independent: list[str]
    dependent: list[list[str]]

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
    "analyze_unused_functions",
    "analyze_facade_shims",
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
# flaky_detector is manual/CLI-only: it spawns repeated pytest runs and must not run alongside
# run_test_suite (resource contention, timeouts, empty capture). See flaky-detector command.
TIER3_TOOL_NAMES = [
    "run_test_suite",
    "analyze_test_markers",
    "analyze_backup_health",
    "analyze_legacy_references",
    "generate_legacy_reference_report",
    "analyze_ruff",
    "analyze_pyright",
    "analyze_bandit",
    "analyze_pip_audit",
    "verify_process_cleanup",
]

# Tools listed in flat membership but not scheduled by get_tier*_groups().
# Tier 1: quick_status is only for explicit Tier 1 / timings include_quick_status runs.
# Tier 3: marker analysis is owned by the explicit ``coverage`` command (see get_tier3_groups docstring).
TIER1_ORCHESTRATION_OMIT: frozenset[str] = frozenset({"quick_status"})
TIER2_ORCHESTRATION_OMIT: frozenset[str] = frozenset()
TIER3_ORCHESTRATION_OMIT: frozenset[str] = frozenset({"analyze_test_markers"})

# Orchestration group maps (execution order). Names must be in the matching TIER*_TOOL_NAMES.
TIER1_GROUP_MAP: _Tier1GroupMap = {
    "core": ["analyze_system_signals"],
    "independent": [
        "analyze_documentation",
        "analyze_config",
        "analyze_ai_work",
        "analyze_dev_tools_import_boundaries",
    ],
    "dependent": [
        ["analyze_function_patterns"],
        ["decision_support"],
    ],
}

TIER2_GROUP_MAP: _Tier2GroupMap = {
    "independent": [
        "analyze_functions",
        "analyze_error_handling",
        "analyze_package_exports",
        "analyze_duplicate_functions",
        "analyze_unused_functions",
        "analyze_facade_shims",
        "analyze_module_refactor_candidates",
    ],
    "dependent": [
        ["analyze_module_imports", "analyze_dependency_patterns", "analyze_module_dependencies"],
        ["analyze_function_registry"],
        ["analyze_documentation_sync"],
        # Last dependent group is rebuilt in get_tier2_groups for unused-imports report scoping.
        ["analyze_unused_imports", "generate_unused_imports_report"],
    ],
}

TIER3_GROUP_MAP: dict[str, list[str]] = {
    "test_suite": ["run_test_suite", "analyze_backup_health"],
    "legacy": ["analyze_legacy_references", "generate_legacy_reference_report"],
    "static_analysis": [
        "analyze_ruff",
        "analyze_pyright",
        "analyze_bandit",
        "analyze_pip_audit",
    ],
    "post_test": ["verify_process_cleanup"],
}


def _flatten_group_values(values: Iterable[Any]) -> list[str]:
    """Flatten nested group-map values (name lists and lists-of-name-lists)."""
    flat: list[str] = []

    def _walk(node: Any) -> None:
        if isinstance(node, (list, tuple)):
            for child in node:
                _walk(child)
            return
        flat.append(str(node))

    for item in values:
        _walk(item)
    return flat


def _validate_tier_group_coverage(
    tier_label: str,
    flat_names: Sequence[str],
    group_map: Mapping[str, Any],
    omit: frozenset[str],
) -> None:
    """Fail fast if orchestration maps drift from flat tier membership."""
    flat_set = set(flat_names)
    unknown_omit = sorted(omit - flat_set)
    if unknown_omit:
        raise ValueError(
            f"{tier_label} orchestration omit not in flat list: {unknown_omit}"
        )
    grouped = set(_flatten_group_values(group_map.values()))
    unknown_grouped = sorted(grouped - flat_set)
    if unknown_grouped:
        raise ValueError(
            f"{tier_label} group map has names not in flat list: {unknown_grouped}"
        )
    missing = sorted(flat_set - grouped - omit)
    if missing:
        raise ValueError(
            f"{tier_label} flat names missing from groups and omit set: {missing}"
        )
    overlap = sorted(grouped & omit)
    if overlap:
        raise ValueError(
            f"{tier_label} names appear in both groups and omit set: {overlap}"
        )


_validate_tier_group_coverage("Tier1", TIER1_TOOL_NAMES, TIER1_GROUP_MAP, TIER1_ORCHESTRATION_OMIT)
_validate_tier_group_coverage("Tier2", TIER2_TOOL_NAMES, TIER2_GROUP_MAP, TIER2_ORCHESTRATION_OMIT)
_validate_tier_group_coverage("Tier3", TIER3_TOOL_NAMES, TIER3_GROUP_MAP, TIER3_ORCHESTRATION_OMIT)


def get_tier3_tool_names_full_repo() -> list[str]:
    """Tier 3 tools for a normal full audit."""
    return list(TIER3_TOOL_NAMES)


def get_tier3_tool_names_dev_tools_only() -> list[str]:
    """Tier 3 tools for `audit --full --dev-tools-only`."""
    return [
        name
        for name in TIER3_TOOL_NAMES
        if name
        not in (
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
    if tool_name == "run_test_suite":
        return service.run_test_suite
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


def _names_to_runnables(service: Any, names: Sequence[str]) -> list[tuple[str, Any]]:
    return [(n, _get_runnable(service, n)) for n in names]


# -----------------------------------------------------------------------------
# Grouped structure for audit_orchestration (derived from TIER*_GROUP_MAP)
# -----------------------------------------------------------------------------


def get_tier1_groups(service: Any) -> tuple[list[tuple[str, Any]], list[tuple[str, Any]], list[list[tuple[str, Any]]]]:
    """Return (core_tools, independent_tools, dependent_groups) for Tier 1."""
    core_names = list(TIER1_GROUP_MAP["core"])
    independent_names = list(TIER1_GROUP_MAP["independent"])
    dependent_group_names = list(TIER1_GROUP_MAP["dependent"])
    core_tools = _names_to_runnables(service, core_names)
    independent_tools = _names_to_runnables(service, independent_names)
    dependent_groups = [_names_to_runnables(service, group) for group in dependent_group_names]
    return core_tools, independent_tools, dependent_groups


def get_tier2_groups(service: Any) -> tuple[list[tuple[str, Any]], list[list[tuple[str, Any]]]]:
    """Return (independent_tools, dependent_groups) for Tier 2."""
    dev_tools_only = bool(getattr(service, "dev_tools_only_mode", False))
    independent_names = list(TIER2_GROUP_MAP["independent"])
    dependent_group_names = [list(group) for group in TIER2_GROUP_MAP["dependent"]]
    # Rebuild unused-imports dependent group for scope (last group in the map).
    unused_imports_group = (
        ["analyze_unused_imports"]
        if dev_tools_only
        else ["analyze_unused_imports", "generate_unused_imports_report"]
    )
    if dependent_group_names:
        dependent_group_names[-1] = unused_imports_group
    if dev_tools_only:
        logger.info(
            "Skipping generate_unused_imports_report (dev-tools-only scope); "
            "development_docs/UNUSED_IMPORTS_REPORT.md left unchanged."
        )
    independent_tools = _names_to_runnables(service, independent_names)
    dependent_groups = [_names_to_runnables(service, group) for group in dependent_group_names]
    return independent_tools, dependent_groups


def get_tier3_groups(
    service: Any,
) -> tuple[
    list[tuple[str, Any]],
    list[tuple[str, Any]],
    list[tuple[str, Any]],
    list[tuple[str, Any]],
]:
    """Return Tier 3 tool groups for orchestration.

    Returns ``(test_suite_group, legacy_group, static_analysis_group, post_test_group)``.

    The test-suite group runs pytest without coverage. ``verify_process_cleanup`` runs in
    ``post_test_group`` after parallel work completes so orphan detection runs when workers
    may exist and does not contend with pytest subprocess startup (Windows SIGINT noise).

    Coverage regeneration, marker analysis, and coverage report generation are reserved for
    the explicit ``coverage`` command (``analyze_test_markers`` is in
    ``TIER3_ORCHESTRATION_OMIT``).
    """
    dev_tools_only = bool(getattr(service, "dev_tools_only_mode", False))
    test_suite_group = _names_to_runnables(service, TIER3_GROUP_MAP["test_suite"])
    legacy_names = list(TIER3_GROUP_MAP["legacy"])
    if dev_tools_only:
        legacy_names = [n for n in legacy_names if n != "generate_legacy_reference_report"]
        logger.info(
            "Skipping generate_legacy_reference_report (dev-tools-only scope); "
            "development_docs/LEGACY_REFERENCE_REPORT.md left unchanged."
        )
    legacy_group = _names_to_runnables(service, legacy_names)
    static_analysis_group = _names_to_runnables(service, TIER3_GROUP_MAP["static_analysis"])
    post_test_group = _names_to_runnables(service, TIER3_GROUP_MAP["post_test"])
    return test_suite_group, legacy_group, static_analysis_group, post_test_group
