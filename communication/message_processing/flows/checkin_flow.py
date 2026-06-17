# communication/message_processing/flows/checkin_flow.py

"""Check-in conversation flow mixin."""

import importlib
from contextlib import suppress
from datetime import timedelta

from checkins.checkin_data_manager import get_recent_checkins
from core import get_user_data
from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import now_datetime_full, now_timestamp_full, parse_timestamp_full

from communication.message_processing.flows.flow_constants import (
    CHECKIN_INACTIVITY_MINUTES,
    CHECKIN_START,
    FLOW_CHECKIN,
    QUESTION_STATES,
)
from communication.message_processing.flows.flow_state import FlowStateMixin

logger = get_component_logger("communication_manager")


class CheckinFlowMixin(FlowStateMixin):
    @handle_errors(
        "starting dynamic checkin",
        default_return=(
            "I'm having trouble starting your check-in. Please try again.",
            True,
        ),
    )
    def _start_dynamic_checkin(self, user_id: str) -> tuple[str, bool]:
        """Start a dynamic check-in flow based on user preferences with weighted question selection"""

        # Get user's check-in preferences
        prefs_result = get_user_data(user_id, "preferences")
        checkin_prefs = prefs_result.get("preferences", {}).get("checkin_settings", {})
        enabled_questions = checkin_prefs.get("questions", {})

        # Merge custom questions into enabled_questions
        custom_questions = checkin_prefs.get("custom_questions", {})
        for custom_key, custom_def in custom_questions.items():
            # Only include if enabled
            if custom_def.get("enabled", False):
                enabled_questions[custom_key] = {
                    "enabled": True,
                    "label": custom_def.get("ui_display_name", custom_key),
                }

        cached_order = self._get_cached_checkin_order(user_id)

        # Use weighted selection for question order unless a same-day cache exists
        question_order = cached_order or self._select_checkin_questions_with_weighting(
            user_id, enabled_questions
        )
        if cached_order:
            logger.info(
                f"FLOW_STATE_CREATE: Reusing cached check-in question order for user {user_id}"
            )

        if not question_order:
            return (
                "No check-in questions are enabled. Please configure your check-in settings.",
                True,
            )

        # Initialize user state with dynamic question order
        user_state = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_START,
            "data": {},
            "question_order": question_order,
            "current_question_index": 0,
            "started_at": now_timestamp_full(),
            "last_activity": now_timestamp_full(),
        }
        self.user_states[user_id] = user_state

        logger.info(
            f"FLOW_STATE_CREATE: Created new check-in flow for user {user_id} | "
            f"Questions: {len(question_order)} | Order: {question_order[:3]}..."
        )
        self._save_user_states()

        # Compose user-requested intro plus first question
        first_question_key = question_order[0]
        first_question_text = self._get_question_text(first_question_key, {}, user_id)
        intro = (
            "🌟 Check-in Time! 🌟\n\n"
            "Hi! It's time for your check-in. This helps me understand how you're doing and provide better support.\n\n"
            f"Let's start: {first_question_text}"
        )

        # Update state to current question without advancing index
        user_state["state"] = QUESTION_STATES.get(first_question_key, CHECKIN_START)
        logger.info(
            f"FLOW_STATE_CREATE: Check-in flow initialized successfully for user {user_id} | First question: {first_question_key}"
        )
        return (intro, False)
    @handle_errors(
        "getting personalized welcome",
        default_return="🌟 Hello! Let's take a moment to check in on how you're feeling today.\n\nI have some quick questions for you today. Type /cancel anytime to skip.",
    )
    def _get_personalized_welcome(self, user_id: str, question_count: int) -> str:
        """Generate a personalized welcome message based on user history"""
        # Get recent check-ins for context
        recent_checkins = get_recent_checkins(user_id, limit=3)

        if recent_checkins:
            # Analyze recent mood trends
            recent_moods = [c.get("mood", 3) for c in recent_checkins if c.get("mood")]
            avg_mood = sum(recent_moods) / len(recent_moods) if recent_moods else 3

            if avg_mood >= 4:
                welcome = "🌟 Great to see you again! I've noticed you've been feeling pretty good lately."
            elif avg_mood <= 2:
                welcome = "🌟 Hi there! I'm here to support you. Let's check in on how you're doing today."
            else:
                welcome = "🌟 Hello! Let's take a moment to check in on how you're feeling today."
        else:
            welcome = (
                "🌟 Welcome to your first check-in! Let's get to know how you're doing."
            )

        return f"{welcome}\n\nI have {question_count} quick questions for you today. Type /cancel anytime to skip."
    @handle_errors(
        "getting next question",
        default_return=(
            "I'm having trouble with the check-in flow. Let's start over.",
            True,
        ),
    )
    def _get_next_question(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Get the next question in the check-in flow"""
        question_order = user_state.get("question_order", [])
        current_index = user_state.get("current_question_index", 0)

        if current_index >= len(question_order):
            # All questions completed
            return self._complete_checkin(user_id, user_state)

        question_key = question_order[current_index]
        question_data = user_state.get("data", {})

        # Get question text based on type (pass user_id for custom questions)
        question_text = self._get_question_text(question_key, question_data, user_id)

        # Update state to current question
        user_state["state"] = QUESTION_STATES.get(question_key, CHECKIN_START)

        return (question_text, False)
    @handle_errors(
        "getting question text", default_return="Please answer this question:"
    )
    def _get_question_text(
        self, question_key: str, previous_data: dict, user_id: str | None = None
    ) -> str:
        """Get appropriate question text based on question type and previous responses"""
        # Import the dynamic checkin manager
        from checkins.checkin_dynamic_manager import dynamic_checkin_manager

        # Get the question text from the dynamic manager (pass user_id for custom questions)
        question_text = dynamic_checkin_manager.get_question_text(question_key, user_id)

        # If this is not the first question and we have previous data,
        # check if we should add a response statement
        if previous_data and len(previous_data) > 0:
            # Find the most recent question that was answered
            # We'll use the last key in previous_data as a simple approach
            recent_questions = list(previous_data.keys())
            if recent_questions:
                last_question = recent_questions[-1]
                last_answer = previous_data[last_question]

                # Build the question with response statement
                return dynamic_checkin_manager.build_next_question_with_response(
                    question_key, last_question, last_answer
                )

        return question_text
    @handle_errors(
        "handling checkin",
        default_return=(
            "I'm having trouble with the check-in. Let's start over.",
            True,
        ),
    )
    def _handle_checkin(
        self, user_id: str, user_state: dict, message_text: str
    ) -> tuple[str, bool]:
        """
        Enhanced check-in flow with dynamic questions and better validation
        """
        # Idle expiry: CHECKIN_INACTIVITY_MINUTES since last activity
        try:
            last_ts = user_state.get("last_activity")
            if last_ts:
                # last_activity is internal persisted state (string timestamp).
                # Parse strictly using canonical helper.
                last_dt = parse_timestamp_full(last_ts)
                if last_dt is not None and now_datetime_full() - last_dt > timedelta(
                    minutes=CHECKIN_INACTIVITY_MINUTES
                ):
                    # Expire flow due to inactivity
                    self._cache_expired_checkin_order(user_id, user_state)
                    self._save_user_states()
                    return (
                        "The previous check-in expired due to inactivity. You can start a new one with /checkin.",
                        True,
                    )
        except Exception:
            pass

        if message_text.lower().startswith("/cancel"):
            self._clear_flow_state(user_id, mark_completion=True)
            return (
                "Check-in canceled. You can start again anytime with /checkin",
                True,
            )

        # If the user sends a clear slash/bang command unrelated to check-in, expire and hand off
        stripped = message_text.strip().lower()
        if stripped.startswith("/") or stripped.startswith("!"):
            # Allow restarting or canceling without expiry message here
            if stripped.startswith("/checkin") or stripped.startswith("!checkin"):
                return (
                    "You're already in a check-in. Type /cancel to cancel the current one, or continue answering.",
                    False,
                )
            if stripped.startswith("/cancel") or stripped.startswith("!cancel"):
                self._clear_flow_state(user_id, mark_completion=True)
                return (
                    "Check-in canceled. You can start again anytime with /checkin",
                    True,
                )

            # Handle /tasks and !tasks explicitly to ensure proper delegation
            if stripped in ["/tasks", "!tasks"]:
                # Expire check-in flow
                self._clear_flow_state(user_id, mark_completion=True)
                # Directly call task handler to avoid parsing issues
                try:
                    from communication.command_handlers.task_handler import (
                        TaskManagementHandler,
                    )

                    handler = TaskManagementHandler()
                    from communication.command_handlers.shared_types import (
                        ParsedCommand,
                    )

                    parsed_cmd = ParsedCommand("list_tasks", {}, 1.0, "show my tasks")
                    response = handler.handle(user_id, parsed_cmd)
                    return (response.message, response.completed)
                except Exception as e:
                    logger.error(
                        f"Error handling /tasks command during checkin for user {user_id}: {e}"
                    )
                    try:
                        _im = importlib.import_module(
                            "communication.message_processing.interaction_manager"
                        )
                        response = _im.handle_user_message(
                            user_id, message_text, "discord"
                        )
                        return (response.message, response.completed)
                    except Exception:
                        return (
                            "I've closed the current check-in. What would you like to do? Try /tasks, /messages, /profile, or /status.",
                            True,
                        )

            # Expire current check-in and delegate to interaction manager
            with suppress(Exception):
                self._clear_flow_state(user_id, mark_completion=True)

            try:
                _im = importlib.import_module(
                    "communication.message_processing.interaction_manager"
                )
                response = _im.handle_user_message(user_id, message_text, "discord")
                return (response.message, response.completed)
            except Exception:
                return (
                    "I've closed the current check-in. What would you like to do? Try /tasks, /messages, /profile, or /status.",
                    True,
                )

        data = user_state["data"]
        question_order = user_state.get("question_order", [])
        current_index = user_state.get("current_question_index", 0)

        if current_index >= len(question_order):
            return self._complete_checkin(user_id, user_state)

        question_key = question_order[current_index]

        # Validate and store the response (pass user_id for custom questions)
        validation_result = self._validate_response(question_key, message_text, user_id)
        if not validation_result["valid"]:
            return (validation_result["message"], False)

        # Store the validated response
        data[question_key] = validation_result["value"]

        # Move to next question and update activity
        user_state["current_question_index"] = current_index + 1
        with suppress(Exception):
            user_state["last_activity"] = now_timestamp_full()

        self._save_user_states()

        # Get next question or complete
        return self._get_next_question(user_id, user_state)
    @handle_errors(
        "validating response",
        default_return={
            "valid": False,
            "value": None,
            "message": "I didn't understand that response. Please try again.",
        },
    )
    def _validate_response(
        self, question_key: str, response: str, user_id: str | None = None
    ) -> dict:
        """Validate user response based on question type using dynamic manager"""
        # Import the dynamic checkin manager
        from checkins.checkin_dynamic_manager import dynamic_checkin_manager

        # Use the dynamic manager to validate the response (pass user_id for custom questions)
        is_valid, value, error_message = dynamic_checkin_manager.validate_answer(
            question_key, response, user_id
        )

        return {"valid": is_valid, "value": value, "message": error_message}
    @handle_errors(
        "completing checkin",
        default_return=(
            "Thanks for completing your check-in! There was an issue saving your responses, but I've recorded what I could.",
            True,
        ),
    )
    def _complete_checkin(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Complete the check-in and provide personalized feedback"""
        data = user_state["data"]
        question_order = user_state.get("question_order", [])

        # Add questions asked to the data for future weighting
        data["questions_asked"] = question_order

        # Store the check-in data using modern function
        from checkins.checkin_data_manager import store_checkin_response

        store_checkin_response(user_id, data)

        # Log user activity for check-in completion
        from core.logger import get_component_logger

        user_logger = get_component_logger("user_activity")
        user_logger.info(
            "User check-in completed",
            user_id=user_id,
            questions_answered=len(data),
            mood=data.get("mood"),
            energy=data.get("energy"),
            sleep_quality=data.get("sleep_quality"),
        )

        # Generate personalized completion message
        completion_message = self._generate_completion_message(user_id, data)

        # Clear the user state
        self._clear_flow_state(user_id, mark_completion=True)

        return (completion_message, True)
    @handle_errors(
        "handling command during checkin",
        default_return=(
            "I'm having trouble with that command right now. Please continue with your check-in.",
            False,
        ),
    )
    def _handle_command_during_checkin(
        self, user_id: str, message_text: str
    ) -> tuple[str, bool]:
        """Handle common commands while user is in a checkin flow"""
        message_lower = message_text.lower().strip()

        # Handle help command
        if message_lower in ["/help", "!help", "/commands", "!commands"]:
            return (
                "You're currently in a check-in. Here are your options:\n"
                "• Continue answering the questions\n"
                "• Type `/cancel` to cancel the check-in\n"
                "• Type `/clear` to clear stuck flows\n"
                "• Type `/tasks` to see your tasks\n"
                "• Type `/profile` to see your profile\n"
                "• Type `/status` to see your status",
                False,
            )

        # Handle clear command
        elif message_lower in ["/clear", "!clear"]:
            return self.clear_stuck_flows(user_id)

        # Handle tasks command
        elif message_lower in ["/tasks", "!tasks"]:
            from communication.command_handlers.interaction_handlers import (
                get_interaction_handler,
            )

            handler = get_interaction_handler("list_tasks")
            if handler is None:
                from communication.command_handlers.task_handler import (
                    TaskManagementHandler,
                )

                handler = TaskManagementHandler()
            response = handler.handle_list_tasks(user_id, {})
            return (response.message, False)

        # Handle profile command
        elif message_lower in ["/profile", "!profile"]:
            from communication.command_handlers.interaction_handlers import (
                get_interaction_handler,
            )

            handler = get_interaction_handler("show_profile")
            if handler is None:
                return (
                    "I couldn't load the profile handler. Please try again.",
                    False,
                )
            response = handler.handle_show_profile(user_id, {})
            return (response.message, False)

        # Handle status command
        elif message_lower in ["/status", "!status"]:
            from communication.command_handlers.interaction_handlers import (
                get_interaction_handler,
            )

            handler = get_interaction_handler("show_analytics")
            if handler is None:
                return (
                    "I couldn't load the status handler. Please try again.",
                    False,
                )
            response = handler.handle_show_status(user_id, {})
            return (response.message, False)

        # Handle analytics command
        elif message_lower in ["/analytics", "!analytics"]:
            from communication.command_handlers.interaction_handlers import (
                get_interaction_handler,
            )

            handler = get_interaction_handler("show_analytics")
            if handler is None:
                return (
                    "I couldn't load the analytics handler. Please try again.",
                    False,
                )
            response = handler.handle_show_analytics(user_id, {})
            return (response.message, False)

        # Handle schedule command
        elif message_lower in ["/schedule", "!schedule"]:
            from communication.command_handlers.interaction_handlers import (
                get_interaction_handler,
            )

            handler = get_interaction_handler("show_schedule")
            if handler is None:
                return (
                    "I couldn't load the schedule handler. Please try again.",
                    False,
                )
            response = handler.handle_show_schedule(user_id, {})
            return (response.message, False)

        # Handle messages command
        elif message_lower in ["/messages", "!messages"]:
            from communication.command_handlers.interaction_handlers import (
                get_interaction_handler,
            )

            handler = get_interaction_handler("messages")
            if handler is None:
                return (
                    "I couldn't load the messages handler. Please try again.",
                    False,
                )
            show_fn = getattr(handler, "handle_show_messages", None)
            if not callable(show_fn):
                return ("Messages command is not available right now.", False)
            response = show_fn(user_id, {})
            msg = (
                getattr(response, "message", str(response))
                if response is not None
                else ""
            )
            return (msg, False)

        # Unknown command
        else:
            return (
                f"Unknown command: {message_text}\n"
                "You're currently in a check-in. Type `/help` for available commands or continue answering the questions.",
                False,
            )
    @handle_errors(
        "generating completion message",
        default_return="✅ Check-in complete! Thanks for taking the time. See you next time! 🌟",
    )
    def _generate_completion_message(self, user_id: str, data: dict) -> str:
        """Generate a personalized completion message based on responses"""
        # Base completion message
        message = "✅ Check-in complete! Thanks for taking the time.\n\n"

        # Add personalized insights
        insights = []

        # Mood insights
        mood = data.get("mood")
        if mood is not None:
            if mood >= 4:
                insights.append("🌟 Great mood today!")
            elif mood <= 2:
                insights.append(
                    "💙 I hope tomorrow is better. Remember, it's okay to not be okay."
                )
            else:
                insights.append("😊 Solid mood today!")

        # Energy insights
        energy = data.get("energy")
        if energy is not None and energy <= 2:
            insights.append(
                "⚡ Low energy - maybe try a short walk or some gentle stretching?"
            )

        # Sleep insights
        sleep_hours = data.get("sleep_hours")
        sleep_schedule = data.get("sleep_schedule")
        if isinstance(sleep_schedule, dict):
            total_sleep_hours = sleep_schedule.get("total_sleep_hours")
            if isinstance(total_sleep_hours, (int, float)):
                sleep_hours = float(total_sleep_hours)
        sleep_quality = data.get("sleep_quality")
        if isinstance(sleep_hours, (int, float)) and sleep_hours < 6:
            insights.append("😴 You might need more sleep tonight.")
        elif sleep_quality is not None and sleep_quality <= 2:
            insights.append(
                "😴 Sleep quality could be better - consider a bedtime routine."
            )

        # Add insights
        if insights:
            message += "💭 " + " ".join(insights) + "\n\n"

        # Encouragement
        message += (
            "You're doing great by checking in with yourself. See you next time! 🌟"
        )

        return message
    @handle_errors("selecting check-in questions with weighted randomization")
    def _select_checkin_questions_with_weighting(
        self, user_id: str, enabled_questions: dict
    ) -> list:
        """
        Select check-in questions using weighted randomization with always/sometimes and min/max configuration.

        Args:
            user_id: User ID
            enabled_questions: Dictionary of enabled questions from user preferences
                Each question can have:
                - 'enabled': bool (whether question is enabled)
                - 'always_include': bool (whether to always include this question)
                - 'sometimes_include': bool (whether to sometimes include this question)

        Returns:
            List of question keys in selected order
        """
        try:
            import random

            # Get user's check-in preferences for min/max settings
            prefs_result = get_user_data(user_id, "preferences")
            checkin_prefs = prefs_result.get("preferences", {}).get(
                "checkin_settings", {}
            )
            min_questions = checkin_prefs.get("min_questions", 1)
            max_questions = checkin_prefs.get("max_questions", 8)

            # Separate questions into always, sometimes, and disabled
            always_questions = []
            sometimes_questions = []

            for key, data in enabled_questions.items():
                if not data.get("enabled", False):
                    continue

                if data.get("always_include", False):
                    always_questions.append(key)
                elif data.get("sometimes_include", False):
                    sometimes_questions.append(key)
                else:
                    # Default: treat as sometimes if not specified
                    sometimes_questions.append(key)

            # Validate min/max constraints
            total_enabled = len(always_questions) + len(sometimes_questions)
            if total_enabled == 0:
                return []

            # Ensure min is at least number of always questions (+1 if any sometimes)
            min_required = len(always_questions)
            if sometimes_questions and min_required == len(always_questions):
                min_required = max(min_required, len(always_questions) + 1)
            min_questions = max(min_questions, min_required, 1)  # Absolute minimum is 1

            # Ensure max is valid
            max_questions = min(max_questions, total_enabled)
            max_questions = max(max_questions, min_questions)

            # Start with always questions
            selected_questions = always_questions.copy()

            # If we already have enough, return early
            if len(selected_questions) >= max_questions:
                random.shuffle(selected_questions)
                return selected_questions[:max_questions]

            # If we need more questions, select from sometimes questions
            if sometimes_questions:
                # Calculate how many more we need
                remaining_slots = max_questions - len(selected_questions)
                needed = max(min_questions - len(selected_questions), 0)

                # Get recent check-in history to avoid repetition
                recent_checkins = get_recent_checkins(user_id, limit=5)
                recently_asked = set()

                # Extract recently asked questions from the last 3 check-ins
                for checkin in recent_checkins[-3:]:
                    if "questions_asked" in checkin:
                        recently_asked.update(checkin["questions_asked"])

                # Define question categories for variety
                question_categories = {
                    "mood": [
                        "mood",
                        "energy",
                        "stress_level",
                        "anxiety_level",
                        "hopelessness_level",
                        "irritability_level",
                    ],
                    "health": [
                        "ate_breakfast",
                        "brushed_teeth",
                        "medication_taken",
                        "exercise",
                        "hydration",
                        "treatment_adherence",
                    ],
                    "sleep": ["sleep_quality", "sleep_schedule"],
                    "social": ["social_interaction"],
                    "reflection": [
                        "focus_level",
                        "daily_reflection",
                        "motivation_level",
                    ],
                }

                # Calculate weights for sometimes questions
                question_weights = []

                for question_key in sometimes_questions:
                    weight = 1.0  # Base weight

                    # Reduce weight for recently asked questions
                    if question_key in recently_asked:
                        weight *= 0.3  # 70% reduction for recently asked

                    # Boost weight for questions from underrepresented categories
                    question_category = None
                    for category, questions in question_categories.items():
                        if question_key in questions:
                            question_category = category
                            break

                    if question_category:
                        # Count how many questions from this category were recently asked
                        category_recent_count = sum(
                            1
                            for q in recently_asked
                            if q in question_categories.get(question_category, [])
                        )
                        if category_recent_count == 0:
                            weight *= 1.5  # Boost for underrepresented categories
                        elif category_recent_count >= 2:
                            weight *= 0.7  # Reduce for overrepresented categories

                    # Add some randomness to prevent predictable patterns
                    weight *= random.uniform(0.8, 1.2)

                    question_weights.append((question_key, weight))

                # Sort by weight (highest first)
                question_weights.sort(key=lambda x: x[1], reverse=True)

                # Select enough questions to meet minimum, up to maximum
                num_to_select = min(remaining_slots, len(sometimes_questions))
                num_to_select = max(num_to_select, needed)  # Ensure we meet minimum

                selected_sometimes = [q[0] for q in question_weights[:num_to_select]]
                selected_questions.extend(selected_sometimes)

            # Shuffle the final order for additional randomness (but keep always questions distributed)
            random.shuffle(selected_questions)

            # Ensure we don't exceed max
            selected_questions = selected_questions[:max_questions]

            logger.debug(
                f"Selected {len(selected_questions)} check-in questions for user {user_id} (always: {len(always_questions)}, sometimes: {len(sometimes_questions)}): {selected_questions}"
            )

            return selected_questions

        except Exception as e:
            logger.error(f"Error selecting check-in questions with weighting: {e}")
            # Fallback: return all enabled questions
            enabled_keys = [
                key
                for key, data in enabled_questions.items()
                if data.get("enabled", False)
            ]
            if not enabled_keys:
                return []
            import random

            return random.sample(enabled_keys, min(len(enabled_keys), 6))
