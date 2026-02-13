# analytics_handler.py

from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import (
    InteractionResponse,
    ParsedCommand,
)

# Route analytics logs to command handlers component
analytics_logger = get_component_logger("analytics_handler")
logger = analytics_logger


class AnalyticsHandler(InteractionHandler):
    """Handler for analytics and insights interactions"""

    @handle_errors("checking if can handle analytics", default_return=False)
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent."""
        return intent in [
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
        ]

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

        if intent == "show_analytics":
            return self._handle_show_analytics(user_id, entities)
        elif intent == "mood_trends":
            return self._handle_mood_trends(user_id, entities)
        elif intent == "energy_trends":
            return self._handle_energy_trends(user_id, entities)
        elif intent == "habit_analysis":
            return self._handle_habit_analysis(user_id, entities)
        elif intent == "sleep_analysis":
            return self._handle_sleep_analysis(user_id, entities)
        elif intent == "wellness_score":
            return self._handle_wellness_score(user_id, entities)
        elif intent == "checkin_history":
            return self._handle_checkin_history(user_id, entities)
        elif intent == "checkin_analysis":
            return self._handle_checkin_analysis(user_id, entities)
        elif intent == "completion_rate":
            return self._handle_completion_rate(user_id, entities)
        elif intent == "task_analytics":
            return self._handle_task_analytics(user_id, entities)
        elif intent == "task_stats":
            return self._handle_task_stats(user_id, entities)
        elif intent == "quant_summary":
            return self._handle_quant_summary(user_id, entities)
        else:
            return InteractionResponse(
                f"I don't understand that analytics command. Try: {', '.join(self.get_examples())}",
                True,
            )

    @handle_errors(
        "showing analytics overview",
        default_return=InteractionResponse(
            "I'm having trouble showing your analytics. Please try again.", True
        ),
    )
    def _handle_show_analytics(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show comprehensive analytics overview"""
        days = entities.get("days", 30)

        try:
            from core.checkin_analytics import CheckinAnalytics

            analytics = CheckinAnalytics()

            basic_data = analytics.get_basic_analytics(user_id, days)
            if "error" in basic_data:
                return InteractionResponse(
                    f"Analytics: no check-ins found in the last {days} days.",
                    True,
                )

            total_checkins = basic_data.get("total_checkins", 0)
            categories = basic_data.get("categories", {})

            response = f"**Check-in Analytics (Last {days} days):**\n\n"
            response += f"Total check-ins: {total_checkins}\n"
            response += "Based on answered questions in this period.\n"

            if not categories:
                response += "\nNo answered questions found in this time window."
                return InteractionResponse(response, True)

            for category_key, category_data in categories.items():
                category_name = category_data.get("name", category_key.title())
                response += f"\n{category_name}\n"
                for question in category_data.get("questions", []):
                    line = self._format_basic_analytics_line(question)
                    if line:
                        response += f"- {line}\n"

            response = self._truncate_response(response)
            return InteractionResponse(response, True)

        except Exception as e:
            from core.error_handling import handle_ai_error

            handle_ai_error(e, "showing analytics", user_id)
            return InteractionResponse(
                "I'm having trouble showing your analytics right now. Please try again.",
                True,
            )

    @handle_errors(
        "showing mood trends",
        default_return=InteractionResponse(
            "I'm having trouble showing mood trends. Please try again.", True
        ),
    )
    def _handle_mood_trends(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show mood trends analysis"""
        days = entities.get("days", 30)

        try:
            from core.checkin_analytics import CheckinAnalytics

            analytics = CheckinAnalytics()

            mood_data = analytics.get_mood_trends(user_id, days)
            if "error" in mood_data:
                return InteractionResponse(
                    "You don't have enough mood data for analysis yet. Try completing some check-ins first!",
                    True,
                )

            response = f"**😊 Mood Trends (Last {days} days):**\n\n"
            response += f"📈 **Average Mood:** {mood_data.get('average_mood', 0)}/5\n"
            response += f"📊 **Mood Range:** {mood_data.get('min_mood', 0)} - {mood_data.get('max_mood', 0)}/5\n"
            response += f"📉 **Trend:** {mood_data.get('trend', 'Stable')}\n\n"

            # Show mood distribution
            distribution = mood_data.get("mood_distribution", {})
            if distribution:
                response += "**Mood Distribution:**\n"
                for mood_level, count in distribution.items():
                    response += f"• {mood_level}: {count} days\n"

            # Add insights
            insights = mood_data.get("insights", [])
            if insights:
                response += "\n💡 **Insights:**\n"
                for insight in insights[:2]:  # Show top 2 insights
                    response += f"• {insight}\n"

            trend_graph = self._build_trend_graph(
                mood_data.get("recent_data", []), "mood", "Mood trend"
            )
            if trend_graph:
                response += f"\n**Trend Graph:**\n{trend_graph}\n"

            return InteractionResponse(response, True)

        except Exception as e:
            from core.error_handling import handle_ai_error

            handle_ai_error(e, "showing mood trends", user_id)
            return InteractionResponse(
                "I'm having trouble showing your mood trends right now. Please try again.",
                True,
            )

    @handle_errors(
        "showing energy trends",
        default_return=InteractionResponse(
            "I'm having trouble showing energy trends. Please try again.", True
        ),
    )
    def _handle_energy_trends(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show energy trends analysis"""
        days = entities.get("days", 30)

        try:
            from core.checkin_analytics import CheckinAnalytics

            analytics = CheckinAnalytics()

            energy_data = analytics.get_energy_trends(user_id, days)
            if "error" in energy_data:
                return InteractionResponse(
                    "You don't have enough energy data for analysis yet. Try completing some check-ins first!",
                    True,
                )

            response = f"**⚡ Energy Trends (Last {days} days):**\n\n"
            response += (
                f"📈 **Average Energy:** {energy_data.get('average_energy', 0)}/5\n"
            )
            response += f"📊 **Energy Range:** {energy_data.get('min_energy', 0)} - {energy_data.get('max_energy', 0)}/5\n"
            response += f"📉 **Trend:** {energy_data.get('trend', 'Stable')}\n\n"

            # Show energy distribution
            distribution = energy_data.get("energy_distribution", {})
            if distribution:
                response += "**Energy Distribution:**\n"
                for energy_level, count in distribution.items():
                    response += f"• {energy_level}: {count} days\n"

            # Add insights
            avg_energy = energy_data.get("average_energy", 0)
            if avg_energy >= 4:
                response += "\n💡 **Insight:** Your energy levels have been consistently high!\n"
            elif avg_energy <= 2:
                response += "\n💡 **Insight:** Your energy levels have been low - consider rest and self-care.\n"

            trend_graph = self._build_trend_graph(
                energy_data.get("recent_data", []), "energy", "Energy trend"
            )
            if trend_graph:
                response += f"\n**Trend Graph:**\n{trend_graph}\n"

            return InteractionResponse(response, True)

        except Exception as e:
            from core.error_handling import handle_ai_error

            handle_ai_error(e, "showing energy trends", user_id)
            return InteractionResponse(
                "I'm having trouble showing your energy trends right now. Please try again.",
                True,
            )

    @handle_errors(
        "showing quantitative summary",
        default_return=InteractionResponse(
            "I'm having trouble showing quantitative summary. Please try again.", True
        ),
    )
    def _handle_quant_summary(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show per-field quantitative summaries for opted-in fields."""
        days = entities.get("days", 30)
        try:
            from core.checkin_analytics import CheckinAnalytics
            from core.user_data_handlers import get_user_data

            analytics = CheckinAnalytics()

            enabled_fields = None
            try:
                prefs = get_user_data(user_id, "preferences") or {}
                checkin_settings = (prefs.get("preferences") or {}).get(
                    "checkin_settings"
                ) or {}
                if isinstance(checkin_settings, dict):
                    questions = checkin_settings.get("questions", {})
                    enabled_fields = [
                        key
                        for key, config in questions.items()
                        if config.get("enabled", False)
                        and config.get("type") in ["scale_1_5", "number", "yes_no"]
                    ]
            except Exception:
                enabled_fields = None

            summaries = analytics.get_quantitative_summaries(
                user_id, days, enabled_fields
            )
            if "error" in summaries:
                return InteractionResponse(
                    "You don't have enough check-in data to compute summaries yet.",
                    True,
                )

            response = f"**Per-field Quantitative Summaries (Last {days} days):**\n\n"
            for field, stats in summaries.items():
                # Determine scale for field
                scale = self._get_field_scale(field)
                scale_suffix = f"/{scale}" if scale else ""

                response += f"• {field.title()}: avg {stats['average']}{scale_suffix} (min {stats['min']}{scale_suffix}, max {stats['max']}{scale_suffix}) over {int(stats['count'])} days\n"
            return InteractionResponse(response, True)
        except Exception as e:
            from core.error_handling import handle_ai_error

            handle_ai_error(e, "computing quantitative summaries", user_id)
            return InteractionResponse(
                "I'm having trouble computing your quantitative summaries right now. Please try again.",
                True,
            )

    @handle_errors(
        "showing habit analysis",
        default_return=InteractionResponse(
            "I'm having trouble showing habit analysis. Please try again.", True
        ),
    )
    def _handle_habit_analysis(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show habit analysis"""
        days = entities.get("days", 30)

        try:
            from core.checkin_analytics import CheckinAnalytics

            analytics = CheckinAnalytics()

            habit_data = analytics.get_habit_analysis(user_id, days)
            if "error" in habit_data:
                return InteractionResponse(
                    "You don't have enough habit data for analysis yet. Try completing some check-ins first!",
                    True,
                )

            habits = habit_data.get("habits", {})
            if not habits:
                return InteractionResponse(
                    f"No habit questions were answered in the last {days} days.",
                    True,
                )

            response = f"**Habit Analysis (Last {days} days):**\n\n"
            response += (
                f"Overall completion: {habit_data.get('overall_completion', 0)}%\n\n"
            )
            response += "Habits:\n"
            for _, habit_stats in sorted(
                habits.items(),
                key=lambda item: item[1].get("name", ""),
            ):
                name = habit_stats.get("name", "Unknown")
                completed = habit_stats.get("completed_days", 0)
                answered = habit_stats.get("answered_days", 0)
                completion = habit_stats.get("completion_rate", 0)
                response += f"- {name}: {completed}/{answered} yes ({completion}%)\n"

            return InteractionResponse(response, True)

        except Exception as e:
            from core.error_handling import handle_ai_error

            handle_ai_error(e, "showing habit analysis", user_id)
            return InteractionResponse(
                "I'm having trouble showing your habit analysis right now. Please try again.",
                True,
            )

    @handle_errors(
        "showing sleep analysis",
        default_return=InteractionResponse(
            "I'm having trouble showing sleep analysis. Please try again.", True
        ),
    )
    def _handle_sleep_analysis(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show sleep analysis"""
        days = entities.get("days", 30)

        try:
            from core.checkin_analytics import CheckinAnalytics

            analytics = CheckinAnalytics()

            sleep_data = analytics.get_sleep_analysis(user_id, days)
            if "error" in sleep_data:
                return InteractionResponse(
                    "You don't have enough sleep data for analysis yet. Try completing some check-ins with sleep information!",
                    True,
                )

            response = f"**😴 Sleep Analysis (Last {days} days):**\n\n"
            response += (
                f"⏰ **Average Hours:** {sleep_data.get('average_hours', 0)} hours\n"
            )
            response += (
                f"⭐ **Average Quality:** {sleep_data.get('average_quality', 0)}/5\n"
            )
            response += (
                f"✅ **Good Sleep Days:** {sleep_data.get('good_sleep_days', 0)} days\n"
            )
            response += f"❌ **Poor Sleep Days:** {sleep_data.get('poor_sleep_days', 0)} days\n\n"

            # Add consistency info
            consistency = sleep_data.get("sleep_consistency", 0)
            response += f"📊 **Sleep Consistency:** {consistency:.1f} (lower = more consistent)\n\n"

            # Add recommendations
            recommendations = sleep_data.get("recommendations", [])
            if recommendations:
                response += "💡 **Sleep Recommendations:**\n"
                for rec in recommendations[:2]:  # Show top 2
                    response += f"• {rec}\n"

            return InteractionResponse(response, True)

        except Exception as e:
            from core.error_handling import handle_ai_error

            handle_ai_error(e, "showing sleep analysis", user_id)
            return InteractionResponse(
                "I'm having trouble showing your sleep analysis right now. Please try again.",
                True,
            )

    @handle_errors(
        "showing wellness score",
        default_return=InteractionResponse(
            "I'm having trouble showing wellness score. Please try again.", True
        ),
    )
    def _handle_wellness_score(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show wellness score"""
        response = self._handle_show_analytics(user_id, entities)
        if response and response.message:
            response.message = (
                "Wellness score has been replaced by basic analytics.\n\n"
                + response.message
            )
        return response

    @handle_errors(
        "showing check-in history",
        default_return=InteractionResponse(
            "I'm having trouble showing check-in history. Please try again.", True
        ),
    )
    def _handle_checkin_history(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show check-in history"""
        days = entities.get("days", 30)
        limit = entities.get("limit")

        try:
            from core.checkin_analytics import CheckinAnalytics
            from core.checkin_dynamic_manager import dynamic_checkin_manager
            from core.response_tracking import get_recent_checkins
            from core.time_utilities import parse_timestamp_full

            analytics = CheckinAnalytics()

            if limit:
                checkin_history = get_recent_checkins(user_id, limit=limit)
            else:
                checkin_history = analytics.get_checkin_history(user_id, days)
            # Handle error case (dict with 'error' key) or empty list
            if isinstance(checkin_history, dict) and "error" in checkin_history:
                return InteractionResponse(
                    "You don't have enough check-in data for history yet. Try completing some check-ins first!",
                    True,
                )

            if not checkin_history:
                if limit:
                    return InteractionResponse(
                        "You haven't completed any check-ins yet. Try starting one with '/checkin'!",
                        True,
                    )
                recent_checkins = get_recent_checkins(user_id, limit=1)
                if recent_checkins:
                    last_timestamp = recent_checkins[0].get("timestamp")
                    last_dt = (
                        parse_timestamp_full(last_timestamp)
                        if last_timestamp
                        else None
                    )
                    last_date = (
                        last_dt.date().isoformat() if last_dt else "an earlier date"
                    )
                    return InteractionResponse(
                        f"No check-ins in the last {days} days. Most recent check-in was on {last_date}.",
                        True,
                    )
                return InteractionResponse(
                    "You haven't completed any check-ins yet. Try starting one with '/checkin'!",
                    True,
                )

            if limit:
                header_label = (
                    f"Last {limit} check-in" if limit == 1 else f"Last {limit} check-ins"
                )
            else:
                header_label = f"Last {days} days"
            response_lines = [f"**Check-in History ({header_label}):**", ""]
            question_defs = dynamic_checkin_manager.get_all_questions(user_id)
            question_keys = set(question_defs.keys())

            for checkin in checkin_history[:5]:  # Show last 5 check-ins
                timestamp = checkin.get("timestamp", "")
                date = checkin.get("date") or (timestamp[:10] if timestamp else "Unknown date")
                responses = self._extract_checkin_responses(checkin, question_keys)
                ordered_keys = self._get_ordered_checkin_keys(checkin, responses)

                response_lines.append(f"- {date}")
                if not ordered_keys:
                    response_lines.append("  - No responses recorded")
                    continue

                for key in ordered_keys:
                    formatted_value = self._format_checkin_response_value(
                        key, responses.get(key), question_defs
                    )
                    if not formatted_value:
                        continue
                    label = self._get_checkin_label(key, question_defs)
                    response_lines.append(f"  - {label}: {formatted_value}")

            if len(checkin_history) > 5:
                response_lines.append(
                    f"... and {len(checkin_history) - 5} more check-ins"
                )

            response = "\n".join(response_lines)
            response = self._truncate_response(response)
            return InteractionResponse(response, True)

        except Exception as e:
            from core.error_handling import handle_ai_error

            handle_ai_error(e, "showing check-in history", user_id)
            return InteractionResponse(
                "I'm having trouble showing your check-in history right now. Please try again.",
                True,
            )

    @handle_errors("extracting check-in responses", default_return={})
    def _extract_checkin_responses(
        self, checkin: dict[str, Any], question_keys: set[str]
    ) -> dict[str, Any]:
        """Extract responses from current check-in records."""
        responses: dict[str, Any] = {}

        for key in question_keys:
            if key in checkin and key not in responses:
                responses[key] = checkin[key]

        reserved_keys = {
            "timestamp",
            "questions_asked",
            "completed",
            "user_id",
            "responses",
            "date",
        }
        for key, value in checkin.items():
            if key in reserved_keys or key in responses:
                continue
            responses[key] = value

        return responses

    @handle_errors("ordering check-in keys", default_return=[])
    def _get_ordered_checkin_keys(
        self, checkin: dict[str, Any], responses: dict[str, Any]
    ) -> list[str]:
        """Preserve original check-in order when available."""
        ordered: list[str] = []
        questions_asked = checkin.get("questions_asked")
        if isinstance(questions_asked, list):
            for key in questions_asked:
                if key in responses and key not in ordered:
                    ordered.append(key)

        for key in sorted(responses.keys()):
            if key not in ordered:
                ordered.append(key)

        return ordered

    @handle_errors("getting check-in label", default_return="")
    def _get_checkin_label(
        self, key: str, question_defs: dict[str, dict[str, Any]]
    ) -> str:
        """Get a readable label for a check-in response key."""
        question_def = question_defs.get(key, {})
        if isinstance(question_def, dict):
            label = question_def.get("ui_display_name") or question_def.get("label")
            if label:
                return self._clean_checkin_label(str(label))
        return self._clean_checkin_label(key.replace("_", " ").strip().title())

    @handle_errors("cleaning check-in label", default_return="")
    def _clean_checkin_label(self, label: str) -> str:
        """Remove redundant suffixes from check-in labels."""
        suffixes = [
            " (1-5 scale)",
            " (1-10 scale)",
            " (yes/no)",
            " (yes-no)",
            " (time pair)",
        ]
        for suffix in suffixes:
            if label.endswith(suffix):
                label = label[: -len(suffix)]
        return label.strip()

    @handle_errors("getting question scale", default_return=None)
    def _get_question_scale(
        self, key: str, question_defs: dict[str, dict[str, Any]]
    ) -> int | float | None:
        """Return scale max for a question when available."""
        question_def = question_defs.get(key, {})
        if isinstance(question_def, dict):
            validation = question_def.get("validation") or {}
            qtype = question_def.get("type")
            max_value = validation.get("max")
            if qtype and str(qtype).startswith("scale_") and isinstance(
                max_value, (int, float)
            ):
                if isinstance(max_value, float) and max_value.is_integer():
                    max_value = int(max_value)
                return max_value
        return self._get_field_scale(key)

    @handle_errors("formatting numeric value", default_return="")
    def _format_numeric_value(self, value: float) -> str:
        """Format numeric values with minimal trailing decimals."""
        if isinstance(value, float) and not value.is_integer():
            return f"{value:.1f}"
        return str(int(value))

    @handle_errors("formatting check-in response value", default_return=None)
    def _format_checkin_response_value(
        self,
        key: str,
        value: Any,
        question_defs: dict[str, dict[str, Any]],
    ) -> str | None:
        """Format a check-in response value for display."""
        if value is None:
            return None
        if value == "SKIPPED":
            return "Skipped"
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, str):
            value_str = value.strip()
            if not value_str:
                return None
            lower_value = value_str.lower()
            if lower_value in {"yes", "y", "true", "1"}:
                return "Yes"
            if lower_value in {"no", "n", "false", "0"}:
                return "No"
            try:
                numeric_value = float(value_str)
                scale = self._get_question_scale(key, question_defs)
                numeric_text = self._format_numeric_value(numeric_value)
                return f"{numeric_text}/{scale}" if scale else numeric_text
            except ValueError:
                return value_str
        if isinstance(value, dict):
            sleep_time = value.get("sleep_time")
            wake_time = value.get("wake_time")
            if sleep_time and wake_time:
                return f"{sleep_time}-{wake_time}"
            if not value:
                return None
            return ", ".join(f"{k}={v}" for k, v in value.items())
        if isinstance(value, list):
            return ", ".join(str(item) for item in value) if value else None
        if isinstance(value, (int, float)):
            scale = self._get_question_scale(key, question_defs)
            numeric_text = self._format_numeric_value(float(value))
            return f"{numeric_text}/{scale}" if scale else numeric_text
        return str(value)

    @handle_errors("building trend graph", default_return="")
    def _build_trend_graph(
        self,
        recent_data: list[dict[str, Any]],
        value_key: str,
        label: str,
        max_points: int = 7,
    ) -> str:
        """Build a simple ASCII trend graph for recent check-in values."""
        series = []
        for entry in recent_data or []:
            value = entry.get(value_key)
            if not isinstance(value, (int, float)):
                continue
            date_value = entry.get("date") or entry.get("timestamp") or "Unknown"
            date_label = (
                date_value[:10] if isinstance(date_value, str) else str(date_value)
            )
            series.append((date_label, float(value)))

        if not series:
            return ""

        series = list(reversed(series[:max_points]))
        lines = [f"{label} (last {len(series)} days):"]
        for date_label, value in series:
            bar_len = max(0, min(10, int(round(value * 2))))
            bar = "#" * bar_len
            lines.append(f"{date_label}: {bar} ({value:.1f})")
        return "\n".join(lines)

    @handle_errors(
        "showing check-in analysis",
        default_return=InteractionResponse(
            "I'm having trouble showing check-in analysis. Please try again.", True
        ),
    )
    def _handle_checkin_analysis(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show comprehensive check-in response analysis"""
        days = entities.get("days", 30)

        try:
            from core.response_tracking import get_checkins_by_days
            from core.checkin_analytics import CheckinAnalytics
            from core.checkin_dynamic_manager import dynamic_checkin_manager

            checkins = get_checkins_by_days(user_id, days)

            if not checkins:
                return InteractionResponse(
                    "You don't have enough check-in data for analysis yet. Try completing some check-ins first!",
                    True,
                )

            analytics = CheckinAnalytics()

            # Get mood trends
            mood_data = analytics.get_mood_trends(user_id, days)

            response = f"**📈 Check-in Analysis (Last {len(checkins)} check-ins):**\n\n"

            # Mood Analysis
            if "error" not in mood_data:
                response += "**😊 Mood Trends:**\n"
                response += f"• Average: {mood_data.get('average_mood', 0):.1f}/5\n"
                response += f"• Range: {mood_data.get('min_mood', 0)} - {mood_data.get('max_mood', 0)}/5\n"
                response += f"• Trend: {mood_data.get('trend', 'Stable')}\n\n"
            else:
                response += "**😊 Mood Data:** Not enough mood data for analysis\n\n"

            # Check-in Patterns
            response += "**📅 Check-in Patterns:**\n"
            response += f"• Total check-ins: {len(checkins)}\n"
            response += f"• Average per day: {len(checkins)/days:.1f}\n"

            # Response Analysis
            response += "\n**💬 Response Analysis:**\n"

            # Analyze common responses
            all_responses = {}
            question_keys = set(
                dynamic_checkin_manager.get_all_questions(user_id).keys()
            )
            for checkin in checkins:
                responses = self._extract_checkin_responses(checkin, question_keys)
                for question, answer in responses.items():
                    if answer == "SKIPPED":
                        continue
                    if question not in all_responses:
                        all_responses[question] = []
                    all_responses[question].append(answer)

            if all_responses:
                response += f"• Questions answered: {len(all_responses)}\n"

                # Show most common responses for key questions
                for question, answers in list(all_responses.items())[:3]:
                    if len(answers) > 1:
                        # Find most common answer
                        from collections import Counter

                        counter = Counter(answers)
                        most_common = counter.most_common(1)[0]
                        response += f"• '{question}': Most common answer: '{most_common[0]}' ({most_common[1]} times)\n"
            else:
                response += "• No detailed responses found\n"

            # Insights
            response += "\n**💡 Insights:**\n"
            if len(checkins) >= 7:
                response += "• You've been consistent with check-ins\n"
            if "error" not in mood_data and mood_data.get("trend") == "improving":
                response += "• Your mood has been improving recently\n"
            elif "error" not in mood_data and mood_data.get("trend") == "declining":
                response += "• Your mood has been declining - consider reaching out for support\n"

            response += "\n💡 **Try these commands for more details:**\n"
            response += "• 'mood trends' - Detailed mood analysis\n"
            response += "• 'checkin history' - View all your check-ins\n"
            response += "• 'habit analysis' - Analyze your habits\n"

            # Truncate response if too long for Discord
            response = self._truncate_response(response)

            return InteractionResponse(response, True)

        except Exception as e:
            from core.error_handling import handle_ai_error

            handle_ai_error(e, "analyzing check-ins", user_id)
            return InteractionResponse(
                "I'm having trouble analyzing your check-ins right now. Please try again.",
                True,
            )

    @handle_errors(
        "showing completion rate",
        default_return=InteractionResponse(
            "I'm having trouble showing completion rate. Please try again.", True
        ),
    )
    def _handle_completion_rate(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show completion rate"""
        days = entities.get("days", 30)

        try:
            from core.checkin_analytics import CheckinAnalytics

            analytics = CheckinAnalytics()

            completion_rate = analytics.get_completion_rate(user_id, days)
            if "error" in completion_rate:
                return InteractionResponse(
                    "You don't have enough check-in data for completion rate yet. Try completing some check-ins first!",
                    True,
                )

            response = f"**📊 Completion Rate (Last {days} days):**\n\n"
            response += (
                f"🎯 **Overall Completion Rate:** {completion_rate.get('rate', 0)}%\n"
            )
            response += (
                f"📅 **Days Completed:** {completion_rate.get('days_completed', 0)}\n"
            )
            response += f"📅 **Days Missed:** {completion_rate.get('days_missed', 0)}\n"
            response += f"📅 **Total Days:** {completion_rate.get('total_days', 0)}\n"

            return InteractionResponse(response, True)

        except Exception as e:
            from core.error_handling import handle_ai_error

            handle_ai_error(e, "calculating completion rate", user_id)
            return InteractionResponse(
                "I'm having trouble calculating your completion rate right now. Please try again.",
                True,
            )

    @handle_errors(
        "showing task analytics",
        default_return=InteractionResponse(
            "I'm having trouble showing task analytics. Please try again.", True
        ),
    )
    def _handle_task_analytics(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show comprehensive task analytics and insights"""
        days = entities.get("days", 30)

        try:
            from tasks.task_management import (
                get_user_task_stats,
                load_active_tasks,
                load_completed_tasks,
            )
            from core.checkin_analytics import CheckinAnalytics

            # Get basic task statistics
            task_stats = get_user_task_stats(user_id)
            load_active_tasks(user_id)
            load_completed_tasks(user_id)

            analytics = CheckinAnalytics()
            task_weekly_stats = analytics.get_task_weekly_stats(user_id, days)

            response = f"**📋 Task Analytics (Last {days} days):**\n\n"

            # Overall Task Statistics
            response += "**📊 Overall Task Status:**\n"
            response += f"• Active Tasks: {task_stats.get('active_count', 0)}\n"
            response += f"• Completed Tasks: {task_stats.get('completed_count', 0)}\n"
            response += f"• Total Tasks: {task_stats.get('total_count', 0)}\n"

            if task_stats.get("total_count", 0) > 0:
                completion_rate = (
                    task_stats.get("completed_count", 0)
                    / task_stats.get("total_count", 0)
                ) * 100
                response += f"• Overall Completion Rate: {completion_rate:.1f}%\n"

            response += "\n"

            # Task Completion Patterns
            if task_weekly_stats and "error" not in task_weekly_stats:
                response += "**📅 Task Completion Patterns:**\n"
                for task_name, stats in task_weekly_stats.items():
                    completion_rate = stats.get("completion_rate", 0)
                    completed_days = stats.get("completed_days", 0)
                    total_days = stats.get("total_days", 0)

                    # Add emoji based on completion rate
                    emoji = (
                        "🟢"
                        if completion_rate >= 80
                        else "🟡" if completion_rate >= 50 else "🔴"
                    )
                    response += f"• {emoji} {task_name}: {completion_rate:.1f}% ({completed_days}/{total_days} days)\n"
            else:
                response += "**📅 Task Completion Patterns:**\n"
                response += "• No detailed task completion data available\n"

            response += "\n"

            # Task Insights
            response += "**💡 Task Insights:**\n"
            if task_stats.get("active_count", 0) > 5:
                response += "• You have many active tasks - consider prioritizing or breaking them down\n"
            elif task_stats.get("active_count", 0) == 0:
                response += "• No active tasks - great job staying on top of things!\n"

            if task_stats.get("completed_count", 0) > 0:
                response += "• You're making good progress on task completion\n"

            # Add recommendations
            response += "\n💡 **Try these commands for more details:**\n"
            response += "• 'task stats' - Detailed task statistics\n"
            response += "• 'show my tasks' - View all your tasks\n"
            response += (
                "• 'habit analysis' - See how your habits relate to task completion\n"
            )

            # Truncate response if too long
            response = self._truncate_response(response)

            return InteractionResponse(response, True)

        except Exception as e:
            from core.error_handling import handle_ai_error

            handle_ai_error(e, "showing task analytics", user_id)
            return InteractionResponse(
                "I'm having trouble showing your task analytics right now. Please try again.",
                True,
            )

    @handle_errors(
        "showing task statistics",
        default_return=InteractionResponse(
            "I'm having trouble showing task statistics. Please try again.", True
        ),
    )
    def _handle_task_stats(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show detailed task statistics"""
        days = entities.get("days", 30)

        try:
            from tasks.task_management import (
                get_user_task_stats,
                load_active_tasks,
                load_completed_tasks,
            )

            # Get task statistics
            task_stats = get_user_task_stats(user_id)
            active_tasks = load_active_tasks(user_id)
            completed_tasks = load_completed_tasks(user_id)

            response = f"**📊 Task Statistics (Last {days} days):**\n\n"

            # Basic Statistics
            response += "**📋 Task Overview:**\n"
            response += f"• Active Tasks: {task_stats.get('active_count', 0)}\n"
            response += f"• Completed Tasks: {task_stats.get('completed_count', 0)}\n"
            response += f"• Total Tasks: {task_stats.get('total_count', 0)}\n"

            if task_stats.get("total_count", 0) > 0:
                completion_rate = (
                    task_stats.get("completed_count", 0)
                    / task_stats.get("total_count", 0)
                ) * 100
                response += f"• Completion Rate: {completion_rate:.1f}%\n"

            response += "\n"

            # Priority Breakdown
            if active_tasks:
                response += "**🎯 Active Task Priorities:**\n"
                priority_counts = {}
                for task in active_tasks:
                    priority = task.get("priority", "medium")
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1

                for priority, count in priority_counts.items():
                    emoji = (
                        "🔴"
                        if priority == "high"
                        else "🟡" if priority == "medium" else "🟢"
                    )
                    response += f"• {emoji} {priority.title()}: {count} tasks\n"

            response += "\n"

            # Recent Completions
            if completed_tasks:
                response += "**✅ Recently Completed:**\n"
                recent_completed = completed_tasks[:5]  # Show last 5
                for task in recent_completed:
                    title = task.get("title", "Unknown Task")
                    response += f"• {title}\n"

            # Truncate response if too long
            response = self._truncate_response(response)

            return InteractionResponse(response, True)

        except Exception as e:
            from core.error_handling import handle_ai_error

            handle_ai_error(e, "showing task statistics", user_id)
            return InteractionResponse(
                "I'm having trouble showing your task statistics right now. Please try again.",
                True,
            )

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

    @handle_errors("formatting basic analytics line", default_return="")
    def _format_basic_analytics_line(self, question: dict[str, Any]) -> str:
        """Format a single basic analytics line."""
        name = question.get("name", "Unknown")
        scale_max = question.get("scale_max")
        if "average" in question:
            avg = self._format_numeric_value(question.get("average", 0))
            min_val = self._format_numeric_value(question.get("min", 0))
            max_val = self._format_numeric_value(question.get("max", 0))
            count = question.get("count", 0)
            scale_suffix = f"/{int(scale_max)}" if scale_max else ""
            return (
                f"{name}: avg {avg}{scale_suffix} "
                f"(min {min_val}{scale_suffix}, max {max_val}{scale_suffix}) "
                f"over {count} answers"
            )
        if "average_hours" in question:
            avg = self._format_numeric_value(question.get("average_hours", 0))
            min_val = self._format_numeric_value(question.get("min_hours", 0))
            max_val = self._format_numeric_value(question.get("max_hours", 0))
            count = question.get("count", 0)
            return (
                f"{name}: avg {avg}h (min {min_val}h, max {max_val}h) "
                f"over {count} answers"
            )
        if "yes_rate" in question:
            yes_count = question.get("yes_count", 0)
            count = question.get("count", 0)
            yes_rate = question.get("yes_rate", 0)
            return f"{name}: Yes {yes_count}/{count} ({yes_rate}%)"
        count = question.get("count", 0)
        return f"{name}: {count} responses"

    @handle_errors("getting field scale", default_return=None)
    def _get_field_scale(self, field: str) -> int:
        """Determine the scale for a field (1-5 scale, or None for other types)

        Returns:
            int: Scale value (5 for 1-5 scale fields, None for other types)
        """
        # Fields that use 1-5 scale
        scale_1_5_fields = [
            "mood",
            "energy",
            "stress_level",
            "sleep_quality",
            "anxiety_level",
            "focus_level",
        ]

        if field in scale_1_5_fields:
            return 5

        # Other fields (sleep_hours, yes/no fields) don't have a scale
        return None

    @handle_errors("truncating response", default_return="")
    def _truncate_response(self, response: str, max_length: int = 1900) -> str:
        """Truncate response to fit Discord message limits"""
        if len(response) <= max_length:
            return response

        # Try to truncate at a reasonable point
        truncated = response[: max_length - 3] + "..."

        # Try to find a better truncation point
        last_newline = truncated.rfind("\n")
        if last_newline > max_length * 0.8:  # If we can find a newline in the last 20%
            truncated = response[:last_newline] + "\n\n... (response truncated)"

        return truncated
