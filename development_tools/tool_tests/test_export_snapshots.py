"""Tests for development_tools.shared export snapshot helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from development_tools.shared import export_code_snapshot, export_docs_snapshot


@pytest.mark.unit
def test_export_code_build_exclusions_include_flags() -> None:
    """Include flags should remove test/dev-tools exclusions while preserving extras."""
    exclusions = export_code_snapshot._build_exclusions(
        tool_type="analysis",
        context="development",
        include_tests=True,
        include_dev_tools=True,
        extra_excludes=["custom_pattern", ""],
    )

    assert "custom_pattern" in exclusions
    assert all("tests" not in pattern and "test_" not in pattern for pattern in exclusions)
    assert all("development_tools" not in pattern for pattern in exclusions)


@pytest.mark.unit
def test_export_code_should_exclude_respects_generated_and_custom_patterns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generated patterns and explicit exclusions should both trigger filtering."""
    monkeypatch.setattr(
        export_code_snapshot,
        "GENERATED_FILE_PATTERNS",
        ("ui/generated/*",),
        raising=False,
    )

    assert export_code_snapshot._should_exclude("ui/generated/view.py", [])
    assert export_code_snapshot._should_exclude("src/tests/test_demo.py", ["tests/"])
    assert not export_code_snapshot._should_exclude("src/app/main.py", ["tests/"])


@pytest.mark.unit
def test_export_code_discover_python_files_filters_and_sorts(
    temp_output_dir: Path,
) -> None:
    """Python discovery should skip excluded paths and return sorted output."""
    root_dir = temp_output_dir / "discover_root"
    root_dir.mkdir(parents=True, exist_ok=True)
    (root_dir / "b.py").write_text("VALUE_B = 2\n", encoding="utf-8")
    (root_dir / "a.py").write_text("VALUE_A = 1\n", encoding="utf-8")
    (root_dir / "skip_dir").mkdir(parents=True, exist_ok=True)
    (root_dir / "skip_dir" / "test_skip.py").write_text("pass\n", encoding="utf-8")

    files = export_code_snapshot._discover_python_files(root_dir, ["skip_dir/"])

    assert [path.name for path in files] == ["a.py", "b.py"]


@pytest.mark.unit
def test_export_code_main_writes_snapshot(
    temp_output_dir: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Main should generate a markdown snapshot in the requested output directory."""
    root_dir = temp_output_dir / "src"
    root_dir.mkdir(parents=True, exist_ok=True)
    (root_dir / "demo.py").write_text("VALUE = 1\n", encoding="utf-8")

    out_dir = temp_output_dir / "out"
    monkeypatch.setattr(
        export_code_snapshot,
        "_build_exclusions",
        lambda **kwargs: [],
        raising=False,
    )
    rc = export_code_snapshot.main(
        [
            "--root",
            str(root_dir),
            "--out",
            str(out_dir),
            "--include-tests",
            "--include-dev-tools",
        ]
    )

    assert rc == 0
    snapshot_files = list(out_dir.glob("code_snapshot_*.md"))
    assert len(snapshot_files) == 1
    content = snapshot_files[0].read_text(encoding="utf-8")
    assert "# Code Snapshot" in content
    assert "demo.py" in content
    assert "Wrote:" in capsys.readouterr().out


@pytest.mark.unit
def test_export_docs_discover_markdown_files_excludes_hidden_and_archive(
    temp_output_dir: Path,
) -> None:
    """Markdown discovery should apply hidden/archive exclusions by default."""
    root_dir = temp_output_dir / "docs_root"
    root_dir.mkdir(parents=True, exist_ok=True)
    (root_dir / "docs").mkdir(parents=True, exist_ok=True)
    (root_dir / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
    (root_dir / ".github").mkdir(parents=True, exist_ok=True)
    (root_dir / ".github" / "workflow.md").write_text("hidden\n", encoding="utf-8")
    (root_dir / "archive").mkdir(parents=True, exist_ok=True)
    (root_dir / "archive" / "old.md").write_text("old\n", encoding="utf-8")

    files = export_docs_snapshot._discover_markdown_files(
        project_root=root_dir,
        root_dir=root_dir,
        exclude_globs=list(export_docs_snapshot.BASE_EXCLUDE_GLOBS),
        include_hidden=False,
    )

    assert [path.as_posix() for path in files] == [
        (root_dir / "docs" / "guide.md").as_posix()
    ]


@pytest.mark.unit
def test_export_docs_main_writes_snapshot(
    temp_output_dir: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Docs snapshot main should write a markdown bundle for discovered docs."""
    root_dir = temp_output_dir / "docs"
    root_dir.mkdir(parents=True, exist_ok=True)
    (root_dir / "README.md").write_text("# Demo\n", encoding="utf-8")

    out_dir = temp_output_dir / "out"
    monkeypatch.setattr(
        export_docs_snapshot,
        "_find_project_root",
        lambda start: temp_output_dir,
        raising=False,
    )
    rc = export_docs_snapshot.main(
        ["--root", str(root_dir), "--out", str(out_dir), "--include-hidden"]
    )

    assert rc == 0
    snapshot_files = list(out_dir.glob("docs_snapshot_*.md"))
    assert len(snapshot_files) == 1
    content = snapshot_files[0].read_text(encoding="utf-8")
    assert "# Documentation Snapshot" in content
    assert "README.md" in content
    assert "Wrote:" in capsys.readouterr().out


@pytest.mark.unit
def test_export_docs_find_project_root_from_core_and_tools(
    temp_output_dir: Path,
) -> None:
    root = temp_output_dir / "mini"
    (root / "core").mkdir(parents=True)
    (root / "development_tools").mkdir(parents=True)
    assert export_docs_snapshot._find_project_root(root) == root


@pytest.mark.unit
def test_export_docs_find_project_root_raises_when_unresolved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Force no README/core/dev_tools hits so walk exhausts (tmp may live under repo tests/data)."""
    leaf = tmp_path / "a" / "b"
    leaf.mkdir(parents=True)
    real_is_dir = Path.is_dir

    def is_dir(self):
        if self.name in ("core", "development_tools"):
            return False
        return real_is_dir(self)

    monkeypatch.setattr(Path, "is_file", lambda self: False)
    monkeypatch.setattr(Path, "is_dir", is_dir)
    with pytest.raises(RuntimeError, match="Could not find project root"):
        export_docs_snapshot._find_project_root(leaf)


@pytest.mark.unit
def test_export_docs_matches_any_glob() -> None:
    assert export_docs_snapshot._matches_any_glob(
        "project/archive/old.md", ["archive/*"]
    )


@pytest.mark.unit
def test_export_docs_main_invalid_root_returns_2(
    temp_output_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        export_docs_snapshot,
        "_find_project_root",
        lambda _start: temp_output_dir,
        raising=False,
    )
    rc = export_docs_snapshot.main(
        ["--root", str(temp_output_dir / "does_not_exist")]
    )
    assert rc == 2


@pytest.mark.unit
def test_export_docs_write_markdown_bundle_read_error(
    temp_output_dir: Path,
) -> None:
    root_dir = temp_output_dir / "scan"
    root_dir.mkdir(parents=True)
    bad = root_dir / "bad.md"
    bad.write_text("x", encoding="utf-8")
    out = temp_output_dir / "bundle.md"
    original_read_text = Path.read_text

    def _read_text(self, *a, **kw):
        if self.name == "bad.md":
            raise OSError("read denied")
        return original_read_text(self, *a, **kw)

    with patch.object(Path, "read_text", _read_text):
        export_docs_snapshot._write_markdown_bundle(
            project_root=root_dir,
            root_dir=root_dir,
            files=[bad],
            output_path=out,
        )
    text = out.read_text(encoding="utf-8")
    assert "[READ ERROR]" in text
    assert "OSError" in text
