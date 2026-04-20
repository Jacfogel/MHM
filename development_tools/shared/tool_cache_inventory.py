# TOOL_TIER: core

"""Inventory of caching strategies for audit tools (V5 §3.19).

Checked-in JSON: ``development_tools/config/tool_cache_inventory.json``.
"""

from __future__ import annotations

from development_tools.shared.audit_tiers import get_expected_tools_for_tier
from development_tools.shared.tool_metadata import CACHE_AWARE_TOOLS, get_script_registry


def _tool_domain_from_registry(script_registry: dict[str, str], tool_name: str) -> str:
    rel = script_registry.get(tool_name, "").replace("\\", "/").strip()
    parts = rel.split("/") if rel else []
    return parts[0] if len(parts) >= 2 else "shared"


def _tier2_and_tier3_tool_names() -> frozenset[str]:
    """Tools that first appear in Tier 2 or Tier 3 (full audit), excluding Tier 1-only tools."""
    tier1_no_quick = {
        t for t in get_expected_tools_for_tier(1) if t != "quick_status"
    }
    full = set(get_expected_tools_for_tier(3, dev_tools_only=False))
    return frozenset(full - tier1_no_quick)


def _cache_entry(tool_name: str, domain: str) -> dict[str, str]:
    static_check_tools = {"analyze_ruff", "analyze_pyright", "analyze_bandit"}
    if tool_name in static_check_tools:
        return {
            "tool": tool_name,
            "strategy": "mtime_json_cache",
            "implementation": "development_tools/shared/service/tool_wrappers.py _try_static_check_cache / _save_static_check_cache",
            "artifact_glob": f"development_tools/**/jsons/scopes/*/{domain}/*{tool_name.split('_', 1)[1]}*.json",
            "invalidation": (
                "Source signature: analyzed *.py + config files in "
                "development_tools.shared.cache_dependency_paths.STATIC_CHECK_CONFIG_RELATIVE_PATHS "
                "(see tool_wrappers._compute_source_signature)"
            ),
        }
    if tool_name == "analyze_pip_audit":
        return {
            "tool": tool_name,
            "strategy": "requirements_hash_json_cache",
            "implementation": "development_tools/shared/service/tool_wrappers.py _try_pip_audit_cache / _save_pip_audit_cache",
            "artifact_glob": "development_tools/**/jsons/scopes/*/static_checks/.analyze_pip_audit_requirements_cache.json",
            "invalidation": (
                "development_tools.shared.cache_dependency_paths.requirements_lock_signature "
                "(PIP_AUDIT_DEPENDENCY_RELATIVE_PATHS; see tool_wrappers pip-audit cache)"
            ),
        }
    if tool_name in {"run_test_coverage", "generate_dev_tools_coverage"}:
        file_name = "coverage.json" if tool_name == "run_test_coverage" else "coverage_dev_tools.json"
        return {
            "tool": tool_name,
            "strategy": "domain_test_file_cache_merge",
            "implementation": "development_tools/tests/run_test_coverage.py (coverage metadata)",
            "artifact_glob": f"development_tools/tests/jsons/{file_name}",
            "invalidation": "Per test-file cache keys; see coverage JSON _metadata",
        }
    if tool_name == "analyze_unused_imports":
        return {
            "tool": tool_name,
            "strategy": "ruff_batch_and_optional_tool_json",
            "implementation": "imports analyzer + optional cache stats in JSON details",
            "artifact_glob": "development_tools/**/jsons/scopes/*/imports/*.json",
            "invalidation": "Ruff batch paths keyed by Path.resolve(); tool JSON mtime",
        }
    if tool_name == "analyze_legacy_references":
        return {
            "tool": tool_name,
            "strategy": "marker_scan_cache",
            "implementation": "details.cache in tool JSON; orchestration CACHE_AWARE_TOOLS",
            "artifact_glob": "development_tools/**/jsons/scopes/*/legacy/*.json",
            "invalidation": "Content hash / scan metadata in tool payload",
        }
    if tool_name == "analyze_documentation_sync":
        return {
            "tool": tool_name,
            "strategy": "paired_doc_cache",
            "implementation": "orchestration cache metadata; doc sync payloads",
            "artifact_glob": "development_tools/**/jsons/scopes/*/docs/*.json",
            "invalidation": "Doc file mtimes and paired-doc registry",
        }
    if tool_name == "analyze_test_markers":
        return {
            "tool": tool_name,
            "strategy": "reads_coverage_artifacts",
            "implementation": "development_tools/tests/analyze_test_markers.py (consumes coverage JSON)",
            "artifact_glob": "development_tools/**/jsons/scopes/*/tests/*test_markers*.json",
            "invalidation": "Re-run when coverage JSON or marker config changes",
        }
    if tool_name == "generate_test_coverage_report":
        return {
            "tool": tool_name,
            "strategy": "downstream_of_coverage_json",
            "implementation": "development_tools/tests/generate_test_coverage_report.py",
            "artifact_glob": "development_tools/tests/jsons/coverage.json; development_docs/TEST_COVERAGE_REPORT.md",
            "invalidation": "Regenerates when upstream coverage data is refreshed",
        }
    if tool_name == "generate_unused_imports_report":
        return {
            "tool": tool_name,
            "strategy": "downstream_of_analyze_unused_imports",
            "implementation": "development_tools/imports/generate_unused_imports_report.py",
            "artifact_glob": "development_tools/**/jsons/scopes/*/imports/*.json; development_docs/UNUSED_IMPORTS_REPORT.md",
            "invalidation": "Regenerates from analyze_unused_imports JSON",
        }
    if tool_name == "generate_legacy_reference_report":
        return {
            "tool": tool_name,
            "strategy": "downstream_of_analyze_legacy_references",
            "implementation": "development_tools/legacy/generate_legacy_reference_report.py",
            "artifact_glob": "development_tools/**/jsons/scopes/*/legacy/*.json; development_docs/LEGACY_REFERENCE_REPORT.md",
            "invalidation": "Regenerates from analyze_legacy_references JSON",
        }
    if tool_name == "verify_process_cleanup":
        return {
            "tool": tool_name,
            "strategy": "no_persistent_tool_json_cache",
            "implementation": "development_tools/tests/verify_process_cleanup.py (process probe)",
            "artifact_glob": "development_tools/**/jsons/scopes/*/verify_process_cleanup*.json",
            "invalidation": "N/A — advisory probe; JSON is per-run output only",
        }
    if tool_name == "analyze_backup_health":
        return {
            "tool": tool_name,
            "strategy": "no_persistent_tool_json_cache",
            "implementation": "development_tools/shared/service/commands.py (backup health command)",
            "artifact_glob": "development_tools/reports/jsons/backup_health_report.json; development_tools/**/jsons/scopes/*/reports/*.json",
            "invalidation": "N/A — live backup checks; JSON overwrites each run",
        }
    return {
        "tool": tool_name,
        "strategy": "per_run_json_overwrite",
        "implementation": "development_tools/shared/service/audit_orchestration.py + tool script",
        "artifact_glob": f"development_tools/**/jsons/scopes/*/{domain}/*.json",
        "invalidation": "Full re-analysis each audit unless covered by a specialized cache above",
    }


def build_tool_cache_inventory() -> dict:
    """Return serializable cache strategy rows for CACHE_AWARE_TOOLS and all Tier 2/3 audit tools."""
    script_registry = get_script_registry()
    inventory_tools = sorted(frozenset(CACHE_AWARE_TOOLS) | _tier2_and_tier3_tool_names())
    entries = []
    for tool_name in inventory_tools:
        domain = _tool_domain_from_registry(script_registry, tool_name)
        entries.append(_cache_entry(tool_name, domain))
    return {
        "schema_version": 1,
        "description": "Cache strategies derived from tool_metadata.CACHE_AWARE_TOOLS; details from wrapper/orchestration semantics.",
        "entries": entries,
        "expansion_candidates": [
            {
                "tool": "analyze_pyright",
                "note": "Already mtime-cached; further invalidation tuning via config only.",
            },
            {
                "tool": "analyze_bandit",
                "note": "Already mtime-cached; Bandit targets exclude tests/ by default.",
            },
        ],
    }
