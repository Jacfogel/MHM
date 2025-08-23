# schedule_handler.py

from typing import Dict, Any, List

from core.logger import get_component_logger
from core.error_handling import handle_errors
from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand

# Route schedule logs to command handlers component
schedule_logger = get_component_logger('schedule_handler')
logger = schedule_logger

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
        
        try:
            from core.schedule_management import get_schedule_time_periods, set_schedule_periods
            
            # Get existing periods
            periods = get_schedule_time_periods(user_id, category)
            
            if period_name not in periods:
                return InteractionResponse(
                    f"Schedule period '{period_name}' not found in {category.title()}. "
                    f"Available periods: {', '.join(periods.keys())}",
                    True
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
                    True
                )
                
        except Exception as e:
            logger.error(f"Error editing schedule period for user {user_id}: {e}")
            return InteractionResponse(f"I'm having trouble editing the schedule period: {str(e)}", True)
    
    def get_help(self) -> str:
        return "Help with schedule management - manage your message, task, and check-in schedules"
    
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
