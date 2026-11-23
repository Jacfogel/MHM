"""Bounded loopback webhook endpoint for Meta verification and signed JSON."""

import hmac
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from core import config
from core.error_handling import handle_errors


class WhatsAppWebhookServer:
    @handle_errors("binding WhatsApp webhook", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def __init__(self, transport, port):
        class Handler(BaseHTTPRequestHandler):
            # devtools: ignore[unused-functions]: BaseHTTPRequestHandler invokes this override dynamically.
            # error_handling_exclude: suppress default logging of tokens, addresses, and request data.
            def log_message(self, format, *args):
                """Suppress request logging so webhook secrets and identifiers stay private."""
                pass

            # devtools: ignore[unused-functions]: BaseHTTPRequestHandler invokes this override dynamically.
            # error_handling_exclude: bounded HTTP callback owns its response boundary.
            def do_GET(self):
                """Validate Meta's webhook challenge without exposing the verify token."""
                parts = urlsplit(self.path)
                query = parse_qs(parts.query)
                valid = (parts.path == "/whatsapp/webhook" and query.get("hub.mode") == ["subscribe"]
                         and len(query.get("hub.verify_token", [])) == 1
                         and hmac.compare_digest(query["hub.verify_token"][0], config.WHATSAPP_VERIFY_TOKEN)
                         and len(query.get("hub.challenge", [])) == 1)
                body = query["hub.challenge"][0].encode() if valid else b""
                self.send_response(200 if valid else 403)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            # devtools: ignore[unused-functions]: BaseHTTPRequestHandler invokes this override dynamically.
            # error_handling_exclude: validate and translate all HTTP input failures without logging raw requests.
            def do_POST(self):
                """Accept bounded signed event bodies and return only safe HTTP status codes."""
                self.connection.settimeout(10)
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if self.path != "/whatsapp/webhook":
                        code = 404
                    elif size <= 0 or size > 131072:
                        code = 413
                    elif self.headers.get_content_type() != "application/json":
                        code = 415
                    else:
                        code = transport.process(self.rfile.read(size), self.headers.get("X-Hub-Signature-256", ""))
                except Exception:
                    code = 503
                self.send_response(code)
                self.send_header("Content-Length", "0")
                self.end_headers()

        self.server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="whatsapp-webhooks")

    @handle_errors("starting WhatsApp webhook", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def start(self):
        self.thread.start()

    @handle_errors("stopping WhatsApp webhook", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
