"""Pure scope-filter helpers for report generation (V6 B-015).

Extracted from ``report_generation.ReportGenerationMixin`` so path and
dev-tools-scoped filter logic can be tested without the full service graph.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any


def path_is_under_development_tools_dir(
    path_str: str, project_root: Path
) -> bool:
    """True if ``path_str`` resolves under ``project_root/development_tools``."""
    if not path_str or not isinstance(path_str, str):
        return False
    try:
        root = Path(project_root).resolve()
        anchor = (root / "development_tools").resolve()
        raw = Path(path_str.strip())
        candidate = (raw if raw.is_absolute() else (root / path_str)).resolve()
        return anchor in candidate.parents or candidate == anchor
    except (OSError, ValueError, RuntimeError):
        norm = path_str.replace("\\", "/").strip().lstrip("./")
        return norm.startswith("development_tools/") or norm == "development_tools"


def filter_duplicate_groups_dev_tools(
    groups: list[Any],
    *,
    path_under_dev_tools: Callable[[str], bool],
) -> list[Any]:
    """Keep duplicate groups where every function maps to a file under development_tools/."""
    out: list[Any] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        funcs = group.get("functions", [])
        if not isinstance(funcs, list) or not funcs:
            continue
        paths: list[str] = []
        for fn in funcs:
            if isinstance(fn, dict):
                fp = fn.get("file", "")
                if fp:
                    paths.append(str(fp))
        if not paths:
            continue
        if all(path_under_dev_tools(p) for p in paths):
            out.append(group)
    return out


def count_duplicate_affected_files_dev_tools(
    groups: list[Any],
    *,
    path_under_dev_tools: Callable[[str], bool],
) -> int:
    """Count unique development_tools files represented by duplicate-function groups."""
    files: set[str] = set()
    for group in groups:
        if not isinstance(group, dict):
            continue
        for fn in group.get("functions", []) or []:
            if isinstance(fn, dict) and fn.get("file"):
                p = str(fn["file"])
                if path_under_dev_tools(p):
                    files.add(p.replace("\\", "/"))
    return len(files)


def count_duplicate_affected_files(groups: list[Any]) -> int:
    """Count unique files represented by duplicate-function groups."""
    files: set[str] = set()
    for group in groups:
        if not isinstance(group, dict):
            continue
        for fn in group.get("functions", []) or []:
            if not isinstance(fn, dict):
                continue
            path_value = str(fn.get("file", "")).strip()
            if path_value:
                files.add(path_value.replace("\\", "/"))
    return len(files)


def filter_circular_dependencies_dev_tools(
    chains: list[Any],
    *,
    path_under_dev_tools: Callable[[str], bool],
) -> list[Any]:
    """Keep dependency cycles that involve at least one module under development_tools/."""
    out: list[Any] = []
    for chain in chains:
        if not isinstance(chain, list):
            continue
        paths = [p for p in chain if isinstance(p, str) and p.strip()]
        if paths and any(path_under_dev_tools(p) for p in paths):
            out.append(chain)
    return out


def filter_high_coupling_dev_tools(
    items: list[Any],
    *,
    path_under_dev_tools: Callable[[str], bool],
) -> list[dict[str, Any]]:
    """Keep high-coupling items whose file is under development_tools/."""
    out: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict) and path_under_dev_tools(str(item.get("file", ""))):
            out.append(item)
    return out
