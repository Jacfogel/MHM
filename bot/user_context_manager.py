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

import core.utils
from core.logger import get_logger
from user.user_context import UserContext
from user.user_preferences import UserPreferences

logger = get_logger(__name__)

class UserContextManager:
    """Manages rich user context for AI conversations."""
    
    def __init__(self):
        # Store conversation history per user
        self.conversation_history: Dict[str, List[Dict]] = {}
    
    def get_current_user_context(self, include_conversation_history: bool = True) -> Dict[str, Any]:
        """
        Get context for the currently logged-in user using the existing UserContext singleton.
        
        Args:
            include_conversation_history: Whether to include recent conversation history
            
        Returns:
            Dict containing all relevant user context for current user
        """
        try:
            user_context = UserContext()
            current_user_id = user_context.get_user_id()
            
            if not current_user_id:
                logger.warning("No user currently logged in")
                return self._get_minimal_context(None)
            
            return self.get_user_context(current_user_id, include_conversation_history)
        except Exception as e:
            logger.error(f"Error getting current user context: {e}")
            return self._get_minimal_context(None)
        
    def get_user_context(self, user_id: str, include_conversation_history: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive user context for AI conversation.
        
        Args:
            user_id: The user's ID
            include_conversation_history: Whether to include recent conversation history
            
        Returns:
            Dict containing all relevant user context
        """
        try:
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
            
        except Exception as e:
            logger.error(f"Error generating context for user {user_id}: {e}")
            return self._get_minimal_context(user_id)
    
    def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get basic user profile information using existing user infrastructure."""
        try:
            # Use existing UserContext and UserPreferences classes
            user_context = UserContext()
            user_context.load_user_data(user_id)
            user_preferences = UserPreferences(user_id)
            
            # Also get additional data from utils for completeness
            user_info = core.utils.load_user_info_data(user_id)
            if not user_info:
                return {}
                
            return {
                'preferred_name': user_context.get_preferred_name() or user_info.get('preferred_name', ''),
                'active_categories': user_preferences.get_preference('categories') or user_info.get('preferences', {}).get('categories', []),
                'messaging_service': user_preferences.get_preference('messaging_service') or user_info.get('preferences', {}).get('messaging_service', ''),
                'active_schedules': self._get_active_schedules(user_info.get('schedules', {}))
            }
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return {}
    
    def _get_recent_activity(self, user_id: str) -> Dict[str, Any]:
        """Get recent user activity and responses."""
        try:
            recent_responses = core.utils.get_recent_daily_checkins(user_id, limit=7)
            
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
            try:
                user_preferences = core.utils.get_user_preferences(user_id)
                categories = user_preferences.get('categories', [])
                
                total_recent_messages = 0
                most_recent_date = None
                
                for category in categories:
                    try:
                        category_messages = core.utils.get_last_10_messages(user_id, category)
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
                
            except Exception as msg_error:
                logger.debug(f"Could not get recent message activity: {msg_error}")
            
            return activity_summary
        except Exception as e:
            logger.error(f"Error getting recent activity for {user_id}: {e}")
            return {}
        
    def _get_conversation_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights from recent chat interactions."""
        try:
            recent_chats = core.utils.get_recent_chat_interactions(user_id, limit=5)
            
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
            
        except Exception as e:
            logger.error(f"Error getting conversation insights for {user_id}: {e}")
            return {"recent_topics": [], "interaction_count": 0}
    
    def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences and settings using existing UserPreferences class."""
        try:
            user_preferences = UserPreferences(user_id)
            
            # Also get from utils as fallback
            preferences = core.utils.get_user_preferences(user_id)
            
            return {
                'categories': user_preferences.get_preference('categories') or preferences.get('categories', []),
                'messaging_service': user_preferences.get_preference('messaging_service') or preferences.get('messaging_service', 'discord'),
                'email': user_preferences.get_preference('email') or preferences.get('email', '')
            }
        except Exception as e:
            logger.error(f"Error getting preferences for {user_id}: {e}")
            return {}
    
    def _get_mood_trends(self, user_id: str) -> Dict[str, Any]:
        """Analyze recent mood and energy trends."""
        try:
            recent_responses = core.utils.get_recent_daily_checkins(user_id, limit=5)
            
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
        except Exception as e:
            logger.error(f"Error analyzing mood trends for {user_id}: {e}")
            return {}
    
    def _get_active_schedules(self, schedules: Dict) -> List[str]:
        """Get list of currently active schedule periods."""
        active_periods = []
        for category, periods in schedules.items():
            for period_name, period_info in periods.items():
                # Use existing UserPreferences schedule methods where possible
                if period_info.get('active', False):
                    active_periods.append(f"{category}:{period_name}")
        return active_periods
    
    def _get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get recent conversation history with this user."""
        return self.conversation_history.get(user_id, [])[-5:]  # Last 5 exchanges
    
    def add_conversation_exchange(self, user_id: str, user_message: str, ai_response: str):
        """Add a conversation exchange to history."""
        try:
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
        except Exception as e:
            logger.error(f"Error adding conversation exchange for {user_id}: {e}")
    
    def _get_minimal_context(self, user_id: str) -> Dict[str, Any]:
        """Fallback minimal context if full context generation fails."""
        try:
            user_info = core.utils.load_user_info_data(user_id)
            preferred_name = user_info.get('preferred_name', '') if user_info else ''
            
            return {
                'user_profile': {'preferred_name': preferred_name},
                'recent_activity': {},
                'preferences': {},
                'mood_trends': {},
                'conversation_history': []
            }
        except:
            return {
                'user_profile': {},
                'recent_activity': {},
                'preferences': {},
                'mood_trends': {},
                'conversation_history': []
            }
    
    def format_context_for_ai(self, context: Dict[str, Any]) -> str:
        """Format user context into a concise string for AI prompt."""
        try:
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
            
        except Exception as e:
            logger.error(f"Error formatting context: {e}")
            return "User context unavailable"

# Global instance
user_context_manager = UserContextManager() 