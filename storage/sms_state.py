"""Transactional SMS receipts and opt-outs. No message bodies or credentials."""

import sqlite3
import hashlib
import secrets
from datetime import timedelta

from core.error_handling import handle_errors
from contextlib import contextmanager

from storage.runtime_state_storage import get_runtime_state_path
from core.time_utilities import now_timestamp_full, now_datetime_full, format_timestamp, TIMESTAMP_FULL


class SmsState:
    """Durable claim-before-mutation receipts; a crash never replays a command."""

    @handle_errors("SMS state __init__", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def __init__(self, path=None):
        """Open the SMS state database and create its receipt tables."""
        self.path = get_runtime_state_path(path or "sms_state.sqlite3")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS enrollments (
                    phone TEXT PRIMARY KEY, user_id TEXT UNIQUE NOT NULL,
                    consent_at TEXT NOT NULL, verified_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS enrollment_challenges (
                    digest TEXT PRIMARY KEY, phone TEXT NOT NULL, owner TEXT NOT NULL,
                    created TEXT NOT NULL, expires TEXT NOT NULL, verified INTEGER NOT NULL DEFAULT 0);
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
    # devtools: intentional[duplicate-functions]: provider-delivery-state-progression
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

    @handle_errors("starting SMS enrollment", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def begin_enrollment(self, phone, owner=""):
        """Issue a short-lived random connection secret without sending an SMS."""
        from core.error_handling import ValidationError
        now = now_datetime_full()
        stamp = format_timestamp(now, TIMESTAMP_FULL)
        cutoff = format_timestamp(now - timedelta(seconds=60), TIMESTAMP_FULL)
        token = secrets.token_hex(16)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM enrollment_challenges WHERE expires<=?", (stamp,))
            if db.execute("SELECT 1 FROM enrollment_challenges WHERE (phone=? OR (owner<>'' AND owner=?)) AND created>?", (phone, owner, cutoff)).fetchone():
                raise ValidationError("Wait one minute before requesting another connection code.")
            db.execute("DELETE FROM enrollment_challenges WHERE phone=? AND owner=?", (phone, owner))
            db.execute("INSERT INTO enrollment_challenges VALUES (?, ?, ?, ?, ?, 0)", (
                hashlib.sha256(token.encode()).hexdigest(), phone, owner, stamp,
                format_timestamp(now + timedelta(minutes=15), TIMESTAMP_FULL),
            ))
        return token

    @handle_errors("verifying SMS enrollment", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def verify_enrollment(self, phone, token):
        """Accept proof only from a signature-validated incoming phone number."""
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.connection() as db:
            result = db.execute("UPDATE enrollment_challenges SET verified=1 WHERE digest=? AND phone=? AND expires>?", (digest, phone, now_timestamp_full()))
            return result.rowcount == 1

    @handle_errors("checking SMS enrollment proof", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def enrollment_verified(self, phone, token, owner=""):
        """Check a phone-bound proof without consuming it."""
        with self.connection() as db:
            return bool(db.execute("SELECT 1 FROM enrollment_challenges WHERE digest=? AND phone=? AND owner=? AND verified=1 AND expires>?", (hashlib.sha256(token.encode()).hexdigest(), phone, owner, now_timestamp_full())).fetchone())

    @handle_errors("saving SMS enrollment", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def bind_enrollment(self, user_id, phone, token, owner=""):
        """Atomically consume a proof and bind one phone to one consenting account."""
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            digest = hashlib.sha256(token.encode()).hexdigest()
            if not db.execute("SELECT 1 FROM enrollment_challenges WHERE digest=? AND phone=? AND owner=? AND verified=1 AND expires>?", (digest, phone, owner, now_timestamp_full())).fetchone():
                return False
            other = db.execute("SELECT user_id FROM enrollments WHERE phone=?", (phone,)).fetchone()
            if other and other[0] != user_id:
                return False
            previous = db.execute("SELECT phone FROM enrollments WHERE user_id=?", (user_id,)).fetchone()
            if previous and previous[0] != phone:
                db.execute("DELETE FROM contexts WHERE phone=?", (previous[0],))
            db.execute("DELETE FROM enrollments WHERE user_id=?", (user_id,))
            db.execute("INSERT INTO enrollments VALUES (?, ?, ?, ?)", (phone, user_id, now_timestamp_full(), now_timestamp_full()))
            db.execute("DELETE FROM enrollment_challenges WHERE digest=?", (digest,))
            return True

    @handle_errors("finding SMS enrollment", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def enrolled_user(self, phone):
        """Return the consenting account bound to a verified number."""
        with self.connection() as db:
            row = db.execute("SELECT user_id FROM enrollments WHERE phone=?", (phone,)).fetchone()
            return row[0] if row else None

    @handle_errors("disconnecting SMS enrollment", user_friendly=False, re_raise=True, retry_after_recovery=False)
    def disconnect_enrollment(self, user_id):
        """Revoke account enrollment while retaining phone opt-out and receipt history."""
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("SELECT phone FROM enrollments WHERE user_id=?", (user_id,)).fetchall()
            for row in rows:
                db.execute("DELETE FROM contexts WHERE phone=?", (row[0],))
            db.execute("DELETE FROM enrollments WHERE user_id=?", (user_id,))
            db.execute("DELETE FROM enrollment_challenges WHERE owner=?", (user_id,))
