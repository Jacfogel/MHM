"""Loopback-only webhook listener, published through an HTTPS reverse proxy."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("communication_manager")


class SmsWebhookServer:
    @handle_errors("binding SMS webhook server", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def __init__(self, transport, port):
        """Bind a loopback listener whose requests use the supplied transport validator."""
        class Handler(BaseHTTPRequestHandler):
            # devtools: ignore[unused-functions]: framework invokes this channel/HTTP override dynamically.
            # error_handling_exclude: pure framework accessor/no-op; no I/O or mutation.
            def log_message(self, format, *args):
                """Do not log request parameters or identifying URLs."""

            # devtools: ignore[unused-functions]: framework invokes this channel/HTTP override dynamically.
            @handle_errors("handling SMS webhook HTTP request", default_return=None, user_friendly=False, retry_after_recovery=False)
            def do_POST(self):
                """Validate bounded form input and return safe HTTP responses without logging content."""
                self.connection.settimeout(10)
                code = 400
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if size <= 0 or size > 16384:
                        code = 413
                    elif self.headers.get_content_type() != "application/x-www-form-urlencoded":
                        code = 415
                    else:
                        raw = self.rfile.read(size)
                        pairs = parse_qsl(raw.decode("utf-8"), keep_blank_values=True,
                                          strict_parsing=True, max_num_fields=100)
                        params = dict(pairs)
                        # Reject duplicate keys rather than validating one value
                        # while routing another; no proxy headers are trusted.
                        if len(params) == len(pairs):
                            code = transport.process(self.path, params, self.headers.get("X-Twilio-Signature", ""))
                except Exception:
                    logger.error("SMS webhook request could not be handled; no request content logged")
                    code = 503
                body = b"<Response/>" if code == 200 else b""
                self.send_response(code)
                self.send_header("Content-Type", "text/xml; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="sms-webhooks")

    @handle_errors("starting SMS webhook listener", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def start(self):
        """Start the bound webhook server on its background thread."""
        self.thread.start()

    @handle_errors("stopping SMS webhook listener", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def stop(self):
        """Stop the listener, release its socket, and wait briefly for its thread."""
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
