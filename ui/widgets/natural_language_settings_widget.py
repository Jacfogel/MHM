# ui/widgets/natural_language_settings_widget.py
# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false

"""Widget for editing per-user natural-language phrase settings."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.natural_language_defaults import (
    NaturalLanguageDefaults,
    merge_natural_language_preferences,
    natural_language_defaults_to_preferences_dict,
)

logger = get_component_logger("ui")


class NaturalLanguageSettingsWidget(QWidget):
    """Edit phrase-to-time mappings stored under preferences.natural_language_defaults."""

    @handle_errors("initializing natural language settings widget", default_return=None)
    def __init__(self, parent=None, user_id: str | None = None):
        super().__init__(parent)
        self.user_id = user_id
        self._build_ui()

    @handle_errors("building natural language settings UI", default_return=None)
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        intro = QLabel(
            "Customize how phrases like tonight, after work, and tomorrow morning "
            "are interpreted. Times accept formats such as 6:00 PM or 18:00."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        group = QGroupBox("Phrase Mappings")
        form = QFormLayout(group)

        self.line_tonight = QLineEdit()
        self.line_after_work = QLineEdit()
        self.line_morning = QLineEdit()
        self.line_afternoon = QLineEdit()
        self.line_evening = QLineEdit()
        self.line_night = QLineEdit()

        form.addRow("Tonight starts at:", self.line_tonight)
        form.addRow("After work / school:", self.line_after_work)
        form.addRow("Morning:", self.line_morning)
        form.addRow("Afternoon:", self.line_afternoon)
        form.addRow("Evening:", self.line_evening)
        form.addRow("Night:", self.line_night)

        self.check_weekend_coming_week = QCheckBox(
            "On Sat/Sun, \"this week\" means the coming week (not the current week)"
        )
        self.check_weekend_coming_week.setTristate(False)
        form.addRow(self.check_weekend_coming_week)

        layout.addWidget(group)
        layout.addStretch(1)

    @handle_errors("loading natural language defaults into widget", default_return=None)
    def set_defaults(self, defaults: NaturalLanguageDefaults) -> None:
        """Populate fields from resolved defaults."""
        tod = defaults.time_of_day_defaults
        self.line_tonight.setText(defaults.tonight_start_time)
        self.line_after_work.setText(defaults.after_work_school_time)
        self.line_morning.setText(tod.get("morning", "9:00"))
        self.line_afternoon.setText(tod.get("afternoon", "14:00"))
        self.line_evening.setText(tod.get("evening", "18:00"))
        self.line_night.setText(tod.get("night", "21:00"))
        self.check_weekend_coming_week.setChecked(
            defaults.weekend_this_week_means_coming_week
        )

    @handle_errors("reading natural language preferences from widget", default_return={})
    def get_preferences_dict(self) -> dict:
        """Return preferences.natural_language_defaults payload from form fields."""
        raw = {
            "tonight_start_time": self.line_tonight.text().strip(),
            "after_work_school_time": self.line_after_work.text().strip(),
            "time_of_day_defaults": {
                "morning": self.line_morning.text().strip(),
                "afternoon": self.line_afternoon.text().strip(),
                "evening": self.line_evening.text().strip(),
                "night": self.line_night.text().strip(),
            },
            "weekend_this_week_means_coming_week": self.check_weekend_coming_week.isChecked(),
        }
        merged = merge_natural_language_preferences(raw)
        return natural_language_defaults_to_preferences_dict(merged)

    @handle_errors("validating natural language settings widget", default_return="")
    def validate_fields(self) -> str:
        """Return an error message when any time field is invalid, else empty string."""
        from tasks.task_time_parsing import parse_time_string

        checks = [
            ("Tonight", self.line_tonight.text().strip()),
            ("After work/school", self.line_after_work.text().strip()),
            ("Morning", self.line_morning.text().strip()),
            ("Afternoon", self.line_afternoon.text().strip()),
            ("Evening", self.line_evening.text().strip()),
            ("Night", self.line_night.text().strip()),
        ]
        for label, value in checks:
            if not value:
                return f"{label} time is required."
            if not parse_time_string(value):
                return f"Could not parse {label} time: {value}"
        return ""
