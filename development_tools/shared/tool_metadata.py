# TOOL_TIER: core

"""
Central registry describing every AI development tool module.

This keeps the tier/trust metadata in one authoritative place so
the CLI help text, documentation, and enforcement scripts stay consistent.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal

Tier = Literal["core", "supporting", "experimental"]
TrustLevel = Literal["stable", "partial", "advisory", "experimental"]


@dataclass(frozen=True)
class ToolInfo:
    name: str
    path: str
    tier: Tier
    trust: TrustLevel
    description: str


_TOOLS: Dict[str, ToolInfo] = {
    "run_development_tools": ToolInfo(
        name="run_development_tools",
        path="development_tools/run_development_tools.py",
        tier="core",
        trust="stable",
        description="CLI entry point that dispatches every development tooling command.",
    ),
    "operations": ToolInfo(
        name="operations",
        path="development_tools/shared/operations.py",
        tier="core",
        trust="stable",
        description="Implements the heavy lifting for each runner command.",
    ),
    "config": ToolInfo(
        name="config",
        path="development_tools/config/config.py",
        tier="core",
        trust="stable",
        description="Shared configuration for tool suites and execution contexts.",
    ),
    "standard_exclusions": ToolInfo(
        name="standard_exclusions",
        path="development_tools/shared/standard_exclusions.py",
        tier="core",
        trust="stable",
        description="Canonical exclusion list used by every scanner.",
    ),
    "constants": ToolInfo(
        name="constants",
        path="development_tools/shared/constants.py",
        tier="core",
        trust="stable",
        description="Doc pairing metadata, directory maps, and shared constants.",
    ),
    "common": ToolInfo(
        name="common",
        path="development_tools/shared/common.py",
        tier="core",
        trust="stable",
        description="Shared file/io helpers used across tooling modules.",
    ),
    "analyze_documentation_sync": ToolInfo(
        name="analyze_documentation_sync",
        path="development_tools/docs/analyze_documentation_sync.py",
        tier="core",
        trust="stable",
        description="Validates human/AI doc pairing and detects drift.",
    ),
    "generate_function_registry": ToolInfo(
        name="generate_function_registry",
        path="development_tools/functions/generate_function_registry.py",
        tier="core",
        trust="stable",
        description="Builds the authoritative function registry via AST parsing.",
    ),
    "generate_module_dependencies": ToolInfo(
        name="generate_module_dependencies",
        path="development_tools/imports/generate_module_dependencies.py",
        tier="core",
        trust="stable",
        description="Calculates inter-module dependencies and enhancement zones.",
    ),
    "fix_legacy_references": ToolInfo(
        name="fix_legacy_references",
        path="development_tools/legacy/fix_legacy_references.py",
        tier="core",
        trust="stable",
        description="Scans and optionally removes LEGACY COMPATIBILITY markers.",
    ),
    "generate_test_coverage": ToolInfo(
        name="generate_test_coverage",
        path="development_tools/tests/generate_test_coverage.py",
        tier="core",
        trust="stable",
        description="Runs pytest coverage and manages coverage artifacts.",
    ),
    "analyze_error_handling": ToolInfo(
        name="analyze_error_handling",
        path="development_tools/error_handling/analyze_error_handling.py",
        tier="core",
        trust="stable",
        description="Audits decorator usage and error handling adherence.",
    ),
    "analyze_functions": ToolInfo(
        name="analyze_functions",
        path="development_tools/functions/analyze_functions.py",
        tier="core",
        trust="stable",
        description="AST discovery utility backing several other tools.",
    ),
    "analyze_documentation": ToolInfo(
        name="analyze_documentation",
        path="development_tools/docs/analyze_documentation.py",
        tier="supporting",
        trust="partial",
        description="Secondary doc analysis focused on corruption detection.",
    ),
    "analyze_function_registry": ToolInfo(
        name="analyze_function_registry",
        path="development_tools/functions/analyze_function_registry.py",
        tier="supporting",
        trust="partial",
        description="Validates generated function registry output.",
    ),
    "analyze_module_dependencies": ToolInfo(
        name="analyze_module_dependencies",
        path="development_tools/imports/analyze_module_dependencies.py",
        tier="supporting",
        trust="partial",
        description="Verifies generated dependency graphs for consistency.",
    ),
    "analyze_package_exports": ToolInfo(
        name="analyze_package_exports",
        path="development_tools/functions/analyze_package_exports.py",
        tier="supporting",
        trust="partial",
        description="Checks declared exports align with package contents.",
    ),
    "analyze_config": ToolInfo(
        name="analyze_config",
        path="development_tools/config/analyze_config.py",
        tier="supporting",
        trust="partial",
        description="Detects config drift and missing values across tools.",
    ),
    "analyze_ai_work": ToolInfo(
        name="analyze_ai_work",
        path="development_tools/ai_work/analyze_ai_work.py",
        tier="supporting",
        trust="partial",
        description="Lightweight structural validator, advisory only.",
    ),
    "analyze_unused_imports": ToolInfo(
        name="analyze_unused_imports",
        path="development_tools/imports/analyze_unused_imports.py",
        tier="supporting",
        trust="partial",
        description="AST-based unused import detector (can be noisy).",
    ),
    "quick_status": ToolInfo(
        name="quick_status",
        path="development_tools/reports/quick_status.py",
        tier="supporting",
        trust="advisory",
        description="Fast cached snapshot that depends on recent audits.",
    ),
    "system_signals": ToolInfo(
        name="system_signals",
        path="development_tools/reports/system_signals.py",
        tier="supporting",
        trust="advisory",
        description="Collects OS/process health signals for reports.",
    ),
    "decision_support": ToolInfo(
        name="decision_support",
        path="development_tools/reports/decision_support.py",
        tier="supporting",
        trust="advisory",
        description="Aggregates metrics into recommendations and priorities.",
    ),
    "file_rotation": ToolInfo(
        name="file_rotation",
        path="development_tools/shared/file_rotation.py",
        tier="supporting",
        trust="stable",
        description="Utility for timestamped file rotation/retention.",
    ),
    "tool_guide": ToolInfo(
        name="tool_guide",
        path="development_tools/shared/tool_guide.py",
        tier="supporting",
        trust="stable",
        description="Generates summarized help text for CLI commands.",
    ),
    "fix_version_sync": ToolInfo(
        name="fix_version_sync",
        path="development_tools/docs/fix_version_sync.py",
        tier="experimental",
        trust="experimental",
        description="Attempts cross-file version synchronization (fragile).",
    ),
    "generate_function_docstrings": ToolInfo(
        name="generate_function_docstrings",
        path="development_tools/functions/generate_function_docstrings.py",
        tier="experimental",
        trust="experimental",
        description="Auto-generates docstrings—high-risk, use with caution.",
    ),
    "generate_consolidated_report": ToolInfo(
        name="generate_consolidated_report",
        path="development_tools/reports/generate_consolidated_report.py",
        tier="supporting",
        trust="stable",
        description="Generates AI_STATUS.md, AI_PRIORITIES.md, and consolidated_report.txt.",
    ),
}


COMMAND_GROUPS = OrderedDict(
    {
        "Core Commands": {
            "tier": "core",
            "description": "Daily-safe commands that power the audit-first workflow.",
            "commands": [
                "audit",
                "quick-audit",
                "docs",
                "doc-sync",
                "config",
                "coverage",
                "legacy",
            ],
        },
        "Supporting Commands": {
            "tier": "supporting",
            "description": "Advisory utilities and helpers that depend on fresh audits.",
            "commands": [
                "status",
                "system-signals",
                "validate",
                "decision-support",
                "unused-imports",
                "workflow",
                "trees",
                "help",
            ],
        },
        "Experimental Commands": {
            "tier": "experimental",
            "description": "High-risk or prototype commands - run only with explicit approval.",
            "commands": [
                "version-sync",
            ],
        },
    }
)


def get_tool_metadata(name: str) -> ToolInfo:
    """Return metadata for a specific tool."""

    if name not in _TOOLS:
        raise KeyError(f"Unknown AI tool '{name}'")
    return _TOOLS[name]


def iter_tools() -> Iterable[ToolInfo]:
    """Yield metadata for every registered tool."""

    return _TOOLS.values()


def get_tools_by_tier(tier: Tier) -> List[ToolInfo]:
    """Return tools that match the requested tier."""

    return [info for info in _TOOLS.values() if info.tier == tier]


def get_command_groups():
    """Return ordered command group metadata used for help output."""

    return COMMAND_GROUPS


__all__ = [
    "ToolInfo",
    "get_tool_metadata",
    "get_tools_by_tier",
    "iter_tools",
    "COMMAND_GROUPS",
    "get_command_groups",
]

