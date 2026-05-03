# Explicit result for outbound message sends (replaces ad hoc string returns + _last_sent_message).

from __future__ import annotations

from dataclasses import dataclass

from core.error_handling import handle_errors


@dataclass(frozen=True)
class MessageSendResult:
    """Outcome of ``CommunicationManager.handle_message_sending``."""

    status: str  # sent | failed | deferred | skipped
    user_id: str
    category: str
    sent_text: str | None = None

    @classmethod
    @handle_errors(
        "building deferred send result", user_friendly=False, re_raise=True
    )
    def deferred(cls, user_id: str, category: str) -> MessageSendResult:
        """Result when a scheduled send is deferred (e.g. user mid-conversation flow)."""
        return cls(status="deferred", user_id=user_id, category=category, sent_text=None)

    @classmethod
    @handle_errors(
        "building skipped send result", user_friendly=False, re_raise=True
    )
    def skipped(cls, user_id: str, category: str) -> MessageSendResult:
        """Result when no message was sent but the run completed without transport error."""
        return cls(status="skipped", user_id=user_id, category=category, sent_text=None)

    @classmethod
    @handle_errors(
        "building failed send result", user_friendly=False, re_raise=True
    )
    def failed(cls, user_id: str = "", category: str = "") -> MessageSendResult:
        """Result when sending failed or prerequisites were missing."""
        return cls(status="failed", user_id=user_id, category=category, sent_text=None)

    @classmethod
    @handle_errors(
        "building sent message result", user_friendly=False, re_raise=True
    )
    def sent(
        cls,
        user_id: str,
        category: str,
        sent_text: str | None = None,
    ) -> MessageSendResult:
        """Result when a message was accepted for delivery (content may be None for some paths)."""
        return cls(
            status="sent",
            user_id=user_id,
            category=category,
            sent_text=sent_text,
        )

    @handle_errors(
        "matching send result to request", user_friendly=False, re_raise=True
    )
    def matches_request(self, user_id: str, category: str) -> bool:
        """True if this result applies to the given test-send request identity."""
        return self.user_id == user_id and self.category == category
