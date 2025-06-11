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

# We'll define states for daily check-in
CHECKIN_MOOD = 100
CHECKIN_BREAKFAST = 101
CHECKIN_ENERGY = 102
CHECKIN_TEETH = 103

class ConversationManager:
    def __init__(self):
        # Store user states: { user_id: {"flow": FLOW_..., "state": int, "data": {} } }
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
                
                user_state["flow"] = FLOW_DAILY_CHECKIN
                user_state["state"] = CHECKIN_MOOD
                self.user_states[user_id] = user_state
                return (
                    "How are you feeling today on a scale of 1 to 5? (1=terrible, 5=great)\nType /cancel to quit.",
                    False
                )

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

    def _handle_daily_checkin(self, user_id: str, user_state: dict, message_text: str) -> tuple[str, bool]:
        """
        For daily check-in flow
        """
        if message_text.lower().startswith("/cancel"):
            self.user_states.pop(user_id, None)
            return ("Daily check-in canceled.", True)

        state = user_state["state"]
        data = user_state["data"]

        if state == CHECKIN_MOOD:
            # parse mood
            try:
                mood_val = int(message_text)
                if not (1 <= mood_val <= 5):
                    raise ValueError("Out of range")
            except ValueError:
                return ("Please enter a number between 1 and 5 for mood.", False)
            data["mood"] = mood_val
            user_state["state"] = CHECKIN_BREAKFAST
            return ("Did you eat breakfast today? (yes/no)", False)

        elif state == CHECKIN_BREAKFAST:
            ate_breakfast = message_text.strip().lower() in ["yes", "y", "yeah", "yep", "true"]
            data["ate_breakfast"] = ate_breakfast
            user_state["state"] = CHECKIN_ENERGY
            return ("How is your energy on a scale of 1 to 5? (1=none, 5=very energetic)", False)

        elif state == CHECKIN_ENERGY:
            try:
                energy_val = int(message_text)
                if not (1 <= energy_val <= 5):
                    raise ValueError("Out of range")
            except ValueError:
                return ("Please enter a number between 1 and 5 for energy.", False)
            data["energy"] = energy_val
            user_state["state"] = CHECKIN_TEETH
            return ("Did you brush your teeth today? (yes/no)", False)

        elif state == CHECKIN_TEETH:
            brushed_teeth = message_text.strip().lower() in ["yes", "y", "yeah", "yep", "true"]
            data["brushed_teeth"] = brushed_teeth

            # We now have all data. Store it as a daily check-in.
            core.utils.store_daily_checkin_response(user_id, data)

            # End the flow
            self.user_states.pop(user_id, None)
            return ("Thanks! Your daily check-in is recorded.", True)

        # fallback
        return ("Something went wrong in daily check-in flow.", True)

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
