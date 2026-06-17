# communication/message_processing/flows/flow_state.py

"""Flow state persistence and lifecycle mixin."""

from datetime import timedelta
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import (
    DATE_ONLY,
    format_timestamp,
    now_datetime_full,
    now_timestamp_full,
    parse_timestamp_full,
)
from storage.runtime_state_storage import (
    get_runtime_state_path,
    load_runtime_state_json,
    save_runtime_state_json,
)

from communication.message_processing.flows.flow_constants import (
    CHECKIN_INACTIVITY_MINUTES,
    FLOW_CHECKIN,
    FLOW_NONE,
    POST_FLOW_COOLDOWN_MINUTES,
)

logger = get_component_logger("communication_manager")


class FlowStateMixin:
    @handle_errors("initializing conversation flow manager", default_return=None)
    def init_flow_state(self):
        # Store user states: { user_id: {"flow": FLOW_..., "state": int, "data": {}, "question_order": [] } }
        """Initialize flow state storage and load persisted user states."""
        self.user_states = {}
        self._checkin_order_cache: dict[str, dict[str, str | list[str]]] = {}
        self._flow_completion_timestamps: dict[str, str] = {}

        # Use BASE_DATA_DIR from config to respect test environment
        from core.config import BASE_DATA_DIR

        self._state_file = get_runtime_state_path(
            "conversation_states.json", base_dir=BASE_DATA_DIR
        ).resolve()

        self._load_user_states()
        self._expire_inactive_checkins()
    @handle_errors("loading user states from disk", default_return=None)
    def _load_user_states(self) -> None:
        """Load user states from disk with comprehensive logging"""
        if self._state_file.exists():
            self.user_states = load_runtime_state_json(self._state_file)

            # When no user states, log at DEBUG to reduce burst noise; INFO when there is state to track
            count = len(self.user_states)
            if count == 0:
                logger.debug(
                    f"FLOW_STATE_LOAD: Loaded 0 user states from disk | File: {str(self._state_file)}"
                )
            else:
                logger.info(
                    f"FLOW_STATE_LOAD: Loaded {count} user states from disk | File: {str(self._state_file)}"
                )

            for user_id, state in self.user_states.items():
                logger.info(
                    f"FLOW_STATE_LOAD: User {user_id} | flow={state.get('flow')}, state={state.get('state')}, "
                    f"question_index={state.get('current_question_index')}, questions={len(state.get('question_order', []))}"
                )
            self._normalize_loaded_flow_task_identifiers()
        else:
            logger.debug(
                f"FLOW_STATE_LOAD: No existing conversation states file found at {str(self._state_file)}"
            )
            self.user_states = {}

    # devtools: ignore[facade-shims]: persisted state migration for active user flow files
    @handle_errors("normalizing legacy flow task keys", default_return=None)
    def _normalize_loaded_flow_task_identifiers(self) -> None:
        """Move persisted legacy task key flow data to ``task_identifier`` and save once."""
        _legacy_flow_tid = "".join(("task", "_", "id"))
        dirty = False
        for state in self.user_states.values():
            data = state.get("data")
            if not isinstance(data, dict):
                continue
            legacy = data.get(_legacy_flow_tid)
            current = data.get("task_identifier")
            if legacy and not current:
                data["task_identifier"] = str(legacy).strip()
                data.pop(_legacy_flow_tid, None)
                dirty = True
            elif legacy and current:
                data.pop(_legacy_flow_tid, None)
                dirty = True
        if dirty:
            self._save_user_states()
    @handle_errors("saving user states to disk", default_return=None)
    def _save_user_states(self) -> None:
        """Save user states to disk with comprehensive logging and error handling"""
        save_runtime_state_json(self._state_file, self.user_states)

        logger.debug(
            f"FLOW_STATE_SAVE: Saved {len(self.user_states)} user states to disk | File: {str(self._state_file)}"
        )
        for user_id, state in self.user_states.items():
            logger.debug(
                f"FLOW_STATE_SAVE: User {user_id} | flow={state.get('flow')}, state={state.get('state')}, "
                f"question_index={state.get('current_question_index')}"
            )
    @handle_errors("resolving task flow identifier", default_return="")
    def _get_task_flow_identifier(self, user_state: dict[str, Any]) -> str:
        """Get canonical task identifier from flow state."""
        data = user_state.get("data") if isinstance(user_state, dict) else {}
        if not isinstance(data, dict):
            return ""

        return str(data.get("task_identifier") or "").strip()
    @handle_errors("marking flow completion", default_return=None)
    def _mark_flow_completion(self, user_id: str) -> None:
        """Record when a user flow completed to enforce post-flow cooldown."""
        if not user_id:
            return
        self._flow_completion_timestamps[user_id] = now_timestamp_full()
    @handle_errors("clearing flow state", default_return=None)
    def _clear_flow_state(self, user_id: str, mark_completion: bool = True) -> None:
        """Clear user flow state and optionally mark completion timestamp."""
        self.user_states.pop(user_id, None)
        if mark_completion:
            self._mark_flow_completion(user_id)
        self._save_user_states()
    @handle_errors("checking active flow state", default_return=False)
    def has_active_flow(self, user_id: str) -> bool:
        """Return True when user currently has an active non-zero flow."""
        if not user_id:
            return False
        user_state = self.user_states.get(user_id)
        return bool(user_state and user_state.get("flow", FLOW_NONE) != FLOW_NONE)
    @handle_errors("checking post-flow cooldown", default_return=False)
    def is_within_post_flow_cooldown(
        self, user_id: str, cooldown_minutes: int = POST_FLOW_COOLDOWN_MINUTES
    ) -> bool:
        """Return True if user is still within post-flow cooldown window."""
        if not user_id:
            return False
        completion_ts = self._flow_completion_timestamps.get(user_id)
        if not completion_ts:
            return False

        completion_dt = parse_timestamp_full(completion_ts)
        if completion_dt is None:
            return False
        return now_datetime_full() - completion_dt <= timedelta(minutes=cooldown_minutes)
    @handle_errors("getting flow block reason", default_return=None)
    def get_flow_block_reason(
        self, user_id: str, cooldown_minutes: int = POST_FLOW_COOLDOWN_MINUTES
    ) -> str | None:
        """Return active flow or cooldown block reason for scheduled sends."""
        if self.has_active_flow(user_id):
            return "active_flow"
        if self.is_within_post_flow_cooldown(user_id, cooldown_minutes):
            return "post_flow_cooldown"
        return None
    @handle_errors("expiring inactive check-in states", default_return=None)
    def _expire_inactive_checkins(self, user_id: str | None = None) -> None:
        """Remove stale check-in flows that have been idle beyond the allowed window."""
        expired_users: list[str] = []
        now = now_datetime_full()

        for uid, state in list(self.user_states.items()):
            if user_id and uid != user_id:
                continue

            if state.get("flow") != FLOW_CHECKIN:
                continue

            last_ts = state.get("last_activity")
            if not last_ts:
                continue

            # last_activity is internal persisted state (string timestamp).
            # Parse strictly using canonical helper.
            last_dt = parse_timestamp_full(last_ts)
            if last_dt is None:
                # If state is malformed, don't crash expiration sweeps.
                continue

            if now - last_dt > timedelta(minutes=CHECKIN_INACTIVITY_MINUTES):
                expired_users.append(uid)

        if not expired_users:
            return

        for uid in expired_users:
            try:
                self._cache_expired_checkin_order(uid, self.user_states.get(uid, {}))
                logger.info(
                    f"FLOW_STATE_EXPIRE: Expired stale check-in flow due to inactivity | "
                    f"user={uid} | threshold_minutes={CHECKIN_INACTIVITY_MINUTES}"
                )
            except Exception:
                continue

        self._save_user_states()
    @handle_errors("caching expired check-in order", default_return=None)
    def _cache_expired_checkin_order(self, user_id: str, user_state: dict) -> None:
        """Cache the question order for a same-day restart after expiration."""
        question_order = user_state.get("question_order", [])
        if not question_order:
            self._clear_flow_state(user_id, mark_completion=True)
            return

        started_at_str = user_state.get("started_at") or user_state.get("last_activity")
        started_dt = (
            parse_timestamp_full(started_at_str) if started_at_str else None
        ) or now_datetime_full()
        started_date = format_timestamp(started_dt, DATE_ONLY)

        self._checkin_order_cache[user_id] = {
            "order": question_order,
            "date": started_date,
        }
        self._clear_flow_state(user_id, mark_completion=True)
    @handle_errors("getting cached check-in order", default_return=None)
    def _get_cached_checkin_order(self, user_id: str) -> list[str] | None:
        """Return same-day cached question order if present and valid."""
        cache = self._checkin_order_cache.get(user_id)
        if not cache:
            return None

        cached_order = cache.get("order")
        cached_date = cache.get("date")
        if not cached_order or not cached_date:
            self._checkin_order_cache.pop(user_id, None)
            return None

        today = format_timestamp(now_datetime_full(), DATE_ONLY)
        if cached_date == today:
            return cached_order

        # Clean up stale cached order
        self._checkin_order_cache.pop(user_id, None)
        return None
    @handle_errors(
        "expiring check-in flow due to unrelated outbound", default_return=False
    )
    def expire_checkin_flow_due_to_unrelated_outbound(self, user_id: str) -> bool:
        """Expire an active check-in flow when an unrelated outbound message is sent.
        Safe no-op if no flow or different flow is active.
        """
        # Reload state from disk to avoid stale in-memory state preventing expiration
        self._load_user_states()

        user_state = self.user_states.get(user_id)
        if user_state and user_state.get("flow") == FLOW_CHECKIN:
            # Log details before expiration
            question_index = user_state.get("current_question_index", 0)
            total_questions = len(user_state.get("question_order", []))
            logger.info(
                f"FLOW_STATE_EXPIRE: Expiring active check-in flow for user {user_id} due to unrelated outbound message | Progress: {question_index}/{total_questions} questions"
            )

            # End the flow silently
            self._cache_expired_checkin_order(user_id, user_state)
            self._save_user_states()
            logger.info(
                f"FLOW_STATE_EXPIRE: Successfully expired and saved state for user {user_id}"
            )
            return True
        else:
            if not user_state:
                logger.debug(
                    f"FLOW_STATE_EXPIRE: No flow state found for user {user_id}, nothing to expire"
                )
            else:
                logger.debug(
                    f"FLOW_STATE_EXPIRE: User {user_id} has flow={user_state.get('flow')}, not check-in, skipping expiration"
                )
        return False
    @handle_errors(
        "clearing stuck flows",
        default_return=(
            "I'm having trouble clearing your flow state. Please try again.",
            True,
        ),
    )
    def clear_stuck_flows(self, user_id: str) -> tuple[str, bool]:
        """Clear any stuck conversation flows for a user."""
        existing_state = self.user_states.get(user_id)
        if existing_state:
            flow_type = existing_state.get("flow", "unknown")
            self._clear_flow_state(user_id, mark_completion=True)
            logger.info(f"Cleared stuck flow {flow_type} for user {user_id}")
            return (
                "Cleared stuck flow state. You can now use commands normally.",
                True,
            )
        return ("No active flow found to clear.", True)
