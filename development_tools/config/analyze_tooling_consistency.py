#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Tooling consistency analyzer for development_tools.

Checks:
1. CLI flag inventory and alias semantics across runner + CLI interface.
2. Scanner exclusion consistency for tool scripts that discover source files.
"""

from __future__ import annotations

import argparse
import inspect
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Add project root to path for absolute imports when run as a script.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.logger import get_component_logger
from development_tools.shared.cli_interface import COMMAND_REGISTRY
from development_tools.shared.standard_exclusions import should_exclude_file

logger = get_component_logger("development_tools")


FLAG_PATTERN = re.compile(r"""['"](--[a-z0-9][a-z0-9-]*)['"]""", re.IGNORECASE)
GLOB_DISCOVERY_PATTERN = re.compile(
    r"""\.(?:rglob|glob)\(\s*['"]\*\.(?:py|md)['"]\s*\)""",
    re.IGNORECASE,
)
OS_WALK_PATTERN = re.compile(r"""\bos\.walk\(""")


def _extract_flags_from_text(text: str) -> List[str]:
    return sorted(set(FLAG_PATTERN.findall(text)))


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _build_command_flag_inventory() -> Dict[str, List[str]]:
    inventory: Dict[str, List[str]] = {}
    for command_name, registration in COMMAND_REGISTRY.items():
        try:
            source = inspect.getsource(registration.handler)
        except (OSError, TypeError):
            source = ""
        inventory[command_name] = _extract_flags_from_text(source)
    return inventory


def _build_global_flag_inventory(project_root: Path) -> List[str]:
    runner_path = project_root / "development_tools" / "run_development_tools.py"
    if not runner_path.exists():
        return []
    return _extract_flags_from_text(_load_text(runner_path))


def _build_standalone_argparse_inventory(project_root: Path) -> Dict[str, List[str]]:
    tools_root = project_root / "development_tools"
    inventory: Dict[str, List[str]] = {}
    for py_file in sorted(tools_root.rglob("*.py")):
        rel = py_file.relative_to(project_root).as_posix()
        if rel.endswith("__init__.py") or "/jsons/" in rel or "/archive/" in rel:
            continue
        text = _load_text(py_file)
        if "argparse.ArgumentParser" not in text or "add_argument(" not in text:
            continue
        inventory[rel] = _extract_flags_from_text(text)
    return inventory


def _check_alias_rules(
    command_flags: Dict[str, List[str]], global_flags: List[str], project_root: Path
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    issues: List[Dict[str, Any]] = []
    checks: List[Dict[str, Any]] = []
    runner_path = project_root / "development_tools" / "run_development_tools.py"
    runner_text = _load_text(runner_path) if runner_path.exists() else ""

    alias_rules = [
        {
            "id": "audit_full_alias_command",
            "description": "`audit --full` must have `full-audit` command alias.",
            "ok": "audit" in command_flags
            and "full-audit" in command_flags
            and "--full" in command_flags.get("audit", []),
            "target": "development_tools/shared/cli_interface.py",
        },
        {
            "id": "cleanup_full_all_alias",
            "description": "`cleanup` must support both `--full` and `--all`.",
            "ok": "--full" in command_flags.get("cleanup", [])
            and "--all" in command_flags.get("cleanup", []),
            "target": "development_tools/shared/cli_interface.py",
        },
        {
            "id": "doc_fix_full_all_alias",
            "description": "`doc-fix` must support both `--all` and `--full`.",
            "ok": "--all" in command_flags.get("doc-fix", [])
            and "--full" in command_flags.get("doc-fix", []),
            "target": "development_tools/shared/cli_interface.py",
        },
        {
            "id": "runner_cache_clear_alias",
            "description": "Runner must support both `--clear-cache` and `--cache-clear`.",
            "ok": "--clear-cache" in global_flags and "--cache-clear" in global_flags,
            "target": "development_tools/run_development_tools.py",
        },
        {
            "id": "full_audit_delegation",
            "description": "`full-audit` should delegate to `_audit_command(... --full ...)`.",
            "ok": "_full_audit_command" in runner_text
            or '"--full", *argv' in _load_text(
                project_root / "development_tools" / "shared" / "cli_interface.py"
            ),
            "target": "development_tools/shared/cli_interface.py",
        },
    ]

    for rule in alias_rules:
        passed = bool(rule["ok"])
        checks.append(
            {
                "id": rule["id"],
                "description": rule["description"],
                "passed": passed,
                "target": rule["target"],
            }
        )
        if not passed:
            issues.append(
                {
                    "type": "alias_rule",
                    "id": rule["id"],
                    "file": rule["target"],
                    "message": f"Alias rule failed: {rule['description']}",
                }
            )
    return checks, issues


def _is_scanner_candidate(path: Path, text: str, project_root: Path) -> bool:
    rel = path.relative_to(project_root).as_posix()
    if rel.endswith("__init__.py"):
        return False
    # Operational cleanup tools may traverse directories but are not analyzers.
    if rel == "development_tools/shared/fix_project_cleanup.py":
        return False
    if rel.startswith("development_tools/reports/") and "analyze_" not in rel:
        return False
    if GLOB_DISCOVERY_PATTERN.search(text):
        return True
    if OS_WALK_PATTERN.search(text):
        return True
    if "iter_python_sources(" in text:
        return True
    return False


def _check_exclusion_consistency(
    project_root: Path,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    tools_root = project_root / "development_tools"
    scanner_candidates: List[str] = []
    compliant_files: List[str] = []
    non_compliant: List[Dict[str, Any]] = []

    for py_file in sorted(tools_root.rglob("*.py")):
        rel = py_file.relative_to(project_root).as_posix()
        if should_exclude_file(rel, tool_type="analysis", context="development"):
            continue
        text = _load_text(py_file)
        if not _is_scanner_candidate(py_file, text, project_root):
            continue
        scanner_candidates.append(rel)
        uses_exclusion = (
            "should_exclude_file(" in text
            or "standard_exclusions.should_exclude_file(" in text
            or "iter_python_sources(" in text
        )
        if uses_exclusion:
            compliant_files.append(rel)
            continue
        non_compliant.append(
            {
                "type": "scanner_exclusion",
                "id": "missing_should_exclude_file",
                "file": rel,
                "message": "Scanner-like file discovery detected without should_exclude_file filtering.",
            }
        )

    summary = {
        "scanner_candidates": len(scanner_candidates),
        "compliant_scanners": len(compliant_files),
        "non_compliant_scanners": len(non_compliant),
        "non_compliant_files": [entry["file"] for entry in non_compliant],
    }
    return summary, non_compliant


def analyze_tooling_consistency(project_root: Path) -> Dict[str, Any]:
    command_flags = _build_command_flag_inventory()
    global_flags = _build_global_flag_inventory(project_root)
    standalone_flags = _build_standalone_argparse_inventory(project_root)
    alias_checks, alias_issues = _check_alias_rules(
        command_flags, global_flags, project_root
    )
    exclusion_summary, exclusion_issues = _check_exclusion_consistency(project_root)

    all_issues = alias_issues + exclusion_issues
    files_affected: Set[str] = {
        issue["file"] for issue in all_issues if issue.get("file")
    }
    status = "PASS" if not all_issues else "FAIL"

    return {
        "summary": {
            "total_issues": len(all_issues),
            "files_affected": len(files_affected),
            "status": status,
        },
        "details": {
            "cli_inventory": {
                "commands": command_flags,
                "global_runner_flags": global_flags,
                "standalone_scripts": standalone_flags,
                "total_commands": len(command_flags),
                "standalone_script_count": len(standalone_flags),
            },
            "alias_checks": alias_checks,
            "scanner_exclusion_checks": exclusion_summary,
            "issues": all_issues,
        },
    }


def _render_human(result: Dict[str, Any]) -> str:
    summary = result.get("summary", {})
    details = result.get("details", {})
    scanner = details.get("scanner_exclusion_checks", {})
    lines = [
        "Tooling Consistency Check",
        "-------------------------",
        f"Status: {summary.get('status', 'UNKNOWN')}",
        f"Total issues: {summary.get('total_issues', 0)}",
        f"Files affected: {summary.get('files_affected', 0)}",
        "",
        "Alias checks:",
    ]
    for check in details.get("alias_checks", []):
        state = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- {state}: {check.get('id')} ({check.get('target')})")
    lines.extend(
        [
            "",
            "Scanner exclusion checks:",
            f"- Candidates: {scanner.get('scanner_candidates', 0)}",
            f"- Compliant: {scanner.get('compliant_scanners', 0)}",
            f"- Non-compliant: {scanner.get('non_compliant_scanners', 0)}",
        ]
    )
    issues = details.get("issues", [])
    if issues:
        lines.append("")
        lines.append("Findings:")
        for issue in issues:
            lines.append(f"- {issue.get('id')}: {issue.get('file')}")
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze CLI alias and scanner exclusion consistency."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Project root path (default: current directory).",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when findings exist.",
    )
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    try:
        result = analyze_tooling_consistency(root)
    except Exception as exc:
        logger.error(f"tooling consistency analysis failed: {exc}", exc_info=True)
        if args.json:
            print(
                json.dumps(
                    {
                        "summary": {
                            "total_issues": 1,
                            "files_affected": 0,
                            "status": "FAIL",
                        },
                        "details": {
                            "issues": [
                                {
                                    "type": "runtime_error",
                                    "id": "analysis_failure",
                                    "file": "",
                                    "message": str(exc),
                                }
                            ]
                        },
                    },
                    indent=2,
                )
            )
        else:
            print(f"Tooling consistency analysis failed: {exc}")
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(_render_human(result))

    total_issues = int(result.get("summary", {}).get("total_issues", 0) or 0)
    if args.strict and total_issues > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
