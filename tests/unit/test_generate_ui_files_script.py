"""Unit tests for ui.generate_ui_files script."""

from __future__ import annotations

import subprocess
import importlib.util
from pathlib import Path

import pytest


_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "ui" / "generate_ui_files.py"

# Load under an isolated module name to avoid mutating shared import state.
_SPEC = importlib.util.spec_from_file_location(
    "isolated_generate_ui_files",
    _SCRIPT_PATH,
)
assert _SPEC is not None and _SPEC.loader is not None
gui_gen = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gui_gen)


@pytest.mark.unit
@pytest.mark.ui
class TestGenerateUiFilesScript:
    def test_generate_ui_file_success(self, test_data_dir, monkeypatch):
        ui_file = Path(test_data_dir) / "sample.ui"
        output_file = Path(test_data_dir) / "sample_pyqt.py"
        ui_file.write_text("<ui></ui>", encoding="utf-8")

        def _run(cmd, capture_output, text, check):
            # Simulate pyside6-uic output file.
            output_file.write_text("class Ui_Form:\n    pass\n", encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(gui_gen.subprocess, "run", _run)
        monkeypatch.setattr(gui_gen, "now_timestamp_full", lambda: "2026-03-02 05:00:00")

        assert gui_gen.generate_ui_file(str(ui_file), str(output_file)) is True
        content = output_file.read_text(encoding="utf-8")
        assert "Generated File Headers" in content
        assert "sample.ui" in content
        assert "2026-03-02 05:00:00" in content
        assert "class Ui_Form" in content

    def test_generate_ui_file_subprocess_error(self, test_data_dir, monkeypatch):
        ui_file = Path(test_data_dir) / "bad.ui"
        output_file = Path(test_data_dir) / "bad_pyqt.py"
        ui_file.write_text("<ui></ui>", encoding="utf-8")

        def _run(*args, **kwargs):
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd="pyside6-uic",
                stderr="compile failed",
            )

        monkeypatch.setattr(gui_gen.subprocess, "run", _run)
        assert gui_gen.generate_ui_file(str(ui_file), str(output_file)) is False

    def test_generate_ui_file_unexpected_error(self, test_data_dir, monkeypatch):
        ui_file = Path(test_data_dir) / "oops.ui"
        output_file = Path(test_data_dir) / "oops_pyqt.py"
        ui_file.write_text("<ui></ui>", encoding="utf-8")

        monkeypatch.setattr(gui_gen.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, "", ""))
        # Ensure file does not exist so read attempt fails.
        if output_file.exists():
            output_file.unlink()

        assert gui_gen.generate_ui_file(str(ui_file), str(output_file)) is False

    def test_generate_all_ui_files_missing_design_dir(self, test_data_dir, monkeypatch):
        fake_script = Path(test_data_dir) / "ui" / "generate_ui_files.py"
        fake_script.parent.mkdir(parents=True, exist_ok=True)
        fake_script.write_text("# fake", encoding="utf-8")
        monkeypatch.setattr(gui_gen, "__file__", str(fake_script))
        assert gui_gen.generate_all_ui_files() is False

    def test_generate_all_ui_files_no_ui_files(self, test_data_dir, monkeypatch):
        fake_script = Path(test_data_dir) / "ui" / "generate_ui_files.py"
        designs = Path(test_data_dir) / "ui" / "designs"
        designs.mkdir(parents=True, exist_ok=True)
        fake_script.parent.mkdir(parents=True, exist_ok=True)
        fake_script.write_text("# fake", encoding="utf-8")
        monkeypatch.setattr(gui_gen, "__file__", str(fake_script))
        assert gui_gen.generate_all_ui_files() is False

    def test_generate_all_ui_files_success_and_partial_failure(self, test_data_dir, monkeypatch):
        fake_script = Path(test_data_dir) / "ui" / "generate_ui_files.py"
        designs = Path(test_data_dir) / "ui" / "designs"
        generated = Path(test_data_dir) / "ui" / "generated"
        designs.mkdir(parents=True, exist_ok=True)
        fake_script.parent.mkdir(parents=True, exist_ok=True)
        fake_script.write_text("# fake", encoding="utf-8")
        (designs / "a.ui").write_text("<ui/>", encoding="utf-8")
        (designs / "b.ui").write_text("<ui/>", encoding="utf-8")
        monkeypatch.setattr(gui_gen, "__file__", str(fake_script))

        monkeypatch.setattr(gui_gen, "generate_ui_file", lambda ui, out: True)
        assert gui_gen.generate_all_ui_files() is True
        assert generated.exists()

        monkeypatch.setattr(
            gui_gen,
            "generate_ui_file",
            lambda ui, out: ui.endswith("a.ui"),
        )
        assert gui_gen.generate_all_ui_files() is False

    def test_main_argument_validation_and_exit_paths(self, test_data_dir, monkeypatch):
        ui_file = Path(test_data_dir) / "one.ui"
        ui_file.write_text("<ui/>", encoding="utf-8")

        monkeypatch.setattr(gui_gen, "generate_ui_file", lambda ui, out: True)
        monkeypatch.setattr(gui_gen.os.path, "exists", lambda path: True)

        monkeypatch.setattr(gui_gen.sys, "argv", ["prog", "not_ui.txt"])
        with pytest.raises(SystemExit):
            gui_gen.main()

        monkeypatch.setattr(gui_gen.sys, "argv", ["prog", "missing.ui"])
        monkeypatch.setattr(gui_gen.os.path, "exists", lambda path: False)
        with pytest.raises(SystemExit):
            gui_gen.main()

        monkeypatch.setattr(gui_gen.sys, "argv", ["prog", str(ui_file)])
        monkeypatch.setattr(gui_gen.os.path, "exists", lambda path: True)
        gui_gen.main()

        monkeypatch.setattr(gui_gen, "generate_ui_file", lambda ui, out: False)
        with pytest.raises(SystemExit):
            gui_gen.main()

    def test_main_generate_all_paths(self, monkeypatch):
        monkeypatch.setattr(gui_gen.sys, "argv", ["prog"])
        monkeypatch.setattr(gui_gen, "generate_all_ui_files", lambda: True)
        gui_gen.main()

        monkeypatch.setattr(gui_gen, "generate_all_ui_files", lambda: False)
        with pytest.raises(SystemExit):
            gui_gen.main()
