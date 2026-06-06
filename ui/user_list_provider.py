"""User list and category selection helpers for the admin UI."""

from importlib import import_module
from typing import Any


_lazy_dependencies = import_module("ui.lazy_dependencies")
handle_errors = _lazy_dependencies.handle_errors
get_all_user_ids = _lazy_dependencies.get_all_user_ids
get_user_data = _lazy_dependencies.get_user_data
_shared__title_case = _lazy_dependencies.shared_title_case

USER_COMBO_PLACEHOLDER = "Select a user..."
CATEGORY_COMBO_PLACEHOLDER = "Select a category..."


class UserListProvider:
    """Loads and formats user/category metadata for admin panel combo boxes."""

    @handle_errors("building enabled user features", default_return=[])
    def build_enabled_features(
        self, user_account: dict[str, Any], user_preferences: dict[str, Any]
    ) -> list[str]:
        """Return enabled feature markers for a user."""
        features = user_account.get("features", {})
        enabled_features: list[str] = []
        if features.get("automated_messages") == "enabled":
            enabled_features.append("automated_messages")
            enabled_features.extend(user_preferences.get("categories", []))
        if features.get("checkins") == "enabled":
            enabled_features.append("checkins")
        if features.get("task_management") == "enabled":
            enabled_features.append("task_management")
        return enabled_features

    @handle_errors("collecting active users for combo", default_return=[])
    def collect_active_users_for_combo(self) -> list[dict[str, Any]]:
        """Load active users and normalized display metadata."""
        users_data: list[dict[str, Any]] = []
        for user_id in get_all_user_ids():
            user_data_result = get_user_data(
                user_id, ["account", "preferences", "context"]
            )
            user_account = user_data_result.get("account", {})
            user_preferences = user_data_result.get("preferences", {})
            user_context = user_data_result.get("context", {})

            if not user_account or user_account.get("account_status") != "active":
                continue

            users_data.append(
                {
                    "user_id": user_id,
                    "internal_username": user_account.get(
                        "internal_username", "Unknown"
                    ),
                    "preferred_name": user_context.get("preferred_name", ""),
                    "channel_type": user_preferences.get("channel", {}).get(
                        "type", "unknown"
                    ),
                    "enabled_features": self.build_enabled_features(
                        user_account, user_preferences
                    ),
                }
            )
        return sorted(
            users_data,
            key=lambda item: (
                item["preferred_name"] or item["internal_username"],
                item["internal_username"],
            ),
        )

    @handle_errors("building user display name", default_return="Unknown")
    def build_user_combo_display_name(self, user_data: dict[str, Any]) -> str:
        """Create user dropdown display text including channel/features."""
        user_id = user_data["user_id"]
        internal_username = user_data["internal_username"]
        channel_type = user_data["channel_type"]
        enabled_features = user_data["enabled_features"]

        feature_summary: list[str] = []
        if "automated_messages" in enabled_features:
            categories = [
                feature
                for feature in enabled_features
                if feature not in ["automated_messages", "checkins", "task_management"]
            ]
            if categories:
                formatted_categories = [
                    _shared__title_case(cat.replace("_", " ")) for cat in categories
                ]
                feature_summary.append(f"Messages: {', '.join(formatted_categories)}")
        if "checkins" in enabled_features:
            feature_summary.append("Check-ins")
        if "task_management" in enabled_features:
            feature_summary.append("Tasks")

        feature_text = f" [{', '.join(feature_summary)}]" if feature_summary else ""
        return f"{internal_username} ({channel_type}){feature_text} - {user_id}"

    @handle_errors("collecting fallback user display names", default_return=[])
    def collect_fallback_display_names(self) -> list[str]:
        """Minimal account/context reads for combo labels when full refresh fails."""
        display_names: list[str] = []
        for user_id in get_all_user_ids():
            user_data_result = get_user_data(user_id, "account")
            user_account = user_data_result.get("account")
            internal_username = (
                user_account.get("internal_username", "Unknown")
                if user_account
                else "Unknown"
            )
            context_result = get_user_data(user_id, "context")
            user_context = context_result.get("context")
            preferred_name = (
                user_context.get("preferred_name", "") if user_context else ""
            )
            if preferred_name:
                display_names.append(
                    f"{preferred_name} ({internal_username}) - {user_id}"
                )
            else:
                display_names.append(f"{internal_username} - {user_id}")
        return display_names

    @staticmethod
    @handle_errors("parsing user id from display", default_return=None)
    def parse_user_id_from_display(user_display: str) -> str | None:
        """Extract trailing user id from combo display text."""
        if not user_display or user_display == USER_COMBO_PLACEHOLDER:
            return None
        if " - " not in user_display:
            return None
        user_id = user_display.split(" - ")[-1].strip()
        return user_id or None

    @staticmethod
    @handle_errors("finding user reselect index", default_return=None)
    def find_reselect_index(item_texts: list[str], user_id: str | None) -> int | None:
        """Return combo index for a prior user id, if still listed."""
        if not user_id:
            return None
        suffix = f" - {user_id}"
        for index, item_text in enumerate(item_texts):
            if suffix in item_text:
                return index
        return None

    @handle_errors("loading user category names", default_return=[])
    def load_category_names(self, user_id: str) -> list[str]:
        """Return category names for the selected user."""
        prefs_result = get_user_data(user_id, "preferences")
        prefs = prefs_result.get("preferences") or {}
        if not prefs or "categories" not in prefs:
            return []

        categories = prefs["categories"]
        if isinstance(categories, dict):
            return list(categories.keys())
        if isinstance(categories, list):
            return categories
        return []

    @staticmethod
    @handle_errors("formatting category display", default_return="")
    def format_category_display(category: str) -> str:
        """Format stored category key for combo display."""
        return _shared__title_case(category.replace("_", " "))
