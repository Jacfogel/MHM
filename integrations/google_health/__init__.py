"""Google Health API integration (read-only wellness data)."""

from integrations.google_health.sync_manager import sync_user_health_data

__all__ = ["sync_user_health_data"]
