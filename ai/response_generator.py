# ai/response_generator.py

"""Conversational response generation: context prompts and engagement helpers."""

from core.config import AI_MIN_RESPONSE_LENGTH
from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.message_management import get_recent_messages
from core.response_tracking import checkin_runtime_timestamp, get_recent_responses
from core.time_utilities import TIME_ONLY_MINUTE, format_timestamp
from ai.prompt_manager import get_prompt_manager
from user.context_manager import user_context_manager

logger = get_component_logger("ai")


class ResponseGenerator:
    """Build conversational prompts and post-process chat responses."""

    @handle_errors("initializing response generator", default_return=None)
    def __init__(self) -> None:
        self._prompt_manager = get_prompt_manager()

    @handle_errors(
        "creating comprehensive context prompt",
        default_return=[
            {
                "role": "system",
                "content": "You are a supportive wellness assistant. Keep responses helpful, encouraging, and conversational.",
            },
            {"role": "user", "content": "Hello"},
        ],
    )
    def create_comprehensive_context_prompt(
        self, user_id: str, user_prompt: str
    ) -> list:
        """Create a comprehensive context prompt with all user data for LM Studio."""
        context = user_context_manager.get_ai_context(
            user_id, include_conversation_history=True
        )

        # Build detailed context string with all available data
        context_parts = []

        # User profile information (natural language)
        profile = context.get("user_profile", {})
        if profile.get("preferred_name"):
            context_parts.append(
                f"The user's preferred name is {profile['preferred_name']}"
            )
        if profile.get("active_categories"):
            categories_str = ", ".join(profile["active_categories"])
            context_parts.append(f"Their interests include: {categories_str}")

        # Neurodivergent-specific context from user data
        user_context_data = context.get("user_context", {})
        if user_context_data:
            # Health conditions (ADHD, depression, etc.)
            health_conditions = user_context_data.get("custom_fields", {}).get(
                "health_conditions", []
            )
            if health_conditions:
                conditions_str = ", ".join(health_conditions)
                context_parts.append(
                    f"They have been diagnosed with or are managing: {conditions_str}"
                )

            # User's notes for AI (specific needs, preferences)
            notes_for_ai = user_context_data.get("notes_for_ai", [])
            if notes_for_ai:
                notes_str = "; ".join(notes_for_ai)
                context_parts.append(f"Important notes about them: {notes_str}")

            # Activities that encourage the user
            encouraging_activities = user_context_data.get(
                "activities_for_encouragement", []
            )
            if encouraging_activities:
                activities_str = ", ".join(encouraging_activities)
                context_parts.append(
                    f"Activities that encourage them include: {activities_str}"
                )

            # Goals and interests
            goals = user_context_data.get("goals", [])
            if goals:
                goals_str = ", ".join(goals)
                context_parts.append(f"Their goals include: {goals_str}")

        # Feature enablement status (important: tell AI what features are available)
        try:
            from core.response_tracking import is_user_checkins_enabled

            checkins_enabled = is_user_checkins_enabled(user_id)
            from tasks import are_tasks_enabled

            tasks_enabled = are_tasks_enabled(user_id) if user_id else False

            # Explicitly tell AI what features are enabled/disabled
            feature_status = []
            if checkins_enabled:
                feature_status.append("check-ins are enabled")
            else:
                feature_status.append(
                    "check-ins are disabled - do NOT mention check-ins, check-in data, or suggest starting check-ins"
                )

            if tasks_enabled:
                feature_status.append("task management is enabled")
            else:
                feature_status.append(
                    "task management is disabled - do NOT mention tasks, task creation, or task reminders"
                )

            if feature_status:
                context_parts.append(
                    f"IMPORTANT - Feature availability: {'; '.join(feature_status)}"
                )
        except Exception as e:
            logger.debug(f"Could not check feature enablement: {e}")
            # Default to disabled if check fails to be safe
            context_parts.append(
                "IMPORTANT - Feature availability: check-ins status unknown, task management status unknown"
            )

        # Recent check-in data analysis (ONLY if check-ins are enabled)
        try:
            from core.response_tracking import is_user_checkins_enabled

            checkins_enabled = is_user_checkins_enabled(user_id)

            if not checkins_enabled:
                # Skip check-in data if disabled
                pass
            else:
                recent_checkins = get_recent_responses(user_id, limit=10)
                if recent_checkins:
                    # Analyze breakfast patterns
                    breakfast_count = sum(
                        1
                        for entry in recent_checkins
                        if entry.get("ate_breakfast") is True
                    )
                    total_entries = len(recent_checkins)
                    breakfast_rate = (
                        (breakfast_count / total_entries) * 100
                        if total_entries > 0
                        else 0
                    )

                    # Analyze mood and energy trends
                    moods = [
                        entry.get("mood")
                        for entry in recent_checkins
                        if entry.get("mood") is not None
                    ]
                    energies = [
                        entry.get("energy")
                        for entry in recent_checkins
                        if entry.get("energy") is not None
                    ]
                    avg_mood = sum(moods) / len(moods) if moods else None
                    avg_energy = sum(energies) / len(energies) if energies else None

                    # Analyze other habits
                    teeth_brushed_count = sum(
                        1
                        for entry in recent_checkins
                        if entry.get("brushed_teeth") is True
                    )
                    teeth_rate = (
                        (teeth_brushed_count / total_entries) * 100
                        if total_entries > 0
                        else 0
                    )

                    # Format check-in data in natural language (better for AI comprehension)
                    summary_lines = []
                    summary_lines.append(f"Over the last {total_entries} check-ins:")
                    if avg_mood:
                        summary_lines.append(
                            f"Their average mood has been {avg_mood:.1f} out of 5"
                        )
                    if avg_energy:
                        summary_lines.append(
                            f"Their average energy level has been {avg_energy:.1f} out of 5"
                        )
                    summary_lines.append(
                        f"They ate breakfast {breakfast_count} out of {total_entries} times ({breakfast_rate:.0f}% of the time)"
                    )
                    summary_lines.append(
                        f"They brushed their teeth {teeth_brushed_count} out of {total_entries} times ({teeth_rate:.0f}% of the time)"
                    )

                    # Add specific recent entries in natural language
                    if recent_checkins[:3]:
                        summary_lines.append("Most recent check-ins:")
                        for i, entry in enumerate(recent_checkins[:3]):
                            entry_desc = []
                            if entry.get("mood") is not None:
                                entry_desc.append(f"mood was {entry['mood']} out of 5")
                            if entry.get("energy") is not None:
                                entry_desc.append(
                                    f"energy was {entry['energy']} out of 5"
                                )
                            if entry.get("ate_breakfast") is not None:
                                entry_desc.append(
                                    f"{'ate' if entry['ate_breakfast'] else 'did not eat'} breakfast"
                                )
                            if entry.get("brushed_teeth") is not None:
                                entry_desc.append(
                                    f"{'brushed' if entry['brushed_teeth'] else 'did not brush'} teeth"
                                )

                            if entry_desc:
                                summary_lines.append(
                                    f"  - Check-in {i + 1}: {', '.join(entry_desc)}"
                                )

                    context_parts.append("\n".join(summary_lines))
                else:
                    # Explicitly state when there are no check-ins to prevent AI from making assumptions
                    context_parts.append("They have not completed any check-ins yet.")
        except Exception as e:
            logger.debug(f"Could not load check-in data for context: {e}")
            pass

        # Recent activity summary (natural language) - only if check-ins enabled
        try:
            from core.response_tracking import is_user_checkins_enabled

            checkins_enabled = is_user_checkins_enabled(user_id)
            if checkins_enabled:
                recent_activity = context.get("recent_activity", {})
                if recent_activity.get("recent_responses_count", 0) > 0:
                    count = recent_activity["recent_responses_count"]
                    context_parts.append(
                        f"They have completed {count} check-in{'s' if count != 1 else ''} recently"
                    )

                # Mood trends (natural language) - only if check-ins enabled
                mood_trends = context.get("mood_trends", {})
                if mood_trends.get("average_mood") is not None:
                    avg_mood = mood_trends["average_mood"]
                    trend = mood_trends.get("trend", "stable")
                    trend_desc = {
                        "improving": "improving",
                        "declining": "declining",
                        "stable": "staying stable",
                    }.get(trend, trend)
                    context_parts.append(
                        f"Their mood has been averaging {avg_mood:.1f} out of 5 and is {trend_desc}"
                    )
        except Exception as e:
            logger.debug(f"Could not check check-in status for activity summary: {e}")
            pass

        # Recent conversation history (natural language)
        conversation_history = context.get("conversation_history", [])
        if conversation_history:
            context_parts.append("In recent conversations, they've talked about:")
            for exchange in conversation_history[-3:]:  # Last 3 exchanges
                user_msg = exchange.get("user_message", "")[:80]
                if user_msg:
                    context_parts.append(
                        f"  - {user_msg}{'...' if len(exchange.get('user_message', '')) > 80 else ''}"
                    )

        # Check-in awareness: include whether today's check-in is completed (ONLY if check-ins enabled)
        try:
            from core.response_tracking import is_user_checkins_enabled

            checkins_enabled = is_user_checkins_enabled(user_id)

            if checkins_enabled:
                from datetime import date

                recent_checkins = get_recent_responses(user_id, limit=1)
                completed_today = False
                completed_at = ""
                if recent_checkins:
                    ts = checkin_runtime_timestamp(recent_checkins[0])
                    mood_val = recent_checkins[0].get("mood")
                    energy_val = recent_checkins[0].get("energy")
                    if ts:
                        try:
                            from core.time_utilities import parse_timestamp_full

                            dt = parse_timestamp_full(ts)
                            if dt is not None and dt.date() == date.today():
                                completed_today = True

                                # Display-only: use canonical formatting helper (no inline strftime usage).
                                completed_at = format_timestamp(dt, TIME_ONLY_MINUTE)
                        except Exception:
                            pass
                if completed_today:
                    details = []
                    if mood_val is not None:
                        details.append(f"mood was {mood_val} out of 5")
                    if energy_val is not None:
                        details.append(f"energy was {energy_val} out of 5")
                    if details:
                        details_str = " and ".join(details)
                        context_parts.append(
                            f"They completed their check-in today at {completed_at}, reporting that their {details_str}"
                        )
                    else:
                        context_parts.append(
                            f"They completed their check-in today at {completed_at}"
                        )
                else:
                    context_parts.append(
                        "They have not completed their check-in for today yet"
                    )
        except Exception:
            pass

        # Recent automated/sent messages (natural language format)
        try:
            recent_sent_all = get_recent_messages(user_id, category=None, limit=5)
            recent_sent = [
                m for m in recent_sent_all if m.get("category") != "checkin"
            ][:3]
            if recent_sent:
                context_parts.append("Recent automated messages sent to them:")
                for idx, msg in enumerate(recent_sent[:3]):
                    category = msg.get("category", "general")
                    text = str(msg.get("sent_text") or "").strip()
                    timestamp = str(msg.get("sent_at") or "").strip()
                    if idx == 0:
                        # Full text for most recent message
                        context_parts.append(
                            f'  - Most recently ({timestamp}): A {category} message: "{text}"'
                        )
                    else:
                        # Concise snippet for older items to control token usage
                        words = text.split()
                        snippet = " ".join(words[:10]) + (
                            "…" if len(words) > 10 else ""
                        )
                        context_parts.append(
                            f'  - Previously ({timestamp}): A {category} message: "{snippet}"'
                        )
        except Exception as e:
            # Non-blocking: if anything goes wrong, just skip this context addition
            # Log the error for debugging (especially in test environments)
            logger.debug(
                f"Could not include recent sent messages in context for user {user_id}: {e}",
                exc_info=True,
            )

        # Most recent task reminder (natural language)
        try:
            task_msgs = (
                [m for m in recent_sent_all if m.get("category") == "task_reminders"]
                if "recent_sent_all" in locals()
                else []
            )
            if task_msgs:
                latest_task = task_msgs[0]
                t_text = str(latest_task.get("sent_text") or "").strip()
                t_ts = str(latest_task.get("sent_at") or "").strip()
                context_parts.append(
                    f'They received a task reminder at {t_ts}: "{t_text}"'
                )
        except Exception:
            pass

        # Task data (available if tasks are enabled)
        try:
            from tasks import (
                load_active_tasks,
                get_user_task_stats,
                get_tasks_due_soon,
                are_tasks_enabled,
            )
            from tasks.task_data_handlers import runtime_task_due_date

            if are_tasks_enabled(user_id):
                active_tasks = load_active_tasks(user_id)
                task_stats = get_user_task_stats(user_id)
                tasks_due_soon = get_tasks_due_soon(user_id, days_ahead=7)

                if task_stats.get("total_count", 0) > 0:
                    context_parts.append("Their task information:")
                    context_parts.append(
                        f"  - They have {task_stats.get('active_count', 0)} active task{'s' if task_stats.get('active_count', 0) != 1 else ''}"
                    )
                    context_parts.append(
                        f"  - They have completed {task_stats.get('completed_count', 0)} task{'s' if task_stats.get('completed_count', 0) != 1 else ''} total"
                    )

                    if tasks_due_soon:
                        context_parts.append(
                            f"  - They have {len(tasks_due_soon)} task{'s' if len(tasks_due_soon) != 1 else ''} due within the next 7 days"
                        )

                        # Include details for tasks due soon (up to 3)
                        for task in tasks_due_soon[:3]:
                            title = task.get("title", "Untitled task")
                            due_date = runtime_task_due_date(task) or ""
                            priority = task.get("priority", "normal")
                            due_desc = f", due on {due_date}" if due_date else ""
                            priority_desc = (
                                f" ({priority} priority)"
                                if priority != "normal"
                                else ""
                            )
                            context_parts.append(
                                f'    * "{title}"{due_desc}{priority_desc}'
                            )

                    # Include a few most recent active tasks (if not already listed)
                    if len(active_tasks) > len(tasks_due_soon[:3]):
                        other_active = [
                            t for t in active_tasks if t not in tasks_due_soon[:3]
                        ][:3]
                        if other_active:
                            context_parts.append("  - Other active tasks:")
                            for task in other_active:
                                title = task.get("title", "Untitled task")
                                context_parts.append(f'    * "{title}"')
        except Exception as e:
            # Non-blocking: if task data unavailable, just skip it
            logger.debug(f"Could not load task data for context: {e}")
            pass

        # Schedule details (what's scheduled and when)
        try:
            profile = context.get("user_profile", {})
            active_schedules = profile.get("active_schedules", [])
            if active_schedules:
                from core import get_user_data

                schedules_data = get_user_data(
                    user_id, "schedules", normalize_on_read=True
                ).get("schedules", {})

                if schedules_data:
                    context_parts.append("Their active schedules:")
                    for schedule_name in active_schedules[:5]:  # Limit to 5 schedules
                        # Find schedule in data structure
                        schedule_info = None
                        for category, category_data in schedules_data.items():
                            if (
                                isinstance(category_data, dict)
                                and "periods" in category_data
                            ):
                                for period_name, period_data in category_data[
                                    "periods"
                                ].items():
                                    if period_name == schedule_name:
                                        schedule_info = {
                                            "category": category,
                                            "period": period_name,
                                            "data": period_data,
                                        }
                                        break
                                if schedule_info:
                                    break

                        if schedule_info:
                            period_data = schedule_info["data"]
                            days = period_data.get("days", ["ALL"])
                            start_time = period_data.get("start_time", "00:00")
                            end_time = period_data.get("end_time", "23:59")
                            days_str = (
                                ", ".join(days) if days != ["ALL"] else "every day"
                            )
                            context_parts.append(
                                f"  - {schedule_name} ({schedule_info['category']}): {days_str} from {start_time} to {end_time}"
                            )
        except Exception as e:
            # Non-blocking: if schedule data unavailable, just skip it
            logger.debug(f"Could not load schedule details for context: {e}")
            pass

        # Create comprehensive context string (but don't include in user message to prevent leakage)
        context_str = (
            "\n".join(context_parts) if context_parts else "New user with no data"
        )

        # Create system message with comprehensive context using custom prompt
        base_prompt = self._prompt_manager.get_prompt("wellness")
        system_message = {
            "role": "system",
            "content": f"""{base_prompt}

    IMPORTANT: The following user context is for your reference only. Do NOT include any of this information in your responses to the user:

    User Context:
    {context_str}

    Additional Instructions:
    - **GREETING HANDLING**: When the user greets you (Hello, Hi, Hey) or asks "How are you?" (referring to you, the AI):
    * ALWAYS acknowledge the greeting first (e.g., "Hello!" or "Hi there!")
    * If they ask "How are you?" about you, answer that question first (e.g., "I'm doing well, thank you for asking!" or "I'm here and ready to help!")
    * THEN you can redirect to asking about them (e.g., "How are you doing today?")
    * NEVER skip acknowledging greetings or redirecting without answering questions about you first
    * BAD examples (NEVER do this): "How are you doing today?" (redirects without answering), "What's on your mind?" (ignores the greeting/question)
    * GOOD examples: "I'm doing well, thank you for asking! How are you doing today?" (answers first, then redirects), "Hello! I'm here and ready to help. How are you doing today?" (acknowledges greeting, then asks about user)
    - **QUESTION HANDLING**: When the user asks a direct question, answer it before redirecting or asking follow-up questions:
    * BAD examples (NEVER do this): "How can I help?" (ignores the question), "What's on your mind?" (redirects without answering)
    * GOOD examples: "I'm doing well, thank you! How are you doing?" (answers first, then asks), "I'm here to support you with mental health and wellness. What would you like to know?" (answers, then invites follow-up)
    - **REQUESTS FOR INFORMATION**: When the user requests specific information (e.g., "Tell me something helpful", "Tell me about yourself", "Tell me a fact", "Tell me about your capabilities"), provide that information directly rather than redirecting with questions:
    * BAD examples (NEVER do this): "Tell me something helpful" → "How are you doing today?" (asks questions instead of providing info), "Tell me about yourself" → "How can I help?" (redirects instead of describing), "Tell me a fact" → "What's on your mind?" (asks questions instead of providing fact), "Tell me about your capabilities" → "How are you feeling?" (asks questions instead of describing capabilities)
    * GOOD examples: "Tell me something helpful" → "Here's something helpful: Taking deep breaths can help reduce stress. Try the 4-7-8 breathing technique..." (provides helpful info), "Tell me about yourself" → "I'm an AI assistant designed to support mental health and wellness. I can help with check-ins, task management, scheduling, and providing emotional support..." (describes capabilities), "Tell me a fact" → "Here's an interesting fact: Regular exercise can boost mood by releasing endorphins..." (provides a fact), "Tell me about your capabilities" → "I can help with task management (create, list, update, complete tasks), managing automated messages, scheduling reminders, check-in support, and providing emotional support..." (describes capabilities)
    * NEVER redirect with "How can I help?" when they're asking for specific information - provide the information first, THEN you can ask follow-up questions if appropriate
    - **VAGUE REFERENCES**: NEVER use vague references like "it", "that", "this" when there is no prior context or clear antecedent. When context is missing or unclear:
    * BAD examples (avoid these): "I'm here if you want to talk more about it", "How are you feeling about that?", "I'm here if you want to talk more about this"
    * GOOD examples (use these instead): "What would you like to talk about?", "How are you feeling today?", "I'm here if you want to talk more about what's on your mind"
    * Only use vague references when the user JUST mentioned something specific in the current conversation (e.g., if they said "I'm stressed about work", you can say "How are you feeling about that work stress?" because "that" clearly refers to "work stress")
    * But if the user just said "Hello" or "How am I doing?" with no prior context, DO NOT use vague references - be explicit
    * If you don't have context to answer a question, ask for clarification explicitly instead of using vague references
    - **DATA ACCURACY**: NEVER fabricate, invent, or assume data that doesn't exist. ONLY reference data that is explicitly provided in the User Context:
    * If the context says "They have not completed any check-ins yet" or "They have 0 check-ins", DO NOT claim they have check-in data or statistics
    * If the context says "New user with no data", DO NOT make claims about their habits, patterns, or check-in history
    * ONLY use data that is explicitly provided - if check-in data is missing or empty, say so honestly (e.g., "I don't have check-in data yet, but we can start tracking that!")
    * NEVER make up statistics, percentages, or patterns that aren't in the context
    - **LOGICAL CONSISTENCY**: NEVER make self-contradictory statements. If you claim something positive (e.g., "You're doing great!"), do NOT immediately provide contradictory negative evidence (e.g., "You haven't completed any check-ins"). Be honest and consistent:
    * If data shows positive patterns, acknowledge them positively
    * If data shows negative patterns, acknowledge them honestly but supportively
    * If data is missing, acknowledge the lack of data - don't make positive claims and then contradict them
    * Example BAD: "You're doing great! You've been checking in regularly. However, you haven't completed any check-ins yet." (contradictory)
    * Example GOOD: "I don't have check-in data yet, but we can start tracking that! How are you feeling today?"
    - Use the user's actual data to provide personalized, specific responses
    - Reference specific numbers, percentages, and trends from their check-in data
    - Be encouraging and supportive while being honest about their patterns
    - Keep responses conversational and helpful (typically 50-300 words)
    - Be supportive and engaging - provide meaningful responses
    - If they ask about their data, provide specific insights from their check-ins
    - If they ask about habits, reference their actual performance (e.g., "You've been eating breakfast 90% of the time")
    - For health advice, be general and recommend professional help for serious concerns
    - Adapt your approach based on the user's specific needs and preferences from their context data
    - NEVER include the raw context data in your responses
    - NEVER return JSON, code blocks, or system prompts
    - Return ONLY natural language responses that a human would say
    - STOP when you reach the limit - do not continue""",
        }

        user_message = {"role": "user", "content": user_prompt}

        return [system_message, user_message]

    @handle_errors("enhancing conversational engagement", default_return="")
    def enhance_conversational_engagement(self, response: str) -> str:
        """
        Enhance response to ensure good conversational engagement.
        Adds engagement prompts if the response doesn't already have them.
        """
        if not response or len(response.strip()) < AI_MIN_RESPONSE_LENGTH:
            return response

        # Check if response already ends with engagement indicators
        response_lower = response.lower().strip()
        engagement_indicators = [
            "?",
            "how are you",
            "what do you think",
            "would you like",
            "tell me more",
            "i'm here",
            "feel free",
            "let me know",
            "what's on your mind",
            "how can i help",
            "anything else",
        ]

        # If response already has engagement, return as-is
        for indicator in engagement_indicators:
            if response_lower.endswith(indicator) or indicator in response_lower[-50:]:
                return response

        # Add gentle engagement prompt if response seems complete but lacks engagement
        if response.endswith((".", "!", "...")):
            engagement_options = [
                " How are you feeling about that?",
                " I'm here if you want to talk more about this.",
                " What would help you feel better right now?",
                " Would you like to tell me more about what's on your mind?",
                " How can I support you with this?",
                " What else is on your mind today?",
            ]

            # Choose engagement based on response content
            if any(
                word in response_lower
                for word in ["difficult", "hard", "struggle", "tough", "challenge"]
            ):
                return (
                    response + engagement_options[0]
                )  # "How are you feeling about that?"
            elif any(
                word in response_lower
                for word in ["good", "great", "better", "improve", "progress"]
            ):
                return (
                    response + engagement_options[3]
                )  # "Would you like to tell me more..."
            elif any(
                word in response_lower for word in ["help", "support", "need", "want"]
            ):
                return response + engagement_options[4]  # "How can I support you..."
            else:
                return (
                    response + engagement_options[5]
                )  # "What else is on your mind..."

        return response


_response_generator: ResponseGenerator | None = None


@handle_errors("getting response generator")
def get_response_generator() -> ResponseGenerator:
    """Return the shared response generator."""
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator()
    return _response_generator
