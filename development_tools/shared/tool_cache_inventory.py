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


def _cache_entry(tool_name: str, domain: str) -> dict[str, str]:
    static_check_tools = {"analyze_ruff", "analyze_pyright", "analyze_bandit"}
    if tool_name in static_check_tools:
        return {
            "tool": tool_name,
            "strategy": "mtime_json_cache",
            "implementation": "development_tools/shared/service/tool_wrappers.py _try_static_check_cache / _save_static_check_cache",
            "artifact_glob": f"development_tools/**/jsons/scopes/*/{domain}/*{tool_name.split('_', 1)[1]}*.json",
            "invalidation": "Static check JSON mtime vs source tree",
        }
    if tool_name == "analyze_pip_audit":
        return {
            "tool": tool_name,
            "strategy": "requirements_hash_json_cache",
            "implementation": "development_tools/shared/service/tool_wrappers.py _try_pip_audit_cache / _save_pip_audit_cache",
            "artifact_glob": "development_tools/**/jsons/scopes/*/static_checks/.analyze_pip_audit_requirements_cache.json",
            "invalidation": "SHA-256 of requirements.txt + pyproject.toml",
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
    return {
        "tool": tool_name,
        "strategy": "cache_metadata_observed",
        "implementation": "development_tools/shared/service/audit_orchestration.py cache metadata",
        "artifact_glob": f"development_tools/**/jsons/scopes/*/{domain}/*.json",
        "invalidation": "Tool-specific metadata in result payload",
    }


def build_tool_cache_inventory() -> dict:
    """Return serializable cache strategy rows derived from CACHE_AWARE_TOOLS."""
    script_registry = get_script_registry()
    tier3_static_checks = {
        name
        for name in get_expected_tools_for_tier(3, dev_tools_only=False)
        if _tool_domain_from_registry(script_registry, name) == "static_checks"
        and name.startswith("analyze_")
    }
    inventory_tools = sorted(set(CACHE_AWARE_TOOLS) | tier3_static_checks)
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
