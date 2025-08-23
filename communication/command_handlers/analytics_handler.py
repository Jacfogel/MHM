# analytics_handler.py

from typing import Dict, Any, List

from core.logger import get_component_logger
from core.error_handling import handle_errors
from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand

# Route analytics logs to command handlers component
analytics_logger = get_component_logger('analytics_handler')
logger = analytics_logger

class AnalyticsHandler(InteractionHandler):
    """Handler for analytics and insights interactions"""
    
    def can_handle(self, intent: str) -> bool:
        return intent in ['show_analytics', 'mood_trends', 'habit_analysis', 'sleep_analysis', 'wellness_score', 'checkin_history', 'completion_rate']
    
    @handle_errors("handling analytics interaction", default_return=InteractionResponse("I'm having trouble with analytics right now. Please try again.", True))
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        intent = parsed_command.intent
        entities = parsed_command.entities
        
        if intent == 'show_analytics':
            return self._handle_show_analytics(user_id, entities)
        elif intent == 'mood_trends':
            return self._handle_mood_trends(user_id, entities)
        elif intent == 'habit_analysis':
            return self._handle_habit_analysis(user_id, entities)
        elif intent == 'sleep_analysis':
            return self._handle_sleep_analysis(user_id, entities)
        elif intent == 'wellness_score':
            return self._handle_wellness_score(user_id, entities)
        elif intent == 'checkin_history':
            return self._handle_checkin_history(user_id, entities)
        elif intent == 'completion_rate':
            return self._handle_completion_rate(user_id, entities)
        else:
            return InteractionResponse(f"I don't understand that analytics command. Try: {', '.join(self.get_examples())}", True)
    
    def _handle_show_analytics(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show comprehensive analytics overview"""
        days = entities.get('days', 30)
        
        try:
            from core.checkin_analytics import CheckinAnalytics
            analytics = CheckinAnalytics()
            
            # Get wellness score
            wellness_data = analytics.get_wellness_score(user_id, days)
            if 'error' in wellness_data:
                return InteractionResponse("You don't have enough check-in data for analytics yet. Try completing some check-ins first!", True)
            
            # Get mood trends
            mood_data = analytics.get_mood_trends(user_id, days)
            mood_summary = ""
            if 'error' not in mood_data:
                avg_mood = mood_data.get('average_mood', 0)
                mood_summary = f"Average mood: {avg_mood}/10"
            
            # Get habit analysis
            habit_data = analytics.get_habit_analysis(user_id, days)
            habit_summary = ""
            if 'error' not in habit_data:
                completion_rate = habit_data.get('overall_completion', 0)
                habit_summary = f"Habit completion: {completion_rate}%"
            
            response = f"**📊 Your Wellness Analytics (Last {days} days):**\n\n"
            response += f"🎯 **Overall Wellness Score:** {wellness_data.get('score', 0)}/100\n"
            response += f"   Level: {wellness_data.get('level', 'Unknown')}\n\n"
            
            if mood_summary:
                response += f"😊 **Mood:** {mood_summary}\n"
            if habit_summary:
                response += f"✅ **Habits:** {habit_summary}\n"
            
            # Add recommendations
            recommendations = wellness_data.get('recommendations', [])
            if recommendations:
                response += "\n💡 **Recommendations:**\n"
                for rec in recommendations[:3]:  # Show top 3
                    response += f"• {rec}\n"
            
            response += "\nTry 'mood trends' or 'habit analysis' for more detailed insights!"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing analytics for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your analytics right now. Please try again.", True)
    
    def _handle_mood_trends(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show mood trends analysis"""
        days = entities.get('days', 30)
        
        try:
            from core.checkin_analytics import CheckinAnalytics
            analytics = CheckinAnalytics()
            
            mood_data = analytics.get_mood_trends(user_id, days)
            if 'error' in mood_data:
                return InteractionResponse("You don't have enough mood data for analysis yet. Try completing some check-ins first!", True)
            
            response = f"**😊 Mood Trends (Last {days} days):**\n\n"
            response += f"📈 **Average Mood:** {mood_data.get('average_mood', 0)}/10\n"
            response += f"📊 **Mood Range:** {mood_data.get('min_mood', 0)} - {mood_data.get('max_mood', 0)}/10\n"
            response += f"📉 **Trend:** {mood_data.get('trend', 'Stable')}\n\n"
            
            # Show mood distribution
            distribution = mood_data.get('mood_distribution', {})
            if distribution:
                response += "**Mood Distribution:**\n"
                for mood_level, count in distribution.items():
                    response += f"• {mood_level}: {count} days\n"
            
            # Add insights
            insights = mood_data.get('insights', [])
            if insights:
                response += "\n💡 **Insights:**\n"
                for insight in insights[:2]:  # Show top 2 insights
                    response += f"• {insight}\n"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing mood trends for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your mood trends right now. Please try again.", True)
    
    def _handle_habit_analysis(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show habit analysis"""
        days = entities.get('days', 30)
        
        try:
            from core.checkin_analytics import CheckinAnalytics
            analytics = CheckinAnalytics()
            
            habit_data = analytics.get_habit_analysis(user_id, days)
            if 'error' in habit_data:
                return InteractionResponse("You don't have enough habit data for analysis yet. Try completing some check-ins first!", True)
            
            response = f"**✅ Habit Analysis (Last {days} days):**\n\n"
            response += f"📊 **Overall Completion:** {habit_data.get('overall_completion', 0)}%\n"
            response += f"🔥 **Current Streak:** {habit_data.get('current_streak', 0)} days\n"
            response += f"🏆 **Best Streak:** {habit_data.get('best_streak', 0)} days\n\n"
            
            # Show individual habits
            habits = habit_data.get('habits', {})
            if habits:
                response += "**Individual Habits:**\n"
                for habit_name, habit_stats in habits.items():
                    completion = habit_stats.get('completion_rate', 0)
                    status = habit_stats.get('status', 'Unknown')
                    response += f"• {habit_name}: {completion}% ({status})\n"
            
            # Add recommendations
            recommendations = habit_data.get('recommendations', [])
            if recommendations:
                response += "\n💡 **Recommendations:**\n"
                for rec in recommendations[:2]:  # Show top 2
                    response += f"• {rec}\n"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing habit analysis for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your habit analysis right now. Please try again.", True)
    
    def _handle_sleep_analysis(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show sleep analysis"""
        days = entities.get('days', 30)
        
        try:
            from core.checkin_analytics import CheckinAnalytics
            analytics = CheckinAnalytics()
            
            sleep_data = analytics.get_sleep_analysis(user_id, days)
            if 'error' in sleep_data:
                return InteractionResponse("You don't have enough sleep data for analysis yet. Try completing some check-ins with sleep information!", True)
            
            response = f"**😴 Sleep Analysis (Last {days} days):**\n\n"
            response += f"⏰ **Average Hours:** {sleep_data.get('average_hours', 0)} hours\n"
            response += f"⭐ **Average Quality:** {sleep_data.get('average_quality', 0)}/5\n"
            response += f"✅ **Good Sleep Days:** {sleep_data.get('good_sleep_days', 0)} days\n"
            response += f"❌ **Poor Sleep Days:** {sleep_data.get('poor_sleep_days', 0)} days\n\n"
            
            # Add consistency info
            consistency = sleep_data.get('sleep_consistency', 0)
            response += f"📊 **Sleep Consistency:** {consistency:.1f} (lower = more consistent)\n\n"
            
            # Add recommendations
            recommendations = sleep_data.get('recommendations', [])
            if recommendations:
                response += "💡 **Sleep Recommendations:**\n"
                for rec in recommendations[:2]:  # Show top 2
                    response += f"• {rec}\n"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing sleep analysis for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your sleep analysis right now. Please try again.", True)
    
    def _handle_wellness_score(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show wellness score"""
        days = entities.get('days', 30)
        
        try:
            from core.checkin_analytics import CheckinAnalytics
            analytics = CheckinAnalytics()
            
            wellness_data = analytics.get_wellness_score(user_id, days)
            if 'error' in wellness_data:
                return InteractionResponse("You don't have enough data for a wellness score yet. Try completing some check-ins first!", True)
            
            response = f"**🎯 Wellness Score (Last {days} days):**\n\n"
            response += f"📊 **Overall Score:** {wellness_data.get('score', 0)}/100\n"
            response += f"📈 **Level:** {wellness_data.get('level', 'Unknown')}\n\n"
            
            # Show component scores
            components = wellness_data.get('components', {})
            if components:
                response += "**Component Scores:**\n"
                response += f"😊 **Mood Score:** {components.get('mood_score', 0)}/100\n"
                response += f"✅ **Habit Score:** {components.get('habit_score', 0)}/100\n"
                response += f"😴 **Sleep Score:** {components.get('sleep_score', 0)}/100\n\n"
            
            # Add recommendations
            recommendations = wellness_data.get('recommendations', [])
            if recommendations:
                response += "💡 **Recommendations:**\n"
                for rec in recommendations[:3]:  # Show top 3
                    response += f"• {rec}\n"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing wellness score for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble calculating your wellness score right now. Please try again.", True)
    
    def _handle_checkin_history(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show check-in history"""
        days = entities.get('days', 30)
        
        try:
            from core.checkin_analytics import CheckinAnalytics
            analytics = CheckinAnalytics()
            
            checkin_history = analytics.get_checkin_history(user_id, days)
            if 'error' in checkin_history:
                return InteractionResponse("You don't have enough check-in data for history yet. Try completing some check-ins first!", True)
            
            response = f"**📅 Check-in History (Last {days} days):**\n\n"
            for checkin in checkin_history[:5]:  # Show last 5 check-ins
                date = checkin.get('date', 'Unknown date')
                mood = checkin.get('mood', 'No mood recorded')
                response += f"📅 {date}: Mood {mood}/10\n"
            
            if len(checkin_history) > 5:
                response += f"... and {len(checkin_history) - 5} more check-ins\n"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing check-in history for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your check-in history right now. Please try again.", True)
    
    def _handle_completion_rate(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show completion rate"""
        days = entities.get('days', 30)
        
        try:
            from core.checkin_analytics import CheckinAnalytics
            analytics = CheckinAnalytics()
            
            completion_rate = analytics.get_completion_rate(user_id, days)
            if 'error' in completion_rate:
                return InteractionResponse("You don't have enough check-in data for completion rate yet. Try completing some check-ins first!", True)
            
            response = f"**📊 Completion Rate (Last {days} days):**\n\n"
            response += f"🎯 **Overall Completion Rate:** {completion_rate.get('rate', 0)}%\n"
            response += f"📅 **Days Completed:** {completion_rate.get('days_completed', 0)}\n"
            response += f"📅 **Days Missed:** {completion_rate.get('days_missed', 0)}\n"
            response += f"📅 **Total Days:** {completion_rate.get('total_days', 0)}\n"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing completion rate for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble calculating your completion rate right now. Please try again.", True)
    
    def get_help(self) -> str:
        return "Help with analytics - view analytics and insights about your wellness patterns"
    
    def get_examples(self) -> List[str]:
        return [
            "show analytics",
            "mood trends",
            "habit analysis",
            "sleep analysis",
            "wellness score",
            "checkin history",
            "completion rate"
        ]
