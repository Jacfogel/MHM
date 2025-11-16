# communication/message_processing/conversation_flow_manager.py

"""
conversation_flow_manager.py

Provides a single place to handle 'conversation flows' that can be used
by any platform: Discord, Email, etc.

We keep track of each user's 'state' in a dictionary, so if a user is in the middle
of check-in or an AI chat flow, we know what question to ask next.

Usage:
  1) The platform bot receives a message or command from user_id.
  2) That bot calls: conversation_manager.handle_inbound_message(user_id, message_text).
  3) This returns (reply_text, completed). The bot sends reply_text to the user.
  4) If completed == True, the flow is done, so we remove them from user_states.
"""

import os
import json
from pathlib import Path
from ai.chatbot import get_ai_chatbot
from core.logger import get_component_logger
from core.user_data_handlers import get_user_data
from core.response_tracking import (
    is_user_checkins_enabled,
    get_recent_checkins,
)
from core.error_handling import handle_errors

# Route conversation orchestration to communication_manager component log
logger = get_component_logger('communication_manager')

# We'll define 'flow' constants
FLOW_NONE = 0
FLOW_CHECKIN = 1
FLOW_TASK_REMINDER = 2



# We'll define states for check-in - now dynamic based on user preferences
CHECKIN_START = 100
CHECKIN_MOOD = 101
CHECKIN_BREAKFAST = 102
CHECKIN_ENERGY = 103
CHECKIN_TEETH = 104
CHECKIN_SLEEP_QUALITY = 105
CHECKIN_SLEEP_HOURS = 106
CHECKIN_ANXIETY = 107
CHECKIN_FOCUS = 108
CHECKIN_MEDICATION = 109
CHECKIN_EXERCISE = 110
CHECKIN_HYDRATION = 111
CHECKIN_SOCIAL = 112
CHECKIN_STRESS = 113
CHECKIN_REFLECTION = 114
CHECKIN_COMPLETE = 200

# Question mapping for dynamic flow
QUESTION_STATES = {
    'mood': CHECKIN_MOOD,
    'ate_breakfast': CHECKIN_BREAKFAST,
    'energy': CHECKIN_ENERGY,
    'brushed_teeth': CHECKIN_TEETH,
    'sleep_quality': CHECKIN_SLEEP_QUALITY,
    'sleep_hours': CHECKIN_SLEEP_HOURS,
    'anxiety_level': CHECKIN_ANXIETY,
    'focus_level': CHECKIN_FOCUS,
    'medication_taken': CHECKIN_MEDICATION,
    'exercise': CHECKIN_EXERCISE,
    'hydration': CHECKIN_HYDRATION,
    'social_interaction': CHECKIN_SOCIAL,
    'stress_level': CHECKIN_STRESS,
    'daily_reflection': CHECKIN_REFLECTION
}

class ConversationManager:
    @handle_errors("initializing conversation flow manager", default_return=None)
    def __init__(self):
        # Store user states: { user_id: {"flow": FLOW_..., "state": int, "data": {}, "question_order": [] } }
        """Initialize the object."""
        self.user_states = {}
        # Use BASE_DATA_DIR from config to respect test environment
        from core.config import BASE_DATA_DIR
        self._state_file = str(Path(BASE_DATA_DIR) / "conversation_states.json")
        self._load_user_states()

    def _load_user_states(self) -> None:
        """Load user states from disk with comprehensive logging"""
        try:
            if os.path.exists(self._state_file):
                with open(self._state_file, 'r', encoding='utf-8') as f:
                    self.user_states = json.load(f)
                logger.info(f"FLOW_STATE_LOAD: Loaded {len(self.user_states)} user states from disk | File: {self._state_file}")
                for user_id, state in self.user_states.items():
                    logger.info(f"FLOW_STATE_LOAD: User {user_id} | flow={state.get('flow')}, state={state.get('state')}, question_index={state.get('current_question_index')}, questions={len(state.get('question_order', []))}")
            else:
                logger.debug(f"FLOW_STATE_LOAD: No existing conversation states file found at {self._state_file}")
        except Exception as e:
            logger.error(f"FLOW_STATE_LOAD_ERROR: Failed to load user states from {self._state_file}: {e}", exc_info=True)
            self.user_states = {}

    def _save_user_states(self) -> None:
        """Save user states to disk with comprehensive logging and error handling"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
            
            with open(self._state_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_states, f, indent=2)
            logger.debug(f"FLOW_STATE_SAVE: Saved {len(self.user_states)} user states to disk | File: {self._state_file}")
            for user_id, state in self.user_states.items():
                logger.debug(f"FLOW_STATE_SAVE: User {user_id} | flow={state.get('flow')}, state={state.get('state')}, question_index={state.get('current_question_index')}")
        except PermissionError as e:
            logger.error(f"FLOW_STATE_SAVE_ERROR: Permission denied saving to {self._state_file}: {e}", exc_info=True)
        except IOError as e:
            logger.error(f"FLOW_STATE_SAVE_ERROR: IO error saving to {self._state_file}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"FLOW_STATE_SAVE_ERROR: Unexpected error saving user states: {e}", exc_info=True)

    def expire_checkin_flow_due_to_unrelated_outbound(self, user_id: str) -> None:
        """Expire an active check-in flow when an unrelated outbound message is sent.
        Safe no-op if no flow or different flow is active.
        """
        try:
            user_state = self.user_states.get(user_id)
            if user_state and user_state.get("flow") == FLOW_CHECKIN:
                # Log details before expiration
                question_index = user_state.get('current_question_index', 0)
                total_questions = len(user_state.get('question_order', []))
                logger.info(f"FLOW_STATE_EXPIRE: Expiring active check-in flow for user {user_id} due to unrelated outbound message | Progress: {question_index}/{total_questions} questions")
                
                # End the flow silently
                self.user_states.pop(user_id, None)
                self._save_user_states()
                logger.info(f"FLOW_STATE_EXPIRE: Successfully expired and saved state for user {user_id}")
            else:
                if not user_state:
                    logger.debug(f"FLOW_STATE_EXPIRE: No flow state found for user {user_id}, nothing to expire")
                else:
                    logger.debug(f"FLOW_STATE_EXPIRE: User {user_id} has flow={user_state.get('flow')}, not check-in, skipping expiration")
        except Exception as e:
            # Don't let this affect outbound sending
            logger.error(f"FLOW_STATE_EXPIRE_ERROR: Could not expire check-in flow for user {user_id}: {e}", exc_info=True)

    @handle_errors("handling inbound message", default_return=("I'm having trouble processing your message right now. Please try again in a moment.", True))
    def handle_inbound_message(self, user_id: str, message_text: str) -> tuple[str, bool]:
        """
        Primary entry point. Takes user's message and returns a (reply_text, completed).
        
        Now defaults to contextual chat for all messages unless user is in a specific flow
        or uses a special command.
        """
        user_state = self.user_states.get(user_id, {"flow": FLOW_NONE, "state": 0, "data": {}})

        # Check if user wants to start a specific flow or use special commands
        if user_state["flow"] == FLOW_NONE:
            # Handle special commands that start specific flows
            if message_text.lower().startswith("/checkin"):
                # Check if check-ins are enabled for this user
                if not is_user_checkins_enabled(user_id):
                    # Clear any existing state for this user
                    self.user_states.pop(user_id, None)
                    self._save_user_states()
                    return (
                        "Check-ins are not enabled for your account. Please contact an administrator to enable check-ins.",
                        True
                    )
                
                # Initialize dynamic check-in flow based on user preferences
                return self._start_dynamic_checkin(user_id)

            elif message_text.lower().startswith("/cancel"):
                return ("Nothing to cancel. You're not in a conversation flow.", True)

            else:
                # Default to contextual chat for all other messages
                # This provides rich, personalized responses using the user's context
                ai_bot = get_ai_chatbot()
                reply = ai_bot.generate_contextual_response(user_id, message_text, timeout=10)
                return (reply, True)  # Single response, no ongoing flow

        # If user is mid-flow, continue the appropriate flow
        flow = user_state["flow"]
        if flow == FLOW_CHECKIN:
            return self._handle_checkin(user_id, user_state, message_text)
        elif flow == FLOW_TASK_REMINDER:
            # Check if user is trying to issue a command instead of responding to reminder question
            # Commands like "update task", "complete task", "delete task" should clear the flow
            message_lower = message_text.lower().strip()
            command_keywords = ['update task', 'complete task', 'delete task', 'show tasks', 'list tasks', '/cancel', 'cancel']
            if any(message_lower.startswith(keyword) for keyword in command_keywords):
                # User is issuing a command, clear the flow and let the command be processed
                logger.debug(f"User in FLOW_TASK_REMINDER but issued command '{message_text}', clearing flow")
                self.user_states.pop(user_id, None)
                self._save_user_states()
                return ("", True)  # Return empty to let command be processed
            return self._handle_task_reminder_followup(user_id, user_state, message_text)
        else:
            # Unknown flow - reset to default contextual chat
            self.user_states.pop(user_id, None)
            self._save_user_states()
            ai_bot = get_ai_chatbot()
            reply = ai_bot.generate_contextual_response(user_id, message_text, timeout=10)
            return (reply, True)

    @handle_errors("starting checkin", default_return=("I'm having trouble starting your check-in. Please try again.", True))
    def start_checkin(self, user_id: str) -> tuple[str, bool]:
        """
        Public method to start a check-in flow for a user.
        This is the proper way to initiate check-ins from external modules.
        """
        # Check if check-ins are enabled for this user
        if not is_user_checkins_enabled(user_id):
            # Clear any existing state for this user
            self.user_states.pop(user_id, None)
            self._save_user_states()
            return (
                "Check-ins are not enabled for your account. Please contact an administrator to enable check-ins.",
                True
            )
        
        # Check if user already has an active checkin flow
        existing_state = self.user_states.get(user_id)
        if existing_state and existing_state.get("flow") == FLOW_CHECKIN:
            # User already has an active checkin - ask if they want to restart
            return (
                "You already have a check-in in progress. Type /cancel to cancel the current check-in, or continue answering the questions.",
                False
            )
        
        # Initialize dynamic check-in flow based on user preferences
        result = self._start_dynamic_checkin(user_id)
        
        # Log user activity for check-in start
        from core.logger import get_component_logger
        user_logger = get_component_logger('user_activity')
        user_logger.info("User check-in started", 
                        user_id=user_id, 
                        checkin_type="daily")
        
        return result

    @handle_errors("clearing stuck flows", default_return=("I'm having trouble clearing your flow state. Please try again.", True))
    def clear_stuck_flows(self, user_id: str) -> tuple[str, bool]:
        """
        Clear any stuck conversation flows for a user.
        This is a safety mechanism to reset flow state when it gets stuck.
        """
        existing_state = self.user_states.get(user_id)
        if existing_state:
            flow_type = existing_state.get("flow", "unknown")
            self.user_states.pop(user_id, None)
            self._save_user_states()
            logger.info(f"Cleared stuck flow {flow_type} for user {user_id}")
            return (f"Cleared stuck flow state. You can now use commands normally.", True)
        else:
            return ("No active flow found to clear.", True)

    @handle_errors("clearing all conversation states", default_return=None)
    def clear_all_states(self):
        """Clear all user states - primarily for testing."""
        self.user_states.clear()
        self._save_user_states()
        logger.info("Cleared all user states")

    @handle_errors("restarting checkin", default_return=("I'm having trouble restarting your check-in. Please try again.", True))
    def restart_checkin(self, user_id: str) -> tuple[str, bool]:
        """
        Force restart a check-in flow, clearing any existing checkin state.
        This should be used when user explicitly wants to start over.
        """
        # Clear any existing checkin state
        existing_state = self.user_states.get(user_id)
        if existing_state and existing_state.get("flow") == FLOW_CHECKIN:
            self.user_states.pop(user_id, None)
            self._save_user_states()
            logger.info(f"Cleared existing checkin flow for user {user_id} before restart")
        
        # Start a new checkin
        return self.start_checkin(user_id)

    # Scaffold for future feature flows to keep architecture consistent and channel-agnostic
    @handle_errors("starting tasks flow", default_return=("I'm having trouble starting the tasks flow.", True))
    def start_tasks_flow(self, user_id: str) -> tuple[str, bool]:
        """Starter for a future tasks multi-step flow (placeholder)."""
        # For now, delegate to single-turn handler semantics until flow is implemented
        from communication.message_processing.interaction_manager import handle_user_message
        resp = handle_user_message(user_id, "show my tasks", "discord")
        return (resp.message, True)

    @handle_errors("starting profile flow", default_return=("I'm having trouble starting the profile flow.", True))
    def start_profile_flow(self, user_id: str) -> tuple[str, bool]:
        from communication.message_processing.interaction_manager import handle_user_message
        resp = handle_user_message(user_id, "show profile", "discord")
        return (resp.message, True)

    @handle_errors("starting schedule flow", default_return=("I'm having trouble starting the schedule flow.", True))
    def start_schedule_flow(self, user_id: str) -> tuple[str, bool]:
        from communication.message_processing.interaction_manager import handle_user_message
        resp = handle_user_message(user_id, "show schedule", "discord")
        return (resp.message, True)

    @handle_errors("starting messages flow", default_return=("I'm having trouble starting the messages flow.", True))
    def start_messages_flow(self, user_id: str) -> tuple[str, bool]:
        from communication.message_processing.interaction_manager import handle_user_message
        resp = handle_user_message(user_id, "show messages", "discord")
        return (resp.message, True)

    @handle_errors("starting analytics flow", default_return=("I'm having trouble starting the analytics flow.", True))
    def start_analytics_flow(self, user_id: str) -> tuple[str, bool]:
        from communication.message_processing.interaction_manager import handle_user_message
        resp = handle_user_message(user_id, "show analytics", "discord")
        return (resp.message, True)

    @handle_errors("starting dynamic checkin", default_return=("I'm having trouble starting your check-in. Please try again.", True))
    def _start_dynamic_checkin(self, user_id: str) -> tuple[str, bool]:
        """Start a dynamic check-in flow based on user preferences with weighted question selection"""
        # Get user's check-in preferences
        prefs_result = get_user_data(user_id, 'preferences')
        checkin_prefs = prefs_result.get('preferences', {}).get('checkin_settings', {})
        enabled_questions = checkin_prefs.get('questions', {})
        
        # Use weighted selection for question order
        question_order = self._select_checkin_questions_with_weighting(user_id, enabled_questions)
        
        if not question_order:
            return ("No check-in questions are enabled. Please configure your check-in settings.", True)
        
        # Initialize user state with dynamic question order
        from datetime import datetime
        user_state = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_START,
            "data": {},
            "question_order": question_order,
            "current_question_index": 0,
            "last_activity": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.user_states[user_id] = user_state
        logger.info(f"FLOW_STATE_CREATE: Created new check-in flow for user {user_id} | Questions: {len(question_order)} | Order: {question_order[:3]}...")
        self._save_user_states()
        
        # Compose user-requested intro plus first question
        first_question_key = question_order[0]
        first_question_text = self._get_question_text(first_question_key, {})
        intro = (
            "🌟 Check-in Time! 🌟\n\n"
            "Hi! It's time for your check-in. This helps me understand how you're doing and provide better support.\n\n"
            f"Let's start: {first_question_text}"
        )
        # Update state to current question without advancing index
        user_state['state'] = QUESTION_STATES.get(first_question_key, CHECKIN_START)
        logger.info(f"FLOW_STATE_CREATE: Check-in flow initialized successfully for user {user_id} | First question: {first_question_key}")
        return (intro, False)

    @handle_errors("getting personalized welcome", default_return="🌟 Hello! Let's take a moment to check in on how you're feeling today.\n\nI have some quick questions for you today. Type /cancel anytime to skip.")
    def _get_personalized_welcome(self, user_id: str, question_count: int) -> str:
        """Generate a personalized welcome message based on user history"""
        # Get recent check-ins for context
        recent_checkins = get_recent_checkins(user_id, limit=3)
        
        if recent_checkins:
            # Analyze recent mood trends
            recent_moods = [c.get('mood', 3) for c in recent_checkins if c.get('mood')]
            avg_mood = sum(recent_moods) / len(recent_moods) if recent_moods else 3
            
            if avg_mood >= 4:
                welcome = "🌟 Great to see you again! I've noticed you've been feeling pretty good lately."
            elif avg_mood <= 2:
                welcome = "🌟 Hi there! I'm here to support you. Let's check in on how you're doing today."
            else:
                welcome = "🌟 Hello! Let's take a moment to check in on how you're feeling today."
        else:
            welcome = "🌟 Welcome to your first check-in! Let's get to know how you're doing."
        
        return f"{welcome}\n\nI have {question_count} quick questions for you today. Type /cancel anytime to skip."

    @handle_errors("getting next question", default_return=("I'm having trouble with the check-in flow. Let's start over.", True))
    def _get_next_question(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Get the next question in the check-in flow"""
        question_order = user_state.get('question_order', [])
        current_index = user_state.get('current_question_index', 0)
        
        if current_index >= len(question_order):
            # All questions completed
            return self._complete_checkin(user_id, user_state)
        
        question_key = question_order[current_index]
        question_data = user_state.get('data', {})
        
        # Get question text based on type
        question_text = self._get_question_text(question_key, question_data)
        
        # Update state to current question
        user_state['state'] = QUESTION_STATES.get(question_key, CHECKIN_START)
        
        return (question_text, False)

    @handle_errors("getting question text", default_return="Please answer this question:")
    def _get_question_text(self, question_key: str, previous_data: dict) -> str:
        """Get appropriate question text based on question type and previous responses"""
        # Import the dynamic checkin manager
        from core.checkin_dynamic_manager import dynamic_checkin_manager
        
        # Get the question text from the dynamic manager
        question_text = dynamic_checkin_manager.get_question_text(question_key)
        
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


    @handle_errors("handling checkin", default_return=("I'm having trouble with the check-in. Let's start over.", True))
    def _handle_checkin(self, user_id: str, user_state: dict, message_text: str) -> tuple[str, bool]:
        """
        Enhanced check-in flow with dynamic questions and better validation
        """
        from datetime import datetime, timedelta

        # Idle expiry: 45 minutes since last activity
        try:
            last_ts = user_state.get('last_activity')
            if last_ts:
                last_dt = datetime.strptime(last_ts, '%Y-%m-%d %H:%M:%S')
                if datetime.now() - last_dt > timedelta(minutes=45):
                    # Expire flow due to inactivity
                    self.user_states.pop(user_id, None)
                    self._save_user_states()
                    return ("The previous check-in expired due to inactivity. You can start a new one with /checkin.", True)
        except Exception:
            pass

        if message_text.lower().startswith("/cancel"):
            self.user_states.pop(user_id, None)
            self._save_user_states()
            return ("Check-in canceled. You can start again anytime with /checkin", True)

        # If the user sends a clear slash/bang command unrelated to check-in, expire and hand off
        stripped = message_text.strip().lower()
        if stripped.startswith("/") or stripped.startswith("!"):
            # Allow restarting or canceling without expiry message here
            if stripped.startswith("/checkin") or stripped.startswith("!checkin"):
                return ("You're already in a check-in. Type /cancel to cancel the current one, or continue answering.", False)
            if stripped.startswith("/cancel") or stripped.startswith("!cancel"):
                self.user_states.pop(user_id, None)
                self._save_user_states()
                return ("Check-in canceled. You can start again anytime with /checkin", True)

            # Expire current check-in and delegate to interaction manager
            try:
                self.user_states.pop(user_id, None)
                self._save_user_states()
            except Exception:
                pass
            try:
                from communication.message_processing.interaction_manager import handle_user_message
                response = handle_user_message(user_id, message_text, "discord")
                return (response.message, response.completed)
            except Exception:
                # Fallback help if delegation fails
                return ("I've closed the current check-in. What would you like to do? Try /tasks, /messages, /profile, or /status.", True)

        state = user_state["state"]
        data = user_state["data"]
        question_order = user_state.get('question_order', [])
        current_index = user_state.get('current_question_index', 0)

        if current_index >= len(question_order):
            return self._complete_checkin(user_id, user_state)

        question_key = question_order[current_index]

        # Validate and store the response
        validation_result = self._validate_response(question_key, message_text)
        if not validation_result['valid']:
            return (validation_result['message'], False)

        # Store the validated response
        data[question_key] = validation_result['value']

        # Move to next question and update activity
        user_state['current_question_index'] = current_index + 1
        try:
            user_state['last_activity'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
        self._save_user_states()

        # Get next question or complete
        return self._get_next_question(user_id, user_state)

    @handle_errors("validating response", default_return={'valid': False, 'value': None, 'message': "I didn't understand that response. Please try again."})
    def _validate_response(self, question_key: str, response: str) -> dict:
        """Validate user response based on question type using dynamic manager"""
        # Import the dynamic checkin manager
        from core.checkin_dynamic_manager import dynamic_checkin_manager
        
        # Use the dynamic manager to validate the response
        is_valid, value, error_message = dynamic_checkin_manager.validate_answer(question_key, response)
        
        return {
            'valid': is_valid,
            'value': value,
            'message': error_message
        }


    @handle_errors("completing checkin", default_return=("Thanks for completing your check-in! There was an issue saving your responses, but I've recorded what I could.", True))
    def _complete_checkin(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Complete the check-in and provide personalized feedback"""
        data = user_state["data"]
        question_order = user_state.get('question_order', [])
        
        # Add questions asked to the data for future weighting
        data['questions_asked'] = question_order
        
        # Store the check-in data using modern function
        from core.response_tracking import store_user_response
        store_user_response(user_id, data, "checkin")
        
        # Log user activity for check-in completion
        from core.logger import get_component_logger
        user_logger = get_component_logger('user_activity')
        user_logger.info("User check-in completed", 
                        user_id=user_id, 
                        questions_answered=len(data),
                        mood=data.get('mood'),
                        energy=data.get('energy'),
                        sleep_quality=data.get('sleep_quality'))
        
        # Generate personalized completion message
        completion_message = self._generate_completion_message(user_id, data)
        
        # Clear the user state
        self.user_states.pop(user_id, None)
        self._save_user_states()
        
        return (completion_message, True)

    @handle_errors("handling command during checkin", default_return=("I'm having trouble with that command right now. Please continue with your check-in.", False))
    def _handle_command_during_checkin(self, user_id: str, message_text: str) -> tuple[str, bool]:
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
                False
            )
        
        # Handle clear command
        elif message_lower in ["/clear", "!clear"]:
            return self.clear_stuck_flows(user_id)
        
        # Handle tasks command
        elif message_lower in ["/tasks", "!tasks"]:
            from communication.command_handlers.task_handler import TaskManagementHandler
            handler = TaskManagementHandler()
            response = handler.handle_list_tasks(user_id, {})
            return (response.message, False)
        
        # Handle profile command
        elif message_lower in ["/profile", "!profile"]:
            from communication.command_handlers.profile_handler import ProfileHandler
            handler = ProfileHandler()
            response = handler.handle_show_profile(user_id, {})
            return (response.message, False)
        
        # Handle status command
        elif message_lower in ["/status", "!status"]:
            from communication.command_handlers.analytics_handler import AnalyticsHandler
            handler = AnalyticsHandler()
            response = handler.handle_show_status(user_id, {})
            return (response.message, False)
        
        # Handle analytics command
        elif message_lower in ["/analytics", "!analytics"]:
            from communication.command_handlers.analytics_handler import AnalyticsHandler
            handler = AnalyticsHandler()
            response = handler.handle_show_analytics(user_id, {})
            return (response.message, False)
        
        # Handle schedule command
        elif message_lower in ["/schedule", "!schedule"]:
            from communication.command_handlers.schedule_handler import ScheduleManagementHandler
            handler = ScheduleManagementHandler()
            response = handler.handle_show_schedule(user_id, {})
            return (response.message, False)
        
        # Handle messages command
        elif message_lower in ["/messages", "!messages"]:
            from communication.command_handlers.interaction_handlers import get_interaction_handler
            handler = get_interaction_handler("messages")
            response = handler.handle_show_messages(user_id, {})
            return (response.message, False)
        
        # Unknown command
        else:
            return (
                f"Unknown command: {message_text}\n"
                "You're currently in a check-in. Type `/help` for available commands or continue answering the questions.",
                False
            )

    @handle_errors("generating completion message", default_return="✅ Check-in complete! Thanks for taking the time. See you next time! 🌟")
    def _generate_completion_message(self, user_id: str, data: dict) -> str:
        """Generate a personalized completion message based on responses"""
        # Base completion message
        message = "✅ Check-in complete! Thanks for taking the time.\n\n"
        
        # Add personalized insights
        insights = []
        
        # Mood insights
        mood = data.get('mood')
        if mood is not None:
            if mood >= 4:
                insights.append("🌟 Great mood today!")
            elif mood <= 2:
                insights.append("💙 I hope tomorrow is better. Remember, it's okay to not be okay.")
            else:
                insights.append("😊 Solid mood today!")
        
        # Energy insights
        energy = data.get('energy')
        if energy is not None and energy <= 2:
            insights.append("⚡ Low energy - maybe try a short walk or some gentle stretching?")
        
        # Sleep insights
        sleep_hours = data.get('sleep_hours')
        sleep_quality = data.get('sleep_quality')
        if sleep_hours is not None and sleep_hours < 6:
            insights.append("😴 You might need more sleep tonight.")
        elif sleep_quality is not None and sleep_quality <= 2:
            insights.append("😴 Sleep quality could be better - consider a bedtime routine.")
                  
        # Add insights
        if insights:
            message += "💭 " + " ".join(insights) + "\n\n"
        
        # Encouragement
        message += "You're doing great by checking in with yourself. See you next time! 🌟"
        
        return message

    @handle_errors("handling contextual question", default_return="I'm having trouble accessing your context right now. Please try again later.")
    def handle_contextual_question(self, user_id: str, message_text: str) -> str:
        """
        Handle a single contextual question without entering a conversation flow.
        Perfect for one-off questions that benefit from user context.
        """
        ai_bot = get_ai_chatbot()
        return ai_bot.generate_contextual_response(user_id, message_text, timeout=8)

    @handle_errors("selecting check-in questions with weighted randomization")
    def _select_checkin_questions_with_weighting(self, user_id: str, enabled_questions: dict) -> list:
        """
        Select check-in questions using weighted randomization to ensure variety.
        
        Args:
            user_id: User ID
            enabled_questions: Dictionary of enabled questions from user preferences
            
        Returns:
            List of question keys in selected order
        """
        try:
            import random
            from datetime import datetime, timedelta
            
            # Get enabled question keys
            enabled_keys = [key for key, data in enabled_questions.items() if data.get('enabled', False)]
            
            if not enabled_keys:
                return []
            
            # If only one question enabled, return it
            if len(enabled_keys) == 1:
                return enabled_keys
            
            # Get recent check-in history to avoid repetition
            recent_checkins = get_recent_checkins(user_id, limit=5)
            recently_asked = set()
            
            # Extract recently asked questions from the last 3 check-ins
            for checkin in recent_checkins[-3:]:
                if 'questions_asked' in checkin:
                    recently_asked.update(checkin['questions_asked'])
            
            # Define question categories for variety
            question_categories = {
                'mood': ['mood', 'energy', 'stress_level', 'anxiety_level'],
                'health': ['ate_breakfast', 'brushed_teeth', 'medication_taken', 'exercise', 'hydration'],
                'sleep': ['sleep_quality', 'sleep_hours'],
                'social': ['social_interaction'],
                'reflection': ['focus_level', 'daily_reflection']
            }
            
            # Calculate weights for each question
            question_weights = []
            
            for question_key in enabled_keys:
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
                    category_recent_count = sum(1 for q in recently_asked if q in question_categories.get(question_category, []))
                    if category_recent_count == 0:
                        weight *= 1.5  # Boost for underrepresented categories
                    elif category_recent_count >= 2:
                        weight *= 0.7  # Reduce for overrepresented categories
                
                # Add some randomness to prevent predictable patterns
                weight *= random.uniform(0.8, 1.2)
                
                question_weights.append((question_key, weight))
            
            # Sort by weight (highest first) and take top questions
            question_weights.sort(key=lambda x: x[1], reverse=True)
            
            # Select questions (limit to reasonable number, e.g., 5-8 questions)
            max_questions = min(len(enabled_keys), 8)
            selected_questions = [q[0] for q in question_weights[:max_questions]]
            
            # Shuffle the final order for additional randomness
            random.shuffle(selected_questions)
            
            logger.debug(f"Selected {len(selected_questions)} check-in questions for user {user_id}: {selected_questions}")
            
            return selected_questions
            
        except Exception as e:
            logger.error(f"Error selecting check-in questions with weighting: {e}")
            # Fallback to simple random selection
            return random.sample(enabled_keys, min(len(enabled_keys), 6))

    def _handle_task_reminder_followup(self, user_id: str, user_state: dict, message_text: str) -> tuple[str, bool]:
        """
        Handle user's response to reminder period question after task creation.
        
        Parses natural language responses like:
        - "30 minutes to an hour before"
        - "3 to 5 hours before"
        - "1 to 2 days before"
        - "No reminders needed" / "No" / "Skip"
        """
        from tasks.task_management import get_task_by_id
        try:
            task_id = user_state.get("data", {}).get("task_id")
            if not task_id:
                logger.error(f"Task reminder follow-up for user {user_id} but no task_id in state")
                self.user_states.pop(user_id, None)
                self._save_user_states()
                return ("I couldn't find the task to update. The task was created successfully.", True)
            
            # Check if user wants to skip reminders
            message_lower = message_text.lower().strip()
            skip_patterns = ["no reminders", "no reminder", "no", "skip", "none", "not needed", "don't need", "don't want"]
            if any(pattern in message_lower for pattern in skip_patterns):
                # User doesn't want reminders - clear flow
                self.user_states.pop(user_id, None)
                self._save_user_states()
                return ("Got it! No reminders will be set for this task.", True)
            
            # Parse reminder periods from natural language
            reminder_periods = self._parse_reminder_periods_from_text(user_id, task_id, message_text)
            logger.debug(f"Parsed reminder_periods for task {task_id}: {reminder_periods}")
            
            # Check if parsing succeeded and if task has due date
            if not reminder_periods or len(reminder_periods) == 0:
                # Couldn't parse - check if task has due date to give better error message
                task = get_task_by_id(user_id, task_id)
                if task and not task.get('due_date'):
                    # Task has no due date, can't set reminder periods
                    self.user_states.pop(user_id, None)
                    self._save_user_states()
                    return ("This task doesn't have a due date, so I can't set reminder periods. You can add a due date and reminders later by updating the task.", True)
                # Couldn't parse reminder periods - ask for clarification
                return (
                    "I'm not sure what reminder timing you'd like. Please specify something like:\n"
                    "- '30 minutes to an hour before'\n"
                    "- '3 to 5 hours before'\n"
                    "- '1 to 2 days before'\n"
                    "- Or say 'no reminders' to skip",
                    False
                )
            
            # Check if task has due date (parsing already checked this, but verify)
            task = get_task_by_id(user_id, task_id)
            if not task:
                logger.error(f"Task {task_id} not found when trying to set reminder periods")
                self.user_states.pop(user_id, None)
                self._save_user_states()
                return ("I couldn't find the task to update. The task was created successfully.", True)
            
            if not task.get('due_date'):
                # Task has no due date, can't set reminder periods
                self.user_states.pop(user_id, None)
                self._save_user_states()
                return ("This task doesn't have a due date, so I can't set reminder periods. You can add a due date and reminders later by updating the task.", True)
            
            if reminder_periods:
                # Update task with reminder periods
                from tasks.task_management import update_task, schedule_task_reminders
                
                logger.debug(f"Updating task {task_id} with reminder periods: {reminder_periods}")
                
                # Update task with reminder periods
                # Note: update_task will also call schedule_task_reminders internally, so we don't need to call it again
                try:
                    update_result = update_task(user_id, task_id, {'reminder_periods': reminder_periods})
                    logger.debug(f"update_task returned: {update_result}")
                    if not update_result:
                        logger.error(f"update_task returned False for task {task_id} with reminder periods for user {user_id}")
                        self.user_states.pop(user_id, None)
                        self._save_user_states()
                        return ("I had trouble saving the reminder periods. The task was created successfully. You can add reminders later by updating the task.", True)
                    
                    # Verify the task was updated correctly by reloading it
                    updated_task = get_task_by_id(user_id, task_id)
                    if not updated_task or 'reminder_periods' not in updated_task:
                        logger.error(f"Task {task_id} was not updated with reminder_periods after update_task returned True")
                        self.user_states.pop(user_id, None)
                        self._save_user_states()
                        return ("I had trouble saving the reminder periods. The task was created successfully. You can add reminders later by updating the task.", True)
                    
                    # Clear flow
                    self.user_states.pop(user_id, None)
                    self._save_user_states()
                    
                    periods_text = ", ".join([f"{p.get('date', '')} {p.get('start_time', '')}-{p.get('end_time', '')}" for p in reminder_periods])
                    return (f"✅ Reminder periods set for this task: {periods_text}", True)
                except Exception as update_error:
                    logger.error(f"Exception in update_task for task {task_id}: {update_error}", exc_info=True)
                    self.user_states.pop(user_id, None)
                    self._save_user_states()
                    return ("I had trouble saving the reminder periods. The task was created successfully. You can add reminders later by updating the task.", True)
            else:
                # Couldn't parse reminder periods - ask for clarification
                return (
                    "I'm not sure what reminder timing you'd like. Please specify something like:\n"
                    "- '30 minutes to an hour before'\n"
                    "- '3 to 5 hours before'\n"
                    "- '1 to 2 days before'\n"
                    "- Or say 'no reminders' to skip",
                    False
                )
                
        except Exception as e:
            logger.error(f"Error handling task reminder follow-up for user {user_id}: {e}", exc_info=True)
            # Don't clear flow on exception if it's a parsing issue - let user try again
            # Only clear if it's a critical error
            if "task_id" in str(e).lower() or "not found" in str(e).lower():
                self.user_states.pop(user_id, None)
                self._save_user_states()
                return ("I had trouble setting up reminders, but your task was created successfully. You can add reminders later by updating the task.", True)
            else:
                # Parsing or other non-critical error - ask for clarification
                return (
                    "I'm not sure what reminder timing you'd like. Please specify something like:\n"
                    "- '30 minutes to an hour before'\n"
                    "- '3 to 5 hours before'\n"
                    "- '1 to 2 days before'\n"
                    "- Or say 'no reminders' to skip",
                    False
                )

    def _parse_reminder_periods_from_text(self, user_id: str, task_id: str, text: str) -> list:
        """
        Parse reminder periods from natural language text.
        
        Examples:
        - "30 minutes to an hour before" -> reminder 30-60 min before due time
        - "3 to 5 hours before" -> reminder 3-5 hours before due time
        - "1 to 2 days before" -> reminder 1-2 days before due date
        
        Returns list of reminder period dicts with date, start_time, end_time.
        """
        try:
            import re
            from datetime import datetime, timedelta
            from tasks.task_management import get_task_by_id
            
            text_lower = text.lower().strip()
            reminder_periods = []
            
            # Get task to find due date/time
            task = get_task_by_id(user_id, task_id)
            if not task or not task.get('due_date'):
                logger.debug(f"Task {task_id} has no due_date, cannot parse reminder periods")
                return []
            
            due_date_str = task.get('due_date')
            due_time_str = task.get('due_time')
            if not due_time_str or due_time_str.strip() == '':
                due_time_str = '09:00'  # Default to 9 AM if no time specified
            
            try:
                # Parse due date and time
                due_datetime = datetime.strptime(f"{due_date_str} {due_time_str}", '%Y-%m-%d %H:%M')
                logger.debug(f"Parsed due datetime for task {task_id}: {due_datetime}")
            except ValueError as e:
                # Try without time
                try:
                    due_datetime = datetime.strptime(due_date_str, '%Y-%m-%d')
                    due_datetime = due_datetime.replace(hour=9, minute=0)  # Default to 9 AM
                    logger.debug(f"Parsed due date only for task {task_id}: {due_datetime}")
                except ValueError as e2:
                    logger.warning(f"Could not parse due date/time for task {task_id}: {due_date_str} {due_time_str}, error: {e2}")
                    return []
            
            # Parse time ranges from text
            # Pattern: "X to Y [unit] before" or "X [unit] to [an] Y [unit] before"
            # Handle "an hour" = 60 minutes (do this before parsing)
            original_text = text_lower
            text_lower = text_lower.replace('an hour', '60 minutes').replace('a hour', '60 minutes')
            
            logger.debug(f"Parsing reminder periods from text '{text}' (lowercase: '{text_lower}') for task {task_id} with due_datetime {due_datetime}")
            
            patterns = [
                # Minutes - handle "X minutes to Y minutes before" or "X to Y minutes before"
                (r'(\d+)\s*minutes?\s*(?:to|-)\s*(\d+)\s*minutes?\s*before', 'minutes'),
                (r'(\d+)\s*(?:to|-)\s*(\d+)\s*minutes?\s*before', 'minutes'),
                (r'(\d+)\s*minutes?\s*before', 'minutes'),  # Single value
                (r'(\d+)\s*min\s*before', 'minutes'),
                # Hours
                (r'(\d+)\s*hours?\s*(?:to|-)\s*(\d+)\s*hours?\s*before', 'hours'),
                (r'(\d+)\s*(?:to|-)\s*(\d+)\s*hours?\s*before', 'hours'),
                (r'(\d+)\s*hours?\s*before', 'hours'),  # Single value
                (r'(\d+)\s*hrs?\s*before', 'hours'),
                # Days
                (r'(\d+)\s*days?\s*(?:to|-)\s*(\d+)\s*days?\s*before', 'days'),
                (r'(\d+)\s*(?:to|-)\s*(\d+)\s*days?\s*before', 'days'),
                (r'(\d+)\s*days?\s*before', 'days'),  # Single value
            ]
            
            for pattern, unit in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    logger.debug(f"Pattern '{pattern}' matched text '{text_lower}' with groups: {match.groups()}")
                    try:
                        start_val = int(match.group(1))
                        # Check if pattern has a second group (for ranges like "3 to 5")
                        if len(match.groups()) >= 2 and match.group(2):
                            end_val = int(match.group(2))
                        else:
                            end_val = start_val  # Single value, use same for start and end
                        
                        logger.debug(f"Parsed values: start_val={start_val}, end_val={end_val}, unit={unit}")
                        
                        # Calculate reminder times
                        if unit == 'minutes':
                            start_delta = timedelta(minutes=end_val)  # End time = earlier (more minutes before)
                            end_delta = timedelta(minutes=start_val)  # Start time = later (fewer minutes before)
                        elif unit == 'hours':
                            start_delta = timedelta(hours=end_val)
                            end_delta = timedelta(hours=start_val)
                        elif unit == 'days':
                            start_delta = timedelta(days=end_val)
                            end_delta = timedelta(days=start_val)
                        else:
                            logger.debug(f"Unknown unit '{unit}', skipping")
                            continue
                        
                        # Calculate reminder datetime range
                        reminder_start = due_datetime - start_delta
                        reminder_end = due_datetime - end_delta
                        
                        logger.debug(f"Calculated reminder times: start={reminder_start}, end={reminder_end}")
                        
                        # Ensure reminder is in the future
                        now = datetime.now()
                        if reminder_end < now:
                            logger.debug(f"Reminder time {reminder_end} is in the past (now={now}), skipping")
                            continue
                        
                        # Create reminder period
                        reminder_date = reminder_start.strftime('%Y-%m-%d')
                        start_time = reminder_start.strftime('%H:%M')
                        end_time = reminder_end.strftime('%H:%M')
                        
                        reminder_periods.append({
                            'date': reminder_date,
                            'start_time': start_time,
                            'end_time': end_time
                        })
                        
                        logger.info(f"Parsed reminder period for task {task_id}: {reminder_date} {start_time}-{end_time}")
                        break  # Only parse first match
                    except (ValueError, IndexError, AttributeError, TypeError) as e:
                        logger.warning(f"Error parsing reminder pattern '{pattern}' for text '{text_lower}': {e}", exc_info=True)
                        continue  # Try next pattern
            
            logger.debug(f"Final reminder_periods for task {task_id}: {reminder_periods}")
            
            return reminder_periods
        except Exception as e:
            logger.error(f"Exception in _parse_reminder_periods_from_text for task {task_id}, text '{text}': {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            return []

    def start_task_reminder_followup(self, user_id: str, task_id: str) -> None:
        """
        Start a task reminder follow-up flow.
        Called by task handler after creating a task.
        """
        self.user_states[user_id] = {
            "flow": FLOW_TASK_REMINDER,
            "state": 0,
            "data": {"task_id": task_id}
        }
        self._save_user_states()
        logger.debug(f"Started task reminder follow-up flow for user {user_id}, task {task_id}")

# Create a global instance for convenience:
conversation_manager = ConversationManager()
