"""Focused tests for development_tools.shared.file_rotation (coverage + safeguards)."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tests.development_tools.conftest import load_development_tools_module


@pytest.fixture
def fr_mod():
    return load_development_tools_module("shared.file_rotation")


@pytest.mark.unit
def test_file_rotator_archive_dir_for_development_tools_named_base(tmp_path, fr_mod):
    """When base_dir ends with development_tools, archive lives under reports/archive."""
    dt = tmp_path / "development_tools"
    dt.mkdir()
    rot = fr_mod.FileRotator(base_dir=str(dt))
    assert rot.archive_dir == dt / "reports" / "archive"


@pytest.mark.unit
def test_file_rotator_archive_dir_generic_base(tmp_path, fr_mod):
    """Non-development_tools base uses base_dir/archive."""
    base = tmp_path / "out"
    base.mkdir()
    rot = fr_mod.FileRotator(base_dir=str(base))
    assert rot.archive_dir == base / "archive"


@pytest.mark.unit
def test_rotate_file_skips_when_disabled(monkeypatch, tmp_path, fr_mod):
    monkeypatch.setenv("DISABLE_LOG_ROTATION", "1")
    p = tmp_path / "a.txt"
    p.write_text("x", encoding="utf-8")
    rot = fr_mod.FileRotator(base_dir=str(tmp_path))
    assert rot.rotate_file(p) == str(p)
    assert p.exists()


@pytest.mark.unit
def test_rotate_file_no_op_when_missing(tmp_path, fr_mod, monkeypatch):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    rot = fr_mod.FileRotator(base_dir=str(tmp_path))
    missing = tmp_path / "nope.txt"
    assert rot.rotate_file(missing) == str(missing)


@pytest.mark.unit
def test_rotate_file_moves_and_archives(tmp_path, fr_mod, monkeypatch):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    rot = fr_mod.FileRotator(base_dir=str(tmp_path))
    src = tmp_path / "doc.txt"
    src.write_text("v1", encoding="utf-8")
    rot.rotate_file(src)
    assert not src.exists()
    archives = list(rot.archive_dir.glob("doc_*"))
    assert len(archives) == 1
    assert archives[0].read_text(encoding="utf-8") == "v1"


@pytest.mark.unit
def test_rotate_file_collision_appends_counter(tmp_path, fr_mod, monkeypatch):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    rot = fr_mod.FileRotator(base_dir=str(tmp_path))
    rot.rotation_suffix = "fixed"
    src = tmp_path / "x.txt"
    src.write_text("a", encoding="utf-8")
    (rot.archive_dir / "x_fixed_0001.txt").write_text("old", encoding="utf-8")
    rot.rotate_file(src, max_versions=5)
    assert not src.exists()
    assert len(list(rot.archive_dir.glob("x_*"))) >= 1


@pytest.mark.unit
def test_get_latest_archive_none_and_some(tmp_path, fr_mod, monkeypatch):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    rot = fr_mod.FileRotator(base_dir=str(tmp_path))
    assert rot.get_latest_archive("missing") is None
    a = rot.archive_dir / "foo_2020-01-01_00000001_0001.txt"
    b = rot.archive_dir / "foo_2020-01-02_00000002_0002.txt"
    a.write_text("a", encoding="utf-8")
    b.write_text("b", encoding="utf-8")
    time.sleep(0.02)
    b.touch()
    latest = rot.get_latest_archive("foo")
    assert latest is not None
    assert latest.name.startswith("foo_")


@pytest.mark.unit
def test_list_archives_orders_newest_first(tmp_path, fr_mod, monkeypatch):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    rot = fr_mod.FileRotator(base_dir=str(tmp_path))
    old = rot.archive_dir / "bar_2020-01-01_00000001_0001.txt"
    new = rot.archive_dir / "bar_2020-01-02_00000002_0002.txt"
    old.write_text("o", encoding="utf-8")
    new.write_text("n", encoding="utf-8")
    time.sleep(0.02)
    new.touch()
    listed = rot.list_archives("bar")
    assert listed[0].name.startswith("bar_2020-01-02")


@pytest.mark.unit
def test_create_output_file_writes_under_tests_tmp(tmp_path, fr_mod, monkeypatch):
    """Paths under pytest temp dirs are treated as safe test directories."""
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    out = tmp_path / "nested" / "out.txt"
    path = fr_mod.create_output_file(out, "hello", rotate=False)
    assert path.read_text(encoding="utf-8") == "hello"


@pytest.mark.unit
def test_create_output_file_resolves_relative_with_project_root(tmp_path, fr_mod, monkeypatch):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    pr = tmp_path / "proj"
    pr.mkdir()
    target = fr_mod.create_output_file(
        "rel/out.txt", "c", rotate=False, project_root=pr
    )
    assert target == pr / "rel" / "out.txt"
    assert target.read_text(encoding="utf-8") == "c"


@pytest.mark.unit
def test_create_output_file_development_tools_subdir_uses_reports_base(tmp_path, fr_mod, monkeypatch):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    dt = tmp_path / "development_tools"
    dt.mkdir()
    f = dt / "AI_STATUS.md"
    f.write_text("old", encoding="utf-8")
    fr_mod.create_output_file(f, "new", rotate=True, project_root=None)
    assert f.read_text(encoding="utf-8") == "new"
    arch = dt / "reports" / "archive"
    assert arch.exists()
    assert any(arch.glob("AI_STATUS_*"))


@pytest.mark.unit
def test_append_to_log_creates_and_appends(tmp_path, fr_mod):
    log = tmp_path / "app.log"
    fr_mod.append_to_log(str(log), "one")
    fr_mod.append_to_log(str(log), "two")
    text = log.read_text(encoding="utf-8")
    assert "one" in text and "two" in text


@pytest.mark.unit
def test_append_to_log_rotates_when_large(tmp_path, fr_mod, monkeypatch):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    log = tmp_path / "big.log"
    log.write_bytes(b"x" * (2 * 1024 * 1024))
    fr_mod.append_to_log(str(log), "tail", max_size_mb=1)
    assert log.exists()


@pytest.mark.unit
def test_create_output_file_directory_tree_name_logs_warning(tmp_path, fr_mod, monkeypatch):
    """create_output_file uses get_component_logger inside the function; patch at core.logger."""
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    p = tmp_path / "PREFIX_DIRECTORY_TREE_SUFFIX.md"
    mock_logger = MagicMock()
    with patch("core.logger.get_component_logger", return_value=mock_logger):
        fr_mod.create_output_file(p, "x", rotate=False)
    mock_logger.warning.assert_called()


@pytest.mark.unit
def test_create_output_file_static_doc_blocks_on_lock(tmp_path, fr_mod, monkeypatch):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    (tmp_path / ".git").mkdir()
    lock = tmp_path / ".audit_in_progress.lock"
    lock.write_text("1", encoding="utf-8")
    target = tmp_path / "DIRECTORY_TREE.md"
    with pytest.raises(RuntimeError, match="DIRECTORY_TREE"):
        fr_mod.create_output_file(target, "x", rotate=False, project_root=tmp_path)


@pytest.mark.unit
def test_create_output_file_resolve_oserror_falls_back(tmp_path, fr_mod, monkeypatch):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)

    real_resolve = Path.resolve

    def boom(self, *a, **kw):
        if self.name == "bad.txt":
            raise OSError("no")
        return real_resolve(self, *a, **kw)

    p = tmp_path / "bad.txt"
    with patch.object(Path, "resolve", boom):
        path = fr_mod.create_output_file(p, "ok", rotate=False)
    assert path.read_text(encoding="utf-8") == "ok"


@pytest.mark.unit
def test_create_output_file_status_blocked_in_test_to_real_project(
    tmp_path, fr_mod, monkeypatch
):
    """PYTEST_CURRENT_TEST + write toward real project root should raise."""
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "x")
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    fake_root = tmp_path / "realproj"
    (fake_root / "development_tools").mkdir(parents=True)
    status_path = fake_root / "development_tools" / "AI_STATUS.md"
    # Under pytest, paths usually match path_looks_like_test_directory; force False
    # so the real-project vs test isolation branch is exercised without leaving tests/.
    with patch.object(fr_mod, "path_looks_like_test_directory", return_value=False):
        with patch(
            "development_tools.config.config.get_project_root",
            return_value=str(fake_root),
        ):
            with pytest.raises(RuntimeError, match="Cannot write AI_STATUS"):
                fr_mod.create_output_file(
                    status_path, "x", rotate=False, project_root=None
                )


@pytest.mark.unit
def test_path_looks_like_test_directory_heuristic(fr_mod):
    assert fr_mod.path_looks_like_test_directory(Path("C:/proj/tests/unit/x.py")) is True
    assert fr_mod.path_looks_like_test_directory(Path("C:/Users/x/AppData/Local/Temp/a")) is True
    assert fr_mod.path_looks_like_test_directory(Path("C:/src/prod_only/main.py")) is False


@pytest.mark.unit
def test_cleanup_old_versions_removes_oldest(tmp_path, fr_mod, monkeypatch):
    monkeypatch.delenv("DISABLE_LOG_ROTATION", raising=False)
    rot = fr_mod.FileRotator(base_dir=str(tmp_path))
    for i in range(5):
        f = rot.archive_dir / f"z_2020-01-0{i}_000000_{i:04d}.txt"
        f.write_text(str(i), encoding="utf-8")
        time.sleep(0.01)
    rot._cleanup_old_versions("z", max_versions=2)
    remaining = list(rot.archive_dir.glob("z_*"))
    assert len(remaining) == 2
