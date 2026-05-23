"""Check-in focused analytics command handling."""

from collections import Counter
from typing import Any

import core
from core import (
    checkin_analytics,
    checkin_dynamic_manager,
    error_handling,
    response_tracking,
    time_utilities,
)

from communication.command_handlers.analytics_formatting import AnalyticsFormattingMixin
from communication.command_handlers.shared_types import InteractionResponse


class CheckinAnalyticsHandler(AnalyticsFormattingMixin):
    """Handle check-in analytics, history, summaries, and completion rates."""

    @error_handling.handle_errors(
        "showing analytics overview",
        default_return=InteractionResponse(
            "I'm having trouble showing your analytics. Please try again.", True
        ),
    )
    def handle_show_analytics(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show comprehensive analytics overview."""
        days = entities.get("days", 30)

        try:
            analytics = checkin_analytics.CheckinAnalytics()

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
            error_handling.handle_ai_error(e, "showing analytics", user_id)
            return InteractionResponse(
                "I'm having trouble showing your analytics right now. Please try again.",
                True,
            )

    @error_handling.handle_errors(
        "showing quantitative summary",
        default_return=InteractionResponse(
            "I'm having trouble showing quantitative summary. Please try again.", True
        ),
    )
    def handle_quant_summary(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show per-field quantitative summaries for opted-in fields."""
        days = entities.get("days", 30)
        try:
            analytics = checkin_analytics.CheckinAnalytics()
            enabled_fields = self._get_enabled_quantitative_fields(user_id)

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
                scale = self._get_field_scale(field)
                scale_suffix = f"/{scale}" if scale else ""

                response += f"â€¢ {field.title()}: avg {stats['average']}{scale_suffix} (min {stats['min']}{scale_suffix}, max {stats['max']}{scale_suffix}) over {int(stats['count'])} days\n"
            return InteractionResponse(response, True)
        except Exception as e:
            error_handling.handle_ai_error(
                e, "computing quantitative summaries", user_id
            )
            return InteractionResponse(
                "I'm having trouble computing your quantitative summaries right now. Please try again.",
                True,
            )

    @error_handling.handle_errors(
        "getting enabled quantitative check-in fields",
        default_return=None,
    )
    def _get_enabled_quantitative_fields(self, user_id: str) -> list[str] | None:
        """Return enabled quantitative check-in fields for a user."""
        prefs = core.get_user_data(user_id, "preferences") or {}
        checkin_settings = (prefs.get("preferences") or {}).get(
            "checkin_settings"
        ) or {}
        if not isinstance(checkin_settings, dict):
            return None
        questions = checkin_settings.get("questions", {})
        return [
            key
            for key, config in questions.items()
            if config.get("enabled", False)
            and config.get("type") in ["scale_1_5", "number", "yes_no"]
        ]

    @error_handling.handle_errors(
        "showing habit analysis",
        default_return=InteractionResponse(
            "I'm having trouble showing habit analysis. Please try again.", True
        ),
    )
    def handle_habit_analysis(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show habit analysis."""
        days = entities.get("days", 30)

        try:
            analytics = checkin_analytics.CheckinAnalytics()
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
            error_handling.handle_ai_error(e, "showing habit analysis", user_id)
            return InteractionResponse(
                "I'm having trouble showing your habit analysis right now. Please try again.",
                True,
            )

    @error_handling.handle_errors(
        "showing sleep analysis",
        default_return=InteractionResponse(
            "I'm having trouble showing sleep analysis. Please try again.", True
        ),
    )
    def handle_sleep_analysis(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show sleep analysis."""
        days = entities.get("days", 30)

        try:
            analytics = checkin_analytics.CheckinAnalytics()
            sleep_data = analytics.get_sleep_analysis(user_id, days)
            if "error" in sleep_data:
                return InteractionResponse(
                    "You don't have enough sleep data for analysis yet. Try completing some check-ins with sleep information!",
                    True,
                )

            response = f"**ðŸ˜´ Sleep Analysis (Last {days} days):**\n\n"
            response += (
                f"â° **Average Hours:** {sleep_data.get('average_hours', 0)} hours\n"
            )
            response += (
                f"â­ **Average Quality:** {sleep_data.get('average_quality', 0)}/5\n"
            )
            response += (
                f"âœ… **Good Sleep Days:** {sleep_data.get('good_sleep_days', 0)} days\n"
            )
            response += f"âŒ **Poor Sleep Days:** {sleep_data.get('poor_sleep_days', 0)} days\n\n"

            consistency = sleep_data.get("sleep_consistency", 0)
            response += f"ðŸ“Š **Sleep Consistency:** {consistency:.1f} (lower = more consistent)\n\n"

            recommendations = sleep_data.get("recommendations", [])
            if recommendations:
                response += "ðŸ’¡ **Sleep Recommendations:**\n"
                for rec in recommendations[:2]:
                    response += f"â€¢ {rec}\n"

            return InteractionResponse(response, True)

        except Exception as e:
            error_handling.handle_ai_error(e, "showing sleep analysis", user_id)
            return InteractionResponse(
                "I'm having trouble showing your sleep analysis right now. Please try again.",
                True,
            )

    @error_handling.handle_errors(
        "showing wellness score",
        default_return=InteractionResponse(
            "I'm having trouble showing wellness score. Please try again.", True
        ),
    )
    def handle_wellness_score(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show wellness score replacement text plus analytics overview."""
        response = self.handle_show_analytics(user_id, entities)
        if response and response.message:
            response.message = (
                "Wellness score has been replaced by basic analytics.\n\n"
                + response.message
            )
        return response

    @error_handling.handle_errors(
        "showing check-in history",
        default_return=InteractionResponse(
            "I'm having trouble showing check-in history. Please try again.", True
        ),
    )
    def handle_checkin_history(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show check-in history."""
        days = entities.get("days", 30)
        limit = entities.get("limit")

        try:
            analytics = checkin_analytics.CheckinAnalytics()

            if limit:
                checkin_history = response_tracking.get_recent_checkins(
                    user_id, limit=limit
                )
            else:
                checkin_history = analytics.get_checkin_history(user_id, days)
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
                recent_checkins = response_tracking.get_recent_checkins(
                    user_id, limit=1
                )
                if recent_checkins:
                    last_timestamp = response_tracking.checkin_runtime_timestamp(
                        recent_checkins[0]
                    )
                    last_dt = (
                        time_utilities.parse_timestamp_full(last_timestamp)
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
                    f"Last {limit} check-in"
                    if limit == 1
                    else f"Last {limit} check-ins"
                )
            else:
                header_label = f"Last {days} days"
            response_lines = [f"**Check-in History ({header_label}):**", ""]
            question_defs = checkin_dynamic_manager.dynamic_checkin_manager.get_all_questions(
                user_id
            )
            question_keys = set(question_defs.keys())

            for checkin in checkin_history[:5]:
                timestamp = response_tracking.checkin_runtime_timestamp(checkin)
                date = checkin.get("date") or (
                    timestamp[:10] if timestamp else "Unknown date"
                )
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
            error_handling.handle_ai_error(e, "showing check-in history", user_id)
            return InteractionResponse(
                "I'm having trouble showing your check-in history right now. Please try again.",
                True,
            )

    @error_handling.handle_errors(
        "showing check-in analysis",
        default_return=InteractionResponse(
            "I'm having trouble showing check-in analysis. Please try again.", True
        ),
    )
    def handle_checkin_analysis(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show comprehensive check-in response analysis."""
        days = entities.get("days", 30)

        try:
            checkins = response_tracking.get_checkins_by_days(user_id, days)

            if not checkins:
                return InteractionResponse(
                    "You don't have enough check-in data for analysis yet. Try completing some check-ins first!",
                    True,
                )

            analytics = checkin_analytics.CheckinAnalytics()
            mood_data = analytics.get_mood_trends(user_id, days)

            response = f"**ðŸ“ˆ Check-in Analysis (Last {len(checkins)} check-ins):**\n\n"

            if "error" not in mood_data:
                response += "**ðŸ˜Š Mood Trends:**\n"
                response += f"â€¢ Average: {mood_data.get('average_mood', 0):.1f}/5\n"
                response += f"â€¢ Range: {mood_data.get('min_mood', 0)} - {mood_data.get('max_mood', 0)}/5\n"
                response += f"â€¢ Trend: {mood_data.get('trend', 'Stable')}\n\n"
            else:
                response += "**ðŸ˜Š Mood Data:** Not enough mood data for analysis\n\n"

            response += "**ðŸ“… Check-in Patterns:**\n"
            response += f"â€¢ Total check-ins: {len(checkins)}\n"
            response += f"â€¢ Average per day: {len(checkins) / days:.1f}\n"

            response += "\n**ðŸ’¬ Response Analysis:**\n"
            all_responses = {}
            question_keys = set(
                checkin_dynamic_manager.dynamic_checkin_manager.get_all_questions(
                    user_id
                ).keys()
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
                response += f"â€¢ Questions answered: {len(all_responses)}\n"
                for question, answers in list(all_responses.items())[:3]:
                    if len(answers) > 1:
                        counter = Counter(answers)
                        most_common = counter.most_common(1)[0]
                        response += f"â€¢ '{question}': Most common answer: '{most_common[0]}' ({most_common[1]} times)\n"
            else:
                response += "â€¢ No detailed responses found\n"

            response += "\n**ðŸ’¡ Insights:**\n"
            if len(checkins) >= 7:
                response += "â€¢ You've been consistent with check-ins\n"
            if "error" not in mood_data and mood_data.get("trend") == "improving":
                response += "â€¢ Your mood has been improving recently\n"
            elif "error" not in mood_data and mood_data.get("trend") == "declining":
                response += "â€¢ Your mood has been declining - consider reaching out for support\n"

            response += "\nðŸ’¡ **Try these commands for more details:**\n"
            response += "â€¢ 'mood trends' - Detailed mood analysis\n"
            response += "â€¢ 'checkin history' - View all your check-ins\n"
            response += "â€¢ 'habit analysis' - Analyze your habits\n"

            response = self._truncate_response(response)
            return InteractionResponse(response, True)

        except Exception as e:
            error_handling.handle_ai_error(e, "analyzing check-ins", user_id)
            return InteractionResponse(
                "I'm having trouble analyzing your check-ins right now. Please try again.",
                True,
            )

    @error_handling.handle_errors(
        "showing completion rate",
        default_return=InteractionResponse(
            "I'm having trouble showing completion rate. Please try again.", True
        ),
    )
    def handle_completion_rate(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show completion rate."""
        days = entities.get("days", 30)

        try:
            analytics = checkin_analytics.CheckinAnalytics()
            completion_rate = analytics.get_completion_rate(user_id, days)
            if "error" in completion_rate:
                return InteractionResponse(
                    "You don't have enough check-in data for completion rate yet. Try completing some check-ins first!",
                    True,
                )

            response = f"**ðŸ“Š Completion Rate (Last {days} days):**\n\n"
            response += (
                f"ðŸŽ¯ **Overall Completion Rate:** {completion_rate.get('rate', 0)}%\n"
            )
            response += (
                f"ðŸ“… **Days Completed:** {completion_rate.get('days_completed', 0)}\n"
            )
            response += f"ðŸ“… **Days Missed:** {completion_rate.get('days_missed', 0)}\n"
            response += f"ðŸ“… **Total Days:** {completion_rate.get('total_days', 0)}\n"

            return InteractionResponse(response, True)

        except Exception as e:
            error_handling.handle_ai_error(e, "calculating completion rate", user_id)
            return InteractionResponse(
                "I'm having trouble calculating your completion rate right now. Please try again.",
                True,
            )
