"""Installation-wide AI settings for desktop administrators."""

from PySide6.QtWidgets import QDialog, QMessageBox

from core.ai_usage_settings import (
    environment_ai_usage_settings,
    read_ai_usage_settings,
    save_ai_usage_settings,
)
from core.error_handling import handle_errors
from ui.generated.ai_controls_dialog_pyqt import Ui_AIControlsDialog


class AIControlsDialog(QDialog):
    """Edit shared global and feature-level AI controls without selecting a user."""

    @handle_errors("initializing desktop AI controls", re_raise=True)
    def __init__(self, parent=None):
        """Build the admin controls and load the effective shared settings."""
        super().__init__(parent)
        self.ui = Ui_AIControlsDialog()
        self.ui.setupUi(self)
        self.feature_controls = {
            "conversation": self.ui.conversationCheckBox,
            "command_interpretation": self.ui.commandInterpretationCheckBox,
            "personalized_messages": self.ui.personalizedMessagesCheckBox,
            "action_planning": self.ui.actionPlanningCheckBox,
            "response_enhancement": self.ui.responseEnhancementCheckBox,
            "task_breakdown": self.ui.taskBreakdownCheckBox,
            "task_effort": self.ui.taskEffortCheckBox,
        }
        settings = read_ai_usage_settings()
        self.ui.useEnvironmentCheckBox.setChecked(settings["source"] == "environment")
        self._populate_policy(settings)
        source = settings["source"]
        self.ui.sourceLabel.setText(
            "AI controls could not be read. AI is off. Save valid settings to repair them."
            if source == "invalid"
            else "Currently using environment defaults. Save an override to change AI usage here."
            if source == "environment"
            else "Currently using saved desktop admin controls."
        )
        self.ui.useEnvironmentCheckBox.toggled.connect(self._environment_changed)
        self.ui.allowAICheckBox.toggled.connect(self._sync_controls)
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.buttonBox.rejected.connect(self.reject)
        self._sync_controls()

    @handle_errors("populating desktop AI controls", re_raise=True)
    def _populate_policy(self, settings: dict) -> None:
        """Display the global switch and preserve feature choices when AI is off."""
        self.ui.allowAICheckBox.setChecked(settings["mode"] == "automatic")
        for feature, control in self.feature_controls.items():
            control.setChecked(feature not in settings["disabled_features"])

    @handle_errors("selecting environment AI defaults", default_return=None)
    def _environment_changed(self, checked: bool) -> None:
        """Preview environment defaults before the administrator saves them."""
        if checked:
            self._populate_policy(environment_ai_usage_settings())
        self._sync_controls()

    @handle_errors("updating desktop AI control availability", default_return=None)
    def _sync_controls(self, _checked: bool = False) -> None:
        """Disable inactive controls without discarding the feature selections."""
        self.ui.policyGroup.setEnabled(not self.ui.useEnvironmentCheckBox.isChecked())
        self.ui.featuresGroup.setEnabled(self.ui.allowAICheckBox.isChecked())

    @handle_errors("saving desktop AI controls dialog", default_return=None)
    def save_settings(self) -> None:
        """Persist valid choices and keep the draft open if storage fails."""
        if not save_ai_usage_settings(
            "automatic" if self.ui.allowAICheckBox.isChecked() else "off",
            [
                feature
                for feature, control in self.feature_controls.items()
                if not control.isChecked()
            ],
            use_environment=self.ui.useEnvironmentCheckBox.isChecked(),
        ):
            QMessageBox.critical(
                self,
                "AI controls were not saved",
                "Could not save AI controls. Your changes are still here. Try saving again.",
            )
            return
        self.accept()
