# profile_handler.py

from typing import Dict, Any, List

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.user_data_handlers import get_user_data, save_user_data
from core.response_tracking import get_recent_checkins
from tasks.task_management import get_user_task_stats
from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import (
    InteractionResponse,
    ParsedCommand,
)

# Route profile logs to command handlers component
profile_logger = get_component_logger("profile_handler")
logger = profile_logger


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

    @handle_errors("handling show profile")
    def _handle_show_profile(self, user_id: str) -> InteractionResponse:
        """Handle showing user profile with comprehensive personalization data"""
        # Load user data
        account_result = get_user_data(user_id, "account")
        context_result = get_user_data(user_id, "context")
        preferences_result = get_user_data(user_id, "preferences")

        account_data = account_result.get("account", {}) if account_result else {}
        context_data = context_result.get("context", {}) if context_result else {}
        preferences_data = (
            preferences_result.get("preferences", {}) if preferences_result else {}
        )

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
        self, user_id: str, entities: Dict[str, Any]
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

        # Load current context data
        context_result = get_user_data(user_id, "context")
        context_data = context_result.get("context", {}) if context_result else {}

        # Initialize custom_fields if not present
        if "custom_fields" not in context_data:
            context_data["custom_fields"] = {}

        # Apply updates
        updates = []

        # Basic info updates
        if "name" in entities:
            context_data["preferred_name"] = entities["name"]
            updates.append("name")

        if "gender_identity" in entities:
            # Handle both string and list formats
            gender_identity = entities["gender_identity"]
            if isinstance(gender_identity, str):
                # Convert comma-separated string to list
                gender_identity = [
                    g.strip() for g in gender_identity.split(",") if g.strip()
                ]
            context_data["gender_identity"] = gender_identity
            updates.append("gender identity")

        if "date_of_birth" in entities:
            context_data["date_of_birth"] = entities["date_of_birth"]
            updates.append("date of birth")

        # Health & Medical updates
        if "health_conditions" in entities:
            health_conditions = entities["health_conditions"]
            if isinstance(health_conditions, str):
                health_conditions = [
                    h.strip() for h in health_conditions.split(",") if h.strip()
                ]
            context_data["custom_fields"]["health_conditions"] = health_conditions
            updates.append("health conditions")

        if "medications" in entities:
            medications = entities["medications"]
            if isinstance(medications, str):
                medications = [m.strip() for m in medications.split(",") if m.strip()]
            context_data["custom_fields"]["medications_treatments"] = medications
            updates.append("medications")

        if "allergies" in entities:
            allergies = entities["allergies"]
            if isinstance(allergies, str):
                allergies = [a.strip() for a in allergies.split(",") if a.strip()]
            context_data["custom_fields"]["allergies_sensitivities"] = allergies
            updates.append("allergies")

        # Personal info updates
        if "interests" in entities:
            interests = entities["interests"]
            if isinstance(interests, str):
                interests = [i.strip() for i in interests.split(",") if i.strip()]
            context_data["interests"] = interests
            updates.append("interests")

        if "goals" in entities:
            goals = entities["goals"]
            if isinstance(goals, str):
                goals = [g.strip() for g in goals.split(",") if g.strip()]
            context_data["goals"] = goals
            updates.append("goals")

        # Support network updates
        if "loved_ones" in entities:
            # Handle loved ones as a list of dictionaries or string format
            loved_ones = entities["loved_ones"]
            if isinstance(loved_ones, str):
                # Parse simple format: "Name - Type - Relationship1,Relationship2"
                loved_ones_list = []
                for line in loved_ones.split("\n"):
                    parts = [p.strip() for p in line.split("-")]
                    if len(parts) >= 1:
                        name = parts[0]
                        person_type = parts[1] if len(parts) > 1 else ""
                        relationships = []
                        if len(parts) > 2:
                            relationships = [
                                r.strip() for r in parts[2].split(",") if r.strip()
                            ]
                        loved_ones_list.append(
                            {
                                "name": name,
                                "type": person_type,
                                "relationships": relationships,
                            }
                        )
                context_data["loved_ones"] = loved_ones_list
            else:
                context_data["loved_ones"] = loved_ones
            updates.append("support network")

        if "notes_for_ai" in entities:
            notes = entities["notes_for_ai"]
            if isinstance(notes, str):
                notes = [notes]  # Store as list
            context_data["notes_for_ai"] = notes
            updates.append("notes for AI")

        # Email update (stored in account data)
        if "email" in entities:
            account_result = get_user_data(user_id, "account")
            account_data = account_result.get("account", {}) if account_result else {}
            account_data["email"] = entities["email"]
            # Save account data separately since it's stored in a different data type
            if save_user_data(user_id, "account", account_data):
                updates.append("email")
            else:
                return InteractionResponse(
                    "❌ Failed to update email. Please try again.", True
                )

        # Save updates
        if updates:
            if save_user_data(user_id, "context", context_data):
                response = f"✅ Profile updated: {', '.join(updates)}"
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
            else:
                return InteractionResponse(
                    "❌ Failed to update profile. Please try again.", True
                )
        else:
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
        task_stats = get_user_task_stats(user_id)

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

    @handle_errors("formatting profile text")
    def _format_profile_text(
        self,
        account_data: Dict[str, Any],
        context_data: Dict[str, Any],
        preferences_data: Dict[str, Any],
    ) -> str:
        """Create a clean, readable profile string for channels like Discord."""
        try:
            response = "**Your Profile:**\n"

            # Basic info - always show, even if empty
            # Ensure we have dicts, not None
            context_data = context_data or {}
            account_data = account_data or {}
            preferences_data = preferences_data or {}

            # Always add basic fields - these are required
            name = context_data.get("preferred_name") or "Not set"
            gender_identity = context_data.get("gender_identity", [])
            date_of_birth = context_data.get("date_of_birth")

            response += f"- Name: {name}\n"

            # Format gender identity (can be a list)
            try:
                if isinstance(gender_identity, list) and gender_identity:
                    gender_str = ", ".join(str(g) for g in gender_identity)
                elif isinstance(gender_identity, str):
                    gender_str = gender_identity
                else:
                    gender_str = "Not set"
            except Exception:
                gender_str = "Not set"
            response += f"- Gender Identity: {gender_str}\n"

            if date_of_birth and date_of_birth != "Not set":
                response += f"- Date of Birth: {date_of_birth}\n"

            # Account info - always show, even if empty
            email = account_data.get("email") or "Not set"
            status = account_data.get("account_status") or "Unknown"
            response += f"- Email: {email}\n"
            response += f"- Status: {status}\n"

            # Health & Medical Information
            try:
                if context_data:
                    custom_fields = context_data.get("custom_fields", {})

                    # Health conditions
                    health_conditions = custom_fields.get("health_conditions", [])
                    if health_conditions:
                        response += f"- Health Conditions: {', '.join(str(h) for h in health_conditions)}\n"

                    # Medications
                    medications = custom_fields.get("medications_treatments", [])
                    if medications:
                        response += f"- Medications/Treatments: {', '.join(str(m) for m in medications)}\n"

                    # Allergies
                    allergies = custom_fields.get("allergies_sensitivities", [])
                    if allergies:
                        response += f"- Allergies/Sensitivities: {', '.join(str(a) for a in allergies)}\n"
            except Exception as e:
                logger.warning(f"Error formatting health information: {e}")

            # Interests
            try:
                interests = context_data.get("interests", [])
                if interests:
                    response += f"- Interests: {', '.join(str(i) for i in interests)}\n"
            except Exception as e:
                logger.warning(f"Error formatting interests: {e}")

            # Goals
            try:
                goals = context_data.get("goals", [])
                if goals:
                    response += f"- Goals: {', '.join(str(g) for g in goals)}\n"
            except Exception as e:
                logger.warning(f"Error formatting goals: {e}")

            # Loved Ones/Support Network
            try:
                loved_ones = context_data.get("loved_ones", [])
                if loved_ones:
                    response += f"- Support Network:\n"
                    for person in loved_ones[:3]:  # Show first 3
                        if isinstance(person, dict):
                            name = person.get("name", "Unknown")
                            person_type = person.get("type", "")
                            relationships = person.get("relationships", [])
                            rel_str = (
                                f" ({', '.join(str(r) for r in relationships)})"
                                if relationships
                                else ""
                            )
                            response += f"  • {name} - {person_type}{rel_str}\n"
                    if len(loved_ones) > 3:
                        response += f"  ... and {len(loved_ones) - 3} more\n"
            except Exception as e:
                logger.warning(f"Error formatting loved ones: {e}")

            # Notes for AI
            try:
                notes = context_data.get("notes_for_ai", [])
                if notes and notes[0]:
                    response += f"- Notes for AI: {str(notes[0])[:100]}{'...' if len(str(notes[0])) > 100 else ''}\n"
            except Exception as e:
                logger.warning(f"Error formatting notes: {e}")

            # Account features - always show
            try:
                features = account_data.get("features", {}) or {}
                checkins_enabled = features.get("checkins") == "enabled"
                tasks_enabled = features.get("task_management") == "enabled"
                response += f"\n**Account Features:**\n"
                response += (
                    f"- Check-ins: {'Enabled' if checkins_enabled else 'Disabled'}\n"
                )
                response += f"- Tasks: {'Enabled' if tasks_enabled else 'Disabled'}\n"
            except Exception as e:
                logger.warning(f"Error formatting account features: {e}")
                # Ensure we still show account features section even on error
                response += f"\n**Account Features:**\n"
                response += f"- Check-ins: Unknown\n"
                response += f"- Tasks: Unknown\n"

            return response
        except Exception as e:
            logger.error(f"Error formatting profile text: {e}", exc_info=True)
            # Return at least the header and basic fields even on error
            try:
                fallback = "**Your Profile:**\n"
                fallback += f"- Name: Not set\n"
                fallback += f"- Gender Identity: Not set\n"
                fallback += f"- Email: Not set\n"
                fallback += f"- Status: Unknown\n"
                fallback += f"\n**Account Features:**\n"
                fallback += f"- Check-ins: Unknown\n"
                fallback += f"- Tasks: Unknown\n"
                return fallback
            except Exception:
                return "**Your Profile:**\nError loading profile information."

    @handle_errors("getting profile handler help")
    def get_help(self) -> str:
        """Get help text for profile management commands."""
        try:
            return "Help with profile management - view and update your information"
        except Exception as e:
            logger.error(f"Error getting profile handler help: {e}")
            return "Profile management help unavailable."

    @handle_errors("getting profile handler examples")
    def get_examples(self) -> List[str]:
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
