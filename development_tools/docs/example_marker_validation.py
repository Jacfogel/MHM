#!/usr/bin/env python3
# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable
"""V5 §3.0 — optional advisory checks for example sections referencing paths without markers.

Scans markdown for headings that mention Examples / Example Usage, then flags lines in that
region that contain typical file paths in backticks but do not start with a standard
example marker ([OK], [AVOID], etc.). Pair with domain-specific analyzers; keep heuristics
conservative to avoid doc-sync noise.
"""

from __future__ import annotations

import re
from pathlib import Path

from development_tools.shared.constants import EXAMPLE_MARKERS

# Headings that open an "example" region (content until the next ## heading).
_EXAMPLE_HEADING = re.compile(
    r"^##+\s+.*\b(examples?|example usage)\b",
    re.IGNORECASE,
)

# Paths in backticks that look like repo file references (not URLs).
_PATH_IN_BACKTICKS = re.compile(r"`[^`]+\.(?:py|md|json|toml|yaml|yml|ini|cfg)`")


def _line_has_example_marker(line: str) -> bool:
    stripped = line.lstrip()
    return any(re.match(pattern, stripped) for pattern in EXAMPLE_MARKERS)


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
                if _PATH_IN_BACKTICKS.search(body) and not _line_has_example_marker(body):
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
