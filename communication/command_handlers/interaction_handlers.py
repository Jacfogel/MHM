# communication/command_handlers/interaction_handlers.py

"""
Interaction handlers for channel-neutral user interactions.

This module provides a framework for handling different types of user interactions
(like task management, check-ins, profile management) in a way that works across
all communication channels (Discord, email, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

# Pending confirmations (simple in-memory store)
PENDING_DELETIONS: Dict[str, str] = {}
from datetime import datetime

from core.logger import get_component_logger
from core.error_handling import handle_errors
from tasks.task_management import (
    create_task, load_active_tasks, complete_task, delete_task, update_task,
    get_user_task_stats, get_tasks_due_soon
)
from core.user_data_handlers import get_user_data, save_user_data
from core.response_tracking import (
    is_user_checkins_enabled, get_recent_checkins
)

from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand

logger = get_component_logger('communication_manager')
handlers_logger = logger

class InteractionHandler(ABC):
    """Abstract base class for interaction handlers"""
    
    @abstractmethod
    @handle_errors("checking if can handle intent", default_return=False)
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent"""
        pass
    
    @abstractmethod
    @handle_errors("handling task management interaction", default_return=InteractionResponse("Error handling task management", "error"))
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        """Handle the interaction and return a response"""
        pass
    
    @abstractmethod
    @handle_errors("getting help text", default_return="Help information not available")
    def get_help(self) -> str:
        """Get help text for this handler"""
        pass
    
    @abstractmethod
    @handle_errors("getting examples", default_return=[])
    def get_examples(self) -> List[str]:
        """Get example commands for this handler"""
        pass

class TaskManagementHandler(InteractionHandler):
    """Handler for task management interactions"""
    
    @handle_errors("checking if can handle task intent", default_return=False)
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
    
    @handle_errors("creating task", default_return=InteractionResponse("I'm having trouble creating your task. Please try again.", True))
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
        
        # If no recurrence pattern specified, check user's default settings
        if not recurrence_pattern:
            try:
                from core.user_data_handlers import get_user_data
                user_data = get_user_data(user_id, 'preferences')
                preferences = user_data.get('preferences', {})
                task_settings = preferences.get('task_settings', {})
                recurring_settings = task_settings.get('recurring_settings', {})
                
                # Use default pattern if available
                default_pattern = recurring_settings.get('default_recurrence_pattern')
                if default_pattern:
                    recurrence_pattern = default_pattern
                    recurrence_interval = recurring_settings.get('default_recurrence_interval', 1)
            except Exception as e:
                # If there's an error loading preferences, continue without defaults
                pass
        
        # Convert relative dates to proper dates
        if due_date:
            due_date = self._handle_create_task__parse_relative_date(due_date)
        
        # Validate priority
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if priority not in valid_priorities:
            priority = 'medium'
        
        # Validate recurrence pattern
        valid_patterns = ['daily', 'weekly', 'monthly', 'yearly']
        if recurrence_pattern and recurrence_pattern not in valid_patterns:
            recurrence_pattern = None
        
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
            
            # Use default repeat_after_completion setting if available
            try:
                from core.user_data_handlers import get_user_data
                user_data = get_user_data(user_id, 'preferences')
                preferences = user_data.get('preferences', {})
                task_settings = preferences.get('task_settings', {})
                recurring_settings = task_settings.get('recurring_settings', {})
                task_data['repeat_after_completion'] = recurring_settings.get('default_repeat_after_completion', True)
            except Exception as e:
                # Default to True if there's an error loading preferences
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
            
            # Ask about reminder periods
            response += "\n\nWould you like to set reminder periods for this task?"
            
            return InteractionResponse(
                response, 
                completed=False,
                suggestions=["30 minutes to an hour before", "3 to 5 hours before", "1 to 2 days before", "No reminders needed"]
            )
        else:
            return InteractionResponse("❌ Failed to create task. Please try again.", True)
    
    @handle_errors("parsing relative date", default_return="")
    def _handle_create_task__parse_relative_date(self, date_str: str) -> str:
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
    
    @handle_errors("listing tasks", default_return=InteractionResponse("I'm having trouble listing your tasks. Please try again.", True))
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
            from datetime import datetime
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

    @handle_errors("generating no tasks response")
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
            
            # Add short task ID for easy completion
            task_id = task.get('task_id', '')
            short_id = f" [{task_id[:8]}]" if task_id else ""
            
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
            
            task_list.append(f"{i}. {priority_emoji} {task['title']}{short_id}{due_info}{recurrence_info}{tags_info}{desc_info}")
        
        return task_list

    @handle_errors("formatting due date")
    def _handle_list_tasks__format_due_date(self, due_date):
        """Format due date with urgency indicator."""
        if not due_date:
            return ""
        
        from datetime import datetime
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

    @handle_errors("building task response")
    def _handle_list_tasks__build_response(self, task_list, filter_info, total_tasks):
        """Build the main task list response."""
        response = "**Your Active Tasks"
        if filter_info:
            response += f" ({', '.join(filter_info)})"
        response += ":**\n" + "\n".join(task_list)
        
        if total_tasks > 10:
            response += f"\n... and {total_tasks - 10} more tasks"
        
        return response

    @handle_errors("generating task suggestions")
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

    @handle_errors("getting task suggestion")
    def _handle_list_tasks__get_suggestion(self, tasks):
        """Get contextual show suggestion based on task analysis."""
        from datetime import datetime, timedelta
        
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

    @handle_errors("creating rich data for tasks")
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
    
    @handle_errors("completing task", default_return=InteractionResponse("I'm having trouble completing your task. Please try again.", True))
    def _handle_complete_task(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle task completion"""
        task_identifier = entities.get('task_identifier')
        if not task_identifier:
            # No specific task mentioned - check for last task reminder first
            # Temporarily disabled due to import issues
            # from communication.core.channel_orchestrator import CommunicationManager
            # comm_manager = CommunicationManager()
            # last_reminder_task_id = comm_manager.get_last_task_reminder(user_id)
            
            # if last_reminder_task_id:
            #     # Try to complete the task from the last reminder
            #     from tasks.task_management import get_task_by_id, complete_task
            #     last_reminder_task = get_task_by_id(user_id, last_reminder_task_id)
                
            #     if last_reminder_task and not last_reminder_task.get('completed', False):
            #         # Complete the task from the last reminder
            #         if complete_task(user_id, last_reminder_task_id):
            #             task_title = last_reminder_task.get('title', 'Unknown Task')
            #             return InteractionResponse(f"✅ Completed: {task_title}", True)
            #         else:
            #             return InteractionResponse("❌ Failed to complete task. Please try again.", True)
            
            # If no last reminder or task already completed, suggest the most likely task
            tasks = load_active_tasks(user_id)
            if not tasks:
                return InteractionResponse(
                    "Which task would you like to complete? You currently have no active tasks. "
                    "You can create a task or list your tasks to choose one.",
                    completed=False,
                    suggestions=["list tasks", "cancel"]
                )
            
            # Find the most urgent task (overdue, then high priority, then due soon)
            suggested_task = self._handle_complete_task__find_most_urgent_task(tasks)
            
            if suggested_task:
                # Suggest the most urgent task
                task_title = suggested_task.get('title', 'Unknown Task')
                task_id = suggested_task.get('task_id', '')
                short_id = task_id[:8] if task_id else ''
                
                response = f"💡 **Did you want to complete this task?**\n\n"
                response += f"**{task_title}**\n"
                
                # Add task details
                if suggested_task.get('due_date'):
                    response += f"📅 Due: {suggested_task['due_date']}\n"
                if suggested_task.get('priority'):
                    response += f"⚡ Priority: {suggested_task['priority'].title()}\n"
                
                response += f"\n**To complete it:**\n"
                response += f"• Reply: `complete task {short_id}`\n"
                response += f"• Or: `complete task \"{task_title}\"`\n"
                response += f"• Or: `list tasks` to see all your tasks"
                
                return InteractionResponse(response, completed=False)
            else:
                return InteractionResponse(
                    "Which task would you like to complete? Please specify the task number or name, or use 'list tasks' to see all your tasks.",
                    completed=False
                )
        
        # Try to find task with disambiguation
        tasks = load_active_tasks(user_id)
        candidates = self._get_task_candidates(tasks, task_identifier)
        if len(candidates) > 1:
            preview = "\n".join([f"{i+1}. {t['title']}" for i, t in enumerate(candidates[:5])])
            suffix = "\nIf you meant one of these, reply with 'complete task <number>'."
            return InteractionResponse(f"I found multiple matching tasks:\n{preview}{suffix}", completed=False)
        task = candidates[0] if candidates else None
        
        if not task:
            return InteractionResponse("❌ Task not found. Please check the task number or name.", True)
        
        # Complete the task
        if complete_task(user_id, task.get('task_id', task.get('id'))):
            return InteractionResponse(f"✅ Completed: {task['title']}", True)
        else:
            return InteractionResponse("❌ Failed to complete task. Please try again.", True)
    
    @handle_errors("deleting task", default_return=InteractionResponse("I'm having trouble deleting your task. Please try again.", True))
    def _handle_delete_task(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle task deletion"""
        task_identifier = entities.get('task_identifier')
        if not task_identifier:
            # If user confirms without identifier, use pending deletion if available
            pending_id = PENDING_DELETIONS.pop(user_id, None)
            if pending_id:
                if delete_task(user_id, pending_id):
                    return InteractionResponse("🗑️ Deleted.", True)
                return InteractionResponse("❌ Failed to delete task. Please try again.", True)
            else:
                return InteractionResponse(
                    "Which task would you like to delete? Please specify the task number or name.",
                    completed=False
                )
        
        # Try to find task with disambiguation
        tasks = load_active_tasks(user_id)
        candidates = self._get_task_candidates(tasks, task_identifier)
        if len(candidates) > 1:
            preview = "\n".join([f"{i+1}. {t['title']}" for i, t in enumerate(candidates[:5])])
            suffix = "\nIf you meant one of these, reply with 'delete task <number>'."
            return InteractionResponse(f"I found multiple matching tasks:\n{preview}{suffix}", completed=False)
        task = candidates[0] if candidates else None
        
        if not task:
            return InteractionResponse("❌ Task not found. Please check the task number or name.", True)
        
        # For name-based selection, require a simple confirmation step
        identifier_str = str(task_identifier).strip().lower()
        is_numeric = identifier_str.isdigit()
        is_exact_id = identifier_str in [str(task.get('task_id','')).lower(), str(task.get('id','')).lower()]
        if not is_numeric and not is_exact_id:
            PENDING_DELETIONS[user_id] = task.get('task_id', task.get('id'))
            title = task.get('title', 'this task')
            return InteractionResponse(
                f"Confirm delete: {title}. Reply 'confirm delete' to proceed.",
                completed=False
            )

        # Delete immediately for numeric or id-based selection
        if delete_task(user_id, task.get('task_id', task.get('id'))):
            return InteractionResponse(f"🗑️ Deleted: {task['title']}", True)
        else:
            return InteractionResponse("❌ Failed to delete task. Please try again.", True)

    def _get_task_candidates(self, tasks: List[Dict], identifier: str) -> List[Dict]:
        """Return candidate tasks matching identifier by id, number, or name."""
        matches: List[Dict] = []
        # Exact id
        for t in tasks:
            if identifier == t.get('task_id') or identifier == t.get('id'):
                return [t]
        # Short id
        if isinstance(identifier, str) and len(identifier) == 8:
            for t in tasks:
                tid = t.get('task_id', '')
                if tid.startswith(identifier):
                    matches.append(t)
            if matches:
                return matches
        # Number
        try:
            n = int(identifier)
            if 1 <= n <= len(tasks):
                return [tasks[n-1]]
        except Exception:
            pass
        # Name-based
        ident = str(identifier).lower().strip()
        exact = [t for t in tasks if t.get('title','').lower() == ident]
        if exact:
            return exact
        contains = [t for t in tasks if ident in t.get('title','').lower()]
        if contains:
            return contains
        words = set(ident.split())
        word_hits = [t for t in tasks if words & set(t.get('title','').lower().split())]
        if word_hits:
            return word_hits
        return []
    
    @handle_errors("updating task", default_return=InteractionResponse("I'm having trouble updating your task. Please try again.", True))
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
        candidates = self._get_task_candidates(tasks, task_identifier)
        if len(candidates) > 1:
            preview = "\n".join([f"{i+1}. {t['title']}" for i, t in enumerate(candidates[:5])])
            suffix = "\nIf you meant one of these, reply with 'update task <number> due date <date>' (or other field)."
            return InteractionResponse(f"I found multiple matching tasks:\n{preview}{suffix}", completed=False)
        task = candidates[0] if candidates else None
        
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
    
    @handle_errors("getting task statistics", default_return=InteractionResponse("I'm having trouble getting your task statistics. Please try again.", True))
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
    
    def _handle_complete_task__find_task_by_identifier(self, tasks: List[Dict], identifier: str) -> Optional[Dict]:
        """Find a task by number, name, or task_id"""
        # Try as task_id first (UUID)
        for task in tasks:
            if task.get('task_id') == identifier or task.get('id') == identifier:
                return task
        
        # Try as short task_id (first 8 characters)
        if len(identifier) == 8:
            for task in tasks:
                task_id = task.get('task_id', '')
                if task_id and task_id.startswith(identifier):
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
    
    def _handle_complete_task__find_most_urgent_task(self, tasks: List[Dict]) -> Optional[Dict]:
        """Find the most urgent task based on priority and due date"""
        if not tasks:
            return None
        
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Priority order: overdue > critical > high > medium > low
        priority_order = {'critical': 5, 'high': 4, 'medium': 3, 'low': 2}
        
        most_urgent = None
        highest_score = -1
        
        for task in tasks:
            score = 0
            
            # Check if overdue (highest priority)
            due_date = task.get('due_date')
            if due_date and due_date < today:
                score += 1000  # Overdue tasks get highest priority
            
            # Add priority score
            priority = task.get('priority', 'medium')
            score += priority_order.get(priority, 0)
            
            # Add due date proximity bonus (closer = higher score)
            if due_date:
                try:
                    due_dt = datetime.strptime(due_date, '%Y-%m-%d')
                    today_dt = datetime.strptime(today, '%Y-%m-%d')
                    days_until_due = (due_dt - today_dt).days
                    if days_until_due <= 0:  # Due today or overdue
                        score += 50
                    elif days_until_due <= 1:  # Due tomorrow
                        score += 30
                    elif days_until_due <= 3:  # Due this week
                        score += 10
                except ValueError:
                    pass  # Invalid date format, ignore
            
            if score > highest_score:
                highest_score = score
                most_urgent = task
        
        return most_urgent
    
    def _handle_delete_task__find_task_by_identifier(self, tasks: List[Dict], identifier: str) -> Optional[Dict]:
        """Find a task by number, name, or task_id"""
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
    
    def _handle_update_task__find_task_by_identifier(self, tasks: List[Dict], identifier: str) -> Optional[Dict]:
        """Find a task by number, name, or task_id"""
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
    
    @handle_errors("getting task help", default_return="Help with task management - create, list, complete, delete, and update tasks")
    def get_help(self) -> str:
        return "Help with task management - create, list, complete, delete, and update tasks"
    
    @handle_errors("getting task examples", default_return=[])
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
    
    @handle_errors("checking if can handle checkin intent", default_return=False)
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
    
    @handle_errors("starting check-in", default_return=InteractionResponse("I'm having trouble starting your check-in. Please try again.", True))
    def _handle_start_checkin(self, user_id: str) -> InteractionResponse:
        """Handle starting a check-in by delegating to conversation manager"""
        if not is_user_checkins_enabled(user_id):
            return InteractionResponse(
                "Check-ins are not enabled for your account. Please contact an administrator to enable check-ins.",
                True
            )
        
        # Check if they've already done a check-in today
        from datetime import datetime, date
        today = date.today()
        
        recent_checkins = get_recent_checkins(user_id, limit=1)
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
        
        # Delegate to conversation manager for proper check-in flow (modern API)
        from communication.message_processing.conversation_flow_manager import conversation_manager
        
        try:
            message, completed = conversation_manager.start_checkin(user_id)
            return InteractionResponse(message, completed)
        except Exception as e:
            logger.error(f"Error starting check-in for user {user_id}: {e}")
            return InteractionResponse(
                "I'm having trouble starting your check-in. Please try again or use /checkin directly.",
                True
            )
    
    @handle_errors("continuing check-in", default_return=InteractionResponse("I'm having trouble continuing your check-in. Please try again.", True))
    def _handle_continue_checkin(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle continuing a check-in"""
        # This would integrate with the existing conversation manager
        # For now, return a placeholder
        return InteractionResponse(
            "Check-in continuation not yet implemented. Please use the existing /checkin command.",
            True
        )
    
    @handle_errors("getting check-in status", default_return=InteractionResponse("I'm having trouble getting your check-in status. Please try again.", True))
    def _handle_checkin_status(self, user_id: str) -> InteractionResponse:
        """Handle check-in status request"""
        if not is_user_checkins_enabled(user_id):
            return InteractionResponse("Check-ins are not enabled for your account.", True)
        
        # Get recent check-ins
        recent_checkins = get_recent_checkins(user_id, limit=7)
        
        if not recent_checkins:
            return InteractionResponse("No check-ins recorded in the last 7 days.", True)
        
        # Format status
        response = "**Recent Check-ins:**\n"
        for checkin in recent_checkins[:5]:  # Show last 5
            date = checkin.get('date', 'Unknown date')
            mood = checkin.get('mood', 'No mood recorded')
            energy = checkin.get('energy', 'No energy recorded')
            
            # Display mood and energy together if both are available
            if energy != 'No energy recorded':
                response += f"📅 {date}: 😊 Mood {mood}/5 | ⚡ Energy {energy}/5\n"
            else:
                response += f"📅 {date}: 😊 Mood {mood}/5\n"
        
        if len(recent_checkins) > 5:
            response += f"... and {len(recent_checkins) - 5} more"
        
        return InteractionResponse(response, True)
    
    @handle_errors("getting checkin help", default_return="Help with check-ins - start check-ins and view your status")
    def get_help(self) -> str:
        return "Help with check-ins - start check-ins and view your status"
    
    @handle_errors("getting checkin examples", default_return=[])
    def get_examples(self) -> List[str]:
        return [
            "start checkin",
            "checkin status",
            "checkin"
        ]

class ProfileHandler(InteractionHandler):
    """Handler for profile management interactions"""
    
    @handle_errors("checking if can handle profile intent", default_return=False)
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
    
    @handle_errors("showing profile", default_return=InteractionResponse("I'm having trouble showing your profile. Please try again.", True))
    def _handle_show_profile(self, user_id: str) -> InteractionResponse:
        """Handle showing user profile with comprehensive personalization data"""
        # Load user data
        account_result = get_user_data(user_id, 'account')
        account_data = account_result.get('account', {}) if account_result else {}
        context_result = get_user_data(user_id, 'context')
        context_data = context_result.get('context', {}) if context_result else {}
        preferences_result = get_user_data(user_id, 'preferences')
        preferences_data = preferences_result.get('preferences', {}) if preferences_result else {}
        
        # Format profile information
        response = "**Your Profile:**\n"
        
        # Basic info
        if context_data:
            name = context_data.get('preferred_name', 'Not set')
            gender_identity = context_data.get('gender_identity', [])
            date_of_birth = context_data.get('date_of_birth', 'Not set')
            
            response += f"👤 **Name:** {name}\n"
            
            # Format gender identity (can be a list)
            if isinstance(gender_identity, list) and gender_identity:
                gender_str = ', '.join(gender_identity)
            elif isinstance(gender_identity, str):
                gender_str = gender_identity
            else:
                gender_str = 'Not set'
            response += f"🎭 **Gender Identity:** {gender_str}\n"
            
            if date_of_birth and date_of_birth != 'Not set':
                response += f"📅 **Date of Birth:** {date_of_birth}\n"
        
        # Account info
        if account_data:
            email = account_data.get('email', 'Not set')
            status = account_data.get('account_status', 'Unknown')
            response += f"📧 **Email:** {email}\n"
            response += f"📊 **Status:** {status}\n"
        
        # Health & Medical Information
        if context_data:
            custom_fields = context_data.get('custom_fields', {})
            
            # Health conditions
            health_conditions = custom_fields.get('health_conditions', [])
            if health_conditions:
                response += f"🏥 **Health Conditions:** {', '.join(health_conditions)}\n"
            
            # Medications
            medications = custom_fields.get('medications_treatments', [])
            if medications:
                response += f"💊 **Medications/Treatments:** {', '.join(medications)}\n"
            
            # Allergies
            allergies = custom_fields.get('allergies_sensitivities', [])
            if allergies:
                response += f"⚠️ **Allergies/Sensitivities:** {', '.join(allergies)}\n"
        
        # Interests
        interests = context_data.get('interests', []) if context_data else []
        if interests:
            response += f"🎯 **Interests:** {', '.join(interests)}\n"
        
        # Goals
        goals = context_data.get('goals', []) if context_data else []
        if goals:
            response += f"🎯 **Goals:** {', '.join(goals)}\n"
        
        # Loved Ones/Support Network
        loved_ones = context_data.get('loved_ones', []) if context_data else []
        if loved_ones:
            response += f"💕 **Support Network:**\n"
            for person in loved_ones[:3]:  # Show first 3
                name = person.get('name', 'Unknown')
                person_type = person.get('type', '')
                relationships = person.get('relationships', [])
                rel_str = f" ({', '.join(relationships)})" if relationships else ""
                response += f"  • {name} - {person_type}{rel_str}\n"
            if len(loved_ones) > 3:
                response += f"  ... and {len(loved_ones) - 3} more\n"
        
        # Notes for AI
        notes = context_data.get('notes_for_ai', []) if context_data else []
        if notes and notes[0]:
            response += f"📝 **Notes for AI:** {notes[0][:100]}{'...' if len(notes[0]) > 100 else ''}\n"
        
        # Account features
        if account_data:
            features = account_data.get('features', {})
            checkins_enabled = features.get('checkins') == 'enabled'
            tasks_enabled = features.get('task_management') == 'enabled'
            response += f"\n**Account Features:**\n"
            response += f"✅ Check-ins: {'Enabled' if checkins_enabled else 'Disabled'}\n"
            response += f"📋 Tasks: {'Enabled' if tasks_enabled else 'Disabled'}\n"
        
        # Create rich data for Discord embeds
        rich_data = {
            'type': 'profile',
            'title': 'Your Profile',
            'fields': []
        }
        
        # Add basic info fields
        if context_data:
            name = context_data.get('preferred_name', 'Not set')
            if name != 'Not set':
                rich_data['fields'].append({
                    'name': 'Name',
                    'value': name,
                    'inline': True
                })
            
            gender_identity = context_data.get('gender_identity', [])
            if gender_identity and isinstance(gender_identity, list):
                gender_str = ', '.join(gender_identity)
                rich_data['fields'].append({
                    'name': 'Gender Identity',
                    'value': gender_str,
                    'inline': True
                })
        
        # Add feature status fields
        if account_data:
            features = account_data.get('features', {})
            checkins_enabled = features.get('checkins') == 'enabled'
            tasks_enabled = features.get('task_management') == 'enabled'
            
            rich_data['fields'].append({
                'name': 'Check-ins',
                'value': '✅ Enabled' if checkins_enabled else '❌ Disabled',
                'inline': True
            })
            
            rich_data['fields'].append({
                'name': 'Tasks',
                'value': '✅ Enabled' if tasks_enabled else '❌ Disabled',
                'inline': True
            })
        
        # Add health info summary
        if context_data:
            custom_fields = context_data.get('custom_fields', {})
            health_count = len(custom_fields.get('health_conditions', []))
            med_count = len(custom_fields.get('medications_treatments', []))
            allergy_count = len(custom_fields.get('allergies_sensitivities', []))
            
            if health_count > 0 or med_count > 0 or allergy_count > 0:
                health_summary = []
                if health_count > 0:
                    health_summary.append(f"{health_count} conditions")
                if med_count > 0:
                    health_summary.append(f"{med_count} medications")
                if allergy_count > 0:
                    health_summary.append(f"{allergy_count} allergies")
                
                rich_data['fields'].append({
                    'name': 'Health Summary',
                    'value': ', '.join(health_summary),
                    'inline': False
                })
        
        return InteractionResponse(
            response, 
            True,
            rich_data=rich_data,
            suggestions=["Update my name", "Add health conditions", "Update interests", "Show profile stats"]
        )
    
    @handle_errors("updating profile", default_return=InteractionResponse("I'm having trouble updating your profile. Please try again.", True))
    def _handle_update_profile(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle comprehensive profile updates"""
        if not entities:
            return InteractionResponse(
                "What would you like to update? Available fields:\n"
                "• Basic: name, gender_identity, date_of_birth\n"
                "• Health: health_conditions, medications, allergies\n"
                "• Personal: interests, goals\n"
                "• Support: loved_ones, notes_for_ai",
                completed=False,
                suggestions=["Update my name", "Add health conditions", "Update interests", "Add goals"]
            )
        
        # Load current context data
        context_result = get_user_data(user_id, 'context')
        context_data = context_result.get('context', {}) if context_result else {}
        
        # Initialize custom_fields if not present
        if 'custom_fields' not in context_data:
            context_data['custom_fields'] = {}
        
        # Apply updates
        updates = []
        
        # Basic info updates
        if 'name' in entities:
            context_data['preferred_name'] = entities['name']
            updates.append('name')
        
        if 'gender_identity' in entities:
            # Handle both string and list formats
            gender_identity = entities['gender_identity']
            if isinstance(gender_identity, str):
                # Convert comma-separated string to list
                gender_identity = [g.strip() for g in gender_identity.split(',') if g.strip()]
            context_data['gender_identity'] = gender_identity
            updates.append('gender identity')
        
        if 'date_of_birth' in entities:
            context_data['date_of_birth'] = entities['date_of_birth']
            updates.append('date of birth')
        
        # Health & Medical updates
        if 'health_conditions' in entities:
            health_conditions = entities['health_conditions']
            if isinstance(health_conditions, str):
                health_conditions = [h.strip() for h in health_conditions.split(',') if h.strip()]
            context_data['custom_fields']['health_conditions'] = health_conditions
            updates.append('health conditions')
        
        if 'medications' in entities:
            medications = entities['medications']
            if isinstance(medications, str):
                medications = [m.strip() for m in medications.split(',') if m.strip()]
            context_data['custom_fields']['medications_treatments'] = medications
            updates.append('medications')
        
        if 'allergies' in entities:
            allergies = entities['allergies']
            if isinstance(allergies, str):
                allergies = [a.strip() for a in allergies.split(',') if a.strip()]
            context_data['custom_fields']['allergies_sensitivities'] = allergies
            updates.append('allergies')
        
        # Personal info updates
        if 'interests' in entities:
            interests = entities['interests']
            if isinstance(interests, str):
                interests = [i.strip() for i in interests.split(',') if i.strip()]
            context_data['interests'] = interests
            updates.append('interests')
        
        if 'goals' in entities:
            goals = entities['goals']
            if isinstance(goals, str):
                goals = [g.strip() for g in goals.split(',') if g.strip()]
            context_data['goals'] = goals
            updates.append('goals')
        
        # Support network updates
        if 'loved_ones' in entities:
            # Handle loved ones as a list of dictionaries or string format
            loved_ones = entities['loved_ones']
            if isinstance(loved_ones, str):
                # Parse simple format: "Name - Type - Relationship1,Relationship2"
                loved_ones_list = []
                for line in loved_ones.split('\n'):
                    parts = [p.strip() for p in line.split('-')]
                    if len(parts) >= 1:
                        name = parts[0]
                        person_type = parts[1] if len(parts) > 1 else ''
                        relationships = []
                        if len(parts) > 2:
                            relationships = [r.strip() for r in parts[2].split(',') if r.strip()]
                        loved_ones_list.append({
                            'name': name,
                            'type': person_type,
                            'relationships': relationships
                        })
                context_data['loved_ones'] = loved_ones_list
            else:
                context_data['loved_ones'] = loved_ones
            updates.append('support network')
        
        if 'notes_for_ai' in entities:
            notes = entities['notes_for_ai']
            if isinstance(notes, str):
                notes = [notes]  # Store as list
            context_data['notes_for_ai'] = notes
            updates.append('notes for AI')
        
        # Email update (stored in account data)
        if 'email' in entities:
            account_result = get_user_data(user_id, 'account')
            account_data = account_result.get('account', {}) if account_result else {}
            account_data['email'] = entities['email']
            # Note: Using save_user_data instead of individual save function
            updates.append('email')
        
        # Save updates
        if updates:
            if save_user_data(user_id, 'context', context_data):
                response = f"✅ Profile updated: {', '.join(updates)}"
                return InteractionResponse(
                    response, 
                    True,
                    suggestions=["Show my profile", "Add more health conditions", "Update goals", "Show profile stats"]
                )
            else:
                return InteractionResponse("❌ Failed to update profile. Please try again.", True)
        else:
            return InteractionResponse(
                "No valid updates found. Please specify what you'd like to update.",
                completed=False,
                suggestions=["Update my name", "Add health conditions", "Update interests", "Add goals"]
            )
    
    @handle_errors("getting profile statistics", default_return=InteractionResponse("I'm having trouble getting your profile statistics. Please try again.", True))
    def _handle_profile_stats(self, user_id: str) -> InteractionResponse:
        """Handle profile statistics"""
        # Get task stats
        task_stats = get_user_task_stats(user_id)
        
        # Get check-in stats
        recent_checkins = get_recent_checkins(user_id, limit=30)
        
        response = "**Your Statistics:**\n"
        response += f"📋 Active tasks: {task_stats.get('active_count', 0)}\n"
        response += f"✅ Completed tasks: {task_stats.get('completed_count', 0)}\n"
        response += f"📊 Task completion rate: {task_stats.get('completion_rate', 0):.1f}%\n"
        response += f"📅 Check-ins this month: {len(recent_checkins)}"
        
        return InteractionResponse(response, True)
    
    @handle_errors("getting profile help", default_return="Help with profile management - view and update your information")
    def get_help(self) -> str:
        return "Help with profile management - view and update your information"
    
    @handle_errors("getting profile examples", default_return=[])
    def get_examples(self) -> List[str]:
        return [
            "show profile",
            "update name 'Julie'",
            "update gender_identity 'Non-binary, Woman'",
            "add health_conditions 'Depression, Anxiety'",
            "update interests 'Reading, Gaming, Hiking'",
            "add goals 'mental_health, career'",
            "add loved_ones 'Mom - Family - Mother, Support'",
            "update notes_for_ai 'I prefer gentle reminders'",
            "profile stats"
        ]

class HelpHandler(InteractionHandler):
    """Handler for help and command information"""
    
    @handle_errors("checking if can handle help intent", default_return=False)
    def can_handle(self, intent: str) -> bool:
        return intent in ['help', 'commands', 'examples', 'status', 'messages']
    
    @handle_errors("handling help interaction", default_return=InteractionResponse("I'm having trouble with help right now. Please try again.", True))
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        intent = parsed_command.intent
        entities = parsed_command.entities
        
        if intent == 'help':
            return self._handle_general_help(user_id, entities)
        elif intent == 'commands':
            return self._handle_commands_list(user_id)
        elif intent == 'examples':
            return self._handle_examples(user_id, entities)
        elif intent == 'status':
            return self._handle_status(user_id)
        elif intent == 'messages':
            return self._handle_messages(user_id)
        else:
            return InteractionResponse("I'm here to help! Try 'help' for general help or 'commands' for a list of commands.", True)
    
    @handle_errors("handling general help", default_return=InteractionResponse("Error providing help", "error"))
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
                "• Task stats: 'task stats' or 'show task statistics'\n"
                "• Weekly progress: 'how am I doing with my tasks this week?'",
                True
            )
        elif topic == 'checkin':
            return InteractionResponse(
                "**Check-in Help:**\n"
                "• Start check-in: 'start checkin' or 'checkin'\n"
                "• Check-in status: 'checkin status' or 'show checkins'\n"
                "• Check-in history: 'show my check-in history'\n"
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
                "**MHM Bot Commands** 🌟\n\n"
                "I understand natural language best! Just talk to me naturally.\n\n"
                "**Tasks**:\n"
                "• \"create a task to...\" - Add new task\n"
                "• \"show my tasks\" - View all tasks\n"
                "• \"complete [task]\" - Mark task done\n"
                "• Or use: /tasks (also !tasks)\n\n"
                "**Check-ins** (Conversational):\n"
                "• \"start a check-in\" - Begin wellness check-in\n"
                "• I'll ask you questions about mood, energy, etc.\n"
                "• Or use: /checkin (also !checkin)\n\n"
                "**Profile**:\n"
                "• \"show my profile\" - View your information\n"
                "• \"update my name to...\" - Change details\n"
                "• Or use: /profile (also !profile)\n\n"
                "**Analytics**:\n"
                "• \"show my analytics\" - View insights\n"
                "• \"what are my mood trends?\" - See patterns\n"
                "• \"how am I doing with habits?\" - Get analysis\n"
                "• Or use: /analytics (also !analytics)\n\n"
                "**Schedule**:\n"
                "• \"show my schedule\" - View time periods\n"
                "• \"add schedule period...\" - Create new periods\n"
                "• Or use: /schedule (also !schedule)\n\n"
                "**Need More Help?**\n"
                "• Say \"examples\" for more natural language examples\n"
                "• Say \"commands\" for a complete command list\n"
                "• Visit DISCORD.md for full documentation\n\n"
                "Just start typing naturally - I'll understand what you want to do!",
                True
            )
    
    @handle_errors("handling commands list", default_return=InteractionResponse("Error listing commands", "error"))
    def _handle_commands_list(self, user_id: str) -> InteractionResponse:
        """Handle commands list request"""
        response = "**Complete Command List:**\n\n"
        
        # Task commands
        response += "📋 **Task Management:**\n"
        response += "• Natural: \"create a task to...\", \"show my tasks\", \"complete [task]\"\n"
        response += "• Explicit: create_task, list_tasks, complete_task, delete_task, update_task, task_stats\n"
        response += "• Slash: /tasks (also !tasks)\n\n"
        
        # Check-in commands
        response += "✅ **Check-ins** (Conversational Flows):\n"
        response += "• Natural: \"start a check-in\", \"how am I feeling?\", \"I want to check in\"\n"
        response += "• Explicit: start_checkin, checkin_status, checkin_history, checkin_analysis\n"
        response += "• Slash: /checkin (also !checkin)\n"
        response += "• Note: Check-ins are conversational - bot asks questions and waits for responses\n\n"
        
        # Profile commands
        response += "👤 **Profile Management:**\n"
        response += "• Natural: \"show my profile\", \"update my name to...\", \"add health condition...\"\n"
        response += "• Explicit: show_profile, update_profile, profile_stats\n"
        response += "• Slash: /profile (also !profile)\n\n"
        
        # Schedule commands
        response += "📅 **Schedule Management:**\n"
        response += "• Natural: \"show my schedule\", \"add schedule period...\", \"what's my schedule status?\"\n"
        response += "• Explicit: show_schedule, update_schedule, schedule_status, add_schedule_period, edit_schedule_period\n"
        response += "• Slash: /schedule (also !schedule)\n\n"
        
        # Analytics commands
        response += "📊 **Analytics & Insights:**\n"
        response += "• Natural: \"show my analytics\", \"what are my mood trends?\", \"how am I doing with habits?\"\n"
        response += "• Explicit: show_analytics, mood_trends, habit_analysis, sleep_analysis, wellness_score\n"
        response += "• More: checkin_history, completion_rate, task_analytics, quant_summary\n"
        response += "• Slash: /analytics (also !analytics)\n\n"
        
        # System commands
        response += "🔧 **System Commands:**\n"
        response += "• Natural: \"help\", \"what commands are available?\", \"show me examples\"\n"
        response += "• Explicit: help, commands, examples, status, clear_flows, cancel\n"
        response += "• Slash: /help, /status, /clear, /cancel\n\n"
        
        response += "**Command Types Explained:**\n"
        response += "• **Single-Turn**: Most commands - you ask, bot responds once\n"
        response += "• **Conversational Flows**: Check-ins, some task creation - multi-turn conversations\n"
        response += "• **Natural Language**: Primary method - just talk naturally!\n"
        response += "• **Explicit Commands**: For precision when needed\n"
        response += "• **Slash Commands**: Discord-native shortcuts (preferred) - also supports !commands\n\n"
        response += "**Flow Management:**\n"
        response += "• To exit a conversation: say \"cancel\" or \"/cancel\"\n"
        response += "• To clear stuck flows: say \"clear flows\" or use /clear\n\n"
        response += "**Need More Help?**\n"
        response += "• Say \"examples\" for natural language examples\n"
        response += "• Say \"help [topic]\" for specific help (tasks, checkin, profile, etc.)\n"
        response += "• Visit DISCORD.md for complete documentation"
        
        return InteractionResponse(response, True)
    
    @handle_errors("handling examples", default_return=InteractionResponse("Error providing examples", "error"))
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
                "• 'Start my check-in'\n"
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
    
    def _handle_status(self, user_id: str) -> InteractionResponse:
        """Handle status request with detailed system information"""
        try:
            from tasks.task_management import load_active_tasks
            from core.response_tracking import is_user_checkins_enabled
            
            # Load user data
            account_result = get_user_data(user_id, 'account')
            account_data = account_result.get('account', {}) if account_result else {}
            if not account_data:
                return InteractionResponse("I'm up and running! 🌟\n\nPlease register first to see your personal status.", True)
            
            # Get user info
            username = account_data.get('internal_username', 'Unknown')
            features = account_data.get('features', {})
            
            # Get active tasks
            tasks = load_active_tasks(user_id)
            task_count = len(tasks) if tasks else 0
            
            # Check if check-ins are enabled
            checkins_enabled = is_user_checkins_enabled(user_id)
            
            # Build status response
            response = f"**System Status for {username}** 🌟\n\n"
            
            # Account status
            response += "👤 **Account Status:**\n"
            response += f"• Username: {username}\n"
            response += f"• Account: Active ✅\n"
            response += f"• Timezone: {account_data.get('timezone', 'Not set')}\n\n"
            
            # Features status
            response += "🔧 **Features:**\n"
            for feature, status in features.items():
                status_icon = "✅" if status == "enabled" else "❌"
                response += f"• {feature.replace('_', ' ').title()}: {status_icon}\n"
            response += "\n"
            
            # Current status
            response += "📊 **Current Status:**\n"
            response += f"• Active Tasks: {task_count}\n"
            response += f"• Check-ins: {'Enabled ✅' if checkins_enabled else 'Disabled ❌'}\n"
            response += f"• System: Running smoothly ✅\n\n"
            
            # Quick actions
            response += "🚀 **Quick Actions:**\n"
            response += "• 'show my tasks' - View your tasks\n"
            response += "• 'start checkin' - Begin check-in\n"
            response += "• 'show profile' - View your profile\n"
            response += "• 'show schedule' - View your schedules\n"
            response += "• 'help' - Get help and examples\n\n"
            
            response += "Just start typing naturally - I'll understand what you want to do!"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error getting status for user {user_id}: {e}")
            return InteractionResponse(
                "I'm up and running! 🌟\n\nI can help you with:\n"
                "📋 **Tasks**: Create, list, complete, and manage tasks\n"
                "✅ **Check-ins**: Wellness check-ins\n"
                "👤 **Profile**: View and update your information\n"
                "📅 **Schedule**: Manage message schedules\n"
                "📊 **Analytics**: View wellness insights\n\n"
                "Just start typing naturally - I'll understand what you want to do!",
                True
            )
    
    def _handle_messages(self, user_id: str) -> InteractionResponse:
        """Handle messages request with message history and settings"""
        try:
            from core.response_tracking import get_recent_checkins
            
            # Load user data
            account_result = get_user_data(user_id, 'account')
            account_data = account_result.get('account', {}) if account_result else {}
            if not account_data:
                return InteractionResponse("Please register first to view your messages.", True)
            
            # Get user info
            username = account_data.get('internal_username', 'Unknown')
            
            # Get recent check-ins (as a proxy for recent messages)
            recent_checkins = get_recent_checkins(user_id, limit=5)
            
            # Build messages response
            response = f"**Messages for {username}** 📬\n\n"
            
            # Message settings
            response += "📧 **Message Settings:**\n"
            response += "• Automated Messages: Enabled ✅\n"
            response += "• Check-ins: Available ✅\n"
            response += "• Task Reminders: Available ✅\n"
            response += "• Motivational Messages: Available ✅\n\n"
            
            # Recent activity
            response += "📅 **Recent Activity:**\n"
            if recent_checkins:
                response += "Recent check-ins:\n"
                for checkin in recent_checkins:
                    date = checkin.get('date', 'Unknown')
                    response += f"• {date}: Check-in completed ✅\n"
            else:
                response += "No recent check-ins found.\n"
            response += "\n"
            
            # Quick actions
            response += "🚀 **Quick Actions:**\n"
            response += "• 'start checkin' - Begin check-in\n"
            response += "• 'show schedule' - View message schedules\n"
            response += "• 'show analytics' - View message analytics\n"
            response += "• 'help' - Get help with messages\n\n"
            
            response += "Your messages are automatically scheduled and delivered based on your preferences!"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error getting messages for user {user_id}: {e}")
            return InteractionResponse(
                "**Messages** 📬\n\n"
                "I can help you with:\n"
                "• check-ins\n"
                "• Task reminders\n"
                "• Motivational messages\n"
                "• Schedule management\n\n"
                "Try 'start checkin' to begin a check-in!",
                True
            )
    
    @handle_errors("getting help help", default_return="Get help and see available commands")
    def get_help(self) -> str:
        return "Get help and see available commands"
    
    @handle_errors("getting help examples", default_return=[])
    def get_examples(self) -> List[str]:
        return [
            "help",
            "help tasks",
            "help checkin",
            "commands",
            "examples",
            "examples tasks"
        ]

class ScheduleManagementHandler(InteractionHandler):
    """Handler for schedule management interactions"""
    
    @handle_errors("checking if can handle schedule intent", default_return=False)
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
    
    @handle_errors("showing schedule", default_return=InteractionResponse("I'm having trouble showing your schedule. Please try again.", True))
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
            
            # Create rich data for Discord embeds
            rich_data = {
                'type': 'schedule',
                'title': f'Schedule for {category.title()}' if category != 'all' else 'Your Current Schedules',
                'fields': []
            }
            
            if category == 'all':
                # Add summary fields for all schedules
                total_periods = 0
                active_periods = 0
                for cat in categories:
                    periods = get_schedule_time_periods(user_id, cat)
                    total_periods += len(periods)
                    active_periods += sum(1 for p in periods.values() if p.get('active', True))
                
                rich_data['fields'].append({
                    'name': 'Total Categories',
                    'value': str(len(categories)),
                    'inline': True
                })
                
                rich_data['fields'].append({
                    'name': 'Total Periods',
                    'value': str(total_periods),
                    'inline': True
                })
                
                rich_data['fields'].append({
                    'name': 'Active Periods',
                    'value': f"{active_periods}/{total_periods}",
                    'inline': True
                })
            else:
                # Add fields for specific category
                periods = get_schedule_time_periods(user_id, category)
                active_count = sum(1 for p in periods.values() if p.get('active', True))
                
                rich_data['fields'].append({
                    'name': 'Total Periods',
                    'value': str(len(periods)),
                    'inline': True
                })
                
                rich_data['fields'].append({
                    'name': 'Active Periods',
                    'value': f"{active_count}/{len(periods)}",
                    'inline': True
                })
            
            return InteractionResponse(response, True, rich_data=rich_data)
            
        except Exception as e:
            logger.error(f"Error showing schedule for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your schedule right now. Please try again.", True)
    
    @handle_errors("updating schedule", default_return=InteractionResponse("I'm having trouble updating your schedule. Please try again.", True))
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
    
    @handle_errors("getting schedule status", default_return=InteractionResponse("I'm having trouble getting your schedule status. Please try again.", True))
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
    
    @handle_errors("adding schedule period", default_return=InteractionResponse("I'm having trouble adding your schedule period. Please try again.", True))
    def _handle_add_schedule_period(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Add a new schedule period with enhanced options"""
        category = entities.get('category')
        period_name = entities.get('period_name')
        start_time = entities.get('start_time')
        end_time = entities.get('end_time')
        days = entities.get('days', ['ALL'])  # Default to all days
        active = entities.get('active', True)  # Default to active
        
        if not all([category, period_name, start_time, end_time]):
            return InteractionResponse(
                "Please provide all details for the new schedule period. "
                "Try: 'Add a new period called morning to my task schedule from 9am to 11am' or "
                "'Add a weekday period called work to my check-in schedule from 8am to 5pm on Monday, Tuesday, Wednesday, Thursday, Friday'",
                completed=False,
                suggestions=["Add morning period 9am-11am", "Add work period 8am-5pm weekdays", "Add evening period 7pm-9pm"]
            )
        
        try:
            from core.schedule_management import add_schedule_period, get_schedule_time_periods, set_schedule_periods
            
            # Parse and validate time formats
            start_time = self._handle_add_schedule_period__parse_time_format(start_time)
            end_time = self._handle_add_schedule_period__parse_time_format(end_time)
            
            # Parse days if provided
            if isinstance(days, str):
                days = [d.strip() for d in days.split(',') if d.strip()]
            
            # Validate days
            valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'ALL']
            if days and not all(day in valid_days for day in days):
                return InteractionResponse(
                    f"Invalid days specified. Valid days are: {', '.join(valid_days)}",
                    True
                )
            
            # Create period data
            period_data = {
                'start_time': start_time,
                'end_time': end_time,
                'days': days,
                'active': active
            }
            
            # Get existing periods and add new one
            periods = get_schedule_time_periods(user_id, category)
            periods[period_name] = period_data
            set_schedule_periods(user_id, category, periods)
            
            # Format response
            days_str = ', '.join(days) if days != ['ALL'] else 'all days'
            status = "active" if active else "inactive"
            response = f"✅ Added new schedule period '{period_name}' to {category.title()}:\n"
            response += f"  • Time: {start_time} - {end_time}\n"
            response += f"  • Days: {days_str}\n"
            response += f"  • Status: {status}"
            
            return InteractionResponse(
                response, 
                True,
                suggestions=["Show my schedule", "Edit this period", "Add another period", "Schedule status"]
            )
            
        except Exception as e:
            logger.error(f"Error adding schedule period for user {user_id}: {e}")
            return InteractionResponse(f"I'm having trouble adding the schedule period: {str(e)}", True)
    
    @handle_errors("parsing time format")
    def _handle_add_schedule_period__parse_time_format(self, time_str: str) -> str:
        """Parse various time formats and convert to standard format"""
        if not time_str:
            return time_str
        
        time_str = time_str.lower().strip()
        
        # Handle common time formats
        if 'am' in time_str or 'pm' in time_str:
            # Already in 12-hour format, just standardize
            return time_str.upper()
        elif ':' in time_str:
            # Assume 24-hour format, convert to 12-hour
            try:
                from datetime import datetime
                time_obj = datetime.strptime(time_str, '%H:%M')
                return time_obj.strftime('%I:%M %p')
            except ValueError:
                return time_str
        else:
            # Try to parse as hour only
            try:
                hour = int(time_str)
                if 0 <= hour <= 23:
                    from datetime import datetime
                    time_obj = datetime.strptime(f"{hour:02d}:00", '%H:%M')
                    return time_obj.strftime('%I:%M %p')
            except ValueError:
                pass
            
            return time_str
    
    @handle_errors("parsing time format for edit")
    def _handle_edit_schedule_period__parse_time_format(self, time_str: str) -> str:
        """Parse various time formats and convert to standard format"""
        if not time_str:
            return time_str
        
        time_str = time_str.lower().strip()
        
        # Handle common time formats
        if 'am' in time_str or 'pm' in time_str:
            # Already in 12-hour format, just standardize
            return time_str.upper()
        elif ':' in time_str:
            # Assume 24-hour format, convert to 12-hour
            try:
                from datetime import datetime
                time_obj = datetime.strptime(time_str, '%H:%M')
                return time_obj.strftime('%I:%M %p')
            except ValueError:
                return time_str
        else:
            # Try to parse as hour only
            try:
                hour = int(time_str)
                if 0 <= hour <= 23:
                    from datetime import datetime
                    time_obj = datetime.strptime(f"{hour:02d}:00", '%H:%M')
                    return time_obj.strftime('%I:%M %p')
            except ValueError:
                pass
            
            return time_str
    
    @handle_errors("editing schedule period", default_return=InteractionResponse("I'm having trouble editing your schedule period. Please try again.", True))
    def _handle_edit_schedule_period(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Edit an existing schedule period with enhanced options"""
        category = entities.get('category')
        period_name = entities.get('period_name')
        new_start_time = entities.get('new_start_time')
        new_end_time = entities.get('new_end_time')
        new_days = entities.get('new_days')
        new_active = entities.get('new_active')
        
        if not category or not period_name:
            return InteractionResponse(
                "Please specify which schedule period you want to edit. "
                "Try: 'Edit the morning period in my task schedule'",
                completed=False,
                suggestions=["Edit morning period", "Edit work period", "Show my schedule"]
            )
        # Curated suggestions when target is identified but times/days/active are missing
        if category and period_name and not any([new_start_time, new_end_time, new_days, new_active]):
            return InteractionResponse(
                f"What would you like to update for '{period_name}' in {category.title()}?",
                completed=False,
                suggestions=["from 9am to 11am", "days Monday,Tuesday"]
            )
        
        try:
            from core.schedule_management import get_schedule_time_periods, set_schedule_periods
            
            # Get existing periods
            periods = get_schedule_time_periods(user_id, category)
            
            if period_name not in periods:
                return InteractionResponse(
                    f"I couldn't find a '{period_name}' period in {category.title()}. What times should it use?",
                    completed=False,
                    suggestions=["from 9am to 11am", "from 7pm to 9pm"]
                )
            
            # Get current period data
            current_period = periods[period_name]
            
            # Apply updates
            updates = []
            
            if new_start_time:
                new_start_time = self._handle_edit_schedule_period__parse_time_format(new_start_time)
                current_period['start_time'] = new_start_time
                updates.append(f"start time to {new_start_time}")
            
            if new_end_time:
                new_end_time = self._handle_edit_schedule_period__parse_time_format(new_end_time)
                current_period['end_time'] = new_end_time
                updates.append(f"end time to {new_end_time}")
            
            if new_days is not None:
                if isinstance(new_days, str):
                    new_days = [d.strip() for d in new_days.split(',') if d.strip()]
                
                # Validate days
                valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'ALL']
                if not all(day in valid_days for day in new_days):
                    return InteractionResponse(
                        f"Invalid days specified. Valid days are: {', '.join(valid_days)}",
                        True
                    )
                
                current_period['days'] = new_days
                days_str = ', '.join(new_days) if new_days != ['ALL'] else 'all days'
                updates.append(f"days to {days_str}")
            
            if new_active is not None:
                current_period['active'] = new_active
                status = "active" if new_active else "inactive"
                updates.append(f"status to {status}")
            
            # Save changes
            set_schedule_periods(user_id, category, periods)
            
            if updates:
                response = f"✅ Updated schedule period '{period_name}' in {category.title()}:\n"
                response += f"  • Changed: {', '.join(updates)}\n"
                response += f"  • Current: {current_period['start_time']} - {current_period['end_time']}\n"
                response += f"  • Days: {', '.join(current_period['days']) if current_period['days'] != ['ALL'] else 'all days'}\n"
                response += f"  • Status: {'active' if current_period['active'] else 'inactive'}"
                
                return InteractionResponse(
                    response, 
                    True,
                    suggestions=["Show my schedule", "Edit another period", "Schedule status"]
                )
            else:
                return InteractionResponse(
                    f"No changes specified for period '{period_name}'. "
                    f"Current settings: {current_period['start_time']} - {current_period['end_time']}",
                    completed=False,
                    suggestions=["from 9am to 11am", "active off"]
                )
                
        except Exception as e:
            logger.error(f"Error editing schedule period for user {user_id}: {e}")
            return InteractionResponse(f"I'm having trouble editing the schedule period: {str(e)}", True)
    
    @handle_errors("getting schedule help", default_return="Help with schedule management - manage your message, task, and check-in schedules")
    def get_help(self) -> str:
        return "Help with schedule management - manage your message, task, and check-in schedules"
    
    @handle_errors("getting schedule examples", default_return=[])
    def get_examples(self) -> List[str]:
        return [
            "show schedule",
            "show my task schedule",
            "schedule status",
            "enable my check-in schedule",
            "add morning period 9am-11am to task schedule",
            "add work period 8am-5pm weekdays to check-in schedule",
            "edit morning period start time to 8am",
            "edit work period days to Monday, Tuesday, Wednesday, Thursday, Friday",
            "disable evening period in task schedule"
        ]

class AnalyticsHandler(InteractionHandler):
    """Handler for analytics and insights interactions"""
    
    @handle_errors("checking if can handle analytics intent", default_return=False)
    def can_handle(self, intent: str) -> bool:
        return intent in ['show_analytics', 'mood_trends', 'energy_trends', 'habit_analysis', 'sleep_analysis', 'wellness_score', 'checkin_history', 'completion_rate', 'quant_summary']
    
    @handle_errors("handling analytics interaction", default_return=InteractionResponse("I'm having trouble with analytics right now. Please try again.", True))
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        intent = parsed_command.intent
        entities = parsed_command.entities
        
        if intent == 'show_analytics':
            return self._handle_show_analytics(user_id, entities)
        elif intent == 'mood_trends':
            return self._handle_mood_trends(user_id, entities)
        elif intent == 'energy_trends':
            return self._handle_energy_trends(user_id, entities)
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
        elif intent == 'quant_summary':
            return self._handle_quant_summary(user_id, entities)
        else:
            return InteractionResponse(f"I don't understand that analytics command. Try: {', '.join(self.get_examples())}", True)
    
    @handle_errors("showing analytics", default_return=InteractionResponse("I'm having trouble showing your analytics. Please try again.", True))
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
            mood_summary = f"Average mood: {avg_mood}/5"
            
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

    def _handle_quant_summary(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show per-field quantitative summaries for opted-in fields."""
        days = entities.get('days', 30)
        try:
            from core.checkin_analytics import CheckinAnalytics
            from core.user_data_handlers import get_user_data
            analytics = CheckinAnalytics()

            enabled_fields = None
            try:
                prefs = get_user_data(user_id, 'preferences') or {}
                checkin_settings = (prefs.get('preferences') or {}).get('checkin_settings') or {}
                if isinstance(checkin_settings, dict):
                    # Get enabled fields from questions configuration
                    questions = checkin_settings.get('questions', {})
                    enabled_fields = [key for key, config in questions.items() 
                                    if config.get('enabled', False) and 
                                    config.get('type') in ['scale_1_5', 'number', 'yes_no']]
            except Exception:
                enabled_fields = None

            summaries = analytics.get_quantitative_summaries(user_id, days, enabled_fields)
            if 'error' in summaries:
                return InteractionResponse("You don't have enough check-in data to compute summaries yet.", True)

            response = f"**Per-field Quantitative Summaries (Last {days} days):**\n\n"
            for field, stats in summaries.items():
                # Determine scale for field
                scale = self._get_field_scale(field)
                scale_suffix = f"/{scale}" if scale else ""
                
                response += f"• {field.title()}: avg {stats['average']}{scale_suffix} (min {stats['min']}{scale_suffix}, max {stats['max']}{scale_suffix}) over {int(stats['count'])} days\n"
            return InteractionResponse(response, True)
        except Exception as e:
            logger.error(f"Error computing quantitative summaries for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble computing your quantitative summaries right now. Please try again.", True)
    
    @handle_errors("showing mood trends", default_return=InteractionResponse("I'm having trouble showing your mood trends. Please try again.", True))
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
            response += f"📈 **Average Mood:** {mood_data.get('average_mood', 0)}/5\n"
            response += f"📊 **Mood Range:** {mood_data.get('min_mood', 0)} - {mood_data.get('max_mood', 0)}/5\n"
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
    
    @handle_errors("showing energy trends", default_return=InteractionResponse("I'm having trouble showing your energy trends. Please try again.", True))
    def _handle_energy_trends(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Show energy trends analysis"""
        days = entities.get('days', 30)
        
        try:
            from core.checkin_analytics import CheckinAnalytics
            analytics = CheckinAnalytics()
            
            energy_data = analytics.get_energy_trends(user_id, days)
            if 'error' in energy_data:
                return InteractionResponse("You don't have enough energy data for analysis yet. Try completing some check-ins first!", True)
            
            response = f"**⚡ Energy Trends (Last {days} days):**\n\n"
            response += f"📈 **Average Energy:** {energy_data.get('average_energy', 0)}/5\n"
            response += f"📊 **Energy Range:** {energy_data.get('min_energy', 0)} - {energy_data.get('max_energy', 0)}/5\n"
            response += f"📉 **Trend:** {energy_data.get('trend', 'Stable')}\n\n"
            
            # Show energy distribution
            distribution = energy_data.get('energy_distribution', {})
            if distribution:
                response += "**Energy Distribution:**\n"
                for energy_level, count in distribution.items():
                    response += f"• {energy_level}: {count} days\n"
            
            # Add insights
            avg_energy = energy_data.get('average_energy', 0)
            if avg_energy >= 4:
                response += "\n💡 **Insight:** Your energy levels have been consistently high!\n"
            elif avg_energy <= 2:
                response += "\n💡 **Insight:** Your energy levels have been low - consider rest and self-care.\n"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing energy trends for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your energy trends right now. Please try again.", True)
    
    @handle_errors("showing habit analysis", default_return=InteractionResponse("I'm having trouble showing your habit analysis. Please try again.", True))
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
    
    @handle_errors("showing sleep analysis", default_return=InteractionResponse("I'm having trouble showing your sleep analysis. Please try again.", True))
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
    
    @handle_errors("showing wellness score", default_return=InteractionResponse("I'm having trouble showing your wellness score. Please try again.", True))
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
                # Convert mood and energy from 0-100 back to 1-5 scale for display
                from core.checkin_analytics import CheckinAnalytics
                mood_score_5 = CheckinAnalytics.convert_score_100_to_5(components.get('mood_score', 0))
                energy_score_5 = CheckinAnalytics.convert_score_100_to_5(components.get('energy_score', 0))
                response += f"😊 **Mood Score:** {mood_score_5}/5\n"
                response += f"⚡ **Energy Score:** {energy_score_5}/5\n"
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
    
    @handle_errors("showing check-in history", default_return=InteractionResponse("I'm having trouble showing your check-in history. Please try again.", True))
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
                energy = checkin.get('energy', 'No energy recorded')
                
                # Display mood and energy together if both are available
                if energy != 'No energy recorded':
                    response += f"📅 {date}: 😊 Mood {mood}/5 | ⚡ Energy {energy}/5\n"
                else:
                    response += f"📅 {date}: 😊 Mood {mood}/5\n"
            
            if len(checkin_history) > 5:
                response += f"... and {len(checkin_history) - 5} more check-ins\n"
            
            return InteractionResponse(response, True)
            
        except Exception as e:
            logger.error(f"Error showing check-in history for user {user_id}: {e}")
            return InteractionResponse("I'm having trouble showing your check-in history right now. Please try again.", True)
    
    @handle_errors("showing completion rate", default_return=InteractionResponse("I'm having trouble showing your completion rate. Please try again.", True))
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
    
    @handle_errors("getting field scale", default_return=None)
    def _get_field_scale(self, field: str) -> int:
        """Determine the scale for a field (1-5 scale, or None for other types)
        
        Returns:
            int: Scale value (5 for 1-5 scale fields, None for other types)
        """
        # Fields that use 1-5 scale
        scale_1_5_fields = [
            'mood', 'energy', 'stress_level', 'sleep_quality', 'anxiety_level', 
            'focus_level'
        ]
        
        if field in scale_1_5_fields:
            return 5
        
        # Other fields (sleep_hours, yes/no fields) don't have a scale
        return None

    @handle_errors("getting analytics help", default_return="Help with analytics - view analytics and insights about your wellness patterns")
    def get_help(self) -> str:
        return "Help with analytics - view analytics and insights about your wellness patterns"
    
    @handle_errors("getting analytics examples", default_return=[])
    def get_examples(self) -> List[str]:
        return [
            "show analytics",
            "mood trends",
            "energy trends",
            "habit analysis",
            "sleep analysis",
            "wellness score",
            "checkin history",
            "completion rate"
        ]

# Registry of all interaction handlers
INTERACTION_HANDLERS = {
    'TaskManagementHandler': TaskManagementHandler(),
    'CheckinHandler': CheckinHandler(),
    'ProfileHandler': ProfileHandler(),
    'HelpHandler': HelpHandler(),
    'ScheduleManagementHandler': ScheduleManagementHandler(),
    'AnalyticsHandler': AnalyticsHandler(),
}

@handle_errors("getting interaction handler", default_return=None)
def get_interaction_handler(intent: str) -> Optional[InteractionHandler]:
    """Get the appropriate handler for an intent"""
    for handler in INTERACTION_HANDLERS.values():
        if handler.can_handle(intent):
            return handler
    return None

@handle_errors("getting all handlers", default_return={})
def get_all_handlers() -> Dict[str, InteractionHandler]:
    """Get all registered handlers"""
    return INTERACTION_HANDLERS.copy() 
