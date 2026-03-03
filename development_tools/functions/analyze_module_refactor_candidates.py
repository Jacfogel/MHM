#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Identify high-complexity or very large modules as candidates for refactoring.

Scans Python modules (files) and flags those that exceed configurable thresholds
for lines of code, function/class count, or aggregate complexity, so they can
be considered for splitting into smaller, more focused modules.

**Complexity metric**: "Complexity" here means AST node count (same as
analyze_functions): for each function, the number of AST nodes in its subtree.
Total complexity is the sum of those counts over all functions in the file.
High/critical counts are functions with node count >= 100 or >= 200. This is
a rough proxy for structural size, not cyclomatic complexity. High-complexity
*functions* are covered by the dedicated analyze_functions tool; this tool
focuses on *module* size, so candidates are sorted by **lines of code** first
(largest files at the top), then by total_complexity as tiebreaker.

Output: Standard JSON with summary (total_issues, files_affected) and details
(refactor_candidates list with file, metrics, and reasons).

**What is excluded from analysis:**
- Only directories listed in config paths.scan_directories are scanned (e.g. ai,
  communication, core, tasks, ui, user). If development_tools or tests are not
  in that list, they are never scanned.
- When run without --include-tests/--include-dev-tools, context is "production":
  standard exclusions exclude development_tools/*, scripts/*, and test *subdirs*
  (e.g. tests/unit/*, tests/integration/*). **Top-level tests/ only** (e.g.
  tests/conftest.py, tests/run_tests.py) are included in production so large
  root test modules can appear as refactor candidates.
- To include all test files: run with --include-tests (context "testing").
- To include development_tools: run with --include-dev-tools (context "development")
  and ensure paths.scan_directories in config includes "development_tools" if
  you want that tree scanned.
- Base exclusions (e.g. __pycache__, .ruff_cache) always apply.

**Compliance (AI_DEVELOPMENT_TOOLS_GUIDE):** Paths and scan directories come from
config (development_tools_config.json); no hardcoded project paths. Tools stay
isolated from MHM business logic. Tool tests live under tests/development_tools/.
"""

from __future__ import annotations

import ast
import argparse
import json
import sys
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

try:
    from .. import config
    from ..shared.standard_exclusions import should_exclude_file
except ImportError:
    from development_tools import config
    from development_tools.shared.standard_exclusions import should_exclude_file

config.load_external_config()

logger = get_component_logger("development_tools")


def _get_config() -> dict[str, Any]:
    """Load tool config (module refactor thresholds)."""
    return config.get_analyze_module_refactor_candidates_config()


def _get_complexity_thresholds() -> tuple[int, int]:
    """Use same high/critical thresholds as analyze_functions for consistency."""
    fn_config = config.get_analyze_functions_config()
    high = int(fn_config.get("high_complexity_threshold", 100))
    critical = int(fn_config.get("critical_complexity_threshold", 200))
    return high, critical


def _count_lines(file_path: Path) -> int:
    """Return number of lines in file (excluding empty lines if desired)."""
    try:
        text = file_path.read_text(encoding="utf-8")
        return len(text.splitlines())
    except Exception as e:
        logger.debug(f"Could not read {file_path}: {e}")
        return 0


def _module_metrics(file_path: Path) -> dict[str, Any] | None:
    """
    Parse a Python file and return per-module metrics.
    Returns None if parse fails.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except Exception as e:
        logger.debug(f"Parse error in {file_path}: {e}")
        return None

    lines = len(content.splitlines())
    function_count = 0
    class_count = 0
    total_function_complexity = 0
    high_complexity_count = 0
    critical_complexity_count = 0
    high_thresh, critical_thresh = _get_complexity_thresholds()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_count += 1
            comp = len(list(ast.walk(node)))
            total_function_complexity += comp
            if comp >= critical_thresh:
                critical_complexity_count += 1
            elif comp >= high_thresh:
                high_complexity_count += 1
        elif isinstance(node, ast.ClassDef):
            class_count += 1

    return {
        "lines": lines,
        "function_count": function_count,
        "class_count": class_count,
        "total_function_complexity": total_function_complexity,
        "high_complexity_count": high_complexity_count,
        "critical_complexity_count": critical_complexity_count,
    }


def _reasons(
    cfg: dict[str, Any],
    metrics: dict[str, Any],
    file_key: str,
) -> list[str]:
    """Return a short reason this module is a refactor candidate (no per-threshold details)."""
    reasons = []
    max_lines = cfg.get("max_lines_per_module")
    max_functions = cfg.get("max_functions_per_module")
    max_total_complexity = cfg.get("max_total_complexity_per_module")
    high_critical_threshold = cfg.get("high_plus_critical_threshold")

    if max_lines is not None and metrics["lines"] >= max_lines:
        reasons.append("exceeds size/complexity thresholds")
        return reasons
    if max_functions is not None and metrics["function_count"] >= max_functions:
        reasons.append("exceeds size/complexity thresholds")
        return reasons
    if max_total_complexity is not None and metrics["total_function_complexity"] >= max_total_complexity:
        reasons.append("exceeds size/complexity thresholds")
        return reasons
    high_plus_critical = metrics["high_complexity_count"] + metrics["critical_complexity_count"]
    if high_critical_threshold is not None and high_plus_critical >= high_critical_threshold:
        reasons.append("exceeds size/complexity thresholds")
    return reasons


def _is_top_level_tests(file_key: str) -> bool:
    """True if file is directly under tests/ (e.g. tests/conftest.py), not in a subdir."""
    if not file_key.startswith("tests/"):
        return False
    # One slash => tests/<name>; more => tests/subdir/...
    return file_key.count("/") == 1


def _scan_and_evaluate(include_tests: bool = False, include_dev_tools: bool = False) -> dict[str, Any]:
    """
    Scan all included Python modules, compute metrics, and return standard-format result.
    Uses same scan directories and exclusions as analyze_functions (production context).
    """
    cfg = _get_config()
    root = Path(config.get_project_root())
    scan_dirs = config.get_scan_directories()

    # Respect include_tests / include_dev_tools by context
    context = "analysis"
    if include_dev_tools:
        context = "development"
    elif include_tests:
        context = "testing"
    else:
        context = "production"

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    for scan_dir in scan_dirs:
        dir_path = root / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            rel = py_file.relative_to(root)
            file_key = str(rel).replace("\\", "/")
            excluded = should_exclude_file(str(py_file), context, "production")
            if excluded and context == "production" and _is_top_level_tests(file_key):
                excluded = False  # Include top-level tests/ (e.g. conftest.py) only
            if excluded:
                continue
            if file_key in seen:
                continue
            seen.add(file_key)

            metrics = _module_metrics(py_file)
            if metrics is None:
                continue

            reason_list = _reasons(cfg, metrics, file_key)
            if not reason_list:
                continue

            candidates.append({
                "file": file_key,
                "lines": metrics["lines"],
                "function_count": metrics["function_count"],
                "class_count": metrics["class_count"],
                "total_function_complexity": metrics["total_function_complexity"],
                "high_complexity_count": metrics["high_complexity_count"],
                "critical_complexity_count": metrics["critical_complexity_count"],
                "reasons": reason_list,
            })

    # Sort by lines descending (large modules first), then total_function_complexity as tiebreaker
    candidates.sort(
        key=lambda x: (x["lines"], x["total_function_complexity"]),
        reverse=True,
    )

    return {
        "summary": {
            "total_issues": len(candidates),
            "files_affected": len(candidates),
            "status": "WARN" if candidates else "PASS",
        },
        "details": {
            "refactor_candidates": candidates,
            "total_candidates": len(candidates),
            "thresholds_used": {
                "max_lines_per_module": cfg.get("max_lines_per_module"),
                "max_functions_per_module": cfg.get("max_functions_per_module"),
                "max_total_complexity_per_module": cfg.get("max_total_complexity_per_module"),
                "high_plus_critical_threshold": cfg.get("high_plus_critical_threshold"),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Identify large or high-complexity modules as refactoring candidates."
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in analysis",
    )
    parser.add_argument(
        "--include-dev-tools",
        action="store_true",
        help="Include development_tools in analysis",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    result = _scan_and_evaluate(
        include_tests=args.include_tests,
        include_dev_tools=args.include_dev_tools,
    )

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    summary = result["summary"]
    candidates = result["details"].get("refactor_candidates", [])
    logger.info(f"Refactor candidates: {summary['total_issues']} modules (files_affected={summary['files_affected']})")
    for c in candidates[:15]:
        logger.info(f"  {c['file']}: lines={c['lines']} functions={c['function_count']} total_function_complexity={c['total_function_complexity']} | {', '.join(c['reasons'])}")
    if len(candidates) > 15:
        logger.info(f"  ... and {len(candidates) - 15} more (use --json for full list)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
