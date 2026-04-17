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
def test_find_unmarked_treats_command_examples_heading_as_example_section() -> None:
    md = """## 2.3. Command Examples

- Use `development_tools/run_development_tools.py` to run audits.
"""
    hits = find_unmarked_example_path_lines(md)
    assert len(hits) == 1


@pytest.mark.unit
def test_find_unmarked_treats_example_code_heading_as_example_section() -> None:
    md = """## 2.4 Example Code:

Use `development_tools/shared/service/commands.py` for orchestration.
"""
    hits = find_unmarked_example_path_lines(md)
    assert len(hits) == 1


@pytest.mark.unit
def test_find_unmarked_skips_bare_filename_without_slash() -> None:
    md = """## Examples

Use `README.md` at repo root.
"""
    assert find_unmarked_example_path_lines(md) == []


@pytest.mark.unit
def test_find_unmarked_skips_marker_on_previous_line() -> None:
    md = """## Examples

[OK] This is the canonical layout.

Later we mention `core/foo.py` again without repeating the tag.
"""
    hits = find_unmarked_example_path_lines(md)
    assert hits == []


@pytest.mark.unit
def test_find_unmarked_with_marker_outside_small_window_is_flagged() -> None:
    md = """## Examples

[OK] Marker too far above for the reduced window.



Use `core/foo.py` for the hook.
"""
    hits = find_unmarked_example_path_lines(md)
    assert len(hits) == 1


@pytest.mark.unit
def test_scan_skips_changelog_named_files(tmp_path: Path) -> None:
    """Changelog bullets cite many paths; exclude *CHANGELOG*.md from advisory scan (V5 §3.0)."""
    cal = tmp_path / "CHANGELOG_DETAIL.md"
    cal.write_text(
        "## Examples\n\n- `development_tools/foo.py` did something.\n",
        encoding="utf-8",
    )
    out = scan_paths_for_example_marker_findings(
        tmp_path, ["CHANGELOG_DETAIL.md"]
    )
    assert out == {}


@pytest.mark.unit
def test_find_unmarked_skips_see_citation_bullet() -> None:
    md = """## Examples

- See `docs/guide.md` for the full checklist.
"""
    assert find_unmarked_example_path_lines(md) == []


@pytest.mark.unit
def test_changelog_heading_with_example_markers_phrase_is_ignored() -> None:
    """Changelog-style headings with 'example markers' are ignored as advisory noise."""
    md = """### 2026-01-01 - Work (example markers) **COMPLETED**

- Bullet with `core/foo.py` path.

    ## Real Examples

Run `core/bar.py` for real.
"""
    hits = find_unmarked_example_path_lines(md)
    assert hits == []


@pytest.mark.unit
def test_find_unmarked_flags_path_inside_fenced_block() -> None:
    md = """## Examples

```
Use `core/hidden.py` in legacy mode.
```
"""
    hits = find_unmarked_example_path_lines(md)
    assert len(hits) == 1


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


@pytest.mark.unit
def test_scan_paths_excludes_changelog_category(tmp_path: Path) -> None:
    changelog = tmp_path / "ai_development_docs" / "AI_CHANGELOG.md"
    changelog.parent.mkdir(parents=True, exist_ok=True)
    changelog.write_text(
        "## Command Examples\n\nUse `core/foo.py`.\n",
        encoding="utf-8",
    )
    guide = tmp_path / "guide.md"
    guide.write_text(
        "## Examples\n\nUse `core/bar.py`.\n",
        encoding="utf-8",
    )
    out = scan_paths_for_example_marker_findings(
        tmp_path,
        ["ai_development_docs/AI_CHANGELOG.md", "guide.md"],
    )
    assert "ai_development_docs/AI_CHANGELOG.md" not in out
    assert "guide.md" in out

