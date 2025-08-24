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
        return intent in ['show_analytics', 'mood_trends', 'habit_analysis', 'sleep_analysis', 'wellness_score', 'checkin_history', 'checkin_analysis', 'completion_rate', 'task_analytics', 'task_stats']
    
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
        elif intent == 'checkin_analysis':
            return self._handle_checkin_analysis(user_id, entities)
        elif intent == 'completion_rate':
            return self._handle_completion_rate(user_id, entities)
        elif intent == 'task_analytics':
            return self._handle_task_analytics(user_id, entities)
        elif intent == 'task_stats':
            return self._handle_task_stats(user_id, entities)
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
            from core.response_tracking import get_recent_checkins
            checkins = get_recent_checkins(user_id, limit=days)
            
            if not checkins:
                return InteractionResponse("You haven't completed any check-ins yet. Try starting one with '/checkin'!", True)
            
            response = f"**📊 Check-in History (Last {len(checkins)} check-ins):**\n\n"
            
            for i, checkin in enumerate(checkins[:10]):  # Show last 10
                timestamp = checkin.get('timestamp', 'Unknown')
                mood = checkin.get('mood', 'N/A')
                energy = checkin.get('energy', 'N/A')
                
                response += f"**{i+1}.** {timestamp}\n"
                response += f"   😊 Mood: {mood}/10 | ⚡ Energy: {energy}/10\n"
                
                # Add some key responses if available
                responses = checkin.get('responses', {})
                if responses:
                    for question, answer in list(responses.items())[:2]:  # Show first 2 responses
                        response += f"   • {question}: {answer}\n"
                response += "\n"
            
            if len(checkins) > 10:
                response += f"... and {len(checkins) - 10} more check-ins\n\n"
            
            response += "💡 **Tip**: Use 'mood trends' to see your mood patterns over time!"
            
            # Truncate response if too long for Discord
            response = self._truncate_response(response)
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing check-in history for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your check-in history right now. Please try again.", True)
    
    def _handle_checkin_analysis(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show comprehensive check-in response analysis"""
        days = entities.get('days', 30)
        
        try:
            from core.response_tracking import get_recent_checkins
            from core.checkin_analytics import CheckinAnalytics
            
            checkins = get_recent_checkins(user_id, limit=days)
            
            if not checkins:
                return InteractionResponse("You don't have enough check-in data for analysis yet. Try completing some check-ins first!", True)
            
            analytics = CheckinAnalytics()
            
            # Get mood trends
            mood_data = analytics.get_mood_trends(user_id, days)
            
            response = f"**📈 Check-in Analysis (Last {len(checkins)} check-ins):**\n\n"
            
            # Mood Analysis
            if 'error' not in mood_data:
                response += f"**😊 Mood Trends:**\n"
                response += f"• Average: {mood_data.get('average_mood', 0):.1f}/10\n"
                response += f"• Range: {mood_data.get('min_mood', 0)} - {mood_data.get('max_mood', 0)}/10\n"
                response += f"• Trend: {mood_data.get('trend', 'Stable')}\n\n"
            else:
                response += f"**😊 Mood Data:** Not enough mood data for analysis\n\n"
            
            # Check-in Patterns
            response += f"**📅 Check-in Patterns:**\n"
            response += f"• Total check-ins: {len(checkins)}\n"
            response += f"• Average per day: {len(checkins)/days:.1f}\n"
            
            # Response Analysis
            response += f"\n**💬 Response Analysis:**\n"
            
            # Analyze common responses
            all_responses = {}
            for checkin in checkins:
                responses = checkin.get('responses', {})
                for question, answer in responses.items():
                    if question not in all_responses:
                        all_responses[question] = []
                    all_responses[question].append(answer)
            
            if all_responses:
                response += f"• Questions answered: {len(all_responses)}\n"
                
                # Show most common responses for key questions
                for question, answers in list(all_responses.items())[:3]:
                    if len(answers) > 1:
                        # Find most common answer
                        from collections import Counter
                        counter = Counter(answers)
                        most_common = counter.most_common(1)[0]
                        response += f"• '{question}': Most common answer: '{most_common[0]}' ({most_common[1]} times)\n"
            else:
                response += "• No detailed responses found\n"
            
            # Insights
            response += f"\n**💡 Insights:**\n"
            if len(checkins) >= 7:
                response += "• You've been consistent with check-ins\n"
            if 'error' not in mood_data and mood_data.get('trend') == 'improving':
                response += "• Your mood has been improving recently\n"
            elif 'error' not in mood_data and mood_data.get('trend') == 'declining':
                response += "• Your mood has been declining - consider reaching out for support\n"
            
            response += f"\n💡 **Try these commands for more details:**\n"
            response += f"• 'mood trends' - Detailed mood analysis\n"
            response += f"• 'checkin history' - View all your check-ins\n"
            response += f"• 'habit analysis' - Analyze your habits\n"
            
            # Truncate response if too long for Discord
            response = self._truncate_response(response)
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error analyzing check-ins for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble analyzing your check-ins right now. Please try again.", True)
    
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
    
    def _handle_task_analytics(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show comprehensive task analytics and insights"""
        days = entities.get('days', 30)
        
        try:
            from tasks.task_management import get_user_task_stats, load_active_tasks, load_completed_tasks
            from core.checkin_analytics import CheckinAnalytics
            
            # Get basic task statistics
            task_stats = get_user_task_stats(user_id)
            active_tasks = load_active_tasks(user_id)
            completed_tasks = load_completed_tasks(user_id)
            
            # Get task analytics from check-in data
            analytics = CheckinAnalytics()
            task_weekly_stats = analytics.get_task_weekly_stats(user_id, days)
            
            response = f"**📋 Task Analytics (Last {days} days):**\n\n"
            
            # Overall Task Statistics
            response += f"**📊 Overall Task Status:**\n"
            response += f"• Active Tasks: {task_stats.get('active_count', 0)}\n"
            response += f"• Completed Tasks: {task_stats.get('completed_count', 0)}\n"
            response += f"• Total Tasks: {task_stats.get('total_count', 0)}\n"
            
            if task_stats.get('total_count', 0) > 0:
                completion_rate = (task_stats.get('completed_count', 0) / task_stats.get('total_count', 0)) * 100
                response += f"• Overall Completion Rate: {completion_rate:.1f}%\n"
            
            response += "\n"
            
            # Task Completion Patterns
            if task_weekly_stats and 'error' not in task_weekly_stats:
                response += f"**📅 Task Completion Patterns:**\n"
                for task_name, stats in task_weekly_stats.items():
                    completion_rate = stats.get('completion_rate', 0)
                    completed_days = stats.get('completed_days', 0)
                    total_days = stats.get('total_days', 0)
                    
                    # Add emoji based on completion rate
                    emoji = "🟢" if completion_rate >= 80 else "🟡" if completion_rate >= 50 else "🔴"
                    response += f"• {emoji} {task_name}: {completion_rate:.1f}% ({completed_days}/{total_days} days)\n"
            else:
                response += f"**📅 Task Completion Patterns:**\n"
                response += "• No detailed task completion data available\n"
            
            response += "\n"
            
            # Task Insights
            response += f"**💡 Task Insights:**\n"
            if task_stats.get('active_count', 0) > 5:
                response += "• You have many active tasks - consider prioritizing or breaking them down\n"
            elif task_stats.get('active_count', 0) == 0:
                response += "• No active tasks - great job staying on top of things!\n"
            
            if task_stats.get('completed_count', 0) > 0:
                response += "• You're making good progress on task completion\n"
            
            # Add recommendations
            response += f"\n💡 **Try these commands for more details:**\n"
            response += f"• 'task stats' - Detailed task statistics\n"
            response += f"• 'show my tasks' - View all your tasks\n"
            response += f"• 'habit analysis' - See how your habits relate to task completion\n"
            
            # Truncate response if too long
            response = self._truncate_response(response)
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing task analytics for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your task analytics right now. Please try again.", True)
    
    def _handle_task_stats(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show detailed task statistics"""
        days = entities.get('days', 30)
        
        try:
            from tasks.task_management import get_user_task_stats, load_active_tasks, load_completed_tasks
            from core.checkin_analytics import CheckinAnalytics
            
            # Get task statistics
            task_stats = get_user_task_stats(user_id)
            active_tasks = load_active_tasks(user_id)
            completed_tasks = load_completed_tasks(user_id)
            
            response = f"**📊 Task Statistics (Last {days} days):**\n\n"
            
            # Basic Statistics
            response += f"**📋 Task Overview:**\n"
            response += f"• Active Tasks: {task_stats.get('active_count', 0)}\n"
            response += f"• Completed Tasks: {task_stats.get('completed_count', 0)}\n"
            response += f"• Total Tasks: {task_stats.get('total_count', 0)}\n"
            
            if task_stats.get('total_count', 0) > 0:
                completion_rate = (task_stats.get('completed_count', 0) / task_stats.get('total_count', 0)) * 100
                response += f"• Completion Rate: {completion_rate:.1f}%\n"
            
            response += "\n"
            
            # Priority Breakdown
            if active_tasks:
                response += f"**🎯 Active Task Priorities:**\n"
                priority_counts = {}
                for task in active_tasks:
                    priority = task.get('priority', 'medium')
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1
                
                for priority, count in priority_counts.items():
                    emoji = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
                    response += f"• {emoji} {priority.title()}: {count} tasks\n"
            
            response += "\n"
            
            # Recent Completions
            if completed_tasks:
                response += f"**✅ Recently Completed:**\n"
                recent_completed = completed_tasks[:5]  # Show last 5
                for task in recent_completed:
                    title = task.get('title', 'Unknown Task')
                    response += f"• {title}\n"
            
            # Truncate response if too long
            response = self._truncate_response(response)
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing task stats for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your task statistics right now. Please try again.", True)
    
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
            "checkin analysis",
            "completion rate",
            "task analytics",
            "task stats"
        ]

    def _truncate_response(self, response: str, max_length: int = 1900) -> str:
        """Truncate response to fit Discord message limits"""
        if len(response) <= max_length:
            return response
        
        # Try to truncate at a reasonable point
        truncated = response[:max_length-3] + "..."
        
        # Try to find a better truncation point
        last_newline = truncated.rfind('\n')
        if last_newline > max_length * 0.8:  # If we can find a newline in the last 20%
            truncated = response[:last_newline] + "\n\n... (response truncated)"
        
        return truncated
