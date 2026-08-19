# profile_handler.py

from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core import get_user_data
from checkins.checkin_data_manager import get_recent_checkins
from user.profile_service import apply_profile_updates, load_profile_sections

from communication.command_handlers.base_handler import InteractionHandler


# Lazy import to avoid circular dependency: tasks -> core -> service -> communication -> profile_handler -> tasks
@handle_errors("loading tasks module", default_return=None, re_raise=True)
def _get_tasks():
    import tasks as _tasks_mod
    return _tasks_mod


from communication.command_handlers.shared_types import (
    InteractionResponse,
    ParsedCommand,
)

# Route profile logs to command handlers component
profile_logger = get_component_logger("communication_manager")
logger = profile_logger

_PROFILE_TEXT_FALLBACK = (
    "**Your Profile:**\n"
    "- Name: Not set\n"
    "- Gender Identity: Not set\n"
    "- Email: Not set\n"
    "- Status: Unknown\n"
    "\n**Account Features:**\n"
    "- Check-ins: Unknown\n"
    "- Tasks: Unknown\n"
)


class ProfileHandler(InteractionHandler):
    """Handler for profile management interactions"""

    @handle_errors("checking if profile handler can handle intent")
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent."""
        try:
            return intent in ["show_profile", "update_profile", "profile_stats"]
        except Exception as e:
            logger.error(f"Error checking if profile handler can handle intent: {e}")
            return False

    @handle_errors(
        "handling profile interaction",
        default_return=InteractionResponse(
            "I'm having trouble with profile management right now. Please try again.",
            True,
        ),
    )
    def handle(
        self, user_id: str, parsed_command: ParsedCommand
    ) -> InteractionResponse:
        """Handle profile management interactions."""
        intent = parsed_command.intent
        entities = parsed_command.entities

        if intent == "show_profile":
            return self._handle_show_profile(user_id)
        elif intent == "update_profile":
            return self._handle_update_profile(user_id, entities)
        elif intent == "profile_stats":
            return self._handle_profile_stats(user_id)
        else:
            return InteractionResponse(
                f"I don't understand that profile command. Try: {', '.join(self.get_examples())}",
                True,
            )

    @handle_errors(
        "showing profile",
        default_return=InteractionResponse(
            "I'm having trouble loading your profile. Please try again.", True
        ),
    )
    def handle_show_profile(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Public entry point for /profile."""
        return self._handle_show_profile(user_id)

    @handle_errors("handling show profile")
    def _handle_show_profile(self, user_id: str) -> InteractionResponse:
        """Handle showing user profile with comprehensive personalization data"""
        sections = load_profile_sections(user_id, get_data=get_user_data)
        account_data = sections.account
        context_data = sections.context
        preferences_data = sections.preferences

        # Create plain-text message via formatter (clean, readable)
        response = self._format_profile_text(
            account_data, context_data, preferences_data
        )

        # Create rich data for Discord embeds
        rich_data = {"type": "profile", "title": "Your Profile", "fields": []}

        # Add basic info fields
        if context_data:
            name = context_data.get("preferred_name", "Not set")
            if name != "Not set":
                rich_data["fields"].append(
                    {"name": "Name", "value": name, "inline": True}
                )

            gender_identity = context_data.get("gender_identity", [])
            if gender_identity and isinstance(gender_identity, list):
                gender_str = ", ".join(gender_identity)
                rich_data["fields"].append(
                    {"name": "Gender Identity", "value": gender_str, "inline": True}
                )

        # Add feature status fields
        if account_data:
            features = account_data.get("features", {})
            checkins_enabled = features.get("checkins") == "enabled"
            tasks_enabled = features.get("task_management") == "enabled"

            rich_data["fields"].append(
                {
                    "name": "Check-ins",
                    "value": "✅ Enabled" if checkins_enabled else "❌ Disabled",
                    "inline": True,
                }
            )

            rich_data["fields"].append(
                {
                    "name": "Tasks",
                    "value": "✅ Enabled" if tasks_enabled else "❌ Disabled",
                    "inline": True,
                }
            )

        # Add health info summary
        if context_data:
            custom_fields = context_data.get("custom_fields", {})
            health_count = len(custom_fields.get("health_conditions", []))
            med_count = len(custom_fields.get("medications_treatments", []))
            allergy_count = len(custom_fields.get("allergies_sensitivities", []))

            if health_count > 0 or med_count > 0 or allergy_count > 0:
                health_summary = []
                if health_count > 0:
                    health_summary.append(f"{health_count} conditions")
                if med_count > 0:
                    health_summary.append(f"{med_count} medications")
                if allergy_count > 0:
                    health_summary.append(f"{allergy_count} allergies")

                rich_data["fields"].append(
                    {
                        "name": "Health Summary",
                        "value": ", ".join(health_summary),
                        "inline": False,
                    }
                )

        # Normalize feature field values for embeds (avoid odd glyphs)
        try:
            features = account_data.get("features", {}) if account_data else {}
            _chk = features.get("checkins") == "enabled"
            _tsk = features.get("task_management") == "enabled"
            for _f in rich_data.get("fields", []):
                if _f.get("name") == "Check-ins":
                    _f["value"] = "Enabled" if _chk else "Disabled"
                elif _f.get("name") == "Tasks":
                    _f["value"] = "Enabled" if _tsk else "Disabled"
        except Exception:
            pass

        return InteractionResponse(
            response,
            True,
            rich_data=rich_data,
            suggestions=[
                "Update my name",
                "Add health conditions",
                "Update interests",
                "Show profile stats",
            ],
        )

    @handle_errors("handling profile update")
    def _handle_update_profile(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle comprehensive profile updates"""
        if not entities:
            return InteractionResponse(
                "What would you like to update? Available fields:\n"
                "• Basic: name, gender_identity, date_of_birth\n"
                "• Health: health_conditions, medications, allergies\n"
                "• Personal: interests, goals\n"
                "• Support: loved_ones, notes_for_ai",
                completed=False,
                suggestions=[
                    "Update my name",
                    "Add health conditions",
                    "Update interests",
                    "Add goals",
                ],
            )

        result = apply_profile_updates(user_id, entities, get_data=get_user_data)
        if result.failed_field == "email":
            return InteractionResponse(
                "❌ Failed to update email. Please try again.", True
            )
        if not result.success:
            return InteractionResponse(
                "❌ Failed to update profile. Please try again.", True
            )
        if result.updates:
            response = f"✅ Profile updated: {', '.join(result.updates)}"
            return InteractionResponse(
                response,
                True,
                suggestions=[
                    "Show my profile",
                    "Add more health conditions",
                    "Update goals",
                    "Show profile stats",
                ],
            )

        return InteractionResponse(
            "No valid updates found. Please specify what you'd like to update.",
            completed=False,
            suggestions=[
                "Update my name",
                "Add health conditions",
                "Update interests",
                "Add goals",
            ],
        )

    @handle_errors("handling profile statistics")
    def _handle_profile_stats(self, user_id: str) -> InteractionResponse:
        """Handle profile statistics"""
        # Get task stats
        task_stats = _get_tasks().get_user_task_stats(user_id)

        # Get check-in stats
        recent_checkins = get_recent_checkins(user_id, limit=30)

        response = "**Your Statistics:**\n"
        response += f"📋 Active tasks: {task_stats.get('active_count', 0)}\n"
        response += f"✅ Completed tasks: {task_stats.get('completed_count', 0)}\n"
        response += (
            f"📊 Task completion rate: {task_stats.get('completion_rate', 0):.1f}%\n"
        )
        response += f"📅 Check-ins this month: {len(recent_checkins)}"

        return InteractionResponse(response, True)

    @handle_errors("formatting gender identity for profile", default_return="Not set")
    def _format_gender_identity(self, gender_identity: Any) -> str:
        """Format gender identity from a list or string."""
        try:
            if isinstance(gender_identity, list) and gender_identity:
                return ", ".join(str(g) for g in gender_identity)
            if isinstance(gender_identity, str):
                return gender_identity
            return "Not set"
        except Exception:
            return "Not set"

    @handle_errors("formatting profile health information", default_return="")
    def _format_profile_health_lines(self, context_data: dict[str, Any]) -> str:
        """Format health-related custom fields, skipping the section on error."""
        try:
            if not context_data:
                return ""
            custom_fields = context_data.get("custom_fields", {})
            field_labels = (
                ("health_conditions", "Health Conditions"),
                ("medications_treatments", "Medications/Treatments"),
                ("allergies_sensitivities", "Allergies/Sensitivities"),
            )
            lines: list[str] = []
            for key, label in field_labels:
                values = custom_fields.get(key, [])
                if values:
                    lines.append(f"- {label}: {', '.join(str(v) for v in values)}\n")
            return "".join(lines)
        except Exception as e:
            logger.warning(f"Error formatting health information: {e}")
            return ""

    @handle_errors("formatting profile list section", default_return="")
    def _format_profile_list_section(
        self,
        context_data: dict[str, Any],
        key: str,
        label: str,
        warning_noun: str,
    ) -> str:
        """Format a simple list field from context, skipping the line on error."""
        try:
            values = context_data.get(key, [])
            if values:
                return f"- {label}: {', '.join(str(v) for v in values)}\n"
            return ""
        except Exception as e:
            logger.warning(f"Error formatting {warning_noun}: {e}")
            return ""

    @handle_errors("formatting profile support network", default_return="")
    def _format_support_network_section(self, context_data: dict[str, Any]) -> str:
        """Format the first few loved-ones entries for the profile display."""
        try:
            loved_ones = context_data.get("loved_ones", [])
            if not loved_ones:
                return ""
            lines = ["- Support Network:\n"]
            for person in loved_ones[:3]:
                if not isinstance(person, dict):
                    continue
                name = person.get("name", "Unknown")
                person_type = person.get("type", "")
                relationships = person.get("relationships", [])
                rel_str = (
                    f" ({', '.join(str(r) for r in relationships)})"
                    if relationships
                    else ""
                )
                lines.append(f"  • {name} - {person_type}{rel_str}\n")
            extra = len(loved_ones) - 3
            if extra > 0:
                lines.append(f"  ... and {extra} more\n")
            return "".join(lines)
        except Exception as e:
            logger.warning(f"Error formatting loved ones: {e}")
            return ""

    @handle_errors("formatting profile notes for AI", default_return="")
    def _format_notes_for_ai_line(self, context_data: dict[str, Any]) -> str:
        """Format the first notes-for-AI value, truncated for channel display."""
        try:
            notes = context_data.get("notes_for_ai", [])
            if not notes or not notes[0]:
                return ""
            note_text = str(notes[0])
            suffix = "..." if len(note_text) > 100 else ""
            return f"- Notes for AI: {note_text[:100]}{suffix}\n"
        except Exception as e:
            logger.warning(f"Error formatting notes: {e}")
            return ""

    @handle_errors("formatting account features for profile", default_return="")
    def _format_account_features_section(self, account_data: dict[str, Any]) -> str:
        """Format the account features block, using Unknown when features cannot be read."""
        try:
            features = account_data.get("features", {}) or {}
            checkins_enabled = features.get("checkins") == "enabled"
            tasks_enabled = features.get("task_management") == "enabled"
            return (
                "\n**Account Features:**\n"
                f"- Check-ins: {'Enabled' if checkins_enabled else 'Disabled'}\n"
                f"- Tasks: {'Enabled' if tasks_enabled else 'Disabled'}\n"
            )
        except Exception as e:
            logger.warning(f"Error formatting account features: {e}")
            return (
                "\n**Account Features:**\n"
                "- Check-ins: Unknown\n"
                "- Tasks: Unknown\n"
            )

    @handle_errors("formatting profile text", default_return=_PROFILE_TEXT_FALLBACK)
    def _format_profile_text(
        self,
        account_data: dict[str, Any],
        context_data: dict[str, Any],
        preferences_data: dict[str, Any],
    ) -> str:
        """Create a clean, readable profile string for channels like Discord."""
        context_data = context_data or {}
        account_data = account_data or {}
        preferences_data = preferences_data or {}

        name = context_data.get("preferred_name") or "Not set"
        date_of_birth = context_data.get("date_of_birth")
        email = account_data.get("email") or "Not set"
        status = account_data.get("account_status") or "Unknown"

        response = "**Your Profile:**\n"
        response += f"- Name: {name}\n"
        response += (
            f"- Gender Identity: {self._format_gender_identity(context_data.get('gender_identity', []))}\n"
        )
        if date_of_birth and date_of_birth != "Not set":
            response += f"- Date of Birth: {date_of_birth}\n"
        response += f"- Email: {email}\n"
        response += f"- Status: {status}\n"
        response += self._format_profile_health_lines(context_data)
        response += self._format_profile_list_section(
            context_data, "interests", "Interests", "interests"
        )
        response += self._format_profile_list_section(
            context_data, "goals", "Goals", "goals"
        )
        response += self._format_support_network_section(context_data)
        response += self._format_notes_for_ai_line(context_data)
        response += self._format_account_features_section(account_data)
        return response

    @handle_errors("getting profile handler help")
    def get_help(self) -> str:
        """Get help text for profile management commands."""
        try:
            return "Help with profile management - view and update your information"
        except Exception as e:
            logger.error(f"Error getting profile handler help: {e}")
            return "Profile management help unavailable."

    @handle_errors("getting profile handler examples")
    def get_examples(self) -> list[str]:
        """Get example commands for profile management."""
        try:
            return [
                "show profile",
                "update name 'Julie'",
                "update gender_identity 'Non-binary, Woman'",
                "add health_conditions 'Depression, Anxiety'",
                "update interests 'Reading, Gaming, Hiking'",
                "add goals 'mental_health, career'",
                "add loved_ones 'Mom - Family - Mother, Support'",
                "update notes_for_ai 'I prefer gentle reminders'",
                "profile stats",
            ]
        except Exception as e:
            logger.error(f"Error getting profile handler examples: {e}")
            return ["show profile", "update profile"]
