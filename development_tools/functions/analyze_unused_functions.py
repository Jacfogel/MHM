#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Detect functions and methods that appear to be unused/uncalled across the codebase.

Uses AST parsing to:
1. Collect all function and method definitions
2. Collect all Name and Attribute references across all files
3. Cross-reference to find definitions whose names never appear as references

Limitations (advisory-level tool):
- Cannot track dynamic dispatch (getattr, string-based lookups, etc.)
- Cannot resolve cross-module attribute chains beyond simple `module.func` patterns
- Callbacks passed as arguments are detected by name reference, not by invocation
- Decorated functions may be called implicitly by frameworks (Discord, Qt, etc.)

Exclusion: Add a comment inside the function (or in the few lines before it):
  # unused_functions_exclude
  or
  # unused functions exclude
(optionally with a reason after a colon) to suppress a specific function.

Use --include-tests and --include-dev-tools to widen the scan scope.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools.shared.logging import get_dev_tools_logger

try:
    from .. import config
    from ..shared.standard_exclusions import should_exclude_file
    from ..shared.exclusion_utilities import (
        has_devtools_ignore_marker,
        is_special_python_method,
        is_test_function,
    )
except ImportError:
    from development_tools import config
    from development_tools.shared.standard_exclusions import should_exclude_file
    from development_tools.shared.exclusion_utilities import (
        has_devtools_ignore_marker,
        is_special_python_method,
        is_test_function,
    )

config.load_external_config()

logger = get_dev_tools_logger("development_tools")


# ---------------------------------------------------------------------------
# Decorator / framework patterns that imply implicit invocation
# ---------------------------------------------------------------------------

_IMPLICIT_DECORATOR_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"command"),
    re.compile(r"listener"),
    re.compile(r"event"),
    re.compile(r"route"),
    re.compile(r"app_commands"),
    re.compile(r"slot"),
    re.compile(r"receiver"),
    re.compile(r"callback"),
    re.compile(r"hook"),
    re.compile(r"register"),
    re.compile(r"task"),
    re.compile(r"celery"),
    re.compile(r"pytest\.fixture"),
    re.compile(r"pytest\.mark"),
    re.compile(r"property"),
    re.compile(r"staticmethod"),
    re.compile(r"classmethod"),
    re.compile(r"abstractmethod"),
    re.compile(r"overload"),
    re.compile(r"override"),
    re.compile(r"handle_errors"),
]

_IMPLICIT_NAME_PREFIXES: tuple[str, ...] = (
    "on_",
    "setup_",
    "teardown_",
    "setUp",
    "tearDown",
    "test_",
    "conftest_",
)

_IMPLICIT_EXACT_NAMES: frozenset[str] = frozenset({
    "main",
    "__init__",
    "__post_init__",
    "__enter__",
    "__exit__",
    "__aenter__",
    "__aexit__",
    "__str__",
    "__repr__",
    "__hash__",
    "__eq__",
    "__ne__",
    "__lt__",
    "__le__",
    "__gt__",
    "__ge__",
    "__len__",
    "__getitem__",
    "__setitem__",
    "__delitem__",
    "__contains__",
    "__iter__",
    "__next__",
    "__call__",
    "__bool__",
    "__add__",
    "__sub__",
    "__mul__",
    "__truediv__",
    "__floordiv__",
    "__mod__",
    "__pow__",
    "__and__",
    "__or__",
    "__xor__",
    "__invert__",
    "__neg__",
    "__pos__",
    "__abs__",
    "__int__",
    "__float__",
    "__index__",
    "__get__",
    "__set__",
    "__delete__",
    "__set_name__",
    "__init_subclass__",
    "__class_getitem__",
    "__missing__",
    "__del__",
    "__new__",
    "__format__",
    "__sizeof__",
    "__reduce__",
    "__reduce_ex__",
    "__getattr__",
    "__setattr__",
    "__delattr__",
    "__getattribute__",
    "__copy__",
    "__deepcopy__",
    "__await__",
    "__aiter__",
    "__anext__",
    "__reversed__",
    "__fspath__",
    "__radd__",
    "__rsub__",
    "__rmul__",
    "__rtruediv__",
    "__iadd__",
    "__isub__",
    "__imul__",
    "__matmul__",
})


@dataclass(frozen=True)
class FunctionDef:
    """A discovered function or method definition."""

    name: str
    full_name: str  # ClassName.method or just name
    file_path: str  # project-relative posix path
    line: int
    class_name: str | None
    is_private: bool
    is_method: bool
    excluded: bool = False


@dataclass
class _FileRefs:
    """All name references found in a single file."""

    name_refs: set[str] = field(default_factory=set)
    attr_refs: set[str] = field(default_factory=set)  # "obj.method" style


# ---------------------------------------------------------------------------
# AST visitors
# ---------------------------------------------------------------------------

class _DefinitionCollector(ast.NodeVisitor):
    """Collect all function/method definitions from a file."""

    def __init__(self, file_path: str, content: str) -> None:
        self.file_path = file_path
        self.content = content
        self._class_stack: list[str] = []
        self.defs: list[FunctionDef] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        class_name = self._class_stack[-1] if self._class_stack else None
        full_name = f"{class_name}.{node.name}" if class_name else node.name

        if _is_implicitly_used(node):
            return

        excluded = has_devtools_ignore_marker(self.content, "unused-functions", node)

        self.defs.append(FunctionDef(
            name=node.name,
            full_name=full_name,
            file_path=self.file_path,
            line=getattr(node, "lineno", 0),
            class_name=class_name,
            is_private=node.name.startswith("_") and not node.name.startswith("__"),
            is_method=class_name is not None,
            excluded=excluded,
        ))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)
        self.generic_visit(node)


class _ReferenceCollector(ast.NodeVisitor):
    """Collect all name references (calls, attribute accesses, plain names) from a file."""

    def __init__(self) -> None:
        self.refs = _FileRefs()

    def visit_Name(self, node: ast.Name) -> None:
        if node.id:
            self.refs.name_refs.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr:
            self.refs.name_refs.add(node.attr)
            # Also record dotted form for "self.method" / "obj.func" patterns
            if isinstance(node.value, ast.Name) and node.value.id:
                self.refs.attr_refs.add(f"{node.value.id}.{node.attr}")
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        # Catch string references (e.g. getattr(obj, "func_name"))
        if isinstance(node.value, str) and node.value.isidentifier():
            self.refs.name_refs.add(node.value)
        self.generic_visit(node)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decorator_name(decorator: ast.expr) -> str:
    """Extract a readable name from a decorator AST node."""
    if isinstance(decorator, ast.Name):
        return decorator.id or ""
    if isinstance(decorator, ast.Attribute):
        parts: list[str] = []
        node: ast.expr = decorator
        while isinstance(node, ast.Attribute):
            if node.attr:
                parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name) and node.id:
            parts.append(node.id)
        return ".".join(reversed(parts))
    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator.func)
    return ""


def _is_implicitly_used(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if the function is implicitly invoked by a framework or convention."""
    name = node.name or ""

    if name in _IMPLICIT_EXACT_NAMES:
        return True

    if is_special_python_method(name):
        return True

    if is_test_function(name):
        return True

    if any(name.startswith(prefix) for prefix in _IMPLICIT_NAME_PREFIXES):
        return True

    for decorator in getattr(node, "decorator_list", []) or []:
        dec_name = _decorator_name(decorator)
        if any(pattern.search(dec_name) for pattern in _IMPLICIT_DECORATOR_PATTERNS):
            return True

    return False


def _normalize_path(path: str, project_root: Path) -> str:
    """Return project-relative posix path."""
    try:
        resolved = Path(path).resolve()
        return resolved.relative_to(project_root.resolve()).as_posix()
    except (ValueError, OSError):
        return path.replace("\\", "/")


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

def _scan_file_definitions(
    file_path: Path, project_root: Path
) -> list[FunctionDef]:
    """Parse a file and return all non-implicit function definitions."""
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except Exception as exc:
        logger.warning(f"Failed to parse {file_path}: {exc}")
        return []

    rel_path = _normalize_path(str(file_path), project_root)
    collector = _DefinitionCollector(rel_path, content)
    collector.visit(tree)
    return collector.defs


def _scan_file_references(file_path: Path) -> _FileRefs:
    """Parse a file and return all name/attribute references."""
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except Exception:
        return _FileRefs()

    collector = _ReferenceCollector()
    collector.visit(tree)
    return collector.refs


def _collect_python_files(
    project_root: Path,
    include_tests: bool,
    include_dev_tools: bool,
    *,
    scan_directories: list[str] | None = None,
    apply_exclusions: bool = True,
) -> list[Path]:
    """Collect all Python files to scan, respecting exclusions."""
    scan_dirs = (
        list(scan_directories)
        if scan_directories is not None
        else list(config.get_scan_directories())
    )
    if include_tests and "tests" not in scan_dirs:
        scan_dirs.append("tests")
    if include_dev_tools and "development_tools" not in scan_dirs:
        scan_dirs.append("development_tools")

    context = "development" if include_tests or include_dev_tools else "production"
    files: list[Path] = []

    for scan_dir in scan_dirs:
        dir_path = project_root / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            if apply_exclusions and should_exclude_file(
                str(py_file), "analysis", context
            ):
                continue
            files.append(py_file)

    for py_file in project_root.glob("*.py"):
        if apply_exclusions and should_exclude_file(str(py_file), "analysis", context):
            continue
        files.append(py_file)

    return files


def _is_init_export(func_def: FunctionDef) -> bool:
    """Return True if the function is in __init__.py and likely re-exported."""
    return func_def.file_path.endswith("__init__.py")


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def analyze_unused_functions(
    include_tests: bool = False,
    include_dev_tools: bool = False,
    include_private_only: bool = False,
    max_results: int = 100,
    *,
    project_root: Path | str | None = None,
    scan_directories: list[str] | None = None,
    apply_exclusions: bool = True,
) -> dict[str, Any]:
    """
    Scan the codebase and return functions that are never referenced.

    Args:
        include_tests: Include test files in the scan.
        include_dev_tools: Include development_tools in the scan.
        include_private_only: Only report private (underscore-prefixed) functions.
        max_results: Cap the number of unused functions reported.
        project_root: Optional root override (tests / external projects).
        scan_directories: Optional scan-dir override; bypasses config when set.
        apply_exclusions: When False, skip ``should_exclude_file`` filtering.

    Returns:
        Dict with summary and details keys matching the standard tool result shape.
    """
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(config.get_project_root()).resolve()
    )
    files = _collect_python_files(
        root,
        include_tests,
        include_dev_tools,
        scan_directories=scan_directories,
        apply_exclusions=apply_exclusions,
    )

    # Phase 1: collect all definitions
    all_defs: list[FunctionDef] = []
    for f in files:
        all_defs.extend(_scan_file_definitions(f, root))

    # Phase 2: collect all references across the entire codebase
    global_name_refs: set[str] = set()
    global_attr_refs: set[str] = set()
    for f in files:
        refs = _scan_file_references(f)
        global_name_refs.update(refs.name_refs)
        global_attr_refs.update(refs.attr_refs)

    # Phase 3: cross-reference
    unused: list[FunctionDef] = []
    excluded_count = 0

    for func_def in all_defs:
        if func_def.excluded:
            excluded_count += 1
            continue

        if include_private_only and not func_def.is_private:
            continue

        # Skip __init__.py definitions (likely package exports)
        if _is_init_export(func_def):
            continue

        # A function is "used" if its short name appears anywhere as a reference
        if func_def.name in global_name_refs:
            continue

        # For methods, also check ClassName.method and self.method patterns
        if func_def.class_name:
            dotted = f"{func_def.class_name}.{func_def.name}"
            if dotted in global_attr_refs or dotted in global_name_refs:
                continue
            if f"self.{func_def.name}" in global_attr_refs:
                continue
            if f"cls.{func_def.name}" in global_attr_refs:
                continue

        unused.append(func_def)

    # Sort: public functions first (higher priority), then by file path
    unused.sort(key=lambda d: (d.is_private, d.file_path, d.line))

    results_capped = len(unused) > max_results
    unused_capped = unused[:max_results]

    # Build per-file groups for readability
    by_file: dict[str, list[dict[str, Any]]] = {}
    for func_def in unused_capped:
        entry = {
            "name": func_def.name,
            "full_name": func_def.full_name,
            "class": func_def.class_name,
            "file": func_def.file_path,
            "line": func_def.line,
            "is_private": func_def.is_private,
            "is_method": func_def.is_method,
        }
        by_file.setdefault(func_def.file_path, []).append(entry)

    files_affected = len(by_file)

    return {
        "summary": {
            "total_issues": len(unused),
            "files_affected": files_affected,
            "total_definitions_scanned": len(all_defs),
            "excluded_by_marker": excluded_count,
        },
        "details": {
            "total_definitions_scanned": len(all_defs),
            "total_files_scanned": len(files),
            "unused_count": len(unused),
            "excluded_by_marker": excluded_count,
            "results_capped": results_capped,
            "max_results": max_results,
            "unused_functions": [
                {
                    "name": d.name,
                    "full_name": d.full_name,
                    "class": d.class_name,
                    "file": d.file_path,
                    "line": d.line,
                    "is_private": d.is_private,
                    "is_method": d.is_method,
                }
                for d in unused_capped
            ],
            "by_file": by_file,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect unused/uncalled functions and methods in the codebase."
    )
    parser.add_argument(
        "--include-tests", action="store_true", help="Include test files in analysis."
    )
    parser.add_argument(
        "--include-dev-tools",
        action="store_true",
        help="Include development_tools in analysis.",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include tests and dev tools.",
    )
    parser.add_argument(
        "--private-only",
        action="store_true",
        help="Only report private (underscore-prefixed) functions.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        metavar="N",
        help="Maximum number of unused functions to report (default: 100).",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results as JSON."
    )

    args = parser.parse_args()

    inc_tests = args.include_tests or args.include_all
    inc_dev = args.include_dev_tools or args.include_all

    result = analyze_unused_functions(
        include_tests=inc_tests,
        include_dev_tools=inc_dev,
        include_private_only=args.private_only,
        max_results=args.max_results,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        summary = result.get("summary", {})
        details = result.get("details", {})
        print("Unused / Uncalled Functions")
        print("=" * 35)
        print(f"Total definitions scanned: {details.get('total_definitions_scanned', 0)}")
        print(f"Total files scanned: {details.get('total_files_scanned', 0)}")
        print(f"Excluded by marker: {details.get('excluded_by_marker', 0)}")
        print(f"Unused functions found: {summary.get('total_issues', 0)}")
        print(f"Files affected: {summary.get('files_affected', 0)}")

        if details.get("results_capped"):
            print(f"(Report capped at {details.get('max_results')}; use --max-results N for more.)")

        unused_list = details.get("unused_functions", [])
        if unused_list:
            print("\nTop unused functions:")
            for entry in unused_list[:30]:
                visibility = "private" if entry.get("is_private") else "public"
                kind = "method" if entry.get("is_method") else "function"
                print(
                    f"  - {entry['full_name']}  "
                    f"({entry['file']}:{entry['line']}) "
                    f"[{visibility} {kind}]"
                )
            if len(unused_list) > 30:
                print(f"  ... and {len(unused_list) - 30} more (use --json for full list)")
        else:
            print("\nNo unused functions detected.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
