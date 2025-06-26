# bot/conversation_manager.py

"""
conversation_manager.py

Provides a single place to handle 'conversation flows' that can be used
by any platform: Telegram, Discord, Email, etc.

We keep track of each user's 'state' in a dictionary, so if a user is in the middle
of daily check-in or an AI chat flow, we know what question to ask next.

Usage:
  1) The platform bot receives a message or command from user_id.
  2) That bot calls: conversation_manager.handle_inbound_message(user_id, message_text).
  3) This returns (reply_text, completed). The bot sends reply_text to the user.
  4) If completed == True, the flow is done, so we remove them from user_states.
"""

import core.utils
from bot.ai_chatbot import get_ai_chatbot
from core.logger import get_logger

logger = get_logger(__name__)

# We'll define 'flow' constants
FLOW_NONE = 0
FLOW_DAILY_CHECKIN = 1

# We'll define states for daily check-in - now dynamic based on user preferences
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
        self.user_states = {}

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
            if message_text.lower().startswith("/dailycheckin"):
                # Check if check-ins are enabled for this user
                if not core.utils.is_user_checkins_enabled(user_id):
                    # Clear any existing state for this user
                    self.user_states.pop(user_id, None)
                    return (
                        "Check-ins are not enabled for your account. Please contact an administrator to enable daily check-ins.",
                        True
                    )
                
                # Initialize dynamic check-in flow based on user preferences
                return self._start_dynamic_checkin(user_id)

            elif message_text.lower().startswith("/cancel"):
                return ("Nothing to cancel. You're not in a conversation flow.", True)

            else:
                # Default to contextual chat for all other messages
                # This provides rich, personalized responses using the user's context
                try:
                    ai_bot = get_ai_chatbot()
                    reply = ai_bot.generate_contextual_response(user_id, message_text, timeout=10)
                    return (reply, True)  # Single response, no ongoing flow
                except Exception as e:
                    logger.error(f"Error in default contextual chat for user {user_id}: {e}")
                    return ("I'm having trouble processing your message right now. Please try again in a moment.", True)

        # If user is mid-flow, continue the appropriate flow
        flow = user_state["flow"]
        if flow == FLOW_DAILY_CHECKIN:
            return self._handle_daily_checkin(user_id, user_state, message_text)
        else:
            # Unknown flow - reset to default contextual chat
            self.user_states.pop(user_id, None)
            try:
                ai_bot = get_ai_chatbot()
                reply = ai_bot.generate_contextual_response(user_id, message_text, timeout=10)
                return (reply, True)
            except Exception as e:
                logger.error(f"Error in fallback contextual chat for user {user_id}: {e}")
                return ("I encountered an issue. Let's start fresh - what can I help you with?", True)

    def _start_dynamic_checkin(self, user_id: str) -> tuple[str, bool]:
        """Start a dynamic check-in flow based on user preferences"""
        try:
            # Get user's check-in preferences
            checkin_prefs = core.utils.get_user_checkin_preferences(user_id)
            enabled_questions = checkin_prefs.get('questions', {})
            
            # Build ordered list of enabled questions
            question_order = []
            for question_key, question_data in enabled_questions.items():
                if question_data.get('enabled', False):
                    question_order.append(question_key)
            
            if not question_order:
                return ("No check-in questions are enabled. Please configure your check-in settings.", True)
            
            # Initialize user state with dynamic question order
            user_state = {
                "flow": FLOW_DAILY_CHECKIN,
                "state": CHECKIN_START,
                "data": {},
                "question_order": question_order,
                "current_question_index": 0
            }
            self.user_states[user_id] = user_state
            
            # Get personalized welcome message
            welcome_msg = self._get_personalized_welcome(user_id, len(question_order))
            
            # Start with first question
            return self._get_next_question(user_id, user_state)
            
        except Exception as e:
            logger.error(f"Error starting dynamic check-in for user {user_id}: {e}")
            return ("I'm having trouble starting your check-in. Please try again.", True)

    def _get_personalized_welcome(self, user_id: str, question_count: int) -> str:
        """Generate a personalized welcome message based on user history"""
        try:
            # Get recent check-ins for context
            recent_checkins = core.utils.get_recent_daily_checkins(user_id, limit=3)
            
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
            
        except Exception as e:
            logger.error(f"Error generating personalized welcome for user {user_id}: {e}")
            return f"🌟 Daily Check-in Time! 🌟\n\nI have {question_count} quick questions for you today. Type /cancel anytime to skip."

    def _get_next_question(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Get the next question in the dynamic check-in flow"""
        try:
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
            
        except Exception as e:
            logger.error(f"Error getting next question for user {user_id}: {e}")
            return ("I'm having trouble with the check-in flow. Let's start over.", True)

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

    def _handle_daily_checkin(self, user_id: str, user_state: dict, message_text: str) -> tuple[str, bool]:
        """
        Enhanced daily check-in flow with dynamic questions and better validation
        """
        if message_text.lower().startswith("/cancel"):
            self.user_states.pop(user_id, None)
            return ("Daily check-in canceled. You can start again anytime with /dailycheckin", True)

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

    def _complete_checkin(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Complete the check-in and provide personalized feedback"""
        try:
            data = user_state["data"]
            
            # Store the check-in data
            core.utils.store_daily_checkin_response(user_id, data)
            
            # Generate personalized completion message
            completion_message = self._generate_completion_message(user_id, data)
            
            # Clear the user state
            self.user_states.pop(user_id, None)
            
            return (completion_message, True)
            
        except Exception as e:
            logger.error(f"Error completing check-in for user {user_id}: {e}")
            self.user_states.pop(user_id, None)
            return ("Thanks for completing your check-in! There was an issue saving your responses, but I've recorded what I could.", True)

    def _generate_completion_message(self, user_id: str, data: dict) -> str:
        """Generate a personalized completion message based on responses"""
        try:
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
            
        except Exception as e:
            logger.error(f"Error generating completion message for user {user_id}: {e}")
            return "✅ Check-in complete! Thanks for taking the time. See you next time! 🌟"

    def handle_contextual_question(self, user_id: str, message_text: str) -> str:
        """
        Handle a single contextual question without entering a conversation flow.
        Perfect for one-off questions that benefit from user context.
        """
        try:
            ai_bot = get_ai_chatbot()
            return ai_bot.generate_contextual_response(user_id, message_text, timeout=8)
        except Exception as e:
            logger.error(f"Error in contextual question handling: {e}")
            return "I'm having trouble accessing your context right now. Please try again later."

# Create a global instance for convenience:
conversation_manager = ConversationManager()
