"""Transactional SMS receipts and opt-outs. No message bodies or credentials."""

import sqlite3

from core.error_handling import handle_errors
from contextlib import contextmanager

from storage.runtime_state_storage import get_runtime_state_path
from core.time_utilities import now_timestamp_full


class SmsState:
    """Durable claim-before-mutation receipts; a crash never replays a command."""

    @handle_errors("SMS state __init__", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def __init__(self, path=None):
        """Open the SMS state database and create its receipt tables."""
        self.path = get_runtime_state_path(path or "sms_state.sqlite3")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS inbound (
                    sid TEXT PRIMARY KEY, state TEXT NOT NULL, updated TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS optouts (
                    phone TEXT PRIMARY KEY, stopped INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS outbound (
                    sid TEXT PRIMARY KEY, status TEXT NOT NULL, error TEXT NOT NULL,
                    updated TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS contexts (
                    phone TEXT NOT NULL, kind TEXT NOT NULL, task_id TEXT NOT NULL,
                    PRIMARY KEY(phone, kind, task_id));
            """)

    @contextmanager
    # error_handling_exclude: generator transaction errors propagate to decorated storage operations; never swallow rollback failures.
    def connection(self):
        """Commit a successful transaction, roll back failures, and always close the connection."""
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    @handle_errors("SMS state claim", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def claim(self, sid):
        """Atomically claim an inbound ID; return false when it was already claimed."""
        with self.connection() as db:
            result = db.execute("INSERT OR IGNORE INTO inbound VALUES (?, 'processing', ?)", (sid, now_timestamp_full()))
            return result.rowcount == 1

    @handle_errors("SMS state finish", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def finish(self, sid, state):
        """Record the final handling outcome without allowing a command replay."""
        with self.connection() as db:
            db.execute("UPDATE inbound SET state=?, updated=? WHERE sid=?", (state, now_timestamp_full(), sid))

    @handle_errors("SMS state stopped", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def stopped(self, phone):
        """Return the durable opt-out flag; propagate storage failures to block sending."""
        with self.connection() as db:
            row = db.execute("SELECT stopped FROM optouts WHERE phone=?", (phone,)).fetchone()
            return bool(row and row[0])

    @handle_errors("SMS state set_stopped", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def set_stopped(self, phone, stopped):
        """Persist the recipient opt-out state before further messages are allowed."""
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO optouts VALUES (?, ?)", (phone, int(stopped)))

    @handle_errors("SMS state record_outbound", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def record_outbound(self, sid, status, error=""):
        """Record provider acceptance without overwriting an earlier status callback."""
        with self.connection() as db:
            db.execute("INSERT OR IGNORE INTO outbound VALUES (?, ?, ?, ?)", (sid, status, error, now_timestamp_full()))

    @handle_errors("SMS state update_status", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def update_status(self, sid, status, error=""):
        """Apply a known delivery state without regressing a terminal status."""
        ranks = {"accepted": 0, "queued": 1, "sending": 2, "sent": 3,
                 "delivered": 4, "undelivered": 4, "failed": 4, "canceled": 4}
        if status not in ranks:
            return False
        with self.connection() as db:
            row = db.execute("SELECT status FROM outbound WHERE sid=?", (sid,)).fetchone()
            if not row:
                db.execute("INSERT INTO outbound VALUES (?, ?, ?, ?)", (sid, status, error, now_timestamp_full()))
                return True
            if ranks.get(row[0], 0) >= 4 or ranks[status] < ranks.get(row[0], 0):
                return False
            db.execute("UPDATE outbound SET status=?, error=?, updated=? WHERE sid=?", (status, error, now_timestamp_full(), sid))
            return True

    @handle_errors("SMS state add_context", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def add_context(self, phone, kind, task_id=""):
        """Remember a possible task or check-in target before submitting its prompt."""
        with self.connection() as db:
            db.execute("INSERT OR IGNORE INTO contexts VALUES (?, ?, ?)", (phone, kind, task_id))

    @handle_errors("SMS state contexts", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def contexts(self, phone):
        """Read the possible prompt targets; never treat read failures as an empty list."""
        with self.connection() as db:
            return db.execute("SELECT kind, task_id FROM contexts WHERE phone=?", (phone,)).fetchall()

    @handle_errors("SMS state clear_context", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def clear_context(self, phone, kind, task_id):
        """Remove only the prompt context whose completion was confirmed."""
        with self.connection() as db:
            db.execute("DELETE FROM contexts WHERE phone=? AND kind=? AND task_id=?", (phone, kind, task_id))
