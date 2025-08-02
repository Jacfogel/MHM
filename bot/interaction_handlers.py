# bot/interaction_handlers.py

"""
Interaction handlers for channel-neutral user interactions.

This module provides a framework for handling different types of user interactions
(like task management, check-ins, profile management) in a way that works across
all communication channels (Discord, email, Telegram, etc.).
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from core.logger import get_logger
from core.error_handling import handle_errors
from tasks.task_management import (
    create_task, load_active_tasks, complete_task, delete_task, update_task,
    get_user_task_stats, get_tasks_due_soon
)
from core.user_management import (
    load_user_account_data, load_user_preferences_data, load_user_context_data,
    save_user_context_data, get_user_categories
)
from core.response_tracking import (
    is_user_checkins_enabled, get_user_checkin_preferences, get_recent_daily_checkins
)
from core.user_management import load_user_schedules_data

logger = get_logger(__name__)

@dataclass
class InteractionResponse:
    """Response from an interaction handler"""
    message: str
    completed: bool = True
    rich_data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None

@dataclass
class ParsedCommand:
    """Parsed command with intent and entities"""
    intent: str
    entities: Dict[str, Any]
    confidence: float
    original_message: str

class InteractionHandler(ABC):
    """Abstract base class for interaction handlers"""
    
    @abstractmethod
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent"""
        pass
    
    @abstractmethod
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        """Handle the interaction and return a response"""
        pass
    
    @abstractmethod
    def get_help(self) -> str:
        """Get help text for this handler"""
        pass
    
    @abstractmethod
    def get_examples(self) -> List[str]:
        """Get example commands for this handler"""
        pass

class TaskManagementHandler(InteractionHandler):
    """Handler for task management interactions"""
    
    def can_handle(self, intent: str) -> bool:
        return intent in ['create_task', 'list_tasks', 'complete_task', 'delete_task', 'update_task', 'task_stats']
    
    @handle_errors("handling task management interaction", default_return=InteractionResponse("I'm having trouble with task management right now. Please try again.", True))
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        intent = parsed_command.intent
        entities = parsed_command.entities
        
        if intent == 'create_task':
            return self._handle_create_task(user_id, entities)
        elif intent == 'list_tasks':
            return self._handle_list_tasks(user_id, entities)
        elif intent == 'complete_task':
            return self._handle_complete_task(user_id, entities)
        elif intent == 'delete_task':
            return self._handle_delete_task(user_id, entities)
        elif intent == 'update_task':
            return self._handle_update_task(user_id, entities)
        elif intent == 'task_stats':
            return self._handle_task_stats(user_id)
        else:
            return InteractionResponse(f"I don't understand that task command. Try: {', '.join(self.get_examples())}", True)
    
    def _handle_create_task(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle task creation"""
        title = entities.get('title')
        if not title:
            return InteractionResponse(
                "What would you like to name the task?",
                completed=False,
                suggestions=["Call mom", "Buy groceries", "Schedule dentist appointment"]
            )
        
        # Extract other task properties
        description = entities.get('description', '')
        due_date = entities.get('due_date')
        priority = entities.get('priority', 'medium')
        
        # Convert relative dates to proper dates
        if due_date:
            due_date = self._parse_relative_date(due_date)
        
        # Create the task
        task_id = create_task(
            user_id=user_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority
        )
        
        if task_id:
            response = f"✅ Task created: '{title}'"
            if due_date:
                response += f" (due: {due_date})"
            if priority != 'medium':
                response += f" (priority: {priority})"
            
            # Ask about reminder periods
            response += "\n\nWould you like to set reminder periods for this task? (e.g., '1 hour before', '30 minutes before', '1 day before')"
            
            return InteractionResponse(
                response, 
                completed=False,
                suggestions=["1 hour before", "30 minutes before", "1 day before", "No reminders needed"]
            )
        else:
            return InteractionResponse("❌ Failed to create task. Please try again.", True)
    
    def _parse_relative_date(self, date_str: str) -> str:
        """Convert relative date strings to proper dates"""
        from datetime import datetime, timedelta
        
        date_str_lower = date_str.lower().strip()
        today = datetime.now()
        
        if date_str_lower == 'today':
            return today.strftime('%Y-%m-%d')
        elif date_str_lower == 'tomorrow':
            tomorrow = today + timedelta(days=1)
            return tomorrow.strftime('%Y-%m-%d')
        elif date_str_lower == 'next week':
            next_week = today + timedelta(days=7)
            return next_week.strftime('%Y-%m-%d')
        elif date_str_lower == 'next month':
            # Simple next month calculation
            if today.month == 12:
                next_month = today.replace(year=today.year + 1, month=1)
            else:
                next_month = today.replace(month=today.month + 1)
            return next_month.strftime('%Y-%m-%d')
        else:
            # Return as-is if it's already a proper date or unknown format
            return date_str
    
    def _handle_list_tasks(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle task listing"""
        tasks = load_active_tasks(user_id)
        
        if not tasks:
            return InteractionResponse("You have no active tasks. Great job staying on top of things! 🎉", True)
        
        # Filter tasks if specified
        filter_type = entities.get('filter')
        if filter_type == 'due_soon':
            tasks = get_tasks_due_soon(user_id, days=7)
            if not tasks:
                return InteractionResponse("No tasks due in the next 7 days! 🎉", True)
        
        # Format task list
        task_list = []
        for i, task in enumerate(tasks[:10], 1):  # Limit to 10 tasks
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(task.get('priority', 'medium'), '🟡')
            due_info = f" (due: {task.get('due_date', 'No due date')})" if task.get('due_date') else ""
            task_list.append(f"{i}. {priority_emoji} {task['title']}{due_info}")
        
        response = "**Your Active Tasks:**\n" + "\n".join(task_list)
        
        if len(tasks) > 10:
            response += f"\n... and {len(tasks) - 10} more tasks"
        
        return InteractionResponse(response, True)
    
    def _handle_complete_task(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle task completion"""
        task_identifier = entities.get('task_identifier')
        if not task_identifier:
            return InteractionResponse(
                "Which task would you like to complete? Please specify the task number or name.",
                completed=False
            )
        
        # Try to find the task
        tasks = load_active_tasks(user_id)
        task = self._find_task_by_identifier(tasks, task_identifier)
        
        if not task:
            return InteractionResponse("❌ Task not found. Please check the task number or name.", True)
        
        # Complete the task
        if complete_task(user_id, task['task_id']):
            return InteractionResponse(f"✅ Completed: {task['title']}", True)
        else:
            return InteractionResponse("❌ Failed to complete task. Please try again.", True)
    
    def _handle_delete_task(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle task deletion"""
        task_identifier = entities.get('task_identifier')
        if not task_identifier:
            return InteractionResponse(
                "Which task would you like to delete? Please specify the task number or name.",
                completed=False
            )
        
        # Try to find the task
        tasks = load_active_tasks(user_id)
        task = self._find_task_by_identifier(tasks, task_identifier)
        
        if not task:
            return InteractionResponse("❌ Task not found. Please check the task number or name.", True)
        
        # Delete the task
        if delete_task(user_id, task['task_id']):
            return InteractionResponse(f"🗑️ Deleted: {task['title']}", True)
        else:
            return InteractionResponse("❌ Failed to delete task. Please try again.", True)
    
    def _handle_update_task(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle task updates"""
        task_identifier = entities.get('task_identifier')
        if not task_identifier:
            return InteractionResponse(
                "Which task would you like to update? Please specify the task number or name.",
                completed=False
            )
        
        # Try to find the task
        tasks = load_active_tasks(user_id)
        task = self._find_task_by_identifier(tasks, task_identifier)
        
        if not task:
            return InteractionResponse("❌ Task not found. Please check the task number or name.", True)
        
        # Prepare updates
        updates = {}
        if 'title' in entities:
            updates['title'] = entities['title']
        if 'description' in entities:
            updates['description'] = entities['description']
        if 'due_date' in entities:
            updates['due_date'] = entities['due_date']
        if 'priority' in entities:
            updates['priority'] = entities['priority']

        
        if not updates:
            return InteractionResponse(
                "What would you like to update? (title, description, due date, or priority)",
                completed=False
            )
        
        # Update the task
        if update_task(user_id, task['task_id'], updates):
            return InteractionResponse(f"✅ Updated: {task['title']}", True)
        else:
            return InteractionResponse("❌ Failed to update task. Please try again.", True)
    
    def _handle_task_stats(self, user_id: str) -> InteractionResponse:
        """Handle task statistics"""
        stats = get_user_task_stats(user_id)
        
        response = f"**Task Statistics:**\n"
        response += f"📋 Active tasks: {stats.get('active_count', 0)}\n"
        response += f"✅ Completed tasks: {stats.get('completed_count', 0)}\n"
        response += f"📅 Due soon (7 days): {stats.get('due_soon_count', 0)}\n"
        response += f"📊 Completion rate: {stats.get('completion_rate', 0):.1f}%"
        
        return InteractionResponse(response, True)
    
    def _find_task_by_identifier(self, tasks: List[Dict], identifier: str) -> Optional[Dict]:
        """Find a task by number or name"""
        # Try as number first
        try:
            task_num = int(identifier)
            if 1 <= task_num <= len(tasks):
                return tasks[task_num - 1]
        except ValueError:
            pass
        
        # Try as name
        identifier_lower = identifier.lower()
        for task in tasks:
            if identifier_lower in task['title'].lower():
                return task
        
        return None
    
    def get_help(self) -> str:
        return "Manage your tasks - create, list, complete, delete, and update tasks"
    
    def get_examples(self) -> List[str]:
        return [
            "create task 'Call mom tomorrow'",
            "list tasks",
            "complete task 1",
            "delete task 'Buy groceries'",
            "update task 2 priority high",
            "task stats"
        ]

class CheckinHandler(InteractionHandler):
    """Handler for check-in interactions"""
    
    def can_handle(self, intent: str) -> bool:
        return intent in ['start_checkin', 'continue_checkin', 'checkin_status']
    
    @handle_errors("handling check-in interaction", default_return=InteractionResponse("I'm having trouble with check-ins right now. Please try again.", True))
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        intent = parsed_command.intent
        entities = parsed_command.entities
        
        if intent == 'start_checkin':
            return self._handle_start_checkin(user_id)
        elif intent == 'continue_checkin':
            return self._handle_continue_checkin(user_id, entities)
        elif intent == 'checkin_status':
            return self._handle_checkin_status(user_id)
        else:
            return InteractionResponse(f"I don't understand that check-in command. Try: {', '.join(self.get_examples())}", True)
    
    def _handle_start_checkin(self, user_id: str) -> InteractionResponse:
        """Handle starting a check-in by delegating to conversation manager"""
        if not is_user_checkins_enabled(user_id):
            return InteractionResponse(
                "Check-ins are not enabled for your account. Please contact an administrator to enable daily check-ins.",
                True
            )
        
        # Check if they've already done a check-in today
        from datetime import datetime, date
        today = date.today()
        
        recent_checkins = get_recent_daily_checkins(user_id, limit=1)
        if recent_checkins:
            last_checkin = recent_checkins[0]
            last_checkin_timestamp = last_checkin.get('timestamp', '')
            
            # Parse the timestamp to check if it's from today
            try:
                if last_checkin_timestamp:
                    last_checkin_date = datetime.strptime(last_checkin_timestamp, "%Y-%m-%d %H:%M:%S").date()
                    if last_checkin_date == today:
                        return InteractionResponse(
                            f"You've already completed a check-in today at {last_checkin_timestamp}. "
                            "You can start a new check-in tomorrow!",
                            True
                        )
            except (ValueError, TypeError):
                # If timestamp parsing fails, continue with check-in
                pass
        
        # Delegate to conversation manager for proper check-in flow
        from bot.conversation_manager import conversation_manager
        
        try:
            message, completed = conversation_manager.start_daily_checkin(user_id)
            return InteractionResponse(message, completed)
        except Exception as e:
            logger.error(f"Error starting check-in for user {user_id}: {e}")
            return InteractionResponse(
                "I'm having trouble starting your check-in. Please try again or use /dailycheckin directly.",
                True
            )
    
    def _handle_continue_checkin(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle continuing a check-in"""
        # This would integrate with the existing conversation manager
        # For now, return a placeholder
        return InteractionResponse(
            "Check-in continuation not yet implemented. Please use the existing /dailycheckin command.",
            True
        )
    
    def _handle_checkin_status(self, user_id: str) -> InteractionResponse:
        """Handle check-in status request"""
        if not is_user_checkins_enabled(user_id):
            return InteractionResponse("Check-ins are not enabled for your account.", True)
        
        # Get recent check-ins
        recent_checkins = get_recent_daily_checkins(user_id, limit=7)
        
        if not recent_checkins:
            return InteractionResponse("No check-ins recorded in the last 7 days.", True)
        
        # Format status
        response = "**Recent Check-ins:**\n"
        for checkin in recent_checkins[:5]:  # Show last 5
            date = checkin.get('date', 'Unknown date')
            mood = checkin.get('mood', 'No mood recorded')
            response += f"📅 {date}: Mood {mood}/10\n"
        
        if len(recent_checkins) > 5:
            response += f"... and {len(recent_checkins) - 5} more"
        
        return InteractionResponse(response, True)
    
    def get_help(self) -> str:
        return "Manage your daily check-ins - start check-ins and view your status"
    
    def get_examples(self) -> List[str]:
        return [
            "start checkin",
            "checkin status",
            "daily checkin"
        ]

class ProfileHandler(InteractionHandler):
    """Handler for profile management interactions"""
    
    def can_handle(self, intent: str) -> bool:
        return intent in ['show_profile', 'update_profile', 'profile_stats']
    
    @handle_errors("handling profile interaction", default_return=InteractionResponse("I'm having trouble with profile management right now. Please try again.", True))
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        intent = parsed_command.intent
        entities = parsed_command.entities
        
        if intent == 'show_profile':
            return self._handle_show_profile(user_id)
        elif intent == 'update_profile':
            return self._handle_update_profile(user_id, entities)
        elif intent == 'profile_stats':
            return self._handle_profile_stats(user_id)
        else:
            return InteractionResponse(f"I don't understand that profile command. Try: {', '.join(self.get_examples())}", True)
    
    def _handle_show_profile(self, user_id: str) -> InteractionResponse:
        """Handle showing user profile"""
        # Load user data
        account_data = load_user_account_data(user_id)
        context_data = load_user_context_data(user_id)
        preferences_data = load_user_preferences_data(user_id)
        
        # Format profile information
        response = "**Your Profile:**\n"
        
        # Basic info
        if context_data:
            name = context_data.get('preferred_name', 'Not set')
            gender_identity = context_data.get('gender_identity', 'Not set')
            response += f"👤 Name: {name}\n"
            response += f"🎭 Gender Identity: {gender_identity}\n"
        
        # Account info
        if account_data:
            email = account_data.get('email', 'Not set')
            status = account_data.get('account_status', 'Unknown')
            response += f"📧 Email: {email}\n"
            response += f"📊 Status: {status}\n"
        
        # Preferences - check account features instead of preferences
        if account_data:
            features = account_data.get('features', {})
            checkins_enabled = features.get('checkins') == 'enabled'
            tasks_enabled = features.get('task_management') == 'enabled'
            response += f"✅ Check-ins: {'Enabled' if checkins_enabled else 'Disabled'}\n"
            response += f"📋 Tasks: {'Enabled' if tasks_enabled else 'Disabled'}\n"
        
        return InteractionResponse(response, True)
    
    def _handle_update_profile(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle profile updates"""
        if not entities:
            return InteractionResponse(
                "What would you like to update? (name, gender_identity, email)",
                completed=False
            )
        
        # Load current context data
        context_data = load_user_context_data(user_id) or {}
        
        # Apply updates
        updates = {}
        if 'name' in entities:
            context_data['preferred_name'] = entities['name']
            updates['name'] = entities['name']
        
        if 'gender_identity' in entities:
            context_data['gender_identity'] = entities['gender_identity']
            updates['gender_identity'] = entities['gender_identity']
        
        if 'email' in entities:
            # Email is stored in account data, not context
            account_data = load_user_account_data(user_id) or {}
            account_data['email'] = entities['email']
            # Note: Would need to implement save_user_account_data
            updates['email'] = entities['email']
        
        # Save updates
        if save_user_context_data(user_id, context_data):
            response = "✅ Profile updated: " + ", ".join(updates.keys())
            return InteractionResponse(response, True)
        else:
            return InteractionResponse("❌ Failed to update profile. Please try again.", True)
    
    def _handle_profile_stats(self, user_id: str) -> InteractionResponse:
        """Handle profile statistics"""
        # Get task stats
        task_stats = get_user_task_stats(user_id)
        
        # Get check-in stats
        recent_checkins = get_recent_daily_checkins(user_id, limit=30)
        
        response = "**Your Statistics:**\n"
        response += f"📋 Active tasks: {task_stats.get('active_count', 0)}\n"
        response += f"✅ Completed tasks: {task_stats.get('completed_count', 0)}\n"
        response += f"📊 Task completion rate: {task_stats.get('completion_rate', 0):.1f}%\n"
        response += f"📅 Check-ins this month: {len(recent_checkins)}"
        
        return InteractionResponse(response, True)
    
    def get_help(self) -> str:
        return "Manage your profile - view and update your information"
    
    def get_examples(self) -> List[str]:
        return [
            "show profile",
            "update name 'Julie'",
            "update gender_identity 'Non-binary'",
            "profile stats"
        ]

class HelpHandler(InteractionHandler):
    """Handler for help and command information"""
    
    def can_handle(self, intent: str) -> bool:
        return intent in ['help', 'commands', 'examples']
    
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        intent = parsed_command.intent
        entities = parsed_command.entities
        
        if intent == 'help':
            return self._handle_general_help(user_id, entities)
        elif intent == 'commands':
            return self._handle_commands_list(user_id)
        elif intent == 'examples':
            return self._handle_examples(user_id, entities)
        else:
            return InteractionResponse("I'm here to help! Try 'help' for general help or 'commands' for a list of commands.", True)
    
    def _handle_general_help(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle general help request"""
        topic = entities.get('topic', 'general')
        
        if topic == 'tasks':
            return InteractionResponse(
                "**Task Management Help:**\n"
                "• Create tasks: 'create task \"Call mom tomorrow\"'\n"
                "• List tasks: 'list tasks' or 'show my tasks'\n"
                "• Complete tasks: 'complete task 1' or 'complete \"Call mom\"'\n"
                "• Delete tasks: 'delete task 2' or 'delete \"Buy groceries\"'\n"
                "• Update tasks: 'update task 1 priority high'\n"
                "• Task stats: 'task stats' or 'show task statistics'",
                True
            )
        elif topic == 'checkin':
            return InteractionResponse(
                "**Check-in Help:**\n"
                "• Start check-in: 'start checkin' or 'daily checkin'\n"
                "• Check-in status: 'checkin status' or 'show checkins'\n"
                "• Cancel check-in: 'cancel' or '/cancel'",
                True
            )
        elif topic == 'profile':
            return InteractionResponse(
                "**Profile Management Help:**\n"
                "• Show profile: 'show profile' or 'my profile'\n"
                            "• Update name: 'update name \"Julie\"'\n"
            "• Update gender identity: 'update gender_identity \"Non-binary\"'\n"
            "• Profile stats: 'profile stats' or 'my statistics'",
                True
            )
        else:
            return InteractionResponse(
                "**Welcome to MHM!** 🌟\n\n"
                "I'm here to help you manage your mental health and daily tasks. "
                "You can interact with me using natural language commands.\n\n"
                "**Main Categories:**\n"
                "• **Tasks**: Create, manage, and track your tasks\n"
                "• **Check-ins**: Daily wellness check-ins\n"
                "• **Profile**: View and update your information\n\n"
                "Try these commands:\n"
                "• 'help tasks' - Task management help\n"
                "• 'help checkin' - Check-in help\n"
                "• 'help profile' - Profile management help\n"
                "• 'commands' - List all available commands\n\n"
                "Just start typing naturally - I'll understand what you want to do!",
                True
            )
    
    def _handle_commands_list(self, user_id: str) -> InteractionResponse:
        """Handle commands list request"""
        response = "**Available Commands:**\n\n"
        
        # Task commands
        response += "📋 **Task Management:**\n"
        response += "• create task, list tasks, complete task, delete task, update task, task stats\n\n"
        
        # Check-in commands
        response += "✅ **Check-ins:**\n"
        response += "• start checkin, checkin status\n\n"
        
        # Profile commands
        response += "👤 **Profile:**\n"
        response += "• show profile, update profile, profile stats\n\n"
        
        # Schedule commands
        response += "📅 **Schedule Management:**\n"
        response += "• show schedule, schedule status, enable/disable schedule, add schedule period\n\n"
        
        # Analytics commands
        response += "📊 **Analytics & Insights:**\n"
        response += "• show analytics, mood trends, habit analysis, sleep analysis, wellness score\n\n"
        
        # Help commands
        response += "❓ **Help:**\n"
        response += "• help, commands, examples\n\n"
        
        response += "You can also use natural language! Try 'I need to create a task' or 'Show me my profile'"
        
        return InteractionResponse(response, True)
    
    def _handle_examples(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle examples request"""
        category = entities.get('category', 'general')
        
        if category == 'tasks':
            return InteractionResponse(
                "**Task Examples:**\n"
                "• 'I need to call mom tomorrow'\n"
                "• 'Create a task to buy groceries'\n"
                "• 'Show me my tasks'\n"
                "• 'What tasks are due soon?'\n"
                "• 'Complete task 1'\n"
                "• 'Delete the grocery task'\n"
                "• 'Update task 2 to high priority'",
                True
            )
        elif category == 'checkin':
            return InteractionResponse(
                "**Check-in Examples:**\n"
                "• 'I want to check in'\n"
                "• 'Start my daily check-in'\n"
                "• 'Show me my check-in history'\n"
                "• 'How am I doing this week?'",
                True
            )
        elif category == 'schedule':
            return InteractionResponse(
                "**Schedule Examples:**\n"
                "• 'Show my schedule'\n"
                "• 'Show my task schedule'\n"
                "• 'Schedule status'\n"
                "• 'Enable my check-in schedule'\n"
                "• 'Add a new period called morning to my task schedule from 9am to 11am'",
                True
            )
        elif category == 'analytics':
            return InteractionResponse(
                "**Analytics Examples:**\n"
                "• 'Show my analytics'\n"
                "• 'Mood trends for 7 days'\n"
                "• 'Habit analysis'\n"
                "• 'Sleep analysis'\n"
                "• 'Wellness score'\n"
                "• 'How am I doing overall?'",
                True
            )
        else:
            return InteractionResponse(
                "**General Examples:**\n"
                "• 'Create a task to call mom tomorrow'\n"
                "• 'Show me my profile'\n"
                "• 'I want to check in'\n"
                "• 'What tasks do I have?'\n"
                "• 'Update my gender identity to Non-binary'\n"
                "• 'How am I doing with tasks?'\n"
                "• 'Show my schedule'\n"
                "• 'Mood trends'\n\n"
                "Try 'examples tasks', 'examples schedule', or 'examples analytics' for specific examples!",
                True
            )
    
    def get_help(self) -> str:
        return "Get help and see available commands"
    
    def get_examples(self) -> List[str]:
        return [
            "help",
            "help tasks",
            "commands",
            "examples",
            "examples tasks"
        ]

class ScheduleManagementHandler(InteractionHandler):
    """Handler for schedule management interactions"""
    
    def can_handle(self, intent: str) -> bool:
        return intent in ['show_schedule', 'update_schedule', 'schedule_status', 'add_schedule_period', 'edit_schedule_period']
    
    @handle_errors("handling schedule management interaction", default_return=InteractionResponse("I'm having trouble with schedule management right now. Please try again.", True))
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        intent = parsed_command.intent
        entities = parsed_command.entities
        
        if intent == 'show_schedule':
            return self._handle_show_schedule(user_id, entities)
        elif intent == 'update_schedule':
            return self._handle_update_schedule(user_id, entities)
        elif intent == 'schedule_status':
            return self._handle_schedule_status(user_id, entities)
        elif intent == 'add_schedule_period':
            return self._handle_add_schedule_period(user_id, entities)
        elif intent == 'edit_schedule_period':
            return self._handle_edit_schedule_period(user_id, entities)
        else:
            return InteractionResponse(f"I don't understand that schedule command. Try: {', '.join(self.get_examples())}", True)
    
    def _handle_show_schedule(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show schedule for a specific category or all categories"""
        category = entities.get('category', 'all')
        
        try:
            from core.schedule_management import get_schedule_time_periods
            from core.user_management import get_user_categories
            
            if category == 'all':
                # Show schedules for all categories
                categories = get_user_categories(user_id)
                response = "**Your Current Schedules:**\n\n"
                
                for cat in categories:
                    periods = get_schedule_time_periods(user_id, cat)
                    if periods:
                        response += f"📅 **{cat.title()}:**\n"
                        for period_name, period_data in periods.items():
                            start_time = period_data.get('start_time', 'Unknown')
                            end_time = period_data.get('end_time', 'Unknown')
                            active = "✅ Active" if period_data.get('active', True) else "❌ Inactive"
                            response += f"  • {period_name}: {start_time} - {end_time} ({active})\n"
                        response += "\n"
                    else:
                        response += f"📅 **{cat.title()}:** No periods configured\n\n"
                
                if not categories:
                    response += "No categories configured yet."
            else:
                # Show schedule for specific category
                periods = get_schedule_time_periods(user_id, category)
                if periods:
                    response = f"**Schedule for {category.title()}:**\n\n"
                    for period_name, period_data in periods.items():
                        start_time = period_data.get('start_time', 'Unknown')
                        end_time = period_data.get('end_time', 'Unknown')
                        active = "✅ Active" if period_data.get('active', True) else "❌ Inactive"
                        days = period_data.get('days', ['ALL'])
                        days_str = ', '.join(days) if days != ['ALL'] else 'All days'
                        response += f"**{period_name}:**\n"
                        response += f"  • Time: {start_time} - {end_time}\n"
                        response += f"  • Days: {days_str}\n"
                        response += f"  • Status: {active}\n\n"
                else:
                    response = f"No schedule periods configured for {category.title()}."
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing schedule for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your schedule right now. Please try again.", True)
    
    def _handle_update_schedule(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Update schedule settings"""
        category = entities.get('category')
        action = entities.get('action')
        
        if not category or not action:
            return InteractionResponse(
                "Please specify what you want to update. Try: 'Update my task schedule to send at 9am' or 'Enable my check-in schedule'",
                True
            )
        
        try:
            from core.schedule_management import get_schedule_time_periods, set_schedule_periods
            
            periods = get_schedule_time_periods(user_id, category)
            
            if action == 'enable':
                # Enable all periods
                for period_name in periods:
                    periods[period_name]['active'] = True
                set_schedule_periods(user_id, category, periods)
                return InteractionResponse(f"✅ All {category} schedule periods have been enabled.", True)
            
            elif action == 'disable':
                # Disable all periods
                for period_name in periods:
                    periods[period_name]['active'] = False
                set_schedule_periods(user_id, category, periods)
                return InteractionResponse(f"❌ All {category} schedule periods have been disabled.", True)
            
            else:
                return InteractionResponse(
                    f"I understand you want to update your {category} schedule, but I need more details. "
                    f"Try 'Enable my {category} schedule' or 'Disable my {category} schedule'",
                    True
                )
                
        except Exception as e:
            logger.error(f"Error updating schedule for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble updating your schedule right now. Please try again.", True)
    
    def _handle_schedule_status(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show status of schedules"""
        try:
            from core.schedule_management import get_schedule_time_periods
            from core.user_management import get_user_categories
            
            categories = get_user_categories(user_id)
            response = "**Schedule Status:**\n\n"
            
            for category in categories:
                periods = get_schedule_time_periods(user_id, category)
                active_periods = sum(1 for p in periods.values() if p.get('active', True))
                total_periods = len(periods)
                
                if total_periods == 0:
                    status = "❌ No periods configured"
                elif active_periods == 0:
                    status = "❌ All periods disabled"
                elif active_periods == total_periods:
                    status = "✅ All periods active"
                else:
                    status = f"⚠️ {active_periods}/{total_periods} periods active"
                
                response += f"📅 **{category.title()}:** {status}\n"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing schedule status for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble checking your schedule status right now. Please try again.", True)
    
    def _handle_add_schedule_period(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Add a new schedule period"""
        category = entities.get('category')
        period_name = entities.get('period_name')
        start_time = entities.get('start_time')
        end_time = entities.get('end_time')
        
        if not all([category, period_name, start_time, end_time]):
            return InteractionResponse(
                "Please provide all details for the new schedule period. "
                "Try: 'Add a new period called morning to my task schedule from 9am to 11am'",
                True
            )
        
        try:
            from core.schedule_management import add_schedule_period
            add_schedule_period(category, period_name, start_time, end_time)
            return InteractionResponse(
                f"✅ Added new schedule period '{period_name}' to {category.title()} from {start_time} to {end_time}.",
                True
            )
        except Exception as e:
            logger.error(f"Error adding schedule period for user {user_id}: {e}")
            return InteractionResponse(f"I'm having trouble adding the schedule period: {str(e)}", True)
    
    def _handle_edit_schedule_period(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Edit an existing schedule period"""
        category = entities.get('category')
        period_name = entities.get('period_name')
        new_start_time = entities.get('new_start_time')
        new_end_time = entities.get('new_end_time')
        
        if not all([category, period_name, new_start_time, new_end_time]):
            return InteractionResponse(
                "Please provide all details for editing the schedule period. "
                "Try: 'Edit the morning period in my task schedule to 8am to 10am'",
                True
            )
        
        try:
            from core.schedule_management import edit_schedule_period
            edit_schedule_period(category, period_name, new_start_time, new_end_time)
            return InteractionResponse(
                f"✅ Updated schedule period '{period_name}' in {category.title()} to {new_start_time} - {new_end_time}.",
                True
            )
        except Exception as e:
            logger.error(f"Error editing schedule period for user {user_id}: {e}")
            return InteractionResponse(f"I'm having trouble editing the schedule period: {str(e)}", True)
    
    def get_help(self) -> str:
        return "Manage your message, task, and check-in schedules"
    
    def get_examples(self) -> List[str]:
        return [
            "show schedule",
            "show my task schedule",
            "schedule status",
            "enable my check-in schedule",
            "add schedule period"
        ]

class AnalyticsHandler(InteractionHandler):
    """Handler for analytics and insights interactions"""
    
    def can_handle(self, intent: str) -> bool:
        return intent in ['show_analytics', 'mood_trends', 'habit_analysis', 'sleep_analysis', 'wellness_score']
    
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
                return InteractionResponse("You don't have enough check-in data for analytics yet. Try completing some daily check-ins first!", True)
            
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
                return InteractionResponse("You don't have enough mood data for analysis yet. Try completing some daily check-ins first!", True)
            
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
                return InteractionResponse("You don't have enough habit data for analysis yet. Try completing some daily check-ins first!", True)
            
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
                return InteractionResponse("You don't have enough sleep data for analysis yet. Try completing some daily check-ins with sleep information!", True)
            
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
                return InteractionResponse("You don't have enough data for a wellness score yet. Try completing some daily check-ins first!", True)
            
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
    
    def get_help(self) -> str:
        return "View analytics and insights about your wellness patterns"
    
    def get_examples(self) -> List[str]:
        return [
            "show analytics",
            "mood trends",
            "habit analysis",
            "sleep analysis",
            "wellness score"
        ]

# Registry of all interaction handlers
INTERACTION_HANDLERS = {
    'task': TaskManagementHandler(),
    'checkin': CheckinHandler(),
    'profile': ProfileHandler(),
    'help': HelpHandler(),
    'schedule': ScheduleManagementHandler(),
    'analytics': AnalyticsHandler(),
}

def get_interaction_handler(intent: str) -> Optional[InteractionHandler]:
    """Get the appropriate handler for an intent"""
    for handler in INTERACTION_HANDLERS.values():
        if handler.can_handle(intent):
            return handler
    return None

def get_all_handlers() -> Dict[str, InteractionHandler]:
    """Get all registered handlers"""
    return INTERACTION_HANDLERS.copy() 