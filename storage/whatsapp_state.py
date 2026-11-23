"""WhatsApp receipts, consent, conversation windows, and pending notifications."""

from core.error_handling import handle_errors
from core.time_utilities import now_datetime_full
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
            db.execute("INSERT INTO pending VALUES (?, ?, ?, ?, ?, ?)", (identifier, phone, user_id, body, kind, task_id))

    @handle_errors("reading WhatsApp pending text", re_raise=True, user_friendly=False, retry_after_recovery=False)
    def pending(self, phone, user_id):
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
