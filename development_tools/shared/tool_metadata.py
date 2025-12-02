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
    "analyze_path_drift": ToolInfo(
        name="analyze_path_drift",
        path="development_tools/docs/analyze_path_drift.py",
        tier="core",
        trust="stable",
        description="Checks for path drift between code and documentation.",
    ),
    "analyze_missing_addresses": ToolInfo(
        name="analyze_missing_addresses",
        path="development_tools/docs/analyze_missing_addresses.py",
        tier="core",
        trust="stable",
        description="Checks for documentation files missing file addresses.",
    ),
    "analyze_ascii_compliance": ToolInfo(
        name="analyze_ascii_compliance",
        path="development_tools/docs/analyze_ascii_compliance.py",
        tier="core",
        trust="stable",
        description="Checks for non-ASCII characters in documentation files.",
    ),
    "analyze_heading_numbering": ToolInfo(
        name="analyze_heading_numbering",
        path="development_tools/docs/analyze_heading_numbering.py",
        tier="core",
        trust="stable",
        description="Checks that H2 and H3 headings are numbered consecutively.",
    ),
    "analyze_unconverted_links": ToolInfo(
        name="analyze_unconverted_links",
        path="development_tools/docs/analyze_unconverted_links.py",
        tier="core",
        trust="stable",
        description="Checks for file path references that should be converted to markdown links.",
    ),
    "generate_directory_tree": ToolInfo(
        name="generate_directory_tree",
        path="development_tools/docs/generate_directory_tree.py",
        tier="core",
        trust="stable",
        description="Generates a directory tree for documentation.",
    ),
    "fix_documentation": ToolInfo(
        name="fix_documentation",
        path="development_tools/docs/fix_documentation.py",
        tier="core",
        trust="stable",
        description="Dispatcher that orchestrates all documentation fix operations (calls specialized fixers).",
    ),
    "fix_documentation_addresses": ToolInfo(
        name="fix_documentation_addresses",
        path="development_tools/docs/fix_documentation_addresses.py",
        tier="core",
        trust="stable",
        description="Adds file addresses to documentation files that don't have them.",
    ),
    "fix_documentation_ascii": ToolInfo(
        name="fix_documentation_ascii",
        path="development_tools/docs/fix_documentation_ascii.py",
        tier="core",
        trust="stable",
        description="Fixes non-ASCII characters in documentation files.",
    ),
    "fix_documentation_headings": ToolInfo(
        name="fix_documentation_headings",
        path="development_tools/docs/fix_documentation_headings.py",
        tier="core",
        trust="stable",
        description="Numbers H2 and H3 headings in documentation files.",
    ),
    "fix_documentation_links": ToolInfo(
        name="fix_documentation_links",
        path="development_tools/docs/fix_documentation_links.py",
        tier="core",
        trust="stable",
        description="Converts file path references to markdown links in documentation.",
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
        description="Orchestrates module dependency analysis and generates dependency documentation.",
    ),
    "analyze_module_imports": ToolInfo(
        name="analyze_module_imports",
        path="development_tools/imports/analyze_module_imports.py",
        tier="core",
        trust="stable",
        description="Extracts and analyzes imports from Python files.",
    ),
    "analyze_dependency_patterns": ToolInfo(
        name="analyze_dependency_patterns",
        path="development_tools/imports/analyze_dependency_patterns.py",
        tier="core",
        trust="stable",
        description="Analyzes dependency patterns, circular dependencies, and risk areas.",
    ),
    "fix_legacy_references": ToolInfo(
        name="fix_legacy_references",
        path="development_tools/legacy/fix_legacy_references.py",
        tier="core",
        trust="stable",
        description="Fixes legacy references using analysis results from analyze_legacy_references.",
    ),
    "analyze_legacy_references": ToolInfo(
        name="analyze_legacy_references",
        path="development_tools/legacy/analyze_legacy_references.py",
        tier="core",
        trust="stable",
        description="Analyzes codebase for legacy references (scan, find, verify).",
    ),
    "generate_legacy_reference_report": ToolInfo(
        name="generate_legacy_reference_report",
        path="development_tools/legacy/generate_legacy_reference_report.py",
        tier="core",
        trust="stable",
        description="Generates markdown reports from legacy reference analysis results.",
    ),
    "generate_test_coverage": ToolInfo(
        name="generate_test_coverage",
        path="development_tools/tests/generate_test_coverage.py",
        tier="core",
        trust="stable",
        description="Runs pytest coverage and manages coverage artifacts.",
    ),
    "analyze_test_coverage": ToolInfo(
        name="analyze_test_coverage",
        path="development_tools/tests/analyze_test_coverage.py",
        tier="core",
        trust="stable",
        description="Analyzes test coverage data from pytest/coverage output.",
    ),
    "generate_test_coverage_reports": ToolInfo(
        name="generate_test_coverage_reports",
        path="development_tools/tests/generate_test_coverage_reports.py",
        tier="core",
        trust="stable",
        description="Generates coverage reports (JSON, HTML, summary) from analysis results.",
    ),
    "analyze_error_handling": ToolInfo(
        name="analyze_error_handling",
        path="development_tools/error_handling/analyze_error_handling.py",
        tier="core",
        trust="stable",
        description="Audits decorator usage and error handling adherence.",
    ),
    "generate_error_handling_report": ToolInfo(
        name="generate_error_handling_report",
        path="development_tools/error_handling/generate_error_handling_report.py",
        tier="supporting",
        trust="stable",
        description="Generates reports from error handling analysis results.",
    ),
    "generate_error_handling_recommendations": ToolInfo(
        name="generate_error_handling_recommendations",
        path="development_tools/error_handling/generate_error_handling_recommendations.py",
        tier="supporting",
        trust="stable",
        description="Generates recommendations for improving error handling based on analysis results.",
    ),
    "analyze_functions": ToolInfo(
        name="analyze_functions",
        path="development_tools/functions/analyze_functions.py",
        tier="core",
        trust="stable",
        description="AST discovery utility backing several other tools.",
    ),
    "analyze_function_patterns": ToolInfo(
        name="analyze_function_patterns",
        path="development_tools/functions/analyze_function_patterns.py",
        tier="core",
        trust="stable",
        description="Analyzes function patterns (handlers, managers, factories, etc.) for AI consumption.",
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
                "doc-fix",
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

