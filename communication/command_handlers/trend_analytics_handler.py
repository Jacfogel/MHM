"""Trend-focused analytics command handling."""

from typing import Any

from core import checkin_analytics, error_handling

from communication.command_handlers.analytics_formatting import AnalyticsFormattingMixin
from communication.command_handlers.shared_types import InteractionResponse


class TrendAnalyticsHandler(AnalyticsFormattingMixin):
    """Handle mood and energy trend analytics."""

    @error_handling.handle_errors(
        "showing mood trends",
        default_return=InteractionResponse(
            "I'm having trouble showing mood trends. Please try again.", True
        ),
    )
    def handle_mood_trends(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show mood trends analysis."""
        days = entities.get("days", 30)

        try:
            analytics = checkin_analytics.CheckinAnalytics()
            mood_data = analytics.get_mood_trends(user_id, days)
            if "error" in mood_data:
                return InteractionResponse(
                    "You don't have enough mood data for analysis yet. Try completing some check-ins first!",
                    True,
                )

            response = f"**ðŸ˜Š Mood Trends (Last {days} days):**\n\n"
            response += f"ðŸ“ˆ **Average Mood:** {mood_data.get('average_mood', 0)}/5\n"
            response += f"ðŸ“Š **Mood Range:** {mood_data.get('min_mood', 0)} - {mood_data.get('max_mood', 0)}/5\n"
            response += f"ðŸ“‰ **Trend:** {mood_data.get('trend', 'Stable')}\n\n"

            distribution = mood_data.get("mood_distribution", {})
            if distribution:
                response += "**Mood Distribution:**\n"
                for mood_level, count in distribution.items():
                    response += f"â€¢ {mood_level}: {count} days\n"

            insights = mood_data.get("insights", [])
            if insights:
                response += "\nðŸ’¡ **Insights:**\n"
                for insight in insights[:2]:
                    response += f"â€¢ {insight}\n"

            trend_graph = self._build_trend_graph(
                mood_data.get("recent_data", []), "mood", "Mood trend"
            )
            if trend_graph:
                response += f"\n**Trend Graph:**\n{trend_graph}\n"

            return InteractionResponse(response, True)

        except Exception as e:
            error_handling.handle_ai_error(e, "showing mood trends", user_id)
            return InteractionResponse(
                "I'm having trouble showing your mood trends right now. Please try again.",
                True,
            )

    @error_handling.handle_errors(
        "showing energy trends",
        default_return=InteractionResponse(
            "I'm having trouble showing energy trends. Please try again.", True
        ),
    )
    def handle_energy_trends(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show energy trends analysis."""
        days = entities.get("days", 30)

        try:
            analytics = checkin_analytics.CheckinAnalytics()
            energy_data = analytics.get_energy_trends(user_id, days)
            if "error" in energy_data:
                return InteractionResponse(
                    "You don't have enough energy data for analysis yet. Try completing some check-ins first!",
                    True,
                )

            response = f"**âš¡ Energy Trends (Last {days} days):**\n\n"
            response += (
                f"ðŸ“ˆ **Average Energy:** {energy_data.get('average_energy', 0)}/5\n"
            )
            response += f"ðŸ“Š **Energy Range:** {energy_data.get('min_energy', 0)} - {energy_data.get('max_energy', 0)}/5\n"
            response += f"ðŸ“‰ **Trend:** {energy_data.get('trend', 'Stable')}\n\n"

            distribution = energy_data.get("energy_distribution", {})
            if distribution:
                response += "**Energy Distribution:**\n"
                for energy_level, count in distribution.items():
                    response += f"â€¢ {energy_level}: {count} days\n"

            avg_energy = energy_data.get("average_energy", 0)
            if avg_energy >= 4:
                response += "\nðŸ’¡ **Insight:** Your energy levels have been consistently high!\n"
            elif avg_energy <= 2:
                response += "\nðŸ’¡ **Insight:** Your energy levels have been low - consider rest and self-care.\n"

            trend_graph = self._build_trend_graph(
                energy_data.get("recent_data", []), "energy", "Energy trend"
            )
            if trend_graph:
                response += f"\n**Trend Graph:**\n{trend_graph}\n"

            return InteractionResponse(response, True)

        except Exception as e:
            error_handling.handle_ai_error(e, "showing energy trends", user_id)
            return InteractionResponse(
                "I'm having trouble showing your energy trends right now. Please try again.",
                True,
            )
