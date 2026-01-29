#!/usr/bin/env python3
# TOOL_TIER: supporting

"""development_tools/shared/export_docs_snapshot.py

Export Markdown documentation files into a single Markdown snapshot for LLM context.

Design goals (intentionally similar to export_code_snapshot.py)
- Runnable from any working directory.
- Defaults to scanning the project root (not the current directory).
- Excludes archived / generated output by default.
- Produces a stable, readable Markdown bundle with an index + per-file fenced blocks.

Usage (recommended)
  python development_tools/shared/export_docs_snapshot.py

Useful options
  --root <path>           Change scan root (default: project root)
  --out <path>            Output directory (default: <project_root>/archive)
  --include-hidden        Include dot-directories (e.g. .github/*.md)
  --include-archived      Include archive*/ and archived*/ directories (default: excluded)
  --include-generated     Include generated*/ directories (default: excluded)
  --exclude <glob>        Additional exclude pattern (repeatable)

Notes
- This tool is for *documentation source* only ("*.md").
- By default, we intentionally exclude:
  - any directory named "archive" / "archived" (any depth)
  - any directory named "generated" / "_generated" (any depth)
  - VCS/venv/cache/build folders

"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import sys
from pathlib import Path
from typing import Iterable, List, Sequence


# ---------------------------------------------------------------------------
# Project root detection + import bootstrap
# ---------------------------------------------------------------------------


def _find_project_root(start: Path) -> Path:
    """Walk upward from `start` to locate the repo root.

    Heuristics (any match wins):
    - README.md exists
    - core/ and development_tools/ directories exist

    Raises:
        RuntimeError if root cannot be found.
    """

    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "README.md").is_file():
            # Strong signal if it *also* has code + tools dirs.
            if (parent / "core").is_dir() and (parent / "development_tools").is_dir():
                return parent
            # Accept README alone as a fallback.
            return parent

        if (parent / "core").is_dir() and (parent / "development_tools").is_dir():
            return parent

    raise RuntimeError(
        f"Could not find project root starting from: {start}. "
        "Expected to find README.md and/or core/ + development_tools/."
    )


def _ensure_project_on_syspath(project_root: Path) -> None:
    """Allow project-relative imports when running as a script.

    This is the common reason you had to `cd` into a folder to run tools:
    Python resolves imports based on the current working directory.

    By inserting the project root, `from development_tools.shared...` works
    from anywhere.
    """

    pr = str(project_root)
    if pr not in sys.path:
        sys.path.insert(0, pr)


# ---------------------------------------------------------------------------
# Discovery + filtering
# ---------------------------------------------------------------------------

DOC_EXTENSIONS = {".md"}

# Hard exclusions that match your "ignore archived / generated entirely" rule.
# These patterns are applied to a *project-root-relative* normalized path.
BASE_EXCLUDE_GLOBS: List[str] = [
    # VCS / venv / caches
    ".git/**",
    ".venv/**",
    "**/__pycache__/**",
    "**/.pytest_cache/**",
    # Common build outputs
    "dist/**",
    "build/**",
    "node_modules/**",
    # Anything under archive/ at any depth
    "archive/**",
    "**/archive/**",
    "archived/**",
    "**/archived/**",
    # Anything under generated/ at any depth
    "generated/**",
    "**/generated/**",
    "_generated/**",
    "**/_generated/**",
]


def _normalize(path: Path) -> str:
    """Return forward-slash path for consistent matching."""

    return str(path).replace("\\", "/")


def _matches_any_glob(norm_path: str, globs: Iterable[str]) -> bool:
    for g in globs:
        # Tolerate either exact relative match or match somewhere deeper.
        if fnmatch.fnmatch(norm_path, g) or fnmatch.fnmatch(norm_path, f"*/{g}"):
            return True
    return False


def _is_hidden(rel_path: Path) -> bool:
    """True if any path component is a dot-dir or dot-file."""

    return any(part.startswith(".") for part in rel_path.parts)


def _discover_markdown_files(
    *,
    project_root: Path,
    root_dir: Path,
    exclude_globs: List[str],
    include_hidden: bool,
) -> List[Path]:
    """Discover .md files under root_dir while applying exclusions."""

    files: List[Path] = []

    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in DOC_EXTENSIONS:
            continue

        try:
            rel_to_project = path.relative_to(project_root)
        except ValueError:
            # If root_dir is outside project_root (rare), fall back to root_dir relativity.
            rel_to_project = path.relative_to(root_dir)

        norm = _normalize(rel_to_project)

        if not include_hidden and _is_hidden(rel_to_project):
            continue

        if _matches_any_glob(norm, exclude_globs):
            continue

        files.append(path)

    files.sort(key=lambda p: _normalize(p).lower())
    return files


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _write_markdown_bundle(
    *,
    project_root: Path,
    root_dir: Path,
    files: List[Path],
    output_path: Path,
) -> None:
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")

    with output_path.open("w", encoding="utf-8") as out:
        out.write("# Documentation Snapshot\n\n")
        out.write(f"- Root: `{root_dir}`\n")
        out.write(f"- Project root: `{project_root}`\n")
        out.write(f"- Generated: `{timestamp}`\n")
        out.write(f"- Files: `{len(files)}`\n\n")

        out.write("## File Index\n\n")
        for f in files:
            try:
                rel = f.relative_to(project_root).as_posix()
            except ValueError:
                rel = f.relative_to(root_dir).as_posix()
            out.write(f"- `{rel}`\n")
        out.write("\n")

        for f in files:
            try:
                rel = f.relative_to(project_root).as_posix()
            except ValueError:
                rel = f.relative_to(root_dir).as_posix()

            out.write(f"## `{rel}`\n\n")
            out.write("```md\n")
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                out.write(f"# [READ ERROR] {type(exc).__name__}: {exc}\n")
                content = ""

            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
            out.write("```\n\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="export-docs",
        description="Export Markdown documentation files into one Markdown snapshot.",
    )
    parser.add_argument(
        "--root",
        default=None,
        help=(
            "Root directory to scan. Default: project root (auto-detected from script location)."
        ),
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory (default: <project_root>/archive).",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include dot-directories (e.g., .github/*.md).",
    )
    parser.add_argument(
        "--include-archived",
        action="store_true",
        help="Include archive*/ and archived*/ directories (default: excluded).",
    )
    parser.add_argument(
        "--include-generated",
        action="store_true",
        help="Include generated*/ directories (default: excluded).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional exclude glob pattern (repeatable).",
    )

    ns = parser.parse_args(list(argv) if argv is not None else None)

    # IMPORTANT: detect root based on where the script lives (not CWD)
    script_dir = Path(__file__).resolve().parent
    project_root = _find_project_root(script_dir)
    _ensure_project_on_syspath(project_root)

    root_dir = Path(ns.root).expanduser().resolve() if ns.root else project_root
    if not root_dir.exists() or not root_dir.is_dir():
        print(f"ERROR: --root is not a directory: {root_dir}")
        return 2

    default_archive_dir = project_root / "archive"
    out_dir = Path(ns.out).expanduser().resolve() if ns.out else default_archive_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    exclude_globs = list(BASE_EXCLUDE_GLOBS)

    if ns.include_archived:
        exclude_globs = [
            g
            for g in exclude_globs
            if "archive" not in g.lower() and "archived" not in g.lower()
        ]

    if ns.include_generated:
        exclude_globs = [g for g in exclude_globs if "generated" not in g.lower()]

    for pat in ns.exclude:
        pat = (pat or "").strip()
        if pat:
            exclude_globs.append(pat)

    files = _discover_markdown_files(
        project_root=project_root,
        root_dir=root_dir,
        exclude_globs=exclude_globs,
        include_hidden=bool(ns.include_hidden),
    )

    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Build a readable, stable name from the scan root (project-root-relative if possible)
    try:
        rel_root = root_dir.relative_to(project_root).as_posix()
    except ValueError:
        rel_root = root_dir.name or "root"

    rel_root = rel_root.strip("./")
    rel_root = rel_root.replace("/", "_").replace("\\", "_")
    if not rel_root:
        rel_root = "project_root"

    output_path = out_dir / f"docs_snapshot_{rel_root}_{stamp}.md"

    _write_markdown_bundle(
        project_root=project_root,
        root_dir=root_dir,
        files=files,
        output_path=output_path,
    )

    print(f"Wrote: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
