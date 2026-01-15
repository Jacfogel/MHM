#!/usr/bin/env python3

"""
user_context_manager.py

Manages comprehensive user context for AI conversations including:
- User profile and preferences
- Recent activity and mood data
- Conversation history
- Personalized insights
"""

from datetime import datetime
from typing import Dict, List, Any

from core.logger import get_component_logger
from core.user_data_handlers import get_user_data
from core.response_tracking import get_recent_checkins, get_recent_chat_interactions
from core.message_management import get_recent_messages
from core.schedule_utilities import get_active_schedules
from core.error_handling import handle_errors
from user.user_context import UserContext

context_logger = get_component_logger("user_activity")
logger = context_logger


class UserContextManager:
    """Manages rich user context for AI conversations."""

    # ERROR_HANDLING_EXCLUDE: Simple constructor that only sets attributes
    def __init__(self):
        """
        Initialize the UserContextManager.

        Sets up conversation history storage for tracking user interactions.
        """
        # Store conversation history per user
        self.conversation_history: Dict[str, List[Dict]] = {}

    @handle_errors("getting current user context", default_return=None)
    def get_current_user_context(
        self, include_conversation_history: bool = True
    ) -> Dict[str, Any]:
        """
        Get context for the currently logged-in user using the existing UserContext singleton.

        Args:
            include_conversation_history: Whether to include recent conversation history

        Returns:
            Dict containing all relevant user context for current user
        """
        user_context = UserContext()
        current_user_id = user_context.get_user_id()

        if not current_user_id:
            logger.warning("No user currently logged in")
            return self._get_minimal_context(None)

        return self.get_ai_context(current_user_id, include_conversation_history)

    @handle_errors("getting AI context", default_return=None)
    def get_ai_context(
        self, user_id: str, include_conversation_history: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive user context for AI conversation.

        Args:
            user_id: The user's ID
            include_conversation_history: Whether to include recent conversation history

        Returns:
            Dict containing all relevant user context for AI processing
        """
        context = {
            "user_profile": self._get_user_profile(user_id),
            "recent_activity": self._get_recent_activity(user_id),
            "conversation_insights": self._get_conversation_insights(user_id),
            "preferences": self._get_user_preferences(user_id),
            "mood_trends": self._get_mood_trends(user_id),
            "conversation_history": (
                self._get_conversation_history(user_id)
                if include_conversation_history
                else []
            ),
        }

        logger.debug(f"Generated AI context for user {user_id}")
        return context

    @handle_errors("getting user profile", default_return={})
    def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get basic user profile information using existing user infrastructure."""
        # Use existing UserContext and UserPreferences classes
        user_context = UserContext()
        user_context.load_user_data(user_id)
        # Get user preferences
        prefs_result = get_user_data(user_id, "preferences")
        user_preferences = prefs_result.get("preferences") or {}
        # Get user account
        user_data_result = get_user_data(user_id, "account")
        user_account = user_data_result.get("account") or {}
        # Get user context
        context_result = get_user_data(user_id, "context")
        user_context_data = context_result.get("context") or {}

        # Get schedules for active schedules check
        schedules_result = get_user_data(user_id, "schedules", normalize_on_read=True)
        schedules_data = (
            schedules_result.get("schedules", {})
            if isinstance(schedules_result, dict) and "schedules" in schedules_result
            else (schedules_result if isinstance(schedules_result, dict) else {})
        )

        return {
            "preferred_name": user_context.get_preferred_name()
            or user_context_data.get("preferred_name", ""),
            "active_categories": user_preferences.get("categories", []),
            "messaging_service": user_preferences.get("channel", {}).get("type", ""),
            "active_schedules": get_active_schedules(
                schedules_data
            ),  # Pass schedules dict, not user_id
        }

    @handle_errors("getting recent activity", default_return={})
    def _get_recent_activity(self, user_id: str) -> Dict[str, Any]:
        """Get recent user activity and responses."""
        recent_responses = get_recent_checkins(user_id, limit=7)

        activity_summary = {
            "recent_responses_count": len(recent_responses),
            "last_response_date": None,
            "recent_messages_count": 0,
            "last_message_date": None,
        }

        if recent_responses:
            latest_response = recent_responses[0]
            if "timestamp" in latest_response:
                timestamp_value = latest_response["timestamp"]
                # Human-readable format - extract the date part
                activity_summary["last_response_date"] = timestamp_value.split(" ")[0]

        # Get recent message activity from all categories
        prefs_result = get_user_data(user_id, "preferences")
        categories = prefs_result.get("preferences", {}).get("categories", [])

        total_recent_messages = 0
        most_recent_date = None

        for category in categories:
            try:
                category_messages = get_recent_messages(
                    user_id, category=category, limit=10
                )
                total_recent_messages += len(category_messages)

                if category_messages:
                    latest_msg = category_messages[
                        0
                    ]  # Already sorted by timestamp desc
                    if "timestamp" in latest_msg:
                        msg_date = latest_msg["timestamp"][:10]
                        if not most_recent_date or msg_date > most_recent_date:
                            most_recent_date = msg_date
            except Exception as cat_error:
                logger.debug(
                    f"Could not get messages for category {category}: {cat_error}"
                )
                continue

        activity_summary["recent_messages_count"] = min(
            total_recent_messages, 10
        )  # Cap at 10 for summary
        activity_summary["last_message_date"] = most_recent_date

        return activity_summary

    @handle_errors("getting conversation insights", default_return={})
    def _get_conversation_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights from recent chat interactions."""
        recent_chats = get_recent_chat_interactions(user_id, limit=5)

        if not recent_chats:
            return {"recent_topics": [], "interaction_count": 0}

        # Analyze recent conversation topics and patterns
        topics = []
        total_user_messages = 0
        total_ai_responses = 0

        for chat in recent_chats:
            user_msg = chat.get("user_message", "")
            # Extract key topics/themes from user messages
            if len(user_msg) > 10:  # Only meaningful messages
                if any(
                    word in user_msg.lower()
                    for word in ["mood", "feeling", "sad", "happy", "stress"]
                ):
                    topics.append("emotional_wellbeing")
                elif any(
                    word in user_msg.lower()
                    for word in ["help", "advice", "how to", "what should"]
                ):
                    topics.append("seeking_guidance")
                elif any(
                    word in user_msg.lower()
                    for word in ["energy", "tired", "sleep", "rest"]
                ):
                    topics.append("energy_health")
                else:
                    topics.append("general_conversation")

            total_user_messages += chat.get("message_length", 0)
            total_ai_responses += chat.get("response_length", 0)

        # Get unique topics
        unique_topics = list(set(topics))

        return {
            "recent_topics": unique_topics,
            "interaction_count": len(recent_chats),
            "avg_message_length": total_user_messages // max(len(recent_chats), 1),
            "engagement_level": (
                "high"
                if len(recent_chats) > 3
                else "moderate" if len(recent_chats) > 1 else "low"
            ),
        }

    @handle_errors("getting user preferences", default_return={})
    def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences using new structure."""
        try:
            prefs_result = get_user_data(user_id, "preferences")
            preferences = prefs_result.get("preferences", {})
            return preferences
        except Exception as e:
            logger.error(f"Error getting preferences for user {user_id}: {e}")
            return {}

    @handle_errors("getting mood trends", default_return={})
    def _get_mood_trends(self, user_id: str) -> Dict[str, Any]:
        """Analyze recent mood and energy trends."""
        recent_responses = get_recent_checkins(user_id, limit=5)

        if not recent_responses:
            return {"trend": "no_data"}

        moods = [r.get("mood") for r in recent_responses if r.get("mood") is not None]
        energies = [
            r.get("energy") for r in recent_responses if r.get("energy") is not None
        ]

        mood_trend = {
            "average_mood": sum(moods) / len(moods) if moods else None,
            "average_energy": sum(energies) / len(energies) if energies else None,
            "trend": "stable",
        }

        # Determine trend
        if len(moods) >= 3:
            recent_avg = sum(moods[:2]) / 2
            older_avg = sum(moods[2:]) / len(moods[2:])

            if recent_avg > older_avg + 0.5:
                mood_trend["trend"] = "improving"
            elif recent_avg < older_avg - 0.5:
                mood_trend["trend"] = "declining"

        return mood_trend

    @handle_errors("getting conversation history", default_return=[])
    def _get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get recent conversation history with this user."""
        return self.conversation_history.get(user_id, [])[-5:]  # Last 5 exchanges

    @handle_errors("adding conversation exchange")
    def add_conversation_exchange(
        self, user_id: str, user_message: str, ai_response: str
    ):
        """
        Add a conversation exchange to history.

        Args:
            user_id: The user's ID
            user_message: The user's message
            ai_response: The AI's response
        """
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "ai_response": ai_response,
            "message_length": len(user_message),
            "response_length": len(ai_response),
        }

        self.conversation_history[user_id].append(exchange)

        # Keep only last 20 exchanges to prevent memory bloat
        if len(self.conversation_history[user_id]) > 20:
            self.conversation_history[user_id] = self.conversation_history[user_id][
                -20:
            ]

        logger.debug(f"Added conversation exchange for user {user_id}")

    @handle_errors("getting minimal context", default_return={})
    def _get_minimal_context(self, user_id: str) -> Dict[str, Any]:
        """
        Fallback minimal context if full context generation fails.

        Args:
            user_id: The user's ID (can be None for anonymous context)

        Returns:
            dict: Minimal context with basic information
        """
        return {
            "user_profile": {
                "preferred_name": "User" if user_id else "Anonymous",
                "active_categories": [],
                "messaging_service": "",
                "active_schedules": [],
            },
            "recent_activity": {
                "recent_responses_count": 0,
                "last_response_date": None,
                "recent_messages_count": 0,
                "last_message_date": None,
            },
            "conversation_insights": {
                "recent_topics": [],
                "interaction_count": 0,
                "avg_message_length": 0,
                "engagement_level": "low",
            },
            "preferences": {},
            "mood_trends": {},
            "conversation_history": [],
        }

    @handle_errors(
        "formatting context for AI", default_return="User context unavailable"
    )
    def format_context_for_ai(self, context: Dict[str, Any]) -> str:
        """
        Format user context into a concise string for AI prompt.

        Args:
            context: User context dictionary

        Returns:
            str: Formatted context string for AI consumption
        """
        if not context:
            return "User context unavailable"

        profile = context.get("user_profile", {})
        activity = context.get("recent_activity", {})
        insights = context.get("conversation_insights", {})

        context_parts = []

        # Basic profile info
        if profile.get("preferred_name"):
            context_parts.append(f"User: {profile['preferred_name']}")

        if profile.get("active_categories"):
            context_parts.append(
                f"Active categories: {', '.join(profile['active_categories'])}"
            )

        # Recent activity
        if activity.get("recent_responses_count", 0) > 0:
            context_parts.append(
                f"Recent check-ins: {activity['recent_responses_count']}"
            )

        if activity.get("last_response_date"):
            context_parts.append(f"Last response: {activity['last_response_date']}")

        # Conversation insights
        if insights.get("recent_topics"):
            context_parts.append(
                f"Recent topics: {', '.join(insights['recent_topics'])}"
            )

        if insights.get("engagement_level"):
            context_parts.append(f"Engagement: {insights['engagement_level']}")

        return " | ".join(context_parts) if context_parts else "No recent activity"


# Global instance
user_context_manager = UserContextManager()
