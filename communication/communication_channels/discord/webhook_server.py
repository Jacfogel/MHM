"""
Discord Webhook Server

HTTP server to receive Discord webhook events for user-installable apps.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Callable
from core.logger import get_component_logger
from core.error_handling import handle_errors
from communication.communication_channels.discord.webhook_handler import (
    verify_webhook_signature,
    parse_webhook_event,
    handle_webhook_event,
    EVENT_APPLICATION_AUTHORIZED
)

logger = get_component_logger('discord')


class DiscordWebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Discord webhook events"""
    
    bot_instance = None  # Will be set by WebhookServer
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr"""
        logger.debug(f"Webhook {format % args}")
    
    @handle_errors("handling webhook request", default_return=None)
    def do_POST(self):
        """Handle POST requests (Discord webhook events) - accepts any path"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # Get signature headers (Discord requires these for security)
            signature = self.headers.get('X-Signature-Ed25519', '')
            timestamp = self.headers.get('X-Signature-Timestamp', '')
            
            # Validate security headers are present
            if not signature or not timestamp:
                logger.warning("Webhook request missing security headers - rejecting")
                self.send_response(401)  # Unauthorized - required by Discord
                self.end_headers()
                return
            
            # Verify ed25519 signature using PyNaCl (Discord's recommended method)
            from core.config import DISCORD_PUBLIC_KEY
            if DISCORD_PUBLIC_KEY:
                try:
                    from nacl.signing import VerifyKey
                    from nacl.exceptions import BadSignatureError
                    
                    # Initialize verify key from public key (hex string)
                    verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
                    
                    # Verify signature: Discord signs timestamp + body
                    # Note: body is already bytes, decode to string then encode for verification
                    body_str = body.decode("utf-8") if isinstance(body, bytes) else body
                    message = f'{timestamp}{body_str}'.encode()
                    verify_key.verify(message, bytes.fromhex(signature))
                    
                    logger.debug("Webhook signature verified successfully")
                    
                except ImportError:
                    logger.error("PyNaCl not installed - cannot verify webhook signatures. Install with: pip install PyNaCl")
                    # Reject request if signature verification is required but library missing
                    self.send_response(401)
                    self.end_headers()
                    return
                except BadSignatureError:
                    logger.warning("Webhook signature verification failed - rejecting")
                    self.send_response(401)  # Unauthorized
                    self.end_headers()
                    return
                except Exception as e:
                    logger.error(f"Error verifying webhook signature: {e}")
                    # If verification fails due to error (not invalid signature), still reject
                    self.send_response(401)
                    self.end_headers()
                    return
            else:
                # Public key not configured - log warning but allow in dev mode
                logger.warning("DISCORD_PUBLIC_KEY not configured - skipping signature verification (dev mode)")
                # In production, this should reject: self.send_response(401)
            
            # Parse event
            event_data = parse_webhook_event(body.decode('utf-8'))
            if not event_data:
                self.send_response(400)
                self.end_headers()
                return
            
            # According to Discord docs: https://discord.com/developers/docs/events/webhook-events#webhook-event-payloads
            # Webhook event payloads have:
            # - 'type': numeric (always 1 for application events)
            # - 'event': object with 'type' field containing the actual event name (e.g., "APPLICATION_AUTHORIZED")
            # - 'data': object containing event-specific data (e.g., user info in 'data.user')
            
            event_type_raw = event_data.get('type')
            
            # Log full payload for debugging
            logger.debug(f"Webhook event payload: {json.dumps(event_data, indent=2)}")
            
            # Handle PING event (Discord sends this to validate the endpoint)
            # PING events have type 0, not type 1
            if event_type_raw == 0:
                logger.info("Received PING event from Discord - responding with 204")
                self.send_response(204)  # No Content - required for PING
                # Discord requires Content-Type header even for 204 responses
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                return
            
            # Get the actual event type from event.type field
            # This is where Discord puts the real event name (APPLICATION_AUTHORIZED, APPLICATION_DEAUTHORIZED, etc.)
            event_obj = event_data.get('event', {})
            event_type = event_obj.get('type', '')
            
            if not event_type:
                logger.warning(f"Webhook event missing 'event.type' field. Full payload: {json.dumps(event_data, indent=2)}")
                # Try fallback locations (shouldn't be needed, but just in case)
                event_type = event_data.get('event_type', '')
                if not event_type:
                    logger.error(f"Could not determine event type from payload")
                    self.send_response(400)
                    self.end_headers()
                    return
            
            # Normalize event type to uppercase
            event_type = event_type.upper()
            
            logger.info(f"Received webhook event: {event_type} (numeric type={event_type_raw})")
            
            # Handle the event
            success = handle_webhook_event(event_type, event_data, self.bot_instance)
            
            # Send response
            if success:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {'received': True}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                self.send_response(500)
                self.end_headers()
                
        except Exception as e:
            logger.error(f"Error handling webhook request: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
    
    def do_GET(self):
        """Handle GET requests (health check)"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Discord Webhook Server - OK')
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests (CORS preflight)"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Signature-Ed25519, X-Signature-Timestamp')
        self.end_headers()


class WebhookServer:
    """HTTP server for receiving Discord webhook events"""
    
    def __init__(self, port: int = 8080, bot_instance=None):
        """
        Initialize webhook server.
        
        Args:
            port: Port to listen on
            bot_instance: Discord bot instance (for sending DMs)
        """
        self.port = port
        self.server = None
        self.bot_instance = bot_instance
        DiscordWebhookHandler.bot_instance = bot_instance
    
    @handle_errors("starting webhook server", default_return=False)
    def start(self) -> bool:
        """Start the webhook server"""
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), DiscordWebhookHandler)
            DiscordWebhookHandler.bot_instance = self.bot_instance
            logger.info(f"Discord webhook server started on port {self.port}")
            
            # Start server in a separate thread
            import threading
            server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            server_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Failed to start webhook server: {e}")
            return False
    
    @handle_errors("stopping webhook server", default_return=None)
    def stop(self):
        """Stop the webhook server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Discord webhook server stopped")

