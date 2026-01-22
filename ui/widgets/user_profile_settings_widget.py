# user_profile_settings_widget.py - User profile settings widget implementation

from typing import Any

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QDate

# Import generated UI class
from ui.generated.user_profile_settings_widget_pyqt import Ui_Form_user_profile_settings

# Import core functionality
from core.logger import setup_logging, get_component_logger
from core.error_handling import handle_errors

setup_logging()
logger = get_component_logger("ui")
widget_logger = logger


class UserProfileSettingsWidget(QWidget):
    """Widget for user profile settings configuration."""

    @handle_errors("initializing user profile settings widget", default_return=None)
    def __init__(
        self,
        parent=None,
        user_id: str | None = None,
        existing_data: dict[str, Any] | None = None,
    ):
        """Initialize the object."""
        try:
            super().__init__(parent)
            self.user_id = user_id
            self.existing_data = existing_data or {}

            # Setup UI
            self.ui = Ui_Form_user_profile_settings()
            self.ui.setupUi(self)

            # Add preferred name field at the top of Basic Info
            if hasattr(self.ui, "verticalLayout_basic_info") and not hasattr(
                self.ui, "lineEdit_preferred_name"
            ):
                from PySide6.QtWidgets import QLineEdit, QLabel

                self.ui.label_preferred_name = QLabel("Preferred Name:")
                self.ui.lineEdit_preferred_name = QLineEdit()
                self.ui.lineEdit_preferred_name.setObjectName("lineEdit_preferred_name")
                self.ui.verticalLayout_basic_info.insertWidget(
                    0, self.ui.label_preferred_name
                )
                self.ui.verticalLayout_basic_info.insertWidget(
                    1, self.ui.lineEdit_preferred_name
                )

            # Populate timezone options
            self.populate_timezones()

            # ----------------------------------------------------------
            # Setup dynamic list containers using Designer-created scroll areas
            # ----------------------------------------------------------
            try:
                from ui.widgets.dynamic_list_container import DynamicListContainer

                # Interests tab - replace content in existing scroll area
                self.interests_container = DynamicListContainer(
                    parent=self.ui.scrollAreaWidgetContents_interests,
                    field_key="interests",
                )
                # Clear existing layout and add dynamic container
                layout = self.ui.scrollAreaWidgetContents_interests.layout()
                if layout:
                    # Remove all existing widgets
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().setParent(None)
                else:
                    layout = QVBoxLayout()
                    self.ui.scrollAreaWidgetContents_interests.setLayout(layout)

                layout.addWidget(self.interests_container)

                # Health & Medical tab - replace content in existing scroll areas
                self.health_conditions_container = DynamicListContainer(
                    parent=self.ui.scrollAreaWidgetContents_medical,
                    field_key="health_conditions",
                )
                layout = self.ui.scrollAreaWidgetContents_medical.layout()
                if layout:
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().setParent(None)
                else:
                    layout = QVBoxLayout()
                    self.ui.scrollAreaWidgetContents_medical.setLayout(layout)
                layout.addWidget(self.health_conditions_container)

                self.allergies_container = DynamicListContainer(
                    parent=self.ui.scrollAreaWidgetContents_allergies,
                    field_key="allergies_sensitivities",
                )
                layout = self.ui.scrollAreaWidgetContents_allergies.layout()
                if layout:
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().setParent(None)
                else:
                    layout = QVBoxLayout()
                    self.ui.scrollAreaWidgetContents_allergies.setLayout(layout)
                layout.addWidget(self.allergies_container)

                # Medications & Reminders tab - replace content in existing scroll areas
                self.medications_container = DynamicListContainer(
                    parent=self.ui.scrollAreaWidgetContents_medications,
                    field_key="medications",
                )
                layout = self.ui.scrollAreaWidgetContents_medications.layout()
                if layout:
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().setParent(None)
                else:
                    layout = QVBoxLayout()
                    self.ui.scrollAreaWidgetContents_medications.setLayout(layout)
                layout.addWidget(self.medications_container)

                # Goals tab - replace content in existing scroll areas
                self.goals_container = DynamicListContainer(
                    parent=self.ui.scrollAreaWidgetContents_goals, field_key="goals"
                )
                layout = self.ui.scrollAreaWidgetContents_goals.layout()
                if layout:
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().setParent(None)
                else:
                    layout = QVBoxLayout()
                    self.ui.scrollAreaWidgetContents_goals.setLayout(layout)
                layout.addWidget(self.goals_container)

            except Exception as e:
                logger.error(f"Failed to set up DynamicListContainer: {e}")

            # Set default tab to Basic Info (index 0)
            if hasattr(self.ui, "tabWidget"):
                self.ui.tabWidget.setCurrentIndex(0)

            # Load existing data
            self.load_existing_data()
        except Exception as e:
            logger.error(f"Error initializing user profile settings widget: {e}")
            raise

    @handle_errors("populating timezones", default_return=None)
    def populate_timezones(self):
        """Populate the timezone combo box with options and enable selection."""
        try:
            pass
        except Exception as e:
            logger.error(f"Error populating timezones: {e}")
            raise

    @handle_errors("loading existing data", default_return=None)
    def load_existing_data(self):
        """Load existing personalization data into the form."""
        try:
            # Preferred Name
            if hasattr(self.ui, "lineEdit_preferred_name"):
                self.ui.lineEdit_preferred_name.setText(
                    self.existing_data.get("preferred_name", "")
                )

            # Gender Identity
            gender_identity = self.existing_data.get("gender_identity", [])
            if hasattr(self.ui, "checkBox_woman"):
                self.ui.checkBox_woman.setChecked("Woman" in gender_identity)
            if hasattr(self.ui, "checkBox_man"):
                self.ui.checkBox_man.setChecked("Man" in gender_identity)
            if hasattr(self.ui, "checkBox_nonbinary"):
                self.ui.checkBox_nonbinary.setChecked("Non-binary" in gender_identity)
            if hasattr(self.ui, "checkBox_none"):
                self.ui.checkBox_none.setChecked("None" in gender_identity)
            if hasattr(self.ui, "checkBox_prefer_not_to_say"):
                self.ui.checkBox_prefer_not_to_say.setChecked(
                    "Prefer not to say" in gender_identity
                )
            if hasattr(self.ui, "lineEdit_custom_gender"):
                custom_genders = [
                    g
                    for g in gender_identity
                    if g
                    not in ["Woman", "Man", "Non-binary", "None", "Prefer not to say"]
                ]
                self.ui.lineEdit_custom_gender.setText(", ".join(custom_genders))

            # Health conditions - use dynamic list container
            custom_fields = self.existing_data.get("custom_fields", {})
            health_conditions = custom_fields.get("health_conditions", [])
            if hasattr(self, "health_conditions_container"):
                self.health_conditions_container.set_values(health_conditions)

            # Medications - use dynamic list container
            medications = custom_fields.get("medications_treatments", [])
            if hasattr(self, "medications_container"):
                self.medications_container.set_values(medications)

            # Allergies/Sensitivities - use dynamic list container
            allergies = custom_fields.get("allergies_sensitivities", [])
            if hasattr(self, "allergies_container"):
                self.allergies_container.set_values(allergies)

            # Goals - use dynamic list container
            goals = self.existing_data.get("goals", [])
            if hasattr(self, "goals_container"):
                self.goals_container.set_values(goals)

            # Loved Ones/Support Network
            loved_ones = self.existing_data.get("loved_ones", [])
            if hasattr(self.ui, "textEdit_loved_ones"):
                lines = []
                for entry in loved_ones:
                    if isinstance(entry, dict):
                        name = entry.get("name", "")
                        type_val = entry.get("type", "")
                        relationships = entry.get("relationships", [])
                        line = name
                        if type_val:
                            line += f" - {type_val}"
                        if relationships:
                            line += f' - {" ,".join(relationships)}'
                        lines.append(line)
                    elif isinstance(entry, str):
                        lines.append(entry)
                self.ui.textEdit_loved_ones.setPlainText("\n".join(lines))

            # Date of Birth (if present in UI)
            if (
                hasattr(self.ui, "calendarWidget_date_of_birth")
                and "date_of_birth" in self.existing_data
            ):
                dob_str = self.existing_data["date_of_birth"]
                if dob_str:
                    try:
                        dob_date = QDate.fromString(dob_str, Qt.DateFormat.ISODate)
                        self.ui.calendarWidget_date_of_birth.setSelectedDate(dob_date)
                    except:
                        # If parsing fails, use current date
                        self.ui.calendarWidget_date_of_birth.setSelectedDate(
                            QDate.currentDate()
                        )

            # Notes (available in UI)
            if (
                hasattr(self.ui, "textEdit_notes")
                and "notes_for_ai" in self.existing_data
            ):
                notes_list = self.existing_data["notes_for_ai"]
                if notes_list and len(notes_list) > 0:
                    self.ui.textEdit_notes.setPlainText(notes_list[0])
                else:
                    self.ui.textEdit_notes.setPlainText("")

            # Interests prepopulation via container
            if hasattr(self, "interests_container"):
                existing_interests = self.existing_data.get("interests", [])
                self.interests_container.set_values(existing_interests)
        except Exception as e:
            logger.error(f"Error loading existing data: {e}")

    @handle_errors("setting checkbox group", default_return=None)
    def set_checkbox_group(self, group_name: str, values: list):
        """Set checkboxes for a specific group based on values."""
        try:
            # Map group names to UI elements (only what's available in the UI)
            group_mappings = {
                "health_conditions": [
                    ("depression", self.ui.checkBox_depression),
                    ("anxiety", self.ui.checkBox_anxiety),
                    ("adhd", self.ui.checkBox_adhd),
                    ("bipolar", self.ui.checkBox_bipolar),
                    ("ptsd", self.ui.checkBox_ptsd),
                    ("ocd", self.ui.checkBox_ocd),
                    ("eating_disorder", self.ui.checkBox_eating_disorder),
                    ("substance_abuse", self.ui.checkBox_substance_abuse),
                    ("sleep_disorder", self.ui.checkBox_sleep_disorder),
                    ("chronic_pain", self.ui.checkBox_chronic_pain),
                    ("autism", self.ui.checkBox_autism),
                    ("other_mental_health", self.ui.checkBox_other_mental_health),
                ],
                "interests": [
                    ("reading", self.ui.checkBox_reading),
                    ("writing", self.ui.checkBox_writing),
                    ("music", self.ui.checkBox_music),
                    ("art", self.ui.checkBox_art),
                    ("gaming", self.ui.checkBox_gaming),
                    ("cooking", self.ui.checkBox_cooking),
                    ("exercise", self.ui.checkBox_exercise),
                    ("nature", self.ui.checkBox_nature),
                    ("technology", self.ui.checkBox_technology),
                    ("photography", self.ui.checkBox_photography),
                    ("travel", self.ui.checkBox_travel),
                    ("volunteering", self.ui.checkBox_volunteering),
                ],
            }

            if group_name in group_mappings:
                for value, checkbox in group_mappings[group_name]:
                    checkbox.setChecked(value in values)

        except Exception as e:
            logger.error(f"Error setting checkbox group {group_name}: {e}")

    @handle_errors("getting personalization data", default_return={})
    def get_personalization_data(self) -> dict[str, Any]:
        """Get all personalization data from the form, preserving existing data structure."""
        try:
            # Start with existing data to preserve fields we don't handle yet
            data = self.existing_data.copy() if self.existing_data else {}

            # Extract data from UI using helper functions
            self._get_personalization_data__extract_basic_fields(data)
            self._get_personalization_data__extract_gender_identity(data)
            self._get_personalization_data__extract_date_of_birth(data)
            self._get_personalization_data__extract_dynamic_containers(data)
            self._get_personalization_data__extract_loved_ones(data)
            self._get_personalization_data__extract_notes(data)
            self._get_personalization_data__ensure_required_fields(data)

            return data
        except Exception as e:
            logger.error(f"Error getting personalization data: {e}")
            return self.existing_data or {}

    @handle_errors(
        "extracting basic fields from personalization data", default_return=None
    )
    def _get_personalization_data__extract_basic_fields(
        self, data: dict[str, Any]
    ) -> None:
        """Extract basic text fields from the UI."""
        try:
            # Preferred Name
            if hasattr(self.ui, "lineEdit_preferred_name"):
                data["preferred_name"] = self.ui.lineEdit_preferred_name.text().strip()
        except Exception as e:
            logger.error(f"Error extracting basic fields: {e}")
            raise

    @handle_errors("extracting gender identity from personalization data")
    def _get_personalization_data__extract_gender_identity(
        self, data: dict[str, Any]
    ) -> None:
        """Extract gender identity from checkboxes and custom input."""
        try:
            gender_identity = []

            # Standard gender identity checkboxes
            gender_mappings = [
                ("checkBox_woman", "Woman"),
                ("checkBox_man", "Man"),
                ("checkBox_nonbinary", "Non-binary"),
                ("checkBox_none", "None"),
                ("checkBox_prefer_not_to_say", "Prefer not to say"),
            ]

            for checkbox_attr, value in gender_mappings:
                if (
                    hasattr(self.ui, checkbox_attr)
                    and getattr(self.ui, checkbox_attr).isChecked()
                ):
                    gender_identity.append(value)

            # Custom gender identities
            if hasattr(self.ui, "lineEdit_custom_gender"):
                custom_genders = self.ui.lineEdit_custom_gender.text().strip()
                if custom_genders:
                    gender_identity.extend(
                        [g.strip() for g in custom_genders.split(",") if g.strip()]
                    )

            data["gender_identity"] = gender_identity
        except Exception as e:
            logger.error(f"Error extracting gender identity: {e}")
            raise

    @handle_errors("extracting date of birth from personalization data")
    def _get_personalization_data__extract_date_of_birth(
        self, data: dict[str, Any]
    ) -> None:
        """Extract date of birth from calendar widget with proper validation."""
        try:
            if not hasattr(self.ui, "calendarWidget_date_of_birth"):
                return

            selected_date = self.ui.calendarWidget_date_of_birth.selectedDate()
            if not selected_date.isValid():
                data["date_of_birth"] = ""
                return

            # Only save the date if it's different from the default (current date)
            # or if there was an existing date of birth
            current_date = QDate.currentDate()
            existing_dob = self.existing_data.get("date_of_birth", "")

            # Convert QDate to ISO format string
            dob_str = selected_date.toString(Qt.DateFormat.ISODate)

            # Only save if user actually selected a date (not default current date)
            # or if there was an existing date of birth that we should preserve
            if selected_date != current_date or existing_dob:
                data["date_of_birth"] = dob_str
            else:
                # Clear date if user didn't actually select one
                data["date_of_birth"] = ""
        except Exception as e:
            logger.error(f"Error extracting date of birth: {e}")
            raise

    @handle_errors("extracting dynamic containers from personalization data")
    def _get_personalization_data__extract_dynamic_containers(
        self, data: dict[str, Any]
    ) -> None:
        """Extract data from all dynamic list containers."""
        try:
            # Ensure custom_fields structure exists
            if "custom_fields" not in data:
                data["custom_fields"] = {}

            # Health conditions - use dynamic list container
            data["custom_fields"][
                "health_conditions"
            ] = self.health_conditions_container.get_values()

            # Medications - use dynamic list container
            data["custom_fields"][
                "medications_treatments"
            ] = self.medications_container.get_values()

            # Allergies/Sensitivities - use dynamic list container
            data["custom_fields"][
                "allergies_sensitivities"
            ] = self.allergies_container.get_values()

            # Interests via dynamic container
            data["interests"] = self.interests_container.get_values()

            # Goals - use dynamic list container
            data["goals"] = self.goals_container.get_values()
        except Exception as e:
            logger.error(f"Error extracting dynamic containers: {e}")
            raise

    @handle_errors("extracting loved ones from personalization data")
    def _get_personalization_data__extract_loved_ones(
        self, data: dict[str, Any]
    ) -> None:
        """Extract loved ones data from text field with structured parsing."""
        try:
            if not hasattr(self.ui, "textEdit_loved_ones"):
                return

            loved_ones_text = self.ui.textEdit_loved_ones.toPlainText().strip()
            loved_ones = []

            if loved_ones_text:
                for line in loved_ones_text.split("\n"):
                    parts = [p.strip() for p in line.split("-")]
                    name = parts[0] if len(parts) > 0 else ""
                    type_val = parts[1] if len(parts) > 1 else ""
                    relationships = []
                    if len(parts) > 2:
                        relationships = [
                            r.strip() for r in parts[2].split(",") if r.strip()
                        ]

                    if name:
                        loved_ones.append(
                            {
                                "name": name,
                                "type": type_val,
                                "relationships": relationships,
                            }
                        )

            data["loved_ones"] = loved_ones
        except Exception as e:
            logger.error(f"Error extracting loved ones: {e}")
            raise

    @handle_errors("extracting notes from personalization data")
    def _get_personalization_data__extract_notes(self, data: dict[str, Any]) -> None:
        """Extract notes for AI from text field."""
        try:
            notes_text = (
                self.ui.textEdit_notes.toPlainText().strip()
                if hasattr(self.ui, "textEdit_notes")
                else ""
            )
            notes_for_ai = [notes_text] if notes_text else []
            data["notes_for_ai"] = notes_for_ai
        except Exception as e:
            logger.error(f"Error extracting notes: {e}")
            raise

    @handle_errors("ensuring required fields in personalization data")
    def _get_personalization_data__ensure_required_fields(
        self, data: dict[str, Any]
    ) -> None:
        """Ensure all required fields exist in the data structure."""
        try:
            # Preserve other fields that we don't handle yet
            required_fields = {
                "timezone": "",
                "reminders_needed": [],
                "activities_for_encouragement": [],
                "preferred_name": "",
            }

            for field, default_value in required_fields.items():
                if field not in data:
                    data[field] = default_value
        except Exception as e:
            logger.error(f"Error ensuring required fields: {e}")
            raise

    @handle_errors("getting settings", default_return={})
    def get_settings(self):
        """Get the current user profile settings."""
        return self.get_personalization_data()

    @handle_errors("setting settings", default_return=False)
    def set_settings(self, settings):
        """Set the user profile settings."""
        self.existing_data = settings
        self.load_existing_data()
