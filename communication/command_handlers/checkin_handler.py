# checkin_handler.py

from typing import Dict, Any, List

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.response_tracking import is_user_checkins_enabled, get_recent_checkins
from datetime import datetime, date
from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand

# Route checkin logs to command handlers component
checkin_logger = get_component_logger('checkin_handler')
logger = checkin_logger

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
                "Check-ins are not enabled for your account. Please contact an administrator to enable check-ins.",
                True
            )
        
        # Check if they've already done a check-in today
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
    
    def _handle_continue_checkin(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
        """Handle continuing a check-in"""
        # This would integrate with the existing conversation manager
        # For now, return a placeholder
        return InteractionResponse(
            "Check-in continuation not yet implemented. Please use the existing /checkin command.",
            True
        )
    
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
            response += f"📅 {date}: Mood {mood}/10\n"
        
        if len(recent_checkins) > 5:
            response += f"... and {len(recent_checkins) - 5} more"
        
        return InteractionResponse(response, True)
    
    def get_help(self) -> str:
        return "Help with check-ins - start check-ins and view your status"
    
    def get_examples(self) -> List[str]:
        return [
            "start checkin",
            "checkin status",
            "checkin"
        ]
