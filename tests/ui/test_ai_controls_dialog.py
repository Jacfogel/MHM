"""Administrator controls save shared policy and preserve drafts on failure."""

from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication, QDialog

from core import config
from core.ai_usage_settings import read_ai_usage_settings
from ui.dialogs.ai_controls_dialog import AIControlsDialog

pytestmark = [pytest.mark.ui]


@pytest.fixture
def controls(tmp_path, monkeypatch):
    """Use real widgets backed by an isolated installation settings directory."""
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(config, "BASE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(config, "AI_USAGE_MODE", "automatic")
    monkeypatch.setattr(config, "AI_DISABLED_FEATURES", "conversation")
    dialog = AIControlsDialog()
    yield dialog
    dialog.close()
    dialog.deleteLater()
    app.processEvents()


def test_controls_are_installation_wide_and_preserve_feature_choices(controls):
    assert controls.ui.useEnvironmentCheckBox.isChecked()
    assert not controls.ui.policyGroup.isEnabled()
    assert not controls.feature_controls["conversation"].isChecked()
    controls.ui.useEnvironmentCheckBox.setChecked(False)
    controls.feature_controls["task_breakdown"].setChecked(False)
    controls.ui.allowAICheckBox.setChecked(False)
    assert not controls.ui.featuresGroup.isEnabled()
    controls.save_settings()
    saved = read_ai_usage_settings()
    assert saved["mode"] == "off"
    assert saved["disabled_features"] == ["conversation", "task_breakdown"]
    assert controls.result() == QDialog.DialogCode.Accepted
    reopened = AIControlsDialog()
    assert not reopened.ui.useEnvironmentCheckBox.isChecked()
    assert not reopened.ui.allowAICheckBox.isChecked()
    reopened.ui.allowAICheckBox.setChecked(True)
    assert not reopened.feature_controls["task_breakdown"].isChecked()
    reopened.close()


def test_cancel_does_not_change_shared_policy(controls):
    controls.ui.useEnvironmentCheckBox.setChecked(False)
    controls.ui.allowAICheckBox.setChecked(False)
    controls.reject()
    assert read_ai_usage_settings()["mode"] == "automatic"
    assert read_ai_usage_settings()["source"] == "environment"


def test_save_failure_keeps_the_draft_available(controls):
    controls.ui.useEnvironmentCheckBox.setChecked(False)
    controls.ui.allowAICheckBox.setChecked(False)
    with (
        patch(
            "ui.dialogs.ai_controls_dialog.save_ai_usage_settings", return_value=False
        ),
        patch("ui.dialogs.ai_controls_dialog.QMessageBox.critical") as warning,
    ):
        controls.save_settings()
    warning.assert_called_once()
    assert controls.result() == QDialog.DialogCode.Rejected
    assert not controls.ui.allowAICheckBox.isChecked()
    assert read_ai_usage_settings()["mode"] == "automatic"


def test_environment_option_previews_and_restores_defaults(controls):
    controls.ui.useEnvironmentCheckBox.setChecked(False)
    controls.ui.allowAICheckBox.setChecked(False)
    controls.save_settings()
    reopened = AIControlsDialog()
    reopened.ui.useEnvironmentCheckBox.setChecked(True)
    assert reopened.ui.allowAICheckBox.isChecked()
    reopened.save_settings()
    assert read_ai_usage_settings()["source"] == "environment"
    assert read_ai_usage_settings()["disabled_features"] == ["conversation"]
    reopened.close()


def test_admin_menu_opens_without_selecting_a_user(controls):
    from ui.admin_actions import AdminActions
    from ui.generated.admin_panel_pyqt import Ui_ui_app_mainwindow
    from PySide6.QtWidgets import QMainWindow

    window = QMainWindow()
    ui = Ui_ui_app_mainwindow()
    ui.setupUi(window)
    assert ui.actionAI_Controls in ui.menuAdmin.actions()
    with patch("ui.admin_actions._load_attr", return_value=AIControlsDialog) as load:
        with patch.object(
            AIControlsDialog, "exec", return_value=QDialog.DialogCode.Rejected
        ):
            AdminActions().manage_ai_controls(window)
    load.assert_called_once_with("ui.dialogs.ai_controls_dialog", "AIControlsDialog")
    window.close()


def test_admin_menu_action_is_connected_to_the_admin_dialog(controls):
    from ui.ui_app_qt import MHMManagerUI

    with patch("ui.ui_app_qt.AdminActions") as actions:
        window = MHMManagerUI()
        assert not window.current_user
        window.ui.actionAI_Controls.trigger()
        actions.return_value.manage_ai_controls.assert_called_once_with(window)
        window.status_timer.stop()
        window.close()
        window.deleteLater()
