# TOOL_TIER: core
# TOOL_PORTABILITY: mhm-specific

"""
Central registry describing every AI development tool module.

This keeps the tier/portability/trust metadata in one authoritative place so
the CLI help text, documentation, and enforcement scripts stay consistent.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal

Tier = Literal["core", "supporting", "experimental"]
Portability = Literal["portable", "mhm-specific"]
TrustLevel = Literal["stable", "partial", "advisory", "experimental"]


@dataclass(frozen=True)
class ToolInfo:
    name: str
    path: str
    tier: Tier
    portability: Portability
    trust: TrustLevel
    description: str


_TOOLS: Dict[str, ToolInfo] = {
    "ai_tools_runner": ToolInfo(
        name="ai_tools_runner",
        path="development_tools/ai_tools_runner.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="CLI entry point that dispatches every AI tooling command.",
    ),
    "operations": ToolInfo(
        name="operations",
        path="development_tools/services/operations.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="Implements the heavy lifting for each runner command.",
    ),
    "config": ToolInfo(
        name="config",
        path="development_tools/config.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="Shared configuration for tool suites and execution contexts.",
    ),
    "standard_exclusions": ToolInfo(
        name="standard_exclusions",
        path="development_tools/services/standard_exclusions.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="Canonical exclusion list used by every scanner.",
    ),
    "constants": ToolInfo(
        name="constants",
        path="development_tools/services/constants.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="Doc pairing metadata, directory maps, and shared constants.",
    ),
    "common": ToolInfo(
        name="common",
        path="development_tools/services/common.py",
        tier="core",
        portability="portable",
        trust="stable",
        description="Shared file/io helpers used across tooling modules.",
    ),
    "documentation_sync_checker": ToolInfo(
        name="documentation_sync_checker",
        path="development_tools/documentation_sync_checker.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="Validates human/AI doc pairing and detects drift.",
    ),
    "generate_function_registry": ToolInfo(
        name="generate_function_registry",
        path="development_tools/generate_function_registry.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="Builds the authoritative function registry via AST parsing.",
    ),
    "generate_module_dependencies": ToolInfo(
        name="generate_module_dependencies",
        path="development_tools/generate_module_dependencies.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="Calculates inter-module dependencies and enhancement zones.",
    ),
    "legacy_reference_cleanup": ToolInfo(
        name="legacy_reference_cleanup",
        path="development_tools/legacy_reference_cleanup.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="Scans and optionally removes LEGACY COMPATIBILITY markers.",
    ),
    "regenerate_coverage_metrics": ToolInfo(
        name="regenerate_coverage_metrics",
        path="development_tools/regenerate_coverage_metrics.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="Runs pytest coverage and manages coverage artifacts.",
    ),
    "error_handling_coverage": ToolInfo(
        name="error_handling_coverage",
        path="development_tools/error_handling_coverage.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="Audits decorator usage and error handling adherence.",
    ),
    "function_discovery": ToolInfo(
        name="function_discovery",
        path="development_tools/function_discovery.py",
        tier="core",
        portability="mhm-specific",
        trust="stable",
        description="AST discovery utility backing several other tools.",
    ),
    "analyze_documentation": ToolInfo(
        name="analyze_documentation",
        path="development_tools/analyze_documentation.py",
        tier="supporting",
        portability="mhm-specific",
        trust="partial",
        description="Secondary doc analysis focused on corruption detection.",
    ),
    "audit_function_registry": ToolInfo(
        name="audit_function_registry",
        path="development_tools/audit_function_registry.py",
        tier="supporting",
        portability="mhm-specific",
        trust="partial",
        description="Validates generated function registry output.",
    ),
    "audit_module_dependencies": ToolInfo(
        name="audit_module_dependencies",
        path="development_tools/audit_module_dependencies.py",
        tier="supporting",
        portability="mhm-specific",
        trust="partial",
        description="Verifies generated dependency graphs for consistency.",
    ),
    "audit_package_exports": ToolInfo(
        name="audit_package_exports",
        path="development_tools/audit_package_exports.py",
        tier="supporting",
        portability="mhm-specific",
        trust="partial",
        description="Checks declared exports align with package contents.",
    ),
    "config_validator": ToolInfo(
        name="config_validator",
        path="development_tools/config_validator.py",
        tier="supporting",
        portability="mhm-specific",
        trust="partial",
        description="Detects config drift and missing values across tools.",
    ),
    "validate_ai_work": ToolInfo(
        name="validate_ai_work",
        path="development_tools/validate_ai_work.py",
        tier="supporting",
        portability="mhm-specific",
        trust="partial",
        description="Lightweight structural validator, advisory only.",
    ),
    "unused_imports_checker": ToolInfo(
        name="unused_imports_checker",
        path="development_tools/unused_imports_checker.py",
        tier="supporting",
        portability="mhm-specific",
        trust="partial",
        description="AST-based unused import detector (can be noisy).",
    ),
    "quick_status": ToolInfo(
        name="quick_status",
        path="development_tools/quick_status.py",
        tier="supporting",
        portability="mhm-specific",
        trust="advisory",
        description="Fast cached snapshot that depends on recent audits.",
    ),
    "system_signals": ToolInfo(
        name="system_signals",
        path="development_tools/system_signals.py",
        tier="supporting",
        portability="portable",
        trust="advisory",
        description="Collects OS/process health signals for reports.",
    ),
    "decision_support": ToolInfo(
        name="decision_support",
        path="development_tools/decision_support.py",
        tier="supporting",
        portability="mhm-specific",
        trust="advisory",
        description="Aggregates metrics into recommendations and priorities.",
    ),
    "file_rotation": ToolInfo(
        name="file_rotation",
        path="development_tools/file_rotation.py",
        tier="supporting",
        portability="portable",
        trust="stable",
        description="Utility for timestamped file rotation/retention.",
    ),
    "tool_guide": ToolInfo(
        name="tool_guide",
        path="development_tools/tool_guide.py",
        tier="supporting",
        portability="mhm-specific",
        trust="stable",
        description="Generates summarized help text for CLI commands.",
    ),
    "version_sync": ToolInfo(
        name="version_sync",
        path="development_tools/experimental/version_sync.py",
        tier="experimental",
        portability="mhm-specific",
        trust="experimental",
        description="Attempts cross-file version synchronization (fragile).",
    ),
    "auto_document_functions": ToolInfo(
        name="auto_document_functions",
        path="development_tools/experimental/auto_document_functions.py",
        tier="experimental",
        portability="mhm-specific",
        trust="experimental",
        description="Auto-generates docstrings—high-risk, use with caution.",
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

