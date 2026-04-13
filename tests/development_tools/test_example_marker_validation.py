"""Tests for development_tools/docs/example_marker_validation.py (V5 §3.0)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools.docs.example_marker_validation import (
    find_unmarked_example_path_lines,
    scan_paths_for_example_marker_findings,
)


@pytest.mark.unit
def test_find_unmarked_flags_path_without_marker() -> None:
    md = """## 1. Examples

Use `core/foo.py` for the hook.
"""
    hits = find_unmarked_example_path_lines(md)
    assert len(hits) == 1
    assert hits[0][0] == 3


@pytest.mark.unit
def test_find_unmarked_skips_when_marker_present() -> None:
    md = """## Example Usage

[OK] `core/foo.py` is the canonical entry.
"""
    hits = find_unmarked_example_path_lines(md)
    assert hits == []


@pytest.mark.unit
def test_scan_paths_resolves_tmp_files(tmp_path: Path) -> None:
    doc = tmp_path / "guide.md"
    doc.write_text(
        "## Examples\n\nRun `tests/test_x.py` for coverage.\n",
        encoding="utf-8",
    )
    out = scan_paths_for_example_marker_findings(tmp_path, ["guide.md"])
    assert "guide.md" in out
    assert any("test_x.py" in x for x in out["guide.md"])

