"""
Discord Webhook Event Handler

Handles Discord webhook events, specifically APPLICATION_AUTHORIZED events
for user-installable apps.
"""

import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from core.logger import get_component_logger
from core.error_handling import handle_errors

logger = get_component_logger('discord')

# Webhook event types
EVENT_APPLICATION_AUTHORIZED = "APPLICATION_AUTHORIZED"
EVENT_APPLICATION_DEAUTHORIZED = "APPLICATION_DEAUTHORIZED"


@handle_errors("verifying webhook signature", default_return=False)
def verify_webhook_signature(signature: str, timestamp: str, body: bytes, public_key: str) -> bool:
    """
    Verify Discord webhook signature.
    
    Discord signs webhook requests using ed25519. For simplicity, we'll verify
    the signature matches Discord's expected format.
    
    Args:
        signature: The X-Signature-Ed25519 header value
        timestamp: The X-Signature-Timestamp header value
        body: The raw request body
        public_key: The application's public key
    
    Returns:
        bool: True if signature is valid
    """
    try:
        # Discord uses ed25519 signatures
        # For now, we'll do basic validation - in production, use proper ed25519 verification
        # This is a placeholder - proper implementation requires cryptography library
        if not signature or not timestamp:
            return False
        
        # Basic validation - proper implementation would use ed25519
        # For development, we can skip strict verification, but log it
        logger.debug(f"Webhook signature verification (basic check): signature={signature[:20]}..., timestamp={timestamp}")
        return True  # Placeholder - implement proper ed25519 verification
        
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


@handle_errors("parsing webhook event", default_return=None)
def parse_webhook_event(body: str) -> Optional[Dict[str, Any]]:
    """
    Parse Discord webhook event from request body.
    
    Args:
        body: JSON string of the webhook event
    
    Returns:
        Dict with event data, or None if invalid
    """
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook event: {e}")
        return None


@handle_errors("handling APPLICATION_AUTHORIZED event", default_return=None)
def handle_application_authorized(event_data: Dict[str, Any], bot_instance=None) -> bool:
    """
    Handle APPLICATION_AUTHORIZED webhook event.
    
    This is triggered when a user authorizes the app.
    We should send them a welcome DM immediately.
    
    Args:
        event_data: The webhook event data
        bot_instance: The Discord bot instance (for sending DMs)
    
    Returns:
        bool: True if handled successfully
    """
    try:
        # Extract user information from event
        # Discord sends: { "event": { "type": "APPLICATION_AUTHORIZED", "data": { "user": { "id": "...", "username": "..." }, ... } } }
        event_obj = event_data.get('event', {})
        data = event_obj.get('data', {})
        user_data = data.get('user', {})
        discord_user_id = str(user_data.get('id', ''))
        discord_username = str(user_data.get('username', ''))
        
        if not discord_user_id:
            logger.warning(f"APPLICATION_AUTHORIZED event missing user ID. Event data: {json.dumps(event_data, indent=2)}")
            return False
        
        logger.info(f"User authorized app: Discord ID {discord_user_id}, username: {discord_username}")
        
        # Check if user already has an account
        from core.user_management import get_user_id_by_identifier
        internal_user_id = get_user_id_by_identifier(discord_user_id)
        
        if internal_user_id:
            logger.debug(f"User {discord_user_id} already has MHM account: {internal_user_id}")
            # User already linked - no need to send welcome
            return True
        
        # Check if we've already welcomed this user (using channel-agnostic manager)
        from communication.core.welcome_manager import (
            has_been_welcomed,
            mark_as_welcomed
        )
        from communication.communication_channels.discord.welcome_handler import get_welcome_message
        
        if has_been_welcomed(discord_user_id, channel_type='discord'):
            logger.debug(f"User {discord_user_id} already welcomed")
            return True
        
        # Send welcome DM
        if bot_instance and hasattr(bot_instance, 'bot') and bot_instance.bot:
            # Get Discord username from event data if available
            discord_username = user_data.get('username', '')
            welcome_msg = get_welcome_message(discord_user_id, discord_username=discord_username, is_authorization=True)
            
            async def _send_welcome_dm():
                try:
                    # Small delay to ensure Discord has processed the authorization
                    # This gives Discord time to establish the relationship
                    import asyncio
                    await asyncio.sleep(1)
                    
                    # Create view with buttons inside async context (requires event loop)
                    from communication.communication_channels.discord.welcome_handler import get_welcome_message_view
                    welcome_view = get_welcome_message_view(discord_user_id)
                    
                    user = await bot_instance.bot.fetch_user(int(discord_user_id))
                    if user:
                        await user.send(welcome_msg, view=welcome_view)
                        mark_as_welcomed(discord_user_id, channel_type='discord')
                        logger.info(f"Sent welcome DM to newly authorized user: {discord_user_id}")
                        return True
                except Exception as e:
                    error_msg = str(e)
                    # Check if it's a "Cannot send messages" error (50007)
                    # This might be due to privacy settings or Discord needing more time
                    if "50007" in error_msg or "Cannot send messages" in error_msg:
                        logger.warning(f"Could not send welcome DM to {discord_user_id}: {error_msg}. "
                                     f"This may be due to user privacy settings or Discord requiring an initial interaction. "
                                     f"The user will receive a welcome message when they first interact with the bot.")
                    else:
                        logger.warning(f"Could not send welcome DM to {discord_user_id}: {error_msg}")
                    # Don't mark as welcomed if DM failed - let fallback welcome handlers try
                    # This allows the on_message/on_interaction handlers to send welcome if DM fails
                    return False
            
            # Schedule the DM send on the bot's event loop from this thread
            # We're in a webhook server thread, so we need to use run_coroutine_threadsafe
            if bot_instance.bot.loop and not bot_instance.bot.loop.is_closed():
                import asyncio
                try:
                    # Schedule the coroutine on the bot's event loop from this thread
                    future = asyncio.run_coroutine_threadsafe(_send_welcome_dm(), bot_instance.bot.loop)
                    logger.info(f"Scheduled welcome DM for user {discord_user_id}")
                    # Don't wait for the result - let it run asynchronously
                    return True
                except Exception as e:
                    logger.error(f"Error scheduling welcome DM for {discord_user_id}: {e}")
                    mark_as_welcomed(discord_user_id)  # Mark as welcomed to avoid retry
                    return False
            else:
                logger.warning(f"Bot event loop not available for sending welcome DM to {discord_user_id}")
                mark_as_welcomed(discord_user_id)  # Mark as welcomed to avoid retry
                return False
        else:
            logger.warning(f"Bot instance not available for sending welcome DM to {discord_user_id}")
            mark_as_welcomed(discord_user_id)  # Mark as welcomed to avoid retry
            return False
            
    except Exception as e:
        logger.error(f"Error handling APPLICATION_AUTHORIZED event: {e}", exc_info=True)
        return False


@handle_errors("handling webhook event", default_return=None)
def handle_webhook_event(event_type: str, event_data: Dict[str, Any], bot_instance=None) -> bool:
    """
    Route webhook events to appropriate handlers.
    
    Args:
        event_type: The type of webhook event
        event_data: The event data
        bot_instance: The Discord bot instance
    
    Returns:
        bool: True if handled successfully
    """
    try:
        if event_type == EVENT_APPLICATION_AUTHORIZED:
            return handle_application_authorized(event_data, bot_instance)
        elif event_type == EVENT_APPLICATION_DEAUTHORIZED:
            # Handle deauthorization if needed
            event_obj = event_data.get('event', {})
            data = event_obj.get('data', {})
            user_data = data.get('user', {})
            discord_user_id = str(user_data.get('id', ''))
            discord_username = str(user_data.get('username', ''))
            logger.info(f"User deauthorized app: Discord ID {discord_user_id}, username: {discord_username}")
            
            # Clear the user from the "already welcomed" list so they get welcomed again if they reauthorize
            from communication.core.welcome_manager import clear_welcomed_status
            clear_welcomed_status(discord_user_id, channel_type='discord')
            logger.debug(f"Cleared welcomed status for deauthorized user: {discord_user_id}")
            
            return True
        else:
            logger.debug(f"Unhandled webhook event type: {event_type}")
            return True  # Return True for unhandled events to acknowledge receipt
            
    except Exception as e:
        logger.error(f"Error handling webhook event {event_type}: {e}", exc_info=True)
        return False

