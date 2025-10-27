﻿#!/usr/bin/env python3
"""Audit script to verify FUNCTION_REGISTRY_DETAIL.md coverage."""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from . import config
    from .services.common import ProjectPaths, ensure_ascii, iter_python_sources, run_cli, summary_block, write_text
except ImportError:
    import config
    from services.common import ProjectPaths, ensure_ascii, iter_python_sources, run_cli, summary_block, write_text

PATHS = ProjectPaths()
REGISTRY_PATH = PATHS.dev_docs / "FUNCTION_REGISTRY_DETAIL.md"
CURRENT_DIR = Path(__file__).parent

FUNCTION_CFG = config.get_function_discovery_config()
HANDLER_KEYWORDS = tuple(keyword.lower() for keyword in FUNCTION_CFG.get("handler_keywords", []))

HIGH_COMPLEXITY_MIN = 50
TOP_COMPLEXITY = 10
TOP_UNDOCUMENTED = 5
TOP_DUPLICATES = 5
ERROR_SAMPLE_LIMIT = 5
MAX_COMPLEXITY_JSON = 200
MAX_UNDOCUMENTED_JSON = 200
MAX_DUPLICATES_JSON = 200


@dataclass(frozen=True)
class FunctionRecord:
    name: str
    line: int
    args: Tuple[str, ...]
    decorators: Tuple[str, ...]
    docstring: str
    is_test: bool
    is_main: bool
    is_handler: bool
    has_docstring: bool
    complexity: int


@dataclass(frozen=True)
class ClassRecord:
    name: str
    line: int
    docstring: str
    methods: Tuple[str, ...]


def decorator_names(node: ast.AST) -> Tuple[str, ...]:
    names: List[str] = []
    for decorator in getattr(node, "decorator_list", []):
        if isinstance(decorator, ast.Name):
            names.append(decorator.id)
        elif isinstance(decorator, ast.Attribute):
            names.append(decorator.attr)
        elif isinstance(decorator, ast.Call):
            func = decorator.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                names.append(func.attr)
    return tuple(names)


def function_arguments(node: ast.FunctionDef) -> Tuple[str, ...]:
    parts: List[str] = []
    for arg in getattr(node.args, "posonlyargs", []):
        parts.append(arg.arg)
    for arg in node.args.args:
        parts.append(arg.arg)
    if node.args.vararg:
        parts.append(f"*{node.args.vararg.arg}")
    for arg in node.args.kwonlyargs:
        parts.append(arg.arg)
    if node.args.kwarg:
        parts.append(f"**{node.args.kwarg.arg}")
    return tuple(parts)


def node_complexity(node: ast.AST) -> int:
    return sum(1 for _ in ast.walk(node))


def extract_functions_and_classes(path: Path, errors: List[str]) -> Tuple[List[FunctionRecord], List[ClassRecord]]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"Read error {path}: {exc}")
        return [], []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        errors.append(f"Syntax error {path}: line {exc.lineno}: {exc.msg}")
        return [], []

    functions: List[FunctionRecord] = []
    classes: List[ClassRecord] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            docstring = ast.get_docstring(node, clean=False) or ""
            functions.append(
                FunctionRecord(
                    name=name,
                    line=node.lineno,
                    args=function_arguments(node),
                    decorators=decorator_names(node),
                    docstring=docstring,
                    is_test=name.startswith("test_") or "test" in name.lower(),
                    is_main=name in {"main", "__main__"},
                    is_handler=any(keyword in name.lower() for keyword in HANDLER_KEYWORDS),
                    has_docstring=bool(docstring.strip()),
                    complexity=node_complexity(node),
                )
            )
        elif isinstance(node, ast.ClassDef):
            docstring = ast.get_docstring(node, clean=False) or ""
            method_names = tuple(
                child.name for child in node.body if isinstance(child, ast.FunctionDef)
            )
            classes.append(
                ClassRecord(
                    name=node.name,
                    line=node.lineno,
                    docstring=docstring,
                    methods=method_names,
                )
            )
    return functions, classes


def collect_project_inventory(errors: List[str]) -> Dict[str, Dict[str, object]]:
    inventory: Dict[str, Dict[str, object]] = {}
    seen: Set[Path] = set()

    for source_path in iter_python_sources(config.get_scan_directories(), context="production"):
        resolved = source_path.resolve()
        seen.add(resolved)
        try:
            relative = resolved.relative_to(PATHS.root)
            key = str(relative).replace("\\", "/")
        except ValueError:
            key = str(resolved)
        functions, classes = extract_functions_and_classes(resolved, errors)
        inventory[key] = {
            "functions": functions,
            "classes": classes,
            "total_functions": len(functions),
            "total_classes": len(classes),
        }

    for source_path in PATHS.root.glob("*.py"):
        resolved = source_path.resolve()
        if resolved in seen or resolved == (CURRENT_DIR / "audit_function_registry.py"):
            continue
        functions, classes = extract_functions_and_classes(resolved, errors)
        inventory[source_path.name] = {
            "functions": functions,
            "classes": classes,
            "total_functions": len(functions),
            "total_classes": len(classes),
        }

    return inventory


def extract_documented_name(line: str) -> str | None:
    if "`" not in line:
        return None
    start = line.index("`") + 1
    end = line.find("`", start)
    if end == -1:
        return None
    signature = line[start:end]
    if not signature:
        return None
    if "(" in signature:
        signature = signature.split("(", 1)[0]
    if "." in signature:
        signature = signature.split(".")[-1]
    return signature.strip()


def parse_registry_document(path: Path = REGISTRY_PATH) -> Dict[str, Set[str]]:
    if not path.exists():
        return {}
    mapping: Dict[str, Set[str]] = {}
    current_file: str | None = None
    in_functions = False

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line.startswith("#### `") and line.endswith("`"):
            current_file = line[5:-1].strip("`")
            mapping.setdefault(current_file, set())
            in_functions = False
            continue
        if line.lower() == "**functions:**":
            in_functions = current_file is not None
            continue
        if line.lower().startswith("**classes:**"):
            in_functions = False
            continue
        if in_functions and line.startswith("-"):
            name = extract_documented_name(line)
            if name:
                mapping[current_file].add(name)
    return mapping


def build_metrics(inventory: Dict[str, Dict[str, object]], registry: Dict[str, Set[str]]) -> Dict[str, object]:
    missing_by_file: Dict[str, List[str]] = {}
    missing_files: List[str] = []
    missing_count = 0

    for file_path, data in inventory.items():
        actual = {record.name for record in data["functions"]}
        documented = registry.get(file_path, set())
        if file_path not in registry and actual:
            missing_files.append(file_path)
        missing = sorted(actual - documented)
        if missing:
            missing_by_file[file_path] = missing
            missing_count += len(missing)

    extra_by_file: Dict[str, List[str]] = {}
    extra_count = 0
    for file_path, documented in registry.items():
        actual = {record.name for record in inventory.get(file_path, {}).get("functions", [])}
        extras = sorted(name for name in documented if name not in actual)
        if extras:
            extra_by_file[file_path] = extras
            extra_count += len(extras)

    totals = {
        "files_scanned": len(inventory),
        "functions_found": sum(data["total_functions"] for data in inventory.values()),
        "classes_found": sum(data["total_classes"] for data in inventory.values()),
        "functions_documented": sum(len(names) for names in registry.values()),
    }
    coverage = 0.0
    if totals["functions_found"]:
        coverage = (totals["functions_documented"] / totals["functions_found"]) * 100.0

    return {
        "totals": totals,
        "coverage": coverage,
        "missing_by_file": missing_by_file,
        "missing_files": sorted(missing_files),
        "missing_count": missing_count,
        "extra_by_file": extra_by_file,
        "extra_count": extra_count,
    }


def build_analysis(inventory: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    high_complexity: List[Dict[str, object]] = []
    undocumented_handlers: List[Dict[str, str]] = []
    undocumented_other: List[Dict[str, str]] = []
    occurrences: Dict[str, Set[str]] = {}

    for file_path, data in inventory.items():
        for record in data["functions"]:
            occurrences.setdefault(record.name, set()).add(file_path)
            if (
                record.complexity > HIGH_COMPLEXITY_MIN
                and not record.is_test
                and not ("generated" in file_path and "_pyqt.py" in file_path)
                and record.name not in {"setupUi", "retranslateUi"}
            ):
                high_complexity.append(
                    {
                        "file": file_path,
                        "name": record.name,
                        "complexity": record.complexity,
                        "has_docstring": record.has_docstring,
                    }
                )
            if not record.has_docstring and not record.is_test and not record.is_main:
                target = undocumented_handlers if record.is_handler else undocumented_other
                target.append({"file": file_path, "name": record.name})

    high_complexity.sort(key=lambda item: item["complexity"], reverse=True)
    undocumented_handlers.sort(key=lambda item: (item["file"], item["name"]))
    undocumented_other.sort(key=lambda item: (item["file"], item["name"]))

    high_total = len(high_complexity)
    if high_total > MAX_COMPLEXITY_JSON:
        high_complexity = high_complexity[:MAX_COMPLEXITY_JSON]

    handlers_total = len(undocumented_handlers)
    if handlers_total > MAX_UNDOCUMENTED_JSON:
        undocumented_handlers = undocumented_handlers[:MAX_UNDOCUMENTED_JSON]

    others_total = len(undocumented_other)
    if others_total > MAX_UNDOCUMENTED_JSON:
        undocumented_other = undocumented_other[:MAX_UNDOCUMENTED_JSON]

    duplicates = {
        name: sorted(files)
        for name, files in occurrences.items()
        if len(files) > 1
    }
    duplicate_count = len(duplicates)
    duplicates_limited = {
        name: duplicates[name]
        for name in sorted(duplicates)[:MAX_DUPLICATES_JSON]
    }

    duplicate_sample = [
        {"name": name, "files": duplicates[name]}
        for name in sorted(duplicates)[:TOP_DUPLICATES]
    ]

    return {
        "high_complexity": high_complexity,
        "high_complexity_total": high_total,
        "undocumented_handlers": undocumented_handlers,
        "undocumented_handlers_total": handlers_total,
        "undocumented_other": undocumented_other,
        "undocumented_other_total": others_total,
        "duplicates": duplicates_limited,
        "duplicate_count": duplicate_count,
        "duplicate_sample": duplicate_sample,
    }


def build_registry_sections(inventory: Dict[str, Dict[str, object]], metrics: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    sections: Dict[str, Dict[str, object]] = {}

    for file_path, missing_names in metrics["missing_by_file"].items():
        data = inventory.get(file_path)
        if not data:
            continue
        sections[file_path] = {
            "functions": [
                {
                    "name": func.name,
                    "args": list(func.args),
                    "docstring": func.docstring.strip(),
                }
                for func in data["functions"]
                if func.name in missing_names
            ],
            "classes": [
                {
                    "name": cls.name,
                    "docstring": cls.docstring.strip(),
                    "methods": list(cls.methods),
                }
                for cls in data["classes"]
            ],
        }

    for file_path in metrics["missing_files"]:
        if file_path in sections:
            continue
        data = inventory.get(file_path)
        if not data:
            continue
        sections[file_path] = {
            "functions": [
                {
                    "name": func.name,
                    "args": list(func.args),
                    "docstring": func.docstring.strip(),
                }
                for func in data["functions"]
            ],
            "classes": [
                {
                    "name": cls.name,
                    "docstring": cls.docstring.strip(),
                    "methods": list(cls.methods),
                }
                for cls in data["classes"]
            ],
        }

    return sections


def summarise_audit(
    inventory: Dict[str, Dict[str, object]],
    metrics: Dict[str, object],
    analysis: Dict[str, object],
    errors: List[str],
) -> str:
    lines: List[str] = []
    lines.append("[SCAN] Scanning all Python files...")
    lines.append("[DOC] Parsing FUNCTION_REGISTRY_DETAIL.md...")
    lines.append("")
    lines.append("=" * 80)
    lines.append("FUNCTION REGISTRY AUDIT REPORT")
    lines.append("=" * 80)
    lines.append("")
    totals = metrics["totals"]
    lines.append("[STATS] OVERALL STATISTICS:")
    lines.append(f"   Files scanned: {totals['files_scanned']}")
    lines.append(f"   Functions found: {totals['functions_found']}")
    lines.append(f"   Classes found: {totals['classes_found']}")
    lines.append(f"   Functions documented: {totals['functions_documented']}")
    lines.append(f"   Coverage: {metrics['coverage']:.1f}%")
    lines.append(f"coverage: {metrics['coverage']:.1f}%")
    lines.append("")

    lines.append("[MISS] MISSING FROM REGISTRY:")
    if metrics["missing_count"] == 0:
        lines.append("   None")
    else:
        for file_path in sorted(metrics["missing_by_file"]):
            missing = metrics["missing_by_file"][file_path]
            lines.append(f"   [FILE] {file_path}:")
            for name in missing[:TOP_UNDOCUMENTED]:
                lines.append(f"      - {name}")
            remaining = max(len(missing) - TOP_UNDOCUMENTED, 0)
            if remaining > 0:
                lines.append(f"      ... +{remaining} more")
        for file_path in metrics["missing_files"]:
            lines.append(f"   [DIR] {file_path} - ENTIRE FILE MISSING")
    lines.append("")
    lines.append(f"   Total missing functions: {metrics['missing_count']}")
    lines.append(f"missing items: {metrics['missing_count']}")
    lines.append("")

    lines.append("[EXTRA] EXTRA IN REGISTRY (not found in files):")
    if metrics["extra_count"] == 0:
        lines.append("   None")
    else:
        for file_path in sorted(metrics["extra_by_file"]):
            extras = metrics["extra_by_file"][file_path]
            lines.append(f"   [FILE] {file_path}:")
            for name in extras[:TOP_UNDOCUMENTED]:
                lines.append(f"      - {name}")
            remaining = max(len(extras) - TOP_UNDOCUMENTED, 0)
            if remaining > 0:
                lines.append(f"      ... +{remaining} more")
    lines.append("")
    lines.append(f"   Total extra functions: {metrics['extra_count']}")
    lines.append("")

    lines.append("[ANALYSIS] FUNCTION ANALYSIS FOR DECISION-MAKING:")
    high_complexity = analysis["high_complexity"]
    high_total = analysis["high_complexity_total"]
    if high_total:
        lines.append("   [WARN] HIGH COMPLEXITY FUNCTIONS (may need refactoring):")
        for item in high_complexity[:TOP_COMPLEXITY]:
            status = "[DOC]" if item["has_docstring"] else "[NO DOC]"
            lines.append(f"      {status} {item['file']}::{item['name']} (complexity: {item['complexity']})")
        leftover = max(high_total - TOP_COMPLEXITY, 0)
        if leftover > 0:
            lines.append(f"      ... +{leftover} more")
    else:
        lines.append("   [WARN] HIGH COMPLEXITY FUNCTIONS (may need refactoring): None")

    handlers = analysis["undocumented_handlers"]
    handlers_total = analysis["undocumented_handlers_total"]
    others = analysis["undocumented_other"]
    others_total = analysis["undocumented_other_total"]
    if handlers_total or others_total:
        lines.append("   [DOC] UNDOCUMENTED FUNCTIONS (need docstrings):")
        if handlers_total:
            lines.append(f"      [HANDLER] Handlers/Utilities ({handlers_total}):")
            for item in handlers[:TOP_UNDOCUMENTED]:
                lines.append(f"         - {item['file']}::{item['name']}")
            leftover = max(handlers_total - TOP_UNDOCUMENTED, 0)
            if leftover > 0:
                lines.append(f"         ... +{leftover} more")
        if others_total:
            lines.append(f"      [OTHER] Other functions ({others_total}):")
            for item in others[:TOP_UNDOCUMENTED]:
                lines.append(f"         - {item['file']}::{item['name']}")
            leftover = max(others_total - TOP_UNDOCUMENTED, 0)
            if leftover > 0:
                lines.append(f"         ... +{leftover} more")
    else:
        lines.append("   [DOC] UNDOCUMENTED FUNCTIONS (need docstrings): None")

    duplicate_sample = analysis["duplicate_sample"]
    duplicate_total = analysis["duplicate_count"]
    if duplicate_total:
        lines.append("")
        lines.append("[DUPE] POTENTIAL DUPLICATE FUNCTION NAMES:")
        for item in duplicate_sample:
            lines.append(f"   '{item['name']}' found in: {', '.join(item['files'])}")
        leftover = max(duplicate_total - len(duplicate_sample), 0)
        if leftover > 0:
            lines.append(f"   ... +{leftover} more")

    dir_stats: Dict[str, Dict[str, int]] = {}
    for file_path, data in inventory.items():
        dir_name = file_path.rsplit("/", 1)[0] if "/" in file_path else "root"
        stats = dir_stats.setdefault(dir_name, {"files": 0, "functions": 0, "classes": 0})
        stats["files"] += 1
        stats["functions"] += data["total_functions"]
        stats["classes"] += data["total_classes"]
    lines.append("")
    lines.append("[DIR] BREAKDOWN BY DIRECTORY:")
    for dir_name in sorted(dir_stats):
        stats = dir_stats[dir_name]
        lines.append(f"   {dir_name}/: {stats['files']} files, {stats['functions']} functions, {stats['classes']} classes")

    if errors:
        lines.append("")
        lines.append("[ERROR] Issues encountered while scanning:")
        for err in errors[:ERROR_SAMPLE_LIMIT]:
            lines.append(f"   - {err}")
        if len(errors) > ERROR_SAMPLE_LIMIT:
            lines.append(f"   ... +{len(errors) - ERROR_SAMPLE_LIMIT} more")

    if metrics["missing_count"]:
        lines.append("")
        lines.append("[GEN] Missing registry sections available via --json (registry_sections).")

    return "\n".join(lines)


def execute(args: argparse.Namespace):
    errors: List[str] = []
    inventory = collect_project_inventory(errors)
    registry = parse_registry_document()
    metrics = build_metrics(inventory, registry)
    analysis = build_analysis(inventory)
    sections = build_registry_sections(inventory, metrics)
    summary = summarise_audit(inventory, metrics, analysis, errors)
    payload = {
        "totals": metrics["totals"],
        "coverage": round(metrics["coverage"], 2),
        "missing": {
            "count": metrics["missing_count"],
            "files": metrics["missing_by_file"],
            "missing_files": metrics["missing_files"],
        },
        "extra": {
            "count": metrics["extra_count"],
            "files": metrics["extra_by_file"],
        },
        "analysis": {
            "high_complexity": analysis["high_complexity"],
            "high_complexity_total": analysis["high_complexity_total"],
            "undocumented_handlers": analysis["undocumented_handlers"],
            "undocumented_handlers_total": analysis["undocumented_handlers_total"],
            "undocumented_other": analysis["undocumented_other"],
            "undocumented_other_total": analysis["undocumented_other_total"],
            "duplicates": analysis["duplicates"],
            "duplicate_count": analysis["duplicate_count"],
            "duplicate_sample": analysis["duplicate_sample"],
        },
        "registry_sections": sections,
        "errors": errors,
    }
    exit_code = 0
    if metrics["missing_count"] or metrics["extra_count"] or errors:
        exit_code = 1
    return exit_code, ensure_ascii(summary), payload


def main() -> int:
    return run_cli(execute, description="Audit function registry against codebase.")


if __name__ == "__main__":
    raise SystemExit(main())

