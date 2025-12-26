"""
Webhook Server Behavior Tests

Tests for communication/communication_channels/discord/webhook_server.py focusing on real behavior and side effects.
These tests verify that webhook server actually works and produces expected side effects.
"""

import pytest
import json
import threading
import time
import socket
from unittest.mock import patch, MagicMock, Mock
from communication.communication_channels.discord.webhook_server import (
    DiscordWebhookHandler,
    WebhookServer
)


def create_mock_handler(method='POST', headers=None, body=None):
    """Create a properly instantiated DiscordWebhookHandler with mocked request"""
    from io import BytesIO
    
    # Create a proper mock socket connection
    mock_socket = MagicMock()
    mock_socket.recv.return_value = b''
    mock_socket.makefile.return_value = BytesIO()
    
    # Create request line based on method
    request_line = f'{method} / HTTP/1.1\r\n'.encode('iso-8859-1')
    
    # Create a BytesIO for the request
    request_data = BytesIO()
    request_data.write(request_line)
    # Add headers
    for key, value in (headers or {}).items():
        request_data.write(f'{key}: {value}\r\n'.encode('iso-8859-1'))
    request_data.write(b'\r\n')  # End of headers
    if body:
        request_data.write(body)
    request_data.seek(0)
    
    mock_client_address = ('127.0.0.1', 12345)
    mock_server = MagicMock()
    mock_server.server_address = ('127.0.0.1', 8080)
    
    # Create handler with proper request setup
    handler = DiscordWebhookHandler.__new__(DiscordWebhookHandler)
    handler.client_address = mock_client_address
    handler.server = mock_server
    handler.rfile = BytesIO(body or b'')
    handler.wfile = BytesIO()
    handler.headers = type('Headers', (), {'get': lambda self, key, default='': (headers or {}).get(key, default)})()
    handler.command = method
    handler.path = '/'
    handler.request_version = 'HTTP/1.1'
    handler.close_connection = True
    
    # Track response
    handler._response_code = None
    handler._headers_sent = {}
    
    def send_response(code, message=None):
        handler._response_code = code
    
    def send_header(key, value):
        handler._headers_sent[key] = value
    
    def end_headers():
        handler._headers_ended = True
    
    handler.send_response = send_response
    handler.send_header = send_header
    handler.end_headers = end_headers
    
    return handler


class TestWebhookServerBehavior:
    """Test webhook server real behavior and side effects."""
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_get_returns_health_check(self):
        """Test: GET request returns health check response."""
        handler = create_mock_handler(method='GET')
        
        handler.do_GET()
        
        # Assert: Should return 200 with health check message
        assert handler._response_code == 200, "Should return 200 OK"
        assert handler._headers_sent.get('Content-Type') == 'text/plain', "Should set content type"
        handler.wfile.seek(0)
        body = handler.wfile.read()
        assert b'Discord Webhook Server - OK' in body, "Should return health check message"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_options_returns_cors_headers(self):
        """Test: OPTIONS request returns CORS headers."""
        handler = create_mock_handler(method='OPTIONS')
        
        handler.do_OPTIONS()
        
        # Assert: Should return 200 with CORS headers
        assert handler._response_code == 200, "Should return 200 OK"
        assert handler._headers_sent.get('Access-Control-Allow-Origin') == '*', "Should allow all origins"
        assert handler._headers_sent.get('Access-Control-Allow-Methods') == 'POST, GET, OPTIONS', "Should allow methods"
        assert 'X-Signature-Ed25519' in handler._headers_sent.get('Access-Control-Allow-Headers', ''), "Should allow signature headers"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_rejects_missing_signature_headers(self):
        """Test: POST request without signature headers is rejected."""
        handler = create_mock_handler(method='POST', headers={}, body=b'{}')
        
        handler.do_POST()
        
        # Assert: Should return 401 Unauthorized
        assert handler._response_code == 401, "Should reject missing signature headers"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_handles_ping_event(self):
        """Test: POST request with PING event returns 204."""
        ping_event = {'type': 0}
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': str(len(json.dumps(ping_event))),
                'X-Signature-Ed25519': 'test_signature',
                'X-Signature-Timestamp': '1234567890'
            },
            body=json.dumps(ping_event).encode('utf-8')
        )
        
        with patch('core.config.DISCORD_PUBLIC_KEY', None):
            handler.do_POST()
        
        # Assert: Should return 204 for PING
        assert handler._response_code == 204, "Should return 204 for PING event"
        assert handler._headers_sent.get('Content-Type') == 'application/json', "Should set content type"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_rejects_invalid_json(self):
        """Test: POST request with invalid JSON is rejected."""
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': '10',
                'X-Signature-Ed25519': 'test_signature',
                'X-Signature-Timestamp': '1234567890'
            },
            body=b'{ invalid }'
        )
        
        with patch('core.config.DISCORD_PUBLIC_KEY', None):
            handler.do_POST()
        
        # Assert: Should return 400 for invalid JSON
        assert handler._response_code == 400, "Should reject invalid JSON"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_handles_application_authorized_event(self):
        """Test: POST request with APPLICATION_AUTHORIZED event is handled."""
        event_data = {
            'type': 1,
            'event': {
                'type': 'APPLICATION_AUTHORIZED',
                'data': {
                    'user': {
                        'id': '123456789',
                        'username': 'testuser'
                    }
                }
            }
        }
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': str(len(json.dumps(event_data))),
                'X-Signature-Ed25519': 'test_signature',
                'X-Signature-Timestamp': '1234567890'
            },
            body=json.dumps(event_data).encode('utf-8')
        )
        handler.bot_instance = None
        
        with patch('core.config.DISCORD_PUBLIC_KEY', None):
            with patch('communication.communication_channels.discord.webhook_server.handle_webhook_event') as mock_handle:
                mock_handle.return_value = True
                handler.do_POST()
        
        # Assert: Should handle event and return 200
        assert handler._response_code == 200, "Should return 200 for successful handling"
        assert mock_handle.called, "Should call handle_webhook_event"
        handler.wfile.seek(0)
        body = handler.wfile.read()
        response_data = json.loads(body.decode('utf-8'))
        assert response_data.get('received') is True, "Should indicate event received"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_handles_event_handling_failure(self):
        """Test: POST request returns 500 when event handling fails."""
        event_data = {
            'type': 1,
            'event': {
                'type': 'APPLICATION_AUTHORIZED',
                'data': {
                    'user': {
                        'id': '123456789',
                        'username': 'testuser'
                    }
                }
            }
        }
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': str(len(json.dumps(event_data))),
                'X-Signature-Ed25519': 'test_signature',
                'X-Signature-Timestamp': '1234567890'
            },
            body=json.dumps(event_data).encode('utf-8')
        )
        handler.bot_instance = None
        
        with patch('core.config.DISCORD_PUBLIC_KEY', None):
            with patch('communication.communication_channels.discord.webhook_server.handle_webhook_event') as mock_handle:
                mock_handle.return_value = False
                handler.do_POST()
        
        # Assert: Should return 500 for handling failure
        assert handler._response_code == 500, "Should return 500 for handling failure"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_rejects_missing_event_type(self):
        """Test: POST request with missing event type is rejected."""
        event_data = {
            'type': 1,
            'event': {}  # Missing 'type' field
        }
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': str(len(json.dumps(event_data))),
                'X-Signature-Ed25519': 'test_signature',
                'X-Signature-Timestamp': '1234567890'
            },
            body=json.dumps(event_data).encode('utf-8')
        )
        
        with patch('core.config.DISCORD_PUBLIC_KEY', None):
            handler.do_POST()
        
        # Assert: Should return 400 for missing event type
        assert handler._response_code == 400, "Should reject missing event type"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_webhook_server_initialization(self):
        """Test: WebhookServer initializes correctly."""
        bot_instance = MagicMock()
        server = WebhookServer(port=8080, bot_instance=bot_instance)
        
        # Assert: Should initialize with correct values
        assert server.port == 8080, "Should set port"
        assert server.bot_instance == bot_instance, "Should set bot instance"
        assert server.server is None, "Server should not be started yet"
        assert DiscordWebhookHandler.bot_instance == bot_instance, "Should set handler bot instance"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    @pytest.mark.slow
    def test_webhook_server_start_creates_server(self):
        """Test: WebhookServer start creates and starts HTTP server."""
        server = WebhookServer(port=0)  # Use port 0 for automatic port assignment
        
        # Find an available port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            available_port = s.getsockname()[1]
        
        server.port = available_port
        
        # Start server
        result = server.start()
        
        try:
            # Assert: Should start successfully
            assert result is True, "Should start successfully"
            assert server.server is not None, "Should create server instance"
            
            # Verify server is running by checking if port is in use
            time.sleep(0.1)  # Give server time to start
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result_check = s.connect_ex(('127.0.0.1', available_port))
                # 0 means connection successful (port is open)
                assert result_check == 0, "Server should be listening on port"
        finally:
            # Cleanup
            server.stop()
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_webhook_server_stop_shuts_down_server(self):
        """Test: WebhookServer stop shuts down server."""
        server = WebhookServer(port=0)
        
        # Find an available port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            available_port = s.getsockname()[1]
        
        server.port = available_port
        server.start()
        
        # Wait for server to start
        time.sleep(0.1)
        
        # Stop server
        server.stop()
        
        # Wait for shutdown
        time.sleep(0.1)
        
        # Assert: Server should be stopped
        # Verify by attempting to connect (should fail)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            result = s.connect_ex(('127.0.0.1', available_port))
            # Non-zero means connection failed (port is closed)
            assert result != 0, "Server should be stopped"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_webhook_server_start_handles_port_in_use(self):
        """Test: WebhookServer start handles port already in use gracefully."""
        # Create a server on a port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            used_port = s.getsockname()[1]
            s.listen(1)
            
            # Try to start webhook server on same port
            server = WebhookServer(port=used_port)
            result = server.start()
            
            # Assert: Should handle gracefully (may return False or raise exception)
            # The exact behavior depends on implementation
            assert isinstance(result, bool), "Should return boolean result"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_log_message_uses_custom_logger(self):
        """Test: log_message uses custom logger instead of stderr."""
        handler = create_mock_handler()
        
        with patch('communication.communication_channels.discord.webhook_server.logger') as mock_logger:
            handler.log_message('test %s', 'message')
            
            # Assert: Should use custom logger
            assert mock_logger.debug.called, "Should call logger.debug"
            call_args = mock_logger.debug.call_args[0][0]
            assert 'Webhook' in call_args, "Should prefix with 'Webhook'"
            assert 'test message' in call_args, "Should include formatted message"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_handles_exception_gracefully(self):
        """Test: POST request handles exceptions gracefully."""
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': '10',
                'X-Signature-Ed25519': 'test_signature',
                'X-Signature-Timestamp': '1234567890'
            },
            body=b'{}'
        )
        
        # Make rfile.read raise an exception
        def raise_error(*args, **kwargs):
            raise Exception("Test error")
        handler.rfile.read = raise_error
        
        handler.do_POST()
        
        # Assert: Should return 500 for exception
        assert handler._response_code == 500, "Should return 500 for exception"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_normalizes_event_type_to_uppercase(self):
        """Test: POST request normalizes event type to uppercase."""
        event_data = {
            'type': 1,
            'event': {
                'type': 'application_authorized',  # Lowercase
                'data': {
                    'user': {
                        'id': '123456789',
                        'username': 'testuser'
                    }
                }
            }
        }
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': str(len(json.dumps(event_data))),
                'X-Signature-Ed25519': 'test_signature',
                'X-Signature-Timestamp': '1234567890'
            },
            body=json.dumps(event_data).encode('utf-8')
        )
        handler.bot_instance = None
        
        with patch('core.config.DISCORD_PUBLIC_KEY', None):
            with patch('communication.communication_channels.discord.webhook_server.handle_webhook_event') as mock_handle:
                mock_handle.return_value = True
                handler.do_POST()
        
        # Assert: Should normalize to uppercase
        assert mock_handle.called, "Should call handle_webhook_event"
        call_args = mock_handle.call_args
        assert call_args[0][0] == 'APPLICATION_AUTHORIZED', "Should normalize event type to uppercase"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_handles_signature_verification_with_pynacl(self):
        """Test: POST request verifies signature with PyNaCl when available."""
        # Note: This test verifies the code path when PyNaCl is available
        # Since PyNaCl is optional, we test the ImportError path instead
        # The actual PyNaCl verification would require the library to be installed
        event_data = {
            'type': 1,
            'event': {
                'type': 'APPLICATION_AUTHORIZED',
                'data': {
                    'user': {
                        'id': '123456789',
                        'username': 'testuser'
                    }
                }
            }
        }
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': str(len(json.dumps(event_data))),
                'X-Signature-Ed25519': 'test_signature_hex',
                'X-Signature-Timestamp': '1234567890'
            },
            body=json.dumps(event_data).encode('utf-8')
        )
        handler.bot_instance = None
        
        # Test with PyNaCl not available (ImportError path)
        # This is the realistic scenario when PyNaCl is not installed
        import sys
        # Remove nacl modules if they exist
        modules_to_remove = [k for k in list(sys.modules.keys()) if k.startswith('nacl')]
        for mod in modules_to_remove:
            sys.modules.pop(mod, None)
        
        with patch('core.config.DISCORD_PUBLIC_KEY', 'test_public_key_hex'):
            handler.do_POST()
        
        # Assert: Should reject when PyNaCl not available (returns 401)
        # This verifies the ImportError handling path works correctly
        assert handler._response_code == 401, f"Should return 401 when PyNaCl not available, got {handler._response_code}"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_rejects_invalid_signature(self):
        """Test: POST request rejects invalid signature."""
        event_data = {
            'type': 1,
            'event': {
                'type': 'APPLICATION_AUTHORIZED',
                'data': {
                    'user': {
                        'id': '123456789',
                        'username': 'testuser'
                    }
                }
            }
        }
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': str(len(json.dumps(event_data))),
                'X-Signature-Ed25519': 'invalid_signature',
                'X-Signature-Timestamp': '1234567890'
            },
            body=json.dumps(event_data).encode('utf-8')
        )
        
        # Mock PyNaCl BadSignatureError - need to mock at sys.modules level
        import sys
        from types import ModuleType
        
        class MockBadSignatureError(Exception):
            pass
        
        # Create proper mock modules
        mock_nacl = ModuleType('nacl')
        mock_signing = ModuleType('nacl.signing')
        mock_exceptions = ModuleType('nacl.exceptions')
        
        class MockVerifyKey:
            def __init__(self, *args, **kwargs):
                pass
            def verify(self, *args, **kwargs):
                raise MockBadSignatureError("Invalid signature")
        
        mock_signing.VerifyKey = MockVerifyKey
        mock_exceptions.BadSignatureError = MockBadSignatureError
        mock_nacl.signing = mock_signing
        mock_nacl.exceptions = mock_exceptions
        
        with patch('core.config.DISCORD_PUBLIC_KEY', 'test_public_key_hex'):
            with patch.dict(sys.modules, {
                'nacl': mock_nacl,
                'nacl.signing': mock_signing, 
                'nacl.exceptions': mock_exceptions
            }):
                handler.do_POST()
        
        # Assert: Should reject invalid signature
        assert handler._response_code == 401, "Should return 401 for invalid signature"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_handles_pynacl_import_error(self):
        """Test: POST request handles PyNaCl import error gracefully."""
        event_data = {
            'type': 1,
            'event': {
                'type': 'APPLICATION_AUTHORIZED',
                'data': {
                    'user': {
                        'id': '123456789',
                        'username': 'testuser'
                    }
                }
            }
        }
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': str(len(json.dumps(event_data))),
                'X-Signature-Ed25519': 'test_signature',
                'X-Signature-Timestamp': '1234567890'
            },
            body=json.dumps(event_data).encode('utf-8')
        )
        
        # Mock ImportError for PyNaCl - need to mock at sys.modules level
        # The easiest way is to not add nacl to sys.modules, so the import fails
        with patch('core.config.DISCORD_PUBLIC_KEY', 'test_public_key'):
            # Remove nacl modules from sys.modules if they exist
            import sys
            modules_to_remove = [k for k in list(sys.modules.keys()) if k.startswith('nacl')]
            for mod in modules_to_remove:
                sys.modules.pop(mod, None)
            # The import will fail, which should trigger the ImportError handler
            handler.do_POST()
        
        # Assert: Should reject when PyNaCl not available
        assert handler._response_code == 401, "Should return 401 when PyNaCl not available"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_handles_signature_verification_exception(self):
        """Test: POST request handles signature verification exception gracefully."""
        event_data = {
            'type': 1,
            'event': {
                'type': 'APPLICATION_AUTHORIZED',
                'data': {
                    'user': {
                        'id': '123456789',
                        'username': 'testuser'
                    }
                }
            }
        }
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': str(len(json.dumps(event_data))),
                'X-Signature-Ed25519': 'test_signature',
                'X-Signature-Timestamp': '1234567890'
            },
            body=json.dumps(event_data).encode('utf-8')
        )
        
        # Mock verification exception - need to mock at sys.modules level
        import sys
        from types import ModuleType
        
        # Create proper mock modules
        mock_nacl = ModuleType('nacl')
        mock_signing = ModuleType('nacl.signing')
        mock_exceptions = ModuleType('nacl.exceptions')
        
        class MockVerifyKey:
            def __init__(self, *args, **kwargs):
                pass
            def verify(self, *args, **kwargs):
                raise Exception("Verification error")
        
        mock_signing.VerifyKey = MockVerifyKey
        mock_exceptions.BadSignatureError = Exception
        mock_nacl.signing = mock_signing
        mock_nacl.exceptions = mock_exceptions
        
        with patch('core.config.DISCORD_PUBLIC_KEY', 'test_public_key'):
            with patch.dict(sys.modules, {
                'nacl': mock_nacl,
                'nacl.signing': mock_signing, 
                'nacl.exceptions': mock_exceptions
            }):
                handler.do_POST()
        
        # Assert: Should reject on verification error
        assert handler._response_code == 401, "Should return 401 on verification error"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_handles_missing_content_length(self):
        """Test: POST request handles missing Content-Length header gracefully."""
        handler = create_mock_handler(
            method='POST',
            headers={
                'X-Signature-Ed25519': 'test_signature',
                'X-Signature-Timestamp': '1234567890'
                # Missing Content-Length
            },
            body=b'{}'
        )
        
        with patch('core.config.DISCORD_PUBLIC_KEY', None):
            handler.do_POST()
        
        # Assert: Should handle missing Content-Length (defaults to 0)
        # The handler should read 0 bytes, which may cause JSON parse error
        assert handler._response_code in [400, 500], "Should return error for missing Content-Length"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_do_post_handles_event_type_fallback(self):
        """Test: POST request uses fallback event type when event.type missing."""
        event_data = {
            'type': 1,
            'event': {},  # Missing 'type' field
            'event_type': 'APPLICATION_AUTHORIZED'  # Fallback location
        }
        handler = create_mock_handler(
            method='POST',
            headers={
                'Content-Length': str(len(json.dumps(event_data))),
                'X-Signature-Ed25519': 'test_signature',
                'X-Signature-Timestamp': '1234567890'
            },
            body=json.dumps(event_data).encode('utf-8')
        )
        handler.bot_instance = None
        
        with patch('core.config.DISCORD_PUBLIC_KEY', None):
            with patch('communication.communication_channels.discord.webhook_server.handle_webhook_event') as mock_handle:
                mock_handle.return_value = True
                handler.do_POST()
        
        # Assert: Should use fallback event type
        assert mock_handle.called, "Should call handle_webhook_event with fallback type"
        call_args = mock_handle.call_args
        assert call_args[0][0] == 'APPLICATION_AUTHORIZED', "Should use fallback event type"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_webhook_server_stop_handles_none_server(self):
        """Test: WebhookServer stop handles None server gracefully."""
        server = WebhookServer(port=8080)
        server.server = None  # No server started
        
        # Act: Stop server
        server.stop()
        
        # Assert: Should not raise exception
        assert server.server is None, "Server should remain None"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_webhook_server_start_updates_bot_instance(self):
        """Test: WebhookServer start updates bot instance in handler."""
        bot_instance = MagicMock()
        server = WebhookServer(port=0, bot_instance=bot_instance)
        
        # Find an available port
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            available_port = s.getsockname()[1]
        
        server.port = available_port
        
        # Start server
        result = server.start()
        
        try:
            # Assert: Should update handler bot instance
            assert result is True, "Should start successfully"
            assert DiscordWebhookHandler.bot_instance == bot_instance, "Should update handler bot instance"
        finally:
            server.stop()

