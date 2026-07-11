"""Profile use-case helpers for command handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core import get_user_data, get_user_id_by_identifier, update_user_account, update_user_context
from core.error_handling import handle_errors


@dataclass(frozen=True)
class ProfileSections:
    """Loaded profile data sections."""

    account: dict[str, Any]
    context: dict[str, Any]
    preferences: dict[str, Any]


@dataclass(frozen=True)
class ProfileUpdateResult:
    """Result of applying profile updates."""

    updates: list[str]
    success: bool
    failed_field: str | None = None


@handle_errors("profile service: normalizing command list value", default_return=[])
def _list_from_command_value(value: Any) -> list[Any]:
    """Normalize a comma-separated command value to a list."""
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


@handle_errors("profile service: loading profile sections", default_return=ProfileSections({}, {}, {}))
def load_profile_sections(user_id: str, *, get_data=None) -> ProfileSections:
    """Load account, context, and preferences sections for profile display."""
    get_data = get_data or get_user_data
    account_result = get_data(user_id, "account")
    context_result = get_data(user_id, "context")
    preferences_result = get_data(user_id, "preferences")
    return ProfileSections(
        account=account_result.get("account", {}) if account_result else {},
        context=context_result.get("context", {}) if context_result else {},
        preferences=(
            preferences_result.get("preferences", {}) if preferences_result else {}
        ),
    )


@handle_errors("profile service: applying profile updates", default_return=ProfileUpdateResult([], False))
def apply_profile_updates(
    user_id: str,
    entities: dict[str, Any],
    *,
    get_data=None,
    save_context=None,
    save_account=None,
) -> ProfileUpdateResult:
    """Apply ParsedCommand profile updates to account/context storage."""
    get_data = get_data or get_user_data
    save_context = save_context or update_user_context
    save_account = save_account or update_user_account
    resolved_user_id = get_user_id_by_identifier(user_id) or user_id
    context_result = get_data(resolved_user_id, "context")
    context_data = context_result.get("context", {}) if context_result else {}
    context_data.setdefault("custom_fields", {})

    updates: list[str] = []

    if "name" in entities:
        context_data["preferred_name"] = entities["name"]
        updates.append("name")
    if "gender_identity" in entities:
        context_data["gender_identity"] = _list_from_command_value(
            entities["gender_identity"]
        )
        updates.append("gender identity")
    if "date_of_birth" in entities:
        context_data["date_of_birth"] = entities["date_of_birth"]
        updates.append("date of birth")
    if "health_conditions" in entities:
        context_data["custom_fields"]["health_conditions"] = _list_from_command_value(
            entities["health_conditions"]
        )
        updates.append("health conditions")
    if "medications" in entities:
        context_data["custom_fields"]["medications_treatments"] = _list_from_command_value(
            entities["medications"]
        )
        updates.append("medications")
    if "allergies" in entities:
        context_data["custom_fields"]["allergies_sensitivities"] = _list_from_command_value(
            entities["allergies"]
        )
        updates.append("allergies")
    if "interests" in entities:
        context_data["interests"] = _list_from_command_value(entities["interests"])
        updates.append("interests")
    if "goals" in entities:
        context_data["goals"] = _list_from_command_value(entities["goals"])
        updates.append("goals")
    if "loved_ones" in entities:
        loved_ones = entities["loved_ones"]
        if isinstance(loved_ones, str):
            loved_ones_list = []
            for line in loved_ones.split("\n"):
                parts = [part.strip() for part in line.split("-")]
                if not parts:
                    continue
                relationships = []
                if len(parts) > 2:
                    relationships = [
                        relationship.strip()
                        for relationship in parts[2].split(",")
                        if relationship.strip()
                    ]
                loved_ones_list.append(
                    {
                        "name": parts[0],
                        "type": parts[1] if len(parts) > 1 else "",
                        "relationships": relationships,
                    }
                )
            context_data["loved_ones"] = loved_ones_list
        else:
            context_data["loved_ones"] = loved_ones
        updates.append("support network")
    if "notes_for_ai" in entities:
        notes = entities["notes_for_ai"]
        context_data["notes_for_ai"] = [notes] if isinstance(notes, str) else notes
        updates.append("notes for AI")

    if "email" in entities:
        account_result = get_data(resolved_user_id, "account")
        account_data = account_result.get("account", {}) if account_result else {}
        account_data["email"] = entities["email"]
        if not save_account(resolved_user_id, account_data):
            return ProfileUpdateResult(updates, False, failed_field="email")
        updates.append("email")

    if not updates:
        return ProfileUpdateResult([], True)
    if not save_context(resolved_user_id, context_data):
        return ProfileUpdateResult(updates, False, failed_field="profile")
    return ProfileUpdateResult(updates, True)
