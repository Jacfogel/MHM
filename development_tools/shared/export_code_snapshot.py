#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Export a directory's Python source into a single Markdown file for LLM context.

- Accepts any root directory (not tied to project root).
- Uses the standard exclusion system (base + context).
- Allows opting back in to tests and development_tools via flags.
- Writes Markdown with per-file headings + fenced code blocks.
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
from pathlib import Path
from typing import List, Sequence

from development_tools.shared.common import _get_project_root
from development_tools.shared.standard_exclusions import (
    GENERATED_FILE_PATTERNS,
    get_exclusions,
)


def _normalize_path(path: Path) -> str:
    """Return forward-slash path for consistent matching."""
    return str(path).replace("\\", "/")


def _build_exclusions(
    *,
    tool_type: str,
    context: str,
    include_tests: bool,
    include_dev_tools: bool,
    extra_excludes: Sequence[str],
) -> List[str]:
    """
    Build a final exclusion list using the standard exclusion system,
    then optionally remove test/dev-tools filters based on CLI flags.
    """
    exclusions = list(get_exclusions(tool_type, context=context))

    if include_tests:
        exclusions = [p for p in exclusions if "tests" not in p and "test_" not in p]

    if include_dev_tools:
        exclusions = [p for p in exclusions if "development_tools" not in p]

    for pat in extra_excludes:
        pat = (pat or "").strip()
        if pat:
            exclusions.append(pat)

    return exclusions


def _should_exclude(normalized_path: str, exclusions: List[str]) -> bool:
    """
    Standardized file exclusion check.

    Mirrors the intent of standard_exclusions.should_exclude_file(), but allows a
    caller-supplied exclusion list (needed for include-tests/include-dev-tools toggles).
    """
    # Generated file patterns are always excluded (ui/generated/* etc.)
    for pattern in GENERATED_FILE_PATTERNS:
        if fnmatch.fnmatch(normalized_path, pattern) or fnmatch.fnmatch(
            normalized_path, f"*/{pattern}"
        ):
            return True

    for pattern in exclusions:
        # Match both glob patterns and substring directory matches
        if fnmatch.fnmatch(normalized_path, pattern) or pattern in normalized_path:
            return True

    return False


def _discover_python_files(root_dir: Path, exclusions: List[str]) -> List[Path]:
    files: List[Path] = []
    for path in root_dir.rglob("*.py"):
        if not path.is_file():
            continue

        normalized = _normalize_path(path)

        if _should_exclude(normalized, exclusions):
            continue

        files.append(path)

    files.sort(key=lambda p: _normalize_path(p).lower())
    return files


def _write_markdown_bundle(
    root_dir: Path, files: List[Path], output_path: Path
) -> None:
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    project_root = _get_project_root()

    with output_path.open("w", encoding="utf-8") as out:
        out.write("# Code Snapshot\n\n")
        out.write(f"- Root: `{root_dir}`\n")
        out.write(f"- Generated: `{timestamp}`\n")
        out.write(f"- Files: `{len(files)}`\n\n")

        out.write("## File Index\n\n")
        for f in files:
            try:
                rel = f.relative_to(project_root).as_posix()
            except ValueError:
                # File is outside the project root; fall back to scan-root-relative
                rel = f.relative_to(root_dir).as_posix()
            out.write(f"- `{rel}`\n")
        out.write("\n")

        for f in files:
            try:
                rel = f.relative_to(project_root).as_posix()
            except ValueError:
                # File is outside the project root; fall back to scan-root-relative
                rel = f.relative_to(root_dir).as_posix()
            out.write(f"## `{rel}`\n\n")
            out.write("```py\n")
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                out.write(f"# [READ ERROR] {type(exc).__name__}: {exc}\n")
                content = ""
            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
            out.write("```\n\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="export-code",
        description="Export Python files from a directory into one Markdown snapshot.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory (default: <project_root>/archive).",
    )
    parser.add_argument(
        "--context",
        choices=["development", "testing", "production"],
        default="development",
        help="Exclusion context bucket to apply.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include tests/ paths (overrides exclusions).",
    )
    parser.add_argument(
        "--include-dev-tools",
        action="store_true",
        help="Include development_tools/ paths (overrides exclusions).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional exclude glob pattern (repeatable).",
    )

    ns = parser.parse_args(list(argv) if argv is not None else None)

    root_dir = Path(ns.root).expanduser().resolve()
    if not root_dir.exists() or not root_dir.is_dir():
        print(f"ERROR: --root is not a directory: {root_dir}")
        return 2

    project_root = _get_project_root()

    default_archive_dir = project_root / "archive"
    out_dir = Path(ns.out).expanduser().resolve() if ns.out else default_archive_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    exclusions = _build_exclusions(
        tool_type="analysis",
        context=ns.context,
        include_tests=ns.include_tests,
        include_dev_tools=ns.include_dev_tools,
        extra_excludes=ns.exclude,
    )

    files = _discover_python_files(root_dir, exclusions)

    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Build a readable, stable name from the scan root
    try:
        # Prefer full project-root-relative path
        rel_root = root_dir.relative_to(project_root).as_posix()
    except ValueError:
        # Fall back to scan-root name only if truly outside project
        rel_root = root_dir.name or "root"

    # Normalize for filesystem safety
    rel_root = rel_root.strip("./")
    rel_root = rel_root.replace("/", "_").replace("\\", "_")

    if not rel_root:
        rel_root = "project_root"

    output_path = out_dir / f"code_snapshot_{rel_root}_{stamp}.md"

    _write_markdown_bundle(root_dir, files, output_path)

    print(f"Wrote: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
