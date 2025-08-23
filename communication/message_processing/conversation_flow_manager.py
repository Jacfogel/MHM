# bot/conversation_manager.py

"""
conversation_manager.py

Provides a single place to handle 'conversation flows' that can be used
by any platform: Telegram, Discord, Email, etc.

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
from ai.chatbot import get_ai_chatbot
from core.logger import get_logger, get_component_logger
from core.response_tracking import (
    is_user_checkins_enabled,
    get_user_checkin_preferences,
    get_recent_checkins,
    store_checkin_response,
    store_checkin_response as _legacy_store_checkin_response,
)

# Expose store_checkin_response for tests that patch it
store_checkin_response = _legacy_store_checkin_response
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

# Route conversation orchestration to communication_manager component log
logger = get_component_logger('communication_manager')

# We'll define 'flow' constants
FLOW_NONE = 0
FLOW_CHECKIN = 1

# LEGACY COMPATIBILITY: Redundant assignment for backward compatibility
# TODO: Remove after all references are updated to use FLOW_CHECKIN directly
# REMOVAL PLAN:
# 1. Search for all references to FLOW_CHECKIN in tests and modules
# 2. Update them to use FLOW_CHECKIN directly
# 3. Remove this redundant assignment
# USAGE TRACKING: Monitor for any remaining references to this constant
FLOW_CHECKIN = FLOW_CHECKIN

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
    def __init__(self):
        # Store user states: { user_id: {"flow": FLOW_..., "state": int, "data": {}, "question_order": [] } }
        """Initialize the object."""
        self.user_states = {}

    def expire_checkin_flow_due_to_unrelated_outbound(self, user_id: str) -> None:
        """Expire an active check-in flow when an unrelated outbound message is sent.
        Safe no-op if no flow or different flow is active.
        """
        try:
            user_state = self.user_states.get(user_id)
            if user_state and user_state.get("flow") == FLOW_CHECKIN:
                # End the flow silently
                self.user_states.pop(user_id, None)
                logger.info(f"Expired active check-in flow for user {user_id} due to unrelated outbound message")
        except Exception:
            # Don't let this affect outbound sending
            logger.debug(f"Could not expire check-in flow for user {user_id}")

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
        else:
            # Unknown flow - reset to default contextual chat
            self.user_states.pop(user_id, None)
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
            return (
                "Check-ins are not enabled for your account. Please contact an administrator to enable check-ins.",
                True
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
        checkin_prefs = get_user_checkin_preferences(user_id)
        enabled_questions = checkin_prefs.get('questions', {})
        
        # Use weighted selection for question order
        question_order = self._select_checkin_questions_with_weighting(user_id, enabled_questions)
        
        if not question_order:
            return ("No check-in questions are enabled. Please configure your check-in settings.", True)
        
        # Initialize user state with dynamic question order
        user_state = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_START,
            "data": {},
            "question_order": question_order,
            "current_question_index": 0
        }
        self.user_states[user_id] = user_state
        
        # Compose user-requested intro plus first question
        first_question_key = question_order[0]
        first_question_text = self._get_question_text(first_question_key, {})
        intro = (
            "🌟 Check-in Time! 🌟\n\n"
            "Hi! It's time for your check-in. This helps me understand how you're doing and provide better support.\n\n"
            f"Let's start: {first_question_text}\n"
            "Type /cancel anytime to skip.\n"
            "Type /checkin anytime to prompt a new check-in"
        )
        # Update state to current question without advancing index
        user_state['state'] = QUESTION_STATES.get(first_question_key, CHECKIN_START)
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
        question_texts = {
            'mood': "How are you feeling today on a scale of 1 to 5? (1=terrible, 5=great)",
            'ate_breakfast': "Did you eat breakfast today? (yes/no)",
            'energy': "How is your energy level on a scale of 1 to 5? (1=exhausted, 5=very energetic)",
            'brushed_teeth': "Did you brush your teeth today? (yes/no)",
            'sleep_quality': "How well did you sleep last night on a scale of 1 to 5? (1=terrible, 5=excellent)",
            'sleep_hours': "How many hours did you sleep last night? (enter a number)",
            'anxiety_level': "How anxious are you feeling today on a scale of 1 to 5? (1=very calm, 5=very anxious)",
            'focus_level': "How focused do you feel today on a scale of 1 to 5? (1=very distracted, 5=very focused)",
            'medication_taken': "Did you take your medication today? (yes/no)",
            'exercise': "Did you do any exercise today? (yes/no)",
            'hydration': "Are you staying hydrated today? (yes/no)",
            'social_interaction': "Did you have any social interaction today? (yes/no)",
            'stress_level': "How stressed are you feeling today on a scale of 1 to 5? (1=very relaxed, 5=very stressed)",
            'daily_reflection': "Any brief thoughts or reflections about today? (optional - just press enter to skip)"
        }
        
        # Add contextual prompts based on previous responses
        if question_key == 'energy' and previous_data.get('mood', 0) <= 2:
            return "I noticed you're feeling down. How is your energy level today on a scale of 1 to 5? (1=exhausted, 5=very energetic)"
        elif question_key == 'sleep_quality' and previous_data.get('energy', 0) <= 2:
            return "Since your energy seems low, how well did you sleep last night on a scale of 1 to 5? (1=terrible, 5=excellent)"
        elif question_key == 'daily_reflection':
            return "Any brief thoughts or reflections about today? (This is optional - just press enter to skip)"
        
        return question_texts.get(question_key, "Please answer this question:")

    @handle_errors("handling checkin", default_return=("I'm having trouble with the check-in. Let's start over.", True))
    def _handle_checkin(self, user_id: str, user_state: dict, message_text: str) -> tuple[str, bool]:
        """
        Enhanced check-in flow with dynamic questions and better validation
        """
        if message_text.lower().startswith("/cancel"):
            self.user_states.pop(user_id, None)
            return ("Check-in canceled. You can start again anytime with /checkin", True)

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
        
        # Move to next question
        user_state['current_question_index'] = current_index + 1
        
        # Get next question or complete
        return self._get_next_question(user_id, user_state)

    @handle_errors("validating response", default_return={'valid': False, 'value': None, 'message': "I didn't understand that response. Please try again."})
    def _validate_response(self, question_key: str, response: str) -> dict:
        """Validate user response based on question type"""
        response = response.strip()
        
        # Yes/no questions
        yes_no_questions = ['ate_breakfast', 'brushed_teeth', 'medication_taken', 'exercise', 'hydration', 'social_interaction']
        if question_key in yes_no_questions:
            is_yes = response.lower() in ["yes", "y", "yeah", "yep", "true", "1"]
            return {
                'valid': True,
                'value': is_yes,
                'message': None
            }
        
        # Scale questions (1-5)
        scale_questions = ['mood', 'energy', 'sleep_quality', 'anxiety_level', 'focus_level', 'stress_level']
        if question_key in scale_questions:
            try:
                value = int(response)
                if 1 <= value <= 5:
                    return {
                        'valid': True,
                        'value': value,
                        'message': None
                    }
                else:
                    return {
                        'valid': False,
                        'value': None,
                        'message': f"Please enter a number between 1 and 5 for {question_key.replace('_', ' ')}."
                    }
            except ValueError:
                return {
                    'valid': False,
                    'value': None,
                    'message': f"Please enter a number between 1 and 5 for {question_key.replace('_', ' ')}."
                }
        
        # Sleep hours (number)
        if question_key == 'sleep_hours':
            try:
                value = float(response)
                if 0 <= value <= 24:
                    return {
                        'valid': True,
                        'value': value,
                        'message': None
                    }
                else:
                    return {
                        'valid': False,
                        'value': None,
                        'message': "Please enter a number between 0 and 24 for sleep hours."
                    }
            except ValueError:
                return {
                    'valid': False,
                    'value': None,
                    'message': "Please enter a number for sleep hours."
                }
        
        # Daily reflection (text, optional)
        if question_key == 'daily_reflection':
            return {
                'valid': True,
                'value': response if response else "No reflection provided",
                'message': None
            }
        
        # Default case
        return {
            'valid': True,
            'value': response,
            'message': None
        }

    @handle_errors("completing checkin", default_return=("Thanks for completing your check-in! There was an issue saving your responses, but I've recorded what I could.", True))
    def _complete_checkin(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Complete the check-in and provide personalized feedback"""
        data = user_state["data"]
        question_order = user_state.get('question_order', [])
        
        # Add questions asked to the data for future weighting
        data['questions_asked'] = question_order
        
        # Store the check-in data (legacy alias retained for tests)
        # Use exposed legacy-compatible function name so tests can patch it
        store_checkin_response(user_id, data)
        
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
        
        return (completion_message, True)

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

# Create a global instance for convenience:
conversation_manager = ConversationManager()
