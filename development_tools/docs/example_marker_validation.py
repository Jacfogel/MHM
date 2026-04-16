#!/usr/bin/env python3
# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable
"""V5 §3.0 — optional advisory checks for example sections referencing paths without markers.

Scans markdown for headings that mention Examples / Example Usage, then flags lines in that
region that contain typical file paths in backticks but do not start with a standard
example marker ([OK], [AVOID], etc.). Pair with domain-specific analyzers; keep heuristics
conservative to avoid doc-sync noise.

Aligns with ai_development_docs/AI_DOCUMENTATION_GUIDE.md section 3.6 using an advisory
marker-nearby heuristic (windowed proximity around path lines).

Callers pass the path list (typically ``DEFAULT_DOCS`` from ``development_tools.shared.constants``,
derived from ``development_tools_config.json`` via ``get_constants_config()`` / ``fix_version_sync``).
"""

from __future__ import annotations

import re
from fnmatch import fnmatch
from pathlib import Path

from development_tools.shared.constants import EXAMPLE_MARKERS
from development_tools.shared.standard_exclusions import HISTORICAL_PRESERVE_FILES

# Headings that open an "example" region (content until the next ## heading).
# Broad on purpose: include headings like "Command Examples".
_EXAMPLE_HEADING = re.compile(r"^##+\s+.*\b(examples?|example usage)\b", re.IGNORECASE)

# Paths in backticks: repo-style (contains /) with a known extension — skips bare `foo.md`
# noise from short citations per §3.7 "full paths from project root".
_PATH_IN_BACKTICKS = re.compile(
    r"`(?=[^`]*\/)[^`]+\.(?:py|md|json|toml|yaml|yml|ini|cfg)`"
)

# Prose bullets that cite a file without implying a good/bad pattern example.
_CITATION_LINE = re.compile(
    r"^\s*[-*+]\s*(see|refer to|for (?:more )?details|read(?:\s+more)?)\b",
    re.IGNORECASE,
)

_MARKER_WINDOW = 2


def _line_has_example_marker(line: str) -> bool:
    stripped = line.lstrip()
    return any(re.match(pattern, stripped) for pattern in EXAMPLE_MARKERS)


def _marker_within_window(lines: list[str], idx: int) -> bool:
    """True if any line within ±_MARKER_WINDOW of idx starts with an example marker."""
    lo = max(0, idx - _MARKER_WINDOW)
    hi = min(len(lines), idx + _MARKER_WINDOW + 1)
    return any(_line_has_example_marker(lines[j]) for j in range(lo, hi))


def _is_changelog_style_doc(relative_path: str) -> bool:
    """Changelog files cite many backtick paths in bullets; skip advisory scan (V5 §3.0)."""
    name = Path(relative_path.replace("\\", "/")).name.lower()
    return "changelog" in name and name.endswith(".md")


def _is_excluded_example_marker_doc(relative_path: str) -> bool:
    """Use historical preserve exclusions to skip citation-heavy docs."""
    if _is_changelog_style_doc(relative_path):
        return True
    rel = relative_path.replace("\\", "/").strip()
    name = Path(rel).name
    for pattern in HISTORICAL_PRESERVE_FILES:
        p = str(pattern).replace("\\", "/").strip()
        if not p:
            continue
        # Directory-like preserve patterns
        if p.endswith("/"):
            if rel.startswith(p) or f"/{p}" in rel:
                return True
            continue
        # Glob patterns and plain filename/path entries
        if fnmatch(rel, p) or fnmatch(name, p):
            return True
    return False


def find_unmarked_example_path_lines(content: str) -> list[tuple[int, str]]:
    """Return (1-based line number, line text) for advisory review only."""
    lines = content.splitlines()
    out: list[tuple[int, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _EXAMPLE_HEADING.match(line):
            i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                body = lines[i]
                if (
                    _PATH_IN_BACKTICKS.search(body)
                    and not _CITATION_LINE.match(body)
                    and not _marker_within_window(lines, i)
                ):
                    out.append((i + 1, body))
                i += 1
            continue
        i += 1
    return out


def scan_paths_for_example_marker_findings(
    project_root: Path, relative_paths: list[str]
) -> dict[str, list[str]]:
    """Load each existing file and collect human-readable finding strings."""
    findings: dict[str, list[str]] = {}
    root = project_root.resolve()
    for rel in relative_paths:
        if _is_excluded_example_marker_doc(rel):
            continue
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        hits = find_unmarked_example_path_lines(text)
        if hits:
            findings[rel] = [f"line {n}: {txt.strip()}" for n, txt in hits]
    return findings
