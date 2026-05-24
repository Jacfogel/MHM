"""Channel recipient resolution for outbound delivery."""

from __future__ import annotations

from core import get_user_data
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("channel_orchestrator")


class RecipientResolver:
    """Resolve a user's channel-specific outbound recipient."""

    @handle_errors("getting recipient for service", default_return=None)
    def get_recipient_for_service(
        self, user_id: str, messaging_service: str, preferences: dict
    ) -> str | None:
        """Resolve channel recipient for a user."""
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            logger.error(f"Invalid user_id: {user_id}")
            return None

        if (
            not messaging_service
            or not isinstance(messaging_service, str)
            or not messaging_service.strip()
        ):
            logger.error(f"Invalid messaging_service: {messaging_service}")
            return None

        if not preferences or not isinstance(preferences, dict):
            logger.error(f"Invalid preferences: {preferences}")
            return None

        resolver_name = f"_resolve_{messaging_service}_recipient"
        resolver = getattr(self, resolver_name, None)
        if not callable(resolver):
            logger.error(f"Unknown messaging service: {messaging_service}")
            return None
        return resolver(user_id, preferences)

    @handle_errors("resolving Discord recipient", default_return=None)
    def _resolve_discord_recipient(
        self, user_id: str, preferences: dict
    ) -> str | None:
        """Return the Discord recipient token for outbound delivery."""
        return f"discord_user:{user_id}"

    @handle_errors("resolving email recipient", default_return=None)
    def _resolve_email_recipient(self, user_id: str, preferences: dict) -> str | None:
        """Return the user's account email address for email delivery."""
        user_data_result = get_user_data(user_id, "account", normalize_on_read=True)
        account_data = user_data_result.get("account")
        if not account_data:
            logger.error(f"User account not found for {user_id}")
            return None
        return account_data.get("email", "") if account_data else None
