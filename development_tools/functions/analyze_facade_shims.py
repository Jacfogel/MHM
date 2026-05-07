#!/usr/bin/env python3
# TOOL_TIER: supporting

"""Detect advisory facade, shim, re-export, alias, and compatibility bridge candidates."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, TypedDict

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools.shared.logging import get_dev_tools_logger

try:
    from .. import config
    from ..shared.exclusion_utilities import has_devtools_ignore_marker
    from ..shared.standard_exclusions import should_exclude_file
except ImportError:
    from development_tools import config
    from development_tools.shared.exclusion_utilities import has_devtools_ignore_marker
    from development_tools.shared.standard_exclusions import should_exclude_file

config.load_external_config()
logger = get_dev_tools_logger("development_tools")


class FacadeShimFinding(TypedDict):
    file: str
    line: int
    symbol: str
    kind: str
    confidence: float
    signals: list[str]
    target: str | None
    inventory_id: str | None
    recommendation: str


_FACADE_WORD_RE = re.compile(
    r"(?:^|[_\W])(facade|shim|compat(?:ibility)?|legacy|deprecated|bridge|adapter|alias)(?:[_\W]|$)",
    re.IGNORECASE,
)


def _normalize_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return str(path).replace("\\", "/")


def _load_inventory(project_root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    legacy_config = config.get_external_value("legacy_cleanup", {})
    configured = "development_tools/config/jsons/DEPRECATION_INVENTORY.json"
    if isinstance(legacy_config, dict):
        configured = legacy_config.get("deprecation_inventory_file", configured)
    inventory_path = Path(str(configured))
    if not inventory_path.is_absolute():
        inventory_path = project_root / inventory_path
    try:
        data = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], {}
    entries = data.get("active_or_candidate_inventory", [])
    if not isinstance(entries, list):
        entries = []
    term_to_id: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = str(entry.get("id", "")).strip()
        terms = entry.get("search_terms", [])
        if not entry_id or not isinstance(terms, list):
            continue
        for term in terms:
            if isinstance(term, str) and term.strip():
                term_to_id[term.strip().lower()] = entry_id
    return [entry for entry in entries if isinstance(entry, dict)], term_to_id


def _call_target(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return _expr_name(node.func)
    return None


def _expr_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _expr_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _function_target(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    body = [stmt for stmt in node.body if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Constant)]
    if len(body) != 1:
        return None
    stmt = body[0]
    if isinstance(stmt, ast.Return) and stmt.value is not None:
        return _call_target(stmt.value)
    if isinstance(stmt, ast.Expr):
        return _call_target(stmt.value)
    return None


def _inventory_id_for_text(text: str, term_to_id: dict[str, str]) -> str | None:
    lower = text.lower()
    for term, entry_id in term_to_id.items():
        if term and term in lower:
            return entry_id
    return None


def _confidence(signals: list[str]) -> float:
    score = 0.35 + (0.15 * len(set(signals)))
    return round(min(score, 0.95), 2)


class _FacadeShimCollector(ast.NodeVisitor):
    def __init__(
        self,
        file_path: Path,
        root: Path,
        content: str,
        term_to_id: dict[str, str],
        *,
        include_low_signal: bool = False,
    ) -> None:
        self.file_path = file_path
        self.root = root
        self.content = content
        self.term_to_id = term_to_id
        self.include_low_signal = include_low_signal
        self.import_aliases: dict[str, str] = {}
        self.findings: list[FacadeShimFinding] = []
        self.low_signal_findings: list[FacadeShimFinding] = []
        self.scope_depth = 0

    def _add(
        self,
        *,
        node: ast.AST,
        symbol: str,
        kind: str,
        signals: list[str],
        target: str | None = None,
        inventory_id: str | None = None,
        low_signal: bool = False,
    ) -> None:
        line = int(getattr(node, "lineno", 0) or 0)
        finding: FacadeShimFinding = {
            "file": _normalize_path(self.file_path, self.root),
            "line": line,
            "symbol": symbol,
            "kind": kind,
            "confidence": _confidence(signals),
            "signals": sorted(set(signals)),
            "target": target,
            "inventory_id": inventory_id,
            "recommendation": (
                "Review whether this compatibility surface is still required; "
                "if retained, track it in the deprecation inventory."
            ),
        }
        if low_signal and not self.include_low_signal:
            self.low_signal_findings.append(finding)
        else:
            self.findings.append(finding)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            local = alias.asname or alias.name
            target = f"{module}.{alias.name}" if module else alias.name
            self.import_aliases[local] = target
            signals: list[str] = []
            if alias.asname:
                signals.append("import_alias")
            if _FACADE_WORD_RE.search(local) or _FACADE_WORD_RE.search(target):
                signals.append("facade_shim_name")
            inventory_id = _inventory_id_for_text(f"{local} {target}", self.term_to_id)
            if inventory_id:
                signals.append("deprecation_inventory_term")
        if signals:
            low_signal = signals == ["import_alias"]
            self._add(
                node=node,
                symbol=local,
                kind="re_export_alias",
                signals=signals,
                target=target,
                inventory_id=inventory_id,
                low_signal=low_signal,
            )

    def visit_Assign(self, node: ast.Assign) -> None:
        if self.scope_depth > 0:
            return
        target_name = _expr_name(node.value)
        if not target_name:
            return
        for target in node.targets:
            alias = _expr_name(target)
            if not alias:
                continue
            signals: list[str] = []
            if _FACADE_WORD_RE.search(alias) or _FACADE_WORD_RE.search(target_name):
                signals.append("facade_shim_name")
            inventory_id = _inventory_id_for_text(f"{alias} {target_name}", self.term_to_id)
            if inventory_id:
                signals.append("deprecation_inventory_term")
            if signals:
                self._add(
                    node=node,
                    symbol=alias,
                    kind="alias",
                    signals=signals,
                    target=target_name,
                    inventory_id=inventory_id,
                )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if has_devtools_ignore_marker(self.content, "facade-shims", node):
            return
        target = _function_target(node)
        doc = ast.get_docstring(node) or ""
        text = f"{node.name} {doc} {target or ''}"
        signals: list[str] = []
        if target:
            signals.append("thin_delegating_wrapper")
        if _FACADE_WORD_RE.search(text):
            signals.append("facade_shim_name_or_doc")
        inventory_id = _inventory_id_for_text(text, self.term_to_id)
        if inventory_id:
            signals.append("deprecation_inventory_term")
        if signals:
            strong_signals = {
                "deprecation_inventory_term",
                "facade_shim_name_or_doc",
            }
            low_signal = target is not None and not (strong_signals & set(signals))
            self._add(
                node=node,
                symbol=node.name,
                kind="thin_wrapper" if target else "compatibility_marker",
                signals=signals,
                target=target,
                inventory_id=inventory_id,
                low_signal=low_signal,
            )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope_depth += 1
        try:
            self.generic_visit(node)
        finally:
            self.scope_depth -= 1


def analyze_project(
    include_tests: bool = False,
    include_dev_tools: bool = False,
    include_low_signal: bool = False,
) -> dict[str, Any]:
    root = Path(config.get_project_root()).resolve()
    scan_dirs = list(config.get_scan_directories())
    if include_tests and "tests" not in scan_dirs:
        scan_dirs.append("tests")
    if include_dev_tools and "development_tools" not in scan_dirs:
        scan_dirs.append("development_tools")
    context = "development" if include_tests or include_dev_tools else "production"
    _entries, term_to_id = _load_inventory(root)

    findings: list[FacadeShimFinding] = []
    low_signal_count = 0
    for scan_dir in scan_dirs:
        dir_path = root / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            rel = _normalize_path(py_file, root)
            if should_exclude_file(rel, "analysis", context):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)
            except Exception as exc:
                logger.warning(f"Failed to parse {py_file}: {exc}")
                continue
            if has_devtools_ignore_marker(content, "facade-shims"):
                continue
            collector = _FacadeShimCollector(
                py_file,
                root,
                content,
                term_to_id,
                include_low_signal=include_low_signal,
            )
            collector.visit(tree)
            findings.extend(collector.findings)
            low_signal_count += len(collector.low_signal_findings)

    findings.sort(key=lambda item: (item["file"], item["line"], item["symbol"]))
    files_affected = {finding["file"] for finding in findings}
    return {
        "summary": {
            "total_issues": len(findings),
            "files_affected": len(files_affected),
        },
        "details": {
            "findings": findings,
            "inventory_terms_loaded": len(term_to_id),
            "low_signal_candidates_filtered": low_signal_count,
            "low_signal_filter": (
                "Plain one-line delegating wrappers and generic import aliases "
                "are filtered unless they also have facade/shim/compatibility naming, "
                "compatibility documentation, or active deprecation-inventory terms. "
                "Use --include-low-signal for the exhaustive advisory list."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect advisory facade/shim/re-export/compatibility bridge candidates."
    )
    parser.add_argument("--include-tests", action="store_true", help="Include test files.")
    parser.add_argument(
        "--include-dev-tools", action="store_true", help="Include development_tools."
    )
    parser.add_argument(
        "--include-low-signal",
        action="store_true",
        help=(
            "Include plain thin wrappers and generic import aliases that lack "
            "compatibility naming, docs, or active deprecation-inventory terms."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    args = parser.parse_args()

    result = analyze_project(
        include_tests=args.include_tests,
        include_dev_tools=args.include_dev_tools,
        include_low_signal=args.include_low_signal,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        summary = result["summary"]
        print("Facade/Shim Candidates")
        print("=======================")
        print(f"Candidates found: {summary['total_issues']}")
        print(f"Files affected: {summary['files_affected']}")
        filtered = result.get("details", {}).get("low_signal_candidates_filtered", 0)
        if filtered:
            print(f"Low-signal candidates filtered: {filtered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
