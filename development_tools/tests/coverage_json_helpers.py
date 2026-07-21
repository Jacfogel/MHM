"""Pure helpers for coverage.json path mapping and totals recompute.

Extracted from ``run_test_coverage.py`` (V6 B-015) so metric regeneration stays
testable without pulling the full CoverageMetricsRegenerator module graph.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def coverage_path_to_rel_posix(path_key: str, project_root: Path) -> str | None:
    """Map a coverage.json file key to a project-relative posix path."""
    raw = str(path_key).replace("\\", "/")
    try:
        p = Path(path_key)
        if p.is_absolute():
            rel = p.resolve().relative_to(project_root.resolve())
            return str(rel).replace("\\", "/")
        return raw
    except ValueError:
        root_norm = str(project_root.resolve()).replace("\\", "/").rstrip("/")
        prefix = root_norm + "/"
        if raw.lower().startswith(prefix.lower()):
            return raw[len(prefix) :].replace("\\", "/")
        return None


def recompute_coverage_totals_from_files(files: dict[str, Any]) -> dict[str, Any]:
    """Build coverage.py-style totals dict from filtered file summaries."""
    num_statements = 0
    missing_lines = 0
    covered_lines = 0
    for info in files.values():
        if not isinstance(info, dict):
            continue
        summary = info.get("summary") or {}
        num_statements += int(summary.get("num_statements", 0) or 0)
        missing_lines += int(summary.get("missing_lines", 0) or 0)
        covered_lines += int(summary.get("covered_lines", 0) or 0)
    pct = round((covered_lines / num_statements * 100), 2) if num_statements else 0.0
    return {
        "covered_lines": covered_lines,
        "num_statements": num_statements,
        "missing_lines": missing_lines,
        "percent_covered": pct,
        "excluded_lines": 0,
    }
