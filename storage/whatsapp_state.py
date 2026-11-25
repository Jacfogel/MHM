"""WhatsApp receipts, consent, conversation windows, and pending notifications."""

from core.error_handling import handle_errors
from core.time_utilities import now_datetime_full, now_timestamp_full, format_timestamp, TIMESTAMP_FULL
from datetime import timedelta
from storage.sms_state import SmsState


class WhatsAppState(SmsState):
    """Reuse transactional phone-channel primitives in a separate database."""

    @handle_errors("opening WhatsApp state", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def __init__(self, path=None):
        super().__init__(path or "whatsapp_state.sqlite3")
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (phone TEXT PRIMARY KEY, last_inbound INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS pending (
                    id TEXT PRIMARY KEY, phone TEXT NOT NULL, user_id TEXT NOT NULL,
                    body TEXT NOT NULL, kind TEXT NOT NULL, task_id TEXT NOT NULL);
            """)
            if "created" not in {row[1] for row in db.execute("PRAGMA table_info(pending)")}:
                db.execute("ALTER TABLE pending ADD COLUMN created TEXT NOT NULL DEFAULT ''")
                db.execute("UPDATE pending SET created=? WHERE created=''", (now_timestamp_full(),))

    @handle_errors("recording WhatsApp window", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def record_inbound(self, phone, timestamp):
        with self.connection() as db:
            db.execute("INSERT INTO sessions VALUES (?, ?) ON CONFLICT(phone) DO UPDATE SET last_inbound=MAX(last_inbound, excluded.last_inbound)", (phone, timestamp))

    @handle_errors("checking WhatsApp window", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def window_open(self, phone):
        with self.connection() as db:
            row = db.execute("SELECT last_inbound FROM sessions WHERE phone=?", (phone,)).fetchone()
        return bool(row and 0 <= now_datetime_full().timestamp() - row[0] < 86400)

    @handle_errors("saving WhatsApp pending text", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def save_pending(self, identifier, phone, user_id, body, kind, task_id):
        with self.connection() as db:
            db.execute("INSERT INTO pending VALUES (?, ?, ?, ?, ?, ?, ?)", (identifier, phone, user_id, body, kind, task_id, now_timestamp_full()))

    @handle_errors("reading WhatsApp pending text", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def pending(self, phone, user_id):
        self.cleanup_retention()
        with self.connection() as db:
            return db.execute("SELECT id, body, kind, task_id FROM pending WHERE phone=? AND user_id=? ORDER BY rowid", (phone, user_id)).fetchall()

    @handle_errors("clearing WhatsApp pending text", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def remove_pending(self, identifier):
        with self.connection() as db:
            db.execute("DELETE FROM pending WHERE id=?", (identifier,))

    @handle_errors("clearing former WhatsApp recipient text", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def clear_former_pending(self, user_id, phone):
        with self.connection() as db:
            db.execute("DELETE FROM pending WHERE user_id=? AND phone<>?", (user_id, phone))

    @handle_errors("recording WhatsApp delivery", re_raise=True, user_friendly=False, retry_after_recovery=False)
    # devtools: intentional[duplicate-functions]: provider-delivery-state-progression
    def update_status(self, sid, status, error=""):
        """Advance a WhatsApp receipt without regressing terminal provider states."""
        ranks = {"accepted": 0, "sent": 1, "delivered": 2, "read": 3, "failed": 3}
        if status not in ranks:
            return False
        with self.connection() as db:
            row = db.execute("SELECT status FROM outbound WHERE sid=?", (sid,)).fetchone()
            if row and (row[0] in {"read", "failed"} or ranks.get(row[0], 0) >= ranks[status]):
                return False
            from core.time_utilities import now_timestamp_full
            db.execute("INSERT INTO outbound VALUES (?, ?, ?, ?) ON CONFLICT(sid) DO UPDATE SET status=excluded.status, error=excluded.error, updated=excluded.updated", (sid, status, error, now_timestamp_full()))
        return True

    @handle_errors("disconnecting WhatsApp enrollment", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def disconnect_enrollment(self, user_id):
        super().disconnect_enrollment(user_id)
        with self.connection() as db:
            db.execute("DELETE FROM pending WHERE user_id=?", (user_id,))


    @handle_errors("exporting WhatsApp account records", re_raise=True, user_friendly=False)
    def export_user(self, user_id):
        result = super().export_user(user_id)
        with self.connection() as db:
            import sqlite3
            db.row_factory = sqlite3.Row
            result["pending"] = [dict(row) for row in db.execute("SELECT * FROM pending WHERE user_id=?", (user_id,))]
            result["sessions"] = [dict(row) for row in db.execute("SELECT s.* FROM sessions s JOIN enrollments e ON e.phone=s.phone WHERE e.user_id=?", (user_id,))]
        return result

    @handle_errors("deleting WhatsApp account records", re_raise=True, user_friendly=False)
    def delete_user(self, user_id):
        with self.connection() as db:
            db.execute("DELETE FROM sessions WHERE phone IN (SELECT phone FROM enrollments WHERE user_id=?)", (user_id,))
            db.execute("DELETE FROM sessions WHERE phone IN (SELECT phone FROM user_phones WHERE user_id=? AND phone NOT IN (SELECT phone FROM enrollments WHERE user_id<>?))", (user_id, user_id))
            db.execute("DELETE FROM pending WHERE user_id=?", (user_id,))
        super().delete_user(user_id)

    @handle_errors("cleaning WhatsApp pending retention", re_raise=True, user_friendly=False)
    def cleanup_retention(self):
        super().cleanup_retention()
        from core.config import WHATSAPP_PENDING_RETENTION_HOURS
        cutoff = format_timestamp(now_datetime_full() - timedelta(hours=WHATSAPP_PENDING_RETENTION_HOURS), TIMESTAMP_FULL)
        with self.connection() as db:
            db.execute("DELETE FROM pending WHERE created<?", (cutoff,))
            db.execute("DELETE FROM sessions WHERE last_inbound<?", (int((now_datetime_full() - timedelta(hours=24)).timestamp()),))
