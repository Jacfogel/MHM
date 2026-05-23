"""Public analytics command router."""

from typing import Any

from core.error_handling import handle_errors

from communication.command_handlers import (
    checkin_analytics_handler,
    task_analytics_handler,
    trend_analytics_handler,
)
from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand


class AnalyticsHandler(InteractionHandler):
    """Route analytics intents to smaller domain-specific handlers."""

    @handle_errors("initializing analytics handler", re_raise=True)
    def __init__(self) -> None:
        """Initialize domain-specific analytics sub-handlers."""
        self.checkin_handler = checkin_analytics_handler.CheckinAnalyticsHandler()
        self.trend_handler = trend_analytics_handler.TrendAnalyticsHandler()
        self.task_handler = task_analytics_handler.TaskAnalyticsHandler()

    @handle_errors("checking if can handle analytics", default_return=False)
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent."""
        return intent in {
            "show_analytics",
            "mood_trends",
            "energy_trends",
            "habit_analysis",
            "sleep_analysis",
            "wellness_score",
            "checkin_history",
            "checkin_analysis",
            "completion_rate",
            "task_analytics",
            "task_stats",
            "quant_summary",
        }

    @handle_errors(
        "handling analytics interaction",
        default_return=InteractionResponse(
            "I'm having trouble with analytics right now. Please try again.", True
        ),
    )
    def handle(
        self, user_id: str, parsed_command: ParsedCommand
    ) -> InteractionResponse:
        """Handle analytics and insights interactions."""
        intent = parsed_command.intent
        entities = parsed_command.entities

        handlers = {
            "show_analytics": self.checkin_handler.handle_show_analytics,
            "mood_trends": self.trend_handler.handle_mood_trends,
            "energy_trends": self.trend_handler.handle_energy_trends,
            "habit_analysis": self.checkin_handler.handle_habit_analysis,
            "sleep_analysis": self.checkin_handler.handle_sleep_analysis,
            "wellness_score": self.checkin_handler.handle_wellness_score,
            "checkin_history": self.checkin_handler.handle_checkin_history,
            "checkin_analysis": self.checkin_handler.handle_checkin_analysis,
            "completion_rate": self.checkin_handler.handle_completion_rate,
            "task_analytics": self.task_handler.handle_task_analytics,
            "task_stats": self.task_handler.handle_task_stats,
            "quant_summary": self.checkin_handler.handle_quant_summary,
        }

        handler = handlers.get(intent)
        if handler:
            return handler(user_id, entities)

        return InteractionResponse(
            f"I don't understand that analytics command. Try: {', '.join(self.get_examples())}",
            True,
        )

    @handle_errors(
        "showing analytics",
        default_return=InteractionResponse(
            "I'm having trouble showing your analytics. Please try again.", True
        ),
    )
    def handle_show_analytics(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Public entry point for /analytics and similar."""
        return self.checkin_handler.handle_show_analytics(user_id, entities)

    @handle_errors(
        "showing status",
        default_return=InteractionResponse(
            "I'm having trouble showing your status. Please try again.", True
        ),
    )
    def handle_show_status(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Public entry point for /status."""
        return self.checkin_handler.handle_show_analytics(user_id, entities)

    @handle_errors(
        "getting analytics help",
        default_return="Help with analytics - view analytics and insights about your wellness patterns",
    )
    def get_help(self) -> str:
        """Get help text for analytics commands."""
        return "Help with analytics - view analytics and insights about your wellness patterns"

    @handle_errors("getting analytics examples", default_return=[])
    def get_examples(self) -> list[str]:
        """Get example commands for analytics."""
        return [
            "show analytics",
            "mood trends",
            "energy trends",
            "habit analysis",
            "sleep analysis",
            "checkin history",
            "checkin analysis",
            "completion rate",
            "task analytics",
            "task stats",
            "quant summary",
        ]
