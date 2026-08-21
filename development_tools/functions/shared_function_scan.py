# TOOL_TIER: core

"""Shared Python parse for function-analysis audit tools.

Audit used to walk and ``ast.parse`` the same files in ``analyze_functions``,
``analyze_function_patterns``, ``decision_support``, duplicates, unused,
facades, and refactor. This module discovers and parses each file once so
those tools can reuse the trees.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from development_tools.shared.logging import get_dev_tools_logger
from development_tools.shared.standard_exclusions import should_exclude_file

try:
    from .. import config
except ImportError:
    from development_tools import config

config.load_external_config()

logger = get_dev_tools_logger("development_tools")


@dataclass(frozen=True)
class ParsedModule:
    """One parsed project Python file. Treat ``tree`` as read-only."""

    path: Path
    relative: str
    source: str
    tree: ast.AST


@dataclass(frozen=True)
class SharedFunctionScan:
    """In-memory parse of the function-analysis file set for one audit run."""

    root: Path
    modules: tuple[ParsedModule, ...]
    include_tests: bool
    include_dev_tools: bool
    context: str


def _analysis_context(*, include_tests: bool, include_dev_tools: bool) -> str:
    if include_tests or include_dev_tools:
        return "development"
    return "production"


def collect_python_files(
    project_root: Path | str | None = None,
    *,
    include_tests: bool = False,
    include_dev_tools: bool = False,
    scan_directories: list[str] | None = None,
    apply_exclusions: bool = True,
) -> list[Path]:
    """Return Python files using the same discovery as ``scan_all_functions``."""
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(config.get_project_root()).resolve()
    )
    scan_dirs = (
        list(scan_directories)
        if scan_directories is not None
        else list(config.get_scan_directories())
    )
    if include_tests and "tests" not in scan_dirs:
        scan_dirs.append("tests")
    if include_dev_tools and "development_tools" not in scan_dirs:
        scan_dirs.append("development_tools")

    context = _analysis_context(
        include_tests=include_tests, include_dev_tools=include_dev_tools
    )
    files: list[Path] = []
    seen: set[Path] = set()

    for scan_dir in scan_dirs:
        dir_path = root / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            if apply_exclusions and should_exclude_file(
                str(py_file), "analysis", context
            ):
                continue
            resolved = py_file.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(resolved)

    for py_file in root.glob("*.py"):
        if apply_exclusions and should_exclude_file(str(py_file), "analysis", context):
            continue
        resolved = py_file.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        files.append(resolved)

    return files


def _relative_key(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return path.name.replace("\\", "/")


def parse_python_modules(files: list[Path], root: Path) -> tuple[ParsedModule, ...]:
    """Read and parse each file once. Skip files that cannot be parsed."""
    modules: list[ParsedModule] = []
    for py_file in files:
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception as exc:
            logger.debug("Skipping unreadable/unparseable file %s: %s", py_file, exc)
            continue
        modules.append(
            ParsedModule(
                path=py_file,
                relative=_relative_key(py_file, root),
                source=source,
                tree=tree,
            )
        )
    return tuple(modules)


def build_shared_function_scan(
    project_root: Path | str | None = None,
    *,
    include_tests: bool = False,
    include_dev_tools: bool = False,
    scan_directories: list[str] | None = None,
    apply_exclusions: bool = True,
) -> SharedFunctionScan:
    """Discover and parse the function-analysis file set once."""
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(config.get_project_root()).resolve()
    )
    context = _analysis_context(
        include_tests=include_tests, include_dev_tools=include_dev_tools
    )
    files = collect_python_files(
        root,
        include_tests=include_tests,
        include_dev_tools=include_dev_tools,
        scan_directories=scan_directories,
        apply_exclusions=apply_exclusions,
    )
    modules = parse_python_modules(files, root)
    logger.info(
        "Shared function scan parsed %s files (include_tests=%s include_dev_tools=%s)",
        len(modules),
        include_tests,
        include_dev_tools,
    )
    return SharedFunctionScan(
        root=root,
        modules=modules,
        include_tests=include_tests,
        include_dev_tools=include_dev_tools,
        context=context,
    )
