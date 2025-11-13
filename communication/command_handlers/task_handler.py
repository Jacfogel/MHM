# communication/command_handlers/task_handler.py

"""
Task management command handler.

This module handles all task-related interactions including creating,
listing, completing, deleting, updating, and getting statistics for tasks.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from core.logger import get_component_logger
from core.error_handling import handle_errors
from tasks.task_management import (
    create_task, load_active_tasks, complete_task, delete_task, update_task,
    get_user_task_stats, get_tasks_due_soon
)

from .base_handler import InteractionHandler, InteractionResponse, ParsedCommand

logger = get_component_logger('communication_manager')
handlers_logger = logger

class TaskManagementHandler(InteractionHandler):
    """Handler for task management interactions"""
    
    @handle_errors("checking if can handle intent")
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
            return self._handle_task_stats(user_id, entities)
        else:
            return InteractionResponse(f"I don't understand that task command. Try: {', '.join(self.get_examples())}", True)
    
    @handle_errors("handling task creation")
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
        tags = entities.get('tags', [])
        recurrence_pattern = entities.get('recurrence_pattern')
        recurrence_interval = entities.get('recurrence_interval', 1)
        
        # Convert relative dates to proper dates
        if due_date:
            due_date = self._handle_create_task__parse_relative_date(due_date)
        
        # Validate priority
        valid_priorities = ['low', 'medium', 'high', 'urgent', 'critical']
        if priority not in valid_priorities:
            logger.warning(f"Invalid priority '{priority}' provided, defaulting to 'medium'")
            priority = 'medium'
        
        # Validate recurrence pattern
        valid_patterns = ['daily', 'weekly', 'monthly', 'yearly']
        if recurrence_pattern and recurrence_pattern not in valid_patterns:
            logger.warning(f"Invalid recurrence_pattern '{recurrence_pattern}' provided, ignoring")
            recurrence_pattern = None
        
        # Validate due_date format if provided
        if due_date:
            try:
                # Try to parse the date to validate format
                datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid due_date format '{due_date}', expected YYYY-MM-DD")
                # Try to parse relative date
                due_date = self._handle_create_task__parse_relative_date(due_date)
        
        # Create the task with enhanced properties
        task_data = {
            'title': title,
            'description': description,
            'due_date': due_date,
            'priority': priority,
            'tags': tags
        }
        
        # Add recurring task fields if specified
        if recurrence_pattern:
            task_data['recurrence_pattern'] = recurrence_pattern
            task_data['recurrence_interval'] = recurrence_interval
            task_data['repeat_after_completion'] = True
        
        task_id = create_task(user_id=user_id, **task_data)
        
        if task_id:
            response = f"✅ Task created: '{title}'"
            if due_date:
                response += f" (due: {due_date})"
            if priority != 'medium':
                response += f" (priority: {priority})"
            if tags:
                response += f" (tags: {', '.join(tags)})"
            if recurrence_pattern:
                interval_text = f"every {recurrence_interval} {recurrence_pattern}"
                if recurrence_interval == 1:
                    interval_text = f"every {recurrence_pattern[:-2]}"  # Remove 'ly' for singular
                response += f" (repeats: {interval_text})"
            
            # Ask about reminder periods and start follow-up flow
            from communication.message_processing.conversation_flow_manager import conversation_manager
            conversation_manager.start_task_reminder_followup(user_id, task_id)
            
            response += "\n\nWould you like to set reminder periods for this task?"
            
            return InteractionResponse(
                response, 
                completed=False,
                suggestions=["30 minutes to an hour before", "3 to 5 hours before", "1 to 2 days before", "No reminders needed"]
            )
        else:
            return InteractionResponse("❌ Failed to create task. Please try again.", True)
    
    @handle_errors("parsing relative date")
    def _handle_create_task__parse_relative_date(self, date_str: str) -> str:
        """Convert relative date strings to proper dates"""
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
    
    @handle_errors("handling task listing")
    def _handle_list_tasks(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle task listing with enhanced filtering and details"""
        tasks = load_active_tasks(user_id)
        
        if not tasks:
            return InteractionResponse("You have no active tasks. Great job staying on top of things! 🎉", True)
        
        # Apply filters
        filter_type = entities.get('filter')
        priority_filter = entities.get('priority')
        tag_filter = entities.get('tag')
        
        # Apply filters and get filtered tasks
        filtered_tasks = self._handle_list_tasks__apply_filters(user_id, tasks, filter_type, priority_filter, tag_filter)
        if not filtered_tasks:
            return self._handle_list_tasks__no_tasks_response(filter_type, priority_filter, tag_filter)
        
        # Sort tasks by priority and due date
        sorted_tasks = self._handle_list_tasks__sort_tasks(filtered_tasks)
        
        # Format task list with enhanced details
        task_list = self._handle_list_tasks__format_list(sorted_tasks)
        
        # Build response with filter info
        filter_info = self._handle_list_tasks__build_filter_info(filter_type, priority_filter, tag_filter)
        response = self._handle_list_tasks__build_response(task_list, filter_info, len(sorted_tasks))
        
        # Generate contextual suggestions
        suggestions = self._handle_list_tasks__generate_suggestions(sorted_tasks, filter_info)
        
        # Create rich data for Discord embeds
        rich_data = self._handle_list_tasks__create_rich_data(filter_info, sorted_tasks)
        
        return InteractionResponse(
            response, 
            True,
            rich_data=rich_data,
            suggestions=suggestions if suggestions else None
        )

    @handle_errors("applying task filters")
    def _handle_list_tasks__apply_filters(self, user_id, tasks, filter_type, priority_filter, tag_filter):
        """Apply filters to tasks and return filtered list."""
        filtered_tasks = tasks.copy()
        
        # Apply filter type
        if filter_type == 'due_soon':
            filtered_tasks = get_tasks_due_soon(user_id, days=7)
        elif filter_type == 'overdue':
            today = datetime.now().strftime('%Y-%m-%d')
            filtered_tasks = [task for task in filtered_tasks if task.get('due_date') and task['due_date'] < today]
        elif filter_type == 'high_priority':
            filtered_tasks = [task for task in filtered_tasks if task.get('priority') == 'high']
        
        # Apply priority filter
        if priority_filter and priority_filter in ['low', 'medium', 'high']:
            filtered_tasks = [task for task in filtered_tasks if task.get('priority') == priority_filter]
        
        # Apply tag filter
        if tag_filter:
            filtered_tasks = [task for task in filtered_tasks if tag_filter in task.get('tags', [])]
        
        return filtered_tasks

    @handle_errors("handling no tasks response")
    def _handle_list_tasks__no_tasks_response(self, filter_type, priority_filter, tag_filter):
        """Get appropriate response when no tasks match filters."""
        if filter_type == 'due_soon':
            return InteractionResponse("No tasks due in the next 7 days! 🎉", True)
        elif filter_type == 'overdue':
            return InteractionResponse("No overdue tasks! 🎉", True)
        elif filter_type == 'high_priority':
            return InteractionResponse("No high priority tasks! 🎉", True)
        elif priority_filter:
            return InteractionResponse(f"No {priority_filter} priority tasks! 🎉", True)
        elif tag_filter:
            return InteractionResponse(f"No tasks with tag '{tag_filter}'! 🎉", True)
        else:
            return InteractionResponse("You have no active tasks. Great job staying on top of things! 🎉", True)

    @handle_errors("sorting tasks")
    def _handle_list_tasks__sort_tasks(self, tasks):
        """Sort tasks by priority and due date."""
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        return sorted(tasks, key=lambda x: (
            priority_order.get(x.get('priority', 'medium'), 1),
            x.get('due_date') or '9999-12-31'  # Handle None due_date properly
        ))

    @handle_errors("formatting task list")
    def _handle_list_tasks__format_list(self, tasks):
        """Format task list with enhanced details."""
        task_list = []
        for i, task in enumerate(tasks[:10], 1):  # Limit to 10 tasks
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(task.get('priority', 'medium'), '🟡')
            
            # Format due date with urgency indicator
            due_info = self._handle_list_tasks__format_due_date(task.get('due_date'))
            
            # Add recurring task indicator
            recurrence_info = ""
            if task.get('recurrence_pattern'):
                pattern = task.get('recurrence_pattern')
                interval = task.get('recurrence_interval', 1)
                if interval == 1:
                    recurrence_info = f" 🔄 {pattern[:-2]}"  # Remove 'ly' for singular
                else:
                    recurrence_info = f" 🔄 every {interval} {pattern}"
            
            # Add tags if present
            tags = task.get('tags', [])
            tags_info = f" [tags: {', '.join(tags)}]" if tags else ""
            
            # Add description preview if present
            description = task.get('description', '')
            desc_info = f" - {description[:50]}..." if description and len(description) > 50 else f" - {description}" if description else ""
            
            task_list.append(f"{i}. {priority_emoji} {task['title']}{due_info}{recurrence_info}{tags_info}{desc_info}")
        
        return task_list

    @handle_errors("formatting due date")
    def _handle_list_tasks__format_due_date(self, due_date):
        """Format due date with urgency indicator."""
        if not due_date:
            return ""
        
        today = datetime.now().strftime('%Y-%m-%d')
        if due_date < today:
            return f" (OVERDUE: {due_date})"
        elif due_date == today:
            return f" (due TODAY: {due_date})"
        else:
            return f" (due: {due_date})"

    @handle_errors("building filter info")
    def _handle_list_tasks__build_filter_info(self, filter_type, priority_filter, tag_filter):
        """Build filter information list."""
        filter_info = []
        if filter_type:
            filter_info.append(f"filter: {filter_type}")
        if priority_filter:
            filter_info.append(f"priority: {priority_filter}")
        if tag_filter:
            filter_info.append(f"tag: {tag_filter}")
        return filter_info

    @handle_errors("building response")
    def _handle_list_tasks__build_response(self, task_list, filter_info, total_tasks):
        """Build the main task list response."""
        response = "**Your Active Tasks"
        if filter_info:
            response += f" ({', '.join(filter_info)})"
        response += ":**\n" + "\n".join(task_list)
        
        if total_tasks > 10:
            response += f"\n... and {total_tasks - 10} more tasks"
        
        return response

    @handle_errors("generating suggestions")
    def _handle_list_tasks__generate_suggestions(self, tasks, filter_info):
        """Generate contextual suggestions based on current state."""
        suggestions = []
        
        # Only add suggestions if we have tasks and no filters are applied
        if not filter_info and len(tasks) > 0:
            # Add one contextual "show" suggestion if available
            contextual_suggestion = self._handle_list_tasks__get_suggestion(tasks)
            if contextual_suggestion:
                suggestions.append(contextual_suggestion)
            
            # Add action-oriented suggestions (only relevant to listing context)
            suggestions.append("Add a reminder to a task")
            suggestions.append("Edit a task")
        
        # If we don't have enough suggestions, add general ones
        while len(suggestions) < 3:
            if "Create a new task" not in suggestions:
                suggestions.append("Create a new task")
            elif "Show all tasks" not in suggestions:
                suggestions.append("Show all tasks")
            else:
                break
        
        # Limit to exactly 3 suggestions
        return suggestions[:3]

    @handle_errors("getting suggestion")
    def _handle_list_tasks__get_suggestion(self, tasks):
        """Get contextual show suggestion based on task analysis."""
        # Check for overdue tasks first
        overdue_count = sum(1 for task in tasks if task.get('due_date') and task['due_date'] < datetime.now().strftime('%Y-%m-%d'))
        if overdue_count > 0:
            return f"Show {overdue_count} overdue tasks"
        
        # Check for high priority tasks
        high_priority_count = sum(1 for task in tasks if task.get('priority') == 'high')
        if high_priority_count > 0:
            return f"Show {high_priority_count} high priority tasks"
        
        # Check for tasks due soon
        due_soon_count = sum(1 for task in tasks if task.get('due_date') and task['due_date'] <= (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'))
        if due_soon_count > 0:
            return f"Show {due_soon_count} tasks due soon"
        
        return None

    @handle_errors("creating rich data")
    def _handle_list_tasks__create_rich_data(self, filter_info, tasks):
        """Create rich data for Discord embeds."""
        rich_data = {
            'type': 'task',
            'title': 'Your Active Tasks',
            'fields': []
        }
        
        # Add filter info as a field if filters are applied
        if filter_info:
            rich_data['fields'].append({
                'name': 'Filters Applied',
                'value': ', '.join(filter_info),
                'inline': True
            })
        
        # Add task count as a field
        rich_data['fields'].append({
            'name': 'Task Count',
            'value': f"{len(tasks)} tasks",
            'inline': True
        })
        
        # Add priority breakdown as a field
        priority_counts = {}
        for task in tasks:
            priority = task.get('priority', 'medium')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        if priority_counts:
            priority_str = ', '.join([f"{count} {priority}" for priority, count in priority_counts.items()])
            rich_data['fields'].append({
                'name': 'Priority Breakdown',
                'value': priority_str,
                'inline': True
            })
        
        return rich_data
    
    @handle_errors("handling task completion")
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
        task = self._handle_complete_task__find_task_by_identifier(tasks, task_identifier)
        
        if not task:
            return InteractionResponse("❌ Task not found. Please check the task number or name.", True)
        
        # Complete the task
        if complete_task(user_id, task.get('task_id', task.get('id'))):
            return InteractionResponse(f"✅ Completed: {task['title']}", True)
        else:
            return InteractionResponse("❌ Failed to complete task. Please try again.", True)
    
    @handle_errors("handling task deletion")
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
        task = self._handle_delete_task__find_task_by_identifier(tasks, task_identifier)
        
        if not task:
            return InteractionResponse("❌ Task not found. Please check the task number or name.", True)
        
        # Delete the task
        if delete_task(user_id, task.get('task_id', task.get('id'))):
            return InteractionResponse(f"🗑️ Deleted: {task['title']}", True)
        else:
            return InteractionResponse("❌ Failed to delete task. Please try again.", True)
    
    @handle_errors("handling task update")
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
        task = self._handle_update_task__find_task_by_identifier(tasks, task_identifier)
        
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
            # Provide targeted, actionable prompts without generic suggestions
            prompt = (
                "What would you like to update for '"
                f"{task.get('title', 'this task')}" "'? You can say, for example:\n"
                "• 'update task " f"{task_identifier}" " due date tomorrow'\n"
                "• 'update task " f"{task_identifier}" " priority high'\n"
                "• 'update task " f"{task_identifier}" " title Brush your teeth tonight'"
            )
            return InteractionResponse(
                prompt,
                completed=False,
                suggestions=[]
            )
        
        # Update the task
        if update_task(user_id, task.get('task_id', task.get('id')), updates):
            return InteractionResponse(f"✅ Updated: {task['title']}", True)
        else:
            return InteractionResponse("❌ Failed to update task. Please try again.", True)
    
    @handle_errors("handling task statistics")
    def _handle_task_stats(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle task statistics with dynamic time periods"""
        # Get time period information
        days = entities.get('days', 7)
        period_name = entities.get('period_name', 'this week')
        offset = entities.get('offset', 0)
        
        try:
            from core.checkin_analytics import CheckinAnalytics
            analytics = CheckinAnalytics()
            
            # Get task statistics for the specified period
            task_stats = analytics.get_task_weekly_stats(user_id, days)
            if 'error' in task_stats:
                return InteractionResponse(f"You don't have enough check-in data for {period_name} statistics yet. Try completing some check-ins first!", True)
            
            # Get overall task stats
            overall_stats = get_user_task_stats(user_id)
            
            response = f"**📊 Task Statistics for {period_name.title()}:**\n\n"
            
            # Show habit-based task completion
            if task_stats:
                response += "**Daily Habits:**\n"
                for task_name, stats in task_stats.items():
                    completion_rate = stats.get('completion_rate', 0)
                    completed_days = stats.get('completed_days', 0)
                    total_days = stats.get('total_days', 0)
                    
                    # Add emoji based on completion rate
                    if completion_rate >= 80:
                        emoji = "🟢"
                    elif completion_rate >= 60:
                        emoji = "🟡"
                    else:
                        emoji = "🔴"
                    
                    response += f"{emoji} **{task_name}:** {completion_rate}% ({completed_days}/{total_days} days)\n"
                
                response += "\n"
            
            # Show overall task statistics
            active_tasks = overall_stats.get('active_tasks', 0)
            completed_tasks = overall_stats.get('completed_tasks', 0)
            total_tasks = active_tasks + completed_tasks
            
            if total_tasks > 0:
                overall_completion_rate = (completed_tasks / total_tasks) * 100
                response += f"**Overall Task Progress:**\n"
                response += f"📋 **Active Tasks:** {active_tasks}\n"
                response += f"✅ **Completed Tasks:** {completed_tasks}\n"
                response += f"📊 **Completion Rate:** {overall_completion_rate:.1f}%\n"
            else:
                response += "**No tasks found.** Create some tasks to get started!\n"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing task statistics for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your task statistics right now. Please try again.", True)
    
    @handle_errors("finding task by identifier")
    def _find_task_by_identifier(self, tasks: List[Dict], identifier: str) -> Optional[Dict]:
        """
        Find a task by number, name, or task_id.
        
        Shared method to eliminate code duplication. Used by complete, delete, and update handlers.
        
        Args:
            tasks: List of task dictionaries to search
            identifier: Task identifier (number, name, or task_id)
            
        Returns:
            Task dictionary if found, None otherwise
        """
        if not identifier or not tasks:
            return None
        
        # Try as task_id first (UUID)
        for task in tasks:
            if task.get('task_id') == identifier or task.get('id') == identifier:
                return task
        
        # Try as number
        try:
            task_num = int(identifier)
            if 1 <= task_num <= len(tasks):
                return tasks[task_num - 1]
        except ValueError:
            pass
        
        # Try as name with improved matching
        identifier_lower = identifier.lower().strip()
        
        # First try exact match
        for task in tasks:
            if identifier_lower == task['title'].lower():
                return task
        
        # Then try contains match
        for task in tasks:
            if identifier_lower in task['title'].lower():
                return task
        
        # Then try word-based matching for common task patterns
        identifier_words = set(identifier_lower.split())
        for task in tasks:
            task_words = set(task['title'].lower().split())
            # Check if any identifier words match task words
            if identifier_words & task_words:  # Set intersection
                return task
        
        # Finally try fuzzy matching for common variations
        common_variations = {
            'teeth': ['brush', 'brushing', 'tooth', 'dental'],
            'hair': ['wash', 'washing', 'shampoo'],
            'dishes': ['wash', 'washing', 'clean', 'cleaning'],
            'laundry': ['wash', 'washing', 'clothes'],
            'exercise': ['workout', 'gym', 'run', 'running', 'walk', 'walking'],
            'medication': ['meds', 'medicine', 'pill', 'pills'],
            'appointment': ['doctor', 'dentist', 'meeting', 'call'],
        }
        
        for task in tasks:
            task_lower = task['title'].lower()
            for variation_key, variations in common_variations.items():
                if identifier_lower in variations or identifier_lower == variation_key:
                    if any(var in task_lower for var in variations + [variation_key]):
                        return task
        
        return None
    
    @handle_errors("finding task by identifier for completion")
    def _handle_complete_task__find_task_by_identifier(self, tasks: List[Dict], identifier: str) -> Optional[Dict]:
        """Find a task by number, name, or task_id - delegates to shared method."""
        return self._find_task_by_identifier(tasks, identifier)
    
    @handle_errors("finding task by identifier for deletion")
    def _handle_delete_task__find_task_by_identifier(self, tasks: List[Dict], identifier: str) -> Optional[Dict]:
        """Find a task by number, name, or task_id - delegates to shared method."""
        return self._find_task_by_identifier(tasks, identifier)
    
    @handle_errors("finding task by identifier for update")
    def _handle_update_task__find_task_by_identifier(self, tasks: List[Dict], identifier: str) -> Optional[Dict]:
        """Find a task by number, name, or task_id - delegates to shared method."""
        return self._find_task_by_identifier(tasks, identifier)
    
    @handle_errors("getting help")
    def get_help(self) -> str:
        return "Help with task management - create, list, complete, delete, and update tasks"
    
    @handle_errors("getting examples")
    def get_examples(self) -> List[str]:
        return [
            "create task 'Call mom tomorrow'",
            "list tasks",
            "complete task 1",
            "delete task 'Buy groceries'",
            "update task 2 priority high",
            "task stats"
        ]
