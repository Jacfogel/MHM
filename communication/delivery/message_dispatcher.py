# Predefined (library) message selection and send pipeline for CommunicationManager.

from __future__ import annotations

import random
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.message_management import get_recent_messages, load_user_messages, store_sent_message
from core.schedule_runtime import (
    get_current_day_names,
    get_current_time_periods_with_validation,
)

logger = get_component_logger("channel_orchestrator")


class PredefinedMessageDispatcher:
    """Loads, filters, selects, and sends predefined category messages."""

    @handle_errors(
        "initializing predefined message dispatcher", user_friendly=False, re_raise=True
    )
    def __init__(self, communication_manager: Any) -> None:
        self._cm = communication_manager

    @handle_errors("normalizing message-selection time periods", default_return=[])
    def normalize_message_selection_periods(
        self, matching_periods: list[str], valid_periods: list[str]
    ) -> list[str]:
        normalized_periods = matching_periods[:]
        if "ALL" in normalized_periods and len(normalized_periods) > 1:
            normalized_periods = [p for p in normalized_periods if p != "ALL"]
            logger.debug(
                f"MESSAGE_SELECTION: Removed 'ALL' from matching_periods, now: {normalized_periods}"
            )
        if not normalized_periods and "ALL" in valid_periods:
            normalized_periods = ["ALL"]
            logger.debug("MESSAGE_SELECTION: Using 'ALL' as fallback period")
        return normalized_periods

    @handle_errors("loading predefined messages library", default_return=None)
    def load_predefined_messages_library(
        self, user_id: str, category: str
    ) -> dict | None:
        messages = load_user_messages(user_id, category)
        if not messages:
            logger.error(
                f"MESSAGE_SELECTION_ERROR: No messages found for category {category} and user {user_id}."
            )
            return None
        return {"messages": messages}

    @handle_errors("filtering messages by day and period", default_return=[])
    def filter_messages_by_day_and_period(
        self,
        messages: list[dict],
        current_days: list[str],
        matching_periods: list[str],
    ) -> list[dict]:
        @handle_errors(
            "extracting message schedule fields", default_return=(["ALL"], ["ALL"])
        )
        def _schedule_fields(msg: dict[str, Any]) -> tuple[list[str], list[str]]:
            schedule = msg.get("schedule")
            if not isinstance(schedule, dict):
                return ["ALL"], ["ALL"]
            days = schedule.get("days")
            periods = schedule.get("periods")
            days_list = [d for d in (days or ["ALL"]) if isinstance(d, str)] or ["ALL"]
            periods_list = (
                [p for p in (periods or ["ALL"]) if isinstance(p, str)] or ["ALL"]
            )
            return days_list, periods_list

        return [
            msg
            for msg in messages
            if (
                lambda days, periods: ("ALL" in days or any(day in days for day in current_days))
                and ("ALL" in periods or any(period in periods for period in matching_periods))
            )(*_schedule_fields(msg))
        ]

    @handle_errors("deduplicating candidate messages", default_return=[])
    def deduplicate_candidate_messages(
        self, user_id: str, category: str, all_messages: list[dict]
    ) -> list[dict]:
        recent_messages = get_recent_messages(
            user_id, category=category, limit=50, days_back=60
        )
        recent_content = {
            msg.get("sent_text", "").strip().lower()
            for msg in recent_messages
            if msg.get("sent_text")
        }

        available_messages = []
        for msg in all_messages:
            message_content = msg.get("text", "").strip()
            if message_content and message_content.lower() not in recent_content:
                available_messages.append(msg)

        if not available_messages:
            logger.info(
                f"No messages available after deduplication for user {user_id}, category {category}. All time-period messages were sent recently."
            )
            return all_messages

        return available_messages

    @handle_errors("sending and storing predefined message", default_return=(False, None))
    def send_and_store_predefined_message(
        self,
        user_id: str,
        category: str,
        messaging_service: str,
        recipient: str,
        message_to_send: dict,
        matching_periods: list[str],
    ) -> tuple[bool, str | None]:
        success = self._cm.send_message_sync(
            messaging_service,
            recipient,
            str(message_to_send.get("text") or ""),
            user_id=user_id,
            category=category,
        )

        current_time_period = matching_periods[0] if matching_periods else None
        selected_message_content = str(message_to_send.get("text") or "")
        selected_message_id = str(message_to_send.get("id") or "")
        message_preview = (
            selected_message_content[:50] + "..."
            if len(selected_message_content) > 50
            else selected_message_content
        )

        if success:
            store_sent_message(
                user_id,
                category,
                selected_message_id,
                selected_message_content,
                time_period=current_time_period,
            )
            logger.info(
                f"Message sent successfully via {messaging_service} to {recipient} | User: {user_id}, Category: {category}, Period: {current_time_period} | Content: '{message_preview}'"
            )
            return True, selected_message_content

        logger.error(
            f"Message send failed via {messaging_service} to {recipient} | User: {user_id}, Category: {category}, Period: {current_time_period} | Content: '{message_preview}'"
        )
        return False, None

    @handle_errors("selecting weighted message", default_return="")
    def select_weighted_message(self, available_messages, matching_periods):
        if not available_messages or not isinstance(available_messages, list):
            logger.error(f"Invalid available_messages: {available_messages}")
            return ""

        if not matching_periods or not isinstance(matching_periods, list):
            logger.error(f"Invalid matching_periods: {matching_periods}")
            return ""

        if not available_messages:
            return None

        specific_period_messages = []
        all_period_messages = []

        for msg in available_messages:
            sched = msg.get("schedule") if isinstance(msg.get("schedule"), dict) else {}
            time_periods = sched.get("periods") or ["ALL"]
            if not isinstance(time_periods, list):
                time_periods = ["ALL"]
            has_specific_periods = any(period != "ALL" for period in time_periods)

            if has_specific_periods:
                specific_period_messages.append(msg)
            else:
                all_period_messages.append(msg)

        if specific_period_messages and random.random() < 0.7:
            selected_message = random.choice(specific_period_messages)
            logger.debug(
                "Selected message with specific time periods (weighted selection)"
            )
        elif all_period_messages:
            selected_message = random.choice(all_period_messages)
            logger.debug(
                "Selected message with 'ALL' time periods (weighted selection)"
            )
        else:
            selected_message = random.choice(available_messages)
            logger.debug("Selected message (fallback selection)")

        return selected_message

    @handle_errors("sending predefined message", default_return=(False, None))
    def send_predefined_message(
        self, user_id: str, category: str, messaging_service: str, recipient: str
    ) -> tuple[bool, str | None]:
        try:
            matching_periods, valid_periods = get_current_time_periods_with_validation(
                user_id, category
            )
            logger.debug(
                f"MESSAGE_SELECTION: User {user_id}, category {category} | Matching periods: {matching_periods}, Valid periods: {valid_periods}"
            )
            matching_periods = self.normalize_message_selection_periods(
                matching_periods, valid_periods
            )

            data = self.load_predefined_messages_library(user_id, category)
            if not data:
                return False, None

            current_days = get_current_day_names()
            logger.debug(f"MESSAGE_SELECTION: Current days: {current_days}")
            logger.debug(
                f"MESSAGE_SELECTION: Total messages in library: {len(data['messages'])}"
            )

            all_messages = self.filter_messages_by_day_and_period(
                data["messages"], current_days, matching_periods
            )

            if not all_messages:
                logger.warning(
                    f"MESSAGE_SELECTION_NO_MATCH: No messages found for user {user_id}, category {category} | Current days: {current_days}, Matching periods: {matching_periods}, Total messages: {len(data['messages'])}"
                )
                sample_messages = data["messages"][:3]
                for i, msg in enumerate(sample_messages):
                    sch = (
                        msg.get("schedule")
                        if isinstance(msg.get("schedule"), dict)
                        else {}
                    )
                    logger.debug(
                        f"MESSAGE_SELECTION_SAMPLE_{i}: days={sch.get('days')}, periods={sch.get('periods')}, text_preview='{str(msg.get('text', ''))[:50]}'"
                    )
                return False, None

            available_messages = self.deduplicate_candidate_messages(
                user_id, category, all_messages
            )
            if not available_messages:
                available_messages = all_messages
                logger.info(
                    f"Using fallback: selecting from all {len(available_messages)} time-period messages"
                )

            message_to_send = self.select_weighted_message(
                available_messages, matching_periods
            )
            logger.debug(
                f"Selected message for user {user_id}, category {category} from {len(available_messages)} available messages"
            )

            try:
                return self.send_and_store_predefined_message(
                    user_id,
                    category,
                    messaging_service,
                    recipient,
                    message_to_send,
                    matching_periods,
                )

            except Exception as send_error:
                logger.error(
                    f"Exception during message send for user {user_id}, category {category}: {send_error}"
                )
                return False, None

        except Exception as e:
            logger.error(
                f"Error in predefined message handling for user {user_id}, category {category}: {e}"
            )
            return False, None
