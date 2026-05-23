"""Task-focused analytics command handling."""

from typing import Any

from core import checkin_analytics, error_handling
import tasks as task_services

from communication.command_handlers.analytics_formatting import AnalyticsFormattingMixin
from communication.command_handlers.shared_types import InteractionResponse


class TaskAnalyticsHandler(AnalyticsFormattingMixin):
    """Handle task analytics and task statistics commands."""

    @error_handling.handle_errors(
        "showing task analytics",
        default_return=InteractionResponse(
            "I'm having trouble showing task analytics. Please try again.", True
        ),
    )
    def handle_task_analytics(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show comprehensive task analytics and insights."""
        days = entities.get("days", 30)

        try:
            task_stats = task_services.get_user_task_stats(user_id)
            task_services.load_active_tasks(user_id)
            task_services.load_completed_tasks(user_id)

            analytics = checkin_analytics.CheckinAnalytics()
            task_weekly_stats = analytics.get_task_weekly_stats(user_id, days)

            response = f"**ðŸ“‹ Task Analytics (Last {days} days):**\n\n"
            response += "**ðŸ“Š Overall Task Status:**\n"
            response += f"â€¢ Active Tasks: {task_stats.get('active_count', 0)}\n"
            response += f"â€¢ Completed Tasks: {task_stats.get('completed_count', 0)}\n"
            response += f"â€¢ Total Tasks: {task_stats.get('total_count', 0)}\n"

            if task_stats.get("total_count", 0) > 0:
                completion_rate = (
                    task_stats.get("completed_count", 0)
                    / task_stats.get("total_count", 0)
                ) * 100
                response += f"â€¢ Overall Completion Rate: {completion_rate:.1f}%\n"

            response += "\n"

            if task_weekly_stats and "error" not in task_weekly_stats:
                response += "**ðŸ“… Task Completion Patterns:**\n"
                for task_name, stats in task_weekly_stats.items():
                    completion_rate = stats.get("completion_rate", 0)
                    completed_days = stats.get("completed_days", 0)
                    total_days = stats.get("total_days", 0)

                    emoji = (
                        "ðŸŸ¢"
                        if completion_rate >= 80
                        else "ðŸŸ¡" if completion_rate >= 50 else "ðŸ”´"
                    )
                    response += f"â€¢ {emoji} {task_name}: {completion_rate:.1f}% ({completed_days}/{total_days} days)\n"
            else:
                response += "**ðŸ“… Task Completion Patterns:**\n"
                response += "â€¢ No detailed task completion data available\n"

            response += "\n"
            response += "**ðŸ’¡ Task Insights:**\n"
            if task_stats.get("active_count", 0) > 5:
                response += "â€¢ You have many active tasks - consider prioritizing or breaking them down\n"
            elif task_stats.get("active_count", 0) == 0:
                response += "â€¢ No active tasks - great job staying on top of things!\n"

            if task_stats.get("completed_count", 0) > 0:
                response += "â€¢ You're making good progress on task completion\n"

            response += "\nðŸ’¡ **Try these commands for more details:**\n"
            response += "â€¢ 'task stats' - Detailed task statistics\n"
            response += "â€¢ 'show my tasks' - View all your tasks\n"
            response += (
                "â€¢ 'habit analysis' - See how your habits relate to task completion\n"
            )

            response = self._truncate_response(response)
            return InteractionResponse(response, True)

        except Exception as e:
            error_handling.handle_ai_error(e, "showing task analytics", user_id)
            return InteractionResponse(
                "I'm having trouble showing your task analytics right now. Please try again.",
                True,
            )

    @error_handling.handle_errors(
        "showing task statistics",
        default_return=InteractionResponse(
            "I'm having trouble showing task statistics. Please try again.", True
        ),
    )
    def handle_task_stats(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Show detailed task statistics."""
        days = entities.get("days", 30)

        try:
            task_stats = task_services.get_user_task_stats(user_id)
            active_tasks = task_services.load_active_tasks(user_id)
            completed_tasks = task_services.load_completed_tasks(user_id)

            response = f"**ðŸ“Š Task Statistics (Last {days} days):**\n\n"
            response += "**ðŸ“‹ Task Overview:**\n"
            response += f"â€¢ Active Tasks: {task_stats.get('active_count', 0)}\n"
            response += f"â€¢ Completed Tasks: {task_stats.get('completed_count', 0)}\n"
            response += f"â€¢ Total Tasks: {task_stats.get('total_count', 0)}\n"

            if task_stats.get("total_count", 0) > 0:
                completion_rate = (
                    task_stats.get("completed_count", 0)
                    / task_stats.get("total_count", 0)
                ) * 100
                response += f"â€¢ Completion Rate: {completion_rate:.1f}%\n"

            response += "\n"

            if active_tasks:
                response += "**ðŸŽ¯ Active Task Priorities:**\n"
                priority_counts = {}
                for task in active_tasks:
                    priority = task.get("priority", "medium")
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1

                for priority, count in priority_counts.items():
                    emoji = (
                        "ðŸ”´"
                        if priority == "high"
                        else "ðŸŸ¡" if priority == "medium" else "ðŸŸ¢"
                    )
                    response += f"â€¢ {emoji} {priority.title()}: {count} tasks\n"

            response += "\n"

            if completed_tasks:
                response += "**âœ… Recently Completed:**\n"
                recent_completed = completed_tasks[:5]
                for task in recent_completed:
                    title = task.get("title", "Unknown Task")
                    response += f"â€¢ {title}\n"

            response = self._truncate_response(response)
            return InteractionResponse(response, True)

        except Exception as e:
            error_handling.handle_ai_error(e, "showing task statistics", user_id)
            return InteractionResponse(
                "I'm having trouble showing your task statistics right now. Please try again.",
                True,
            )
