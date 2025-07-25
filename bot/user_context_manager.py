#!/usr/bin/env python3

"""
user_context_manager.py

Manages comprehensive user context for AI conversations including:
- User profile and preferences
- Recent activity and mood data  
- Conversation history
- Personalized insights
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from core.logger import get_logger
from core.user_management import get_user_data
from core.response_tracking import get_recent_daily_checkins, get_recent_chat_interactions
from core.message_management import get_last_10_messages
from core.error_handling import handle_errors
from user.user_context import UserContext
from user.user_preferences import UserPreferences

logger = get_logger(__name__)

class UserContextManager:
    """Manages rich user context for AI conversations."""
    
    def __init__(self):
        # Store conversation history per user
        self.conversation_history: Dict[str, List[Dict]] = {}
    
    @handle_errors("getting current user context", default_return=None)
    def get_current_user_context(self, include_conversation_history: bool = True) -> Dict[str, Any]:
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
        
        return self.get_user_context(current_user_id, include_conversation_history)
        
    @handle_errors("getting user context", default_return=None)
    def get_user_context(self, user_id: str, include_conversation_history: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive user context for AI conversation.
        
        Args:
            user_id: The user's ID
            include_conversation_history: Whether to include recent conversation history
            
        Returns:
            Dict containing all relevant user context
        """
        context = {
            'user_profile': self._get_user_profile(user_id),
            'recent_activity': self._get_recent_activity(user_id),
            'conversation_insights': self._get_conversation_insights(user_id),
            'preferences': self._get_user_preferences(user_id),
            'mood_trends': self._get_mood_trends(user_id),
            'conversation_history': self._get_conversation_history(user_id) if include_conversation_history else []
        }
        
        logger.debug(f"Generated context for user {user_id}")
        return context
    
    @handle_errors("getting user profile", default_return={})
    def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get basic user profile information using existing user infrastructure."""
        # Use existing UserContext and UserPreferences classes
        user_context = UserContext()
        user_context.load_user_data(user_id)
        # Get user preferences
        prefs_result = get_user_data(user_id, 'preferences')
        user_preferences = prefs_result.get('preferences') or {}
        # Get user account
        user_data_result = get_user_data(user_id, 'account')
        user_account = user_data_result.get('account') or {}
        # Get user context
        context_result = get_user_data(user_id, 'context')
        user_context_data = context_result.get('context') or {}
            
        return {
            'preferred_name': user_context.get_preferred_name() or user_context_data.get('preferred_name', ''),
            'active_categories': user_preferences.get_preference('categories') or user_preferences.get('categories', []),
            'messaging_service': user_preferences.get_preference('channel', {}).get('type', ''),
            'active_schedules': self._get_active_schedules({})  # Schedules handled separately
        }
    
    @handle_errors("getting recent activity", default_return={})
    def _get_recent_activity(self, user_id: str) -> Dict[str, Any]:
        """Get recent user activity and responses."""
        recent_responses = get_recent_daily_checkins(user_id, limit=7)
        
        activity_summary = {
            'recent_responses_count': len(recent_responses),
            'last_response_date': None,
            'recent_messages_count': 0,
            'last_message_date': None
        }
        
        if recent_responses:
            latest_response = recent_responses[0]
            if 'timestamp' in latest_response:
                timestamp_value = latest_response['timestamp']
                # Human-readable format - extract the date part
                activity_summary['last_response_date'] = timestamp_value.split(' ')[0]
        
        # Get recent message activity from all categories
        prefs_result = get_user_data(user_id, 'preferences')
        categories = prefs_result.get('preferences', {}).get('categories', [])
        
        total_recent_messages = 0
        most_recent_date = None
        
        for category in categories:
            try:
                category_messages = get_last_10_messages(user_id, category)
                total_recent_messages += len(category_messages)
                
                if category_messages:
                    latest_msg = category_messages[0]  # Already sorted by timestamp desc
                    if 'timestamp' in latest_msg:
                        msg_date = latest_msg['timestamp'][:10]
                        if not most_recent_date or msg_date > most_recent_date:
                            most_recent_date = msg_date
            except Exception as cat_error:
                logger.debug(f"Could not get messages for category {category}: {cat_error}")
                continue
        
        activity_summary['recent_messages_count'] = min(total_recent_messages, 10)  # Cap at 10 for summary
        activity_summary['last_message_date'] = most_recent_date
        
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
            user_msg = chat.get('user_message', '')
            # Extract key topics/themes from user messages
            if len(user_msg) > 10:  # Only meaningful messages
                if any(word in user_msg.lower() for word in ['mood', 'feeling', 'sad', 'happy', 'stress']):
                    topics.append('emotional_wellbeing')
                elif any(word in user_msg.lower() for word in ['help', 'advice', 'how to', 'what should']):
                    topics.append('seeking_guidance')
                elif any(word in user_msg.lower() for word in ['energy', 'tired', 'sleep', 'rest']):
                    topics.append('energy_health')
                else:
                    topics.append('general_conversation')
            
            total_user_messages += chat.get('message_length', 0)
            total_ai_responses += chat.get('response_length', 0)
        
        # Get unique topics
        unique_topics = list(set(topics))
        
        return {
            "recent_topics": unique_topics,
            "interaction_count": len(recent_chats),
            "avg_message_length": total_user_messages // max(len(recent_chats), 1),
            "engagement_level": "high" if len(recent_chats) > 3 else "moderate" if len(recent_chats) > 1 else "low"
        }
    
    @handle_errors("getting user preferences", default_return={})
    def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences using new structure."""
        try:
            prefs_result = get_user_data(user_id, 'preferences')
            preferences = prefs_result.get('preferences', {})
            return preferences
        except Exception as e:
            logger.error(f"Error getting preferences for user {user_id}: {e}")
            return {}
    
    @handle_errors("getting mood trends", default_return={})
    def _get_mood_trends(self, user_id: str) -> Dict[str, Any]:
        """Analyze recent mood and energy trends."""
        recent_responses = get_recent_daily_checkins(user_id, limit=5)
        
        if not recent_responses:
            return {'trend': 'no_data'}
        
        moods = [r.get('mood') for r in recent_responses if r.get('mood') is not None]
        energies = [r.get('energy') for r in recent_responses if r.get('energy') is not None]
        
        mood_trend = {
            'average_mood': sum(moods) / len(moods) if moods else None,
            'average_energy': sum(energies) / len(energies) if energies else None,
            'trend': 'stable'
        }
        
        # Determine trend
        if len(moods) >= 3:
            recent_avg = sum(moods[:2]) / 2
            older_avg = sum(moods[2:]) / len(moods[2:])
            
            if recent_avg > older_avg + 0.5:
                mood_trend['trend'] = 'improving'
            elif recent_avg < older_avg - 0.5:
                mood_trend['trend'] = 'declining'
        
        return mood_trend
    
    @handle_errors("getting active schedules", default_return=[])
    def _get_active_schedules(self, schedules: Dict) -> List[str]:
        """Get list of currently active schedule periods."""
        active_periods = []
        for category, periods in schedules.items():
            for period_name, period_info in periods.items():
                # Use existing UserPreferences schedule methods where possible
                if period_info.get('active', False):
                    active_periods.append(f"{category}:{period_name}")
        return active_periods
    
    @handle_errors("getting conversation history", default_return=[])
    def _get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get recent conversation history with this user."""
        return self.conversation_history.get(user_id, [])[-5:]  # Last 5 exchanges
    
    @handle_errors("adding conversation exchange")
    def add_conversation_exchange(self, user_id: str, user_message: str, ai_response: str):
        """Add a conversation exchange to history."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        exchange = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response
        }
        
        self.conversation_history[user_id].append(exchange)
        
        # Keep only last 10 exchanges per user
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
            
        logger.debug(f"Added conversation exchange for user {user_id}")
    
    @handle_errors("getting minimal context", default_return={})
    def _get_minimal_context(self, user_id: str) -> Dict[str, Any]:
        """Fallback minimal context if full context generation fails."""
        # Legacy import removed - using get_user_data() instead
        user_data_result = get_user_data(user_id, 'account')
        user_account = user_data_result.get('account')
        context_result = get_user_data(user_id, 'context')
        user_context = context_result.get('context')
        preferred_name = user_context.get('preferred_name', '') if user_context else ''
        
        return {
            'user_profile': {'preferred_name': preferred_name},
            'recent_activity': {},
            'preferences': {},
            'mood_trends': {},
            'conversation_history': []
        }
    
    @handle_errors("formatting context for AI", default_return="User context unavailable")
    def format_context_for_ai(self, context: Dict[str, Any]) -> str:
        """Format user context into a concise string for AI prompt."""
        parts = []
        
        # User profile
        profile = context.get('user_profile', {})
        if profile.get('preferred_name'):
            parts.append(f"User: {profile['preferred_name']}")
        
        if profile.get('active_categories'):
            parts.append(f"Interests: {', '.join(profile['active_categories'])}")
        
        # Recent activity
        activity = context.get('recent_activity', {})
        if activity.get('recent_responses_count', 0) > 0:
            parts.append(f"Recent activity: {activity['recent_responses_count']} check-ins")
        
        # Mood trends
        mood = context.get('mood_trends', {})
        if mood.get('average_mood') is not None:
            avg_mood = mood['average_mood']
            trend = mood.get('trend', 'stable')
            parts.append(f"Recent mood: {avg_mood:.1f}/5 ({trend})")
        
        # Recent conversation
        conversation = context.get('conversation_history', [])
        if conversation:
            last_exchange = conversation[-1]
            parts.append(f"Previous topic: {last_exchange['user_message'][:30]}...")
        
        return " | ".join(parts) if parts else "New user"

# Global instance
user_context_manager = UserContextManager() 