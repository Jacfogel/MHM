"""
Debug script for Qt UI test access violations on Windows.

Run on both PCs (working and failing) and compare output to find environment
differences. Usage (from project root, with venv active):

  python tests/debug_qt_ui_windows.py

Optionally set env vars before running to try workarounds:
  set QT_OPENGL=software
  set QT_QPA_PLATFORM=offscreen
  python tests/debug_qt_ui_windows.py

Then run the two crashing test modules (without skip) to see if they pass:
  python -m pytest tests/ui/test_checkin_settings_widget_question_counts.py tests/ui/test_dialog_coverage_expansion.py -v --tb=short
"""

from __future__ import annotations

import os
import platform
import sys


def _section(title: str) -> None:
    print(f"\n{'='*60}\n{title}\n{'='*60}")


def main() -> None:
    _section("Python")
    print(f"  executable: {sys.executable}")
    print(f"  version:    {sys.version}")

    _section("OS")
    print(f"  platform:  {sys.platform}")
    print(f"  machine:   {platform.machine()}")
    print(f"  processor: {platform.processor()}")
    print(f"  release:   {platform.release()}")
    print(f"  version:   {platform.version()}")
    if sys.platform == "win32":
        print(f"  win32_ver: {platform.win32_ver()}")

    _section("Qt / PySide6 (before any widget creation)")
    try:
        import PySide6
        from PySide6 import QtCore
        print(f"  PySide6.__file__: {getattr(PySide6, '__file__', '?')}")
        print(f"  PySide6 version:  {getattr(PySide6, '__version__', '?')}")
        print(f"  QtCore version:   {QtCore.__version__ if hasattr(QtCore, '__version__') else QtCore.qVersion()}")
    except ImportError as e:
        print(f"  Import error: {e}")
        return

    _section("Relevant env vars")
    for key in ("QT_QPA_PLATFORM", "QT_OPENGL", "QT_QUICK_BACKEND", "DISPLAY", "MHM_QT_UI_FORCE"):
        print(f"  {key}: {os.environ.get(key, '<not set>')}")

    _section("Minimal Qt widget test (QApplication + QWidget)")
    # Use same offscreen as conftest so behavior matches test runs
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    try:
        from PySide6.QtWidgets import QApplication, QWidget
        app = QApplication.instance() or QApplication([])
        w = QWidget()
        w.setWindowTitle("Minimal test")
        w.resize(100, 100)
        w.show()  # may be no-op with offscreen
        # Process events once
        QApplication.processEvents()
        w.close()
        del w
        if app != QApplication.instance():
            app.quit()
        print("  OK: Minimal QApplication + QWidget succeeded.")
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return

    _section("CheckinSettingsWidget (crash site: _setup_question_count_controls)")
    try:
        from PySide6.QtWidgets import QApplication, QSpinBox, QFormLayout, QGroupBox
        app = QApplication.instance() or QApplication([])
        grp = QGroupBox("Test")
        layout = QFormLayout(grp)
        sp = QSpinBox()
        sp.setMinimum(1)
        sp.setMaximum(50)
        layout.addRow("Min:", sp)
        sp2 = QSpinBox()
        sp2.setMinimum(1)
        sp2.setMaximum(50)
        layout.addRow("Max:", sp2)
        QApplication.processEvents()
        print("  OK: QGroupBox + QFormLayout + QSpinBox (same pattern as CheckinSettingsWidget) succeeded.")
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    _section("Done")
    print("  Compare this output with the same script on your other Windows PC.")
    print("  If 'Minimal Qt widget test' or 'CheckinSettingsWidget' FAIL here but OK there,")
    print("  differences in Qt version, GPU drivers, or Windows build may explain the crash.\n")


if __name__ == "__main__":
    main()
