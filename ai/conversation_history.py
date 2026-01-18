# conversation_history.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.time_utilities import now_timestamp_filename

# Route conversation history logs to AI component
history_logger = get_component_logger("ai_conversation")
logger = history_logger


@dataclass
class ConversationMessage:
    """A single message in a conversation"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: dict[str, Any] | None = None

    @handle_errors("post-initializing conversation message", default_return=None)
    def __post_init__(self):
        """Post-initialization setup"""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ConversationSession:
    """A conversation session with multiple messages"""

    session_id: str
    user_id: str
    start_time: datetime
    end_time: datetime | None = None
    messages: list[ConversationMessage] | None = None
    metadata: dict[str, Any] | None = None

    @handle_errors("post-initializing conversation session", default_return=None)
    def __post_init__(self):
        """Post-initialization setup"""
        if self.messages is None:
            self.messages = []
        if self.metadata is None:
            self.metadata = {}


class ConversationHistory:
    """Manages conversation history for AI interactions"""

    @handle_errors("initializing conversation history", default_return=None)
    def __init__(
        self, max_sessions_per_user: int = 10, max_messages_per_session: int = 50
    ):
        """Initialize the conversation history manager"""
        self.max_sessions_per_user = max_sessions_per_user
        self.max_messages_per_session = max_messages_per_session
        self._sessions: dict[str, list[ConversationSession]] = {}  # user_id -> sessions
        self._active_sessions: dict[str, ConversationSession] = (
            {}
        )  # user_id -> active session

    @handle_errors("starting conversation session", default_return=None)
    def start_session(self, user_id: str, session_id: str | None = None) -> str:
        """
        Start a new conversation session

        Args:
            user_id: User ID
            session_id: Optional custom session ID

        Returns:
            Session ID
        """
        try:
            if session_id is None:
                # Session IDs behave like identifiers/filenames: readable + Windows-safe
                session_id = f"{user_id}_{now_timestamp_filename()}"

            # End any existing active session
            if user_id in self._active_sessions:
                self.end_session(user_id)

            # Create new session
            session = ConversationSession(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
            )

            # Store session
            if user_id not in self._sessions:
                self._sessions[user_id] = []
            self._sessions[user_id].append(session)
            self._active_sessions[user_id] = session

            self._cleanup_old_sessions(user_id)

            logger.debug(
                f"Started conversation session {session_id} for user {user_id}"
            )
            return session_id

        except Exception as e:
            logger.error(f"Error starting session for user {user_id}: {e}")
            return None

    @handle_errors("ending conversation session")
    def end_session(self, user_id: str) -> bool:
        """
        End the active conversation session for a user

        Args:
            user_id: User ID

        Returns:
            True if session was ended successfully
        """
        try:
            if user_id in self._active_sessions:
                session = self._active_sessions[user_id]
                session.end_time = datetime.now()
                del self._active_sessions[user_id]

                logger.debug(
                    f"Ended conversation session {session.session_id} for user {user_id}"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error ending session for user {user_id}: {e}")
            return False

    @handle_errors("adding message to conversation", default_return=False)
    def add_message(
        self, user_id: str, role: str, content: str, metadata: dict[str, Any] = None
    ) -> bool:
        """
        Add a message to the active conversation session

        Args:
            user_id: User ID
            role: Message role ("user" or "assistant")
            content: Message content
            metadata: Optional message metadata

        Returns:
            True if message was added successfully
        """
        try:
            # Ensure there's an active session
            if user_id not in self._active_sessions:
                self.start_session(user_id)

            session = self._active_sessions[user_id]

            # Create message
            message = ConversationMessage(
                role=role,
                content=content,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )

            # Add to session
            if session.messages is None:
                session.messages = []
            session.messages.append(message)

            # Clean up if too many messages
            if (
                session.messages
                and len(session.messages) > self.max_messages_per_session
            ):
                # Keep only the most recent messages
                session.messages = session.messages[-self.max_messages_per_session :]

            # Note: store_chat_interaction is for check-ins/chat pairs, not generic chat history
            # If you want a general chat log, create a dedicated writer later

            logger.debug(
                f"Added {role} message to session {session.session_id} for user {user_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error adding message for user {user_id}: {e}")
            return False

    @handle_errors("getting conversation history", default_return=[])
    def get_history(
        self, user_id: str, limit: int | None = None, include_metadata: bool = False
    ) -> list[dict[str, Any]]:
        """
        Get conversation history for a user

        Args:
            user_id: User ID
            limit: Maximum number of messages to return
            include_metadata: Whether to include message metadata

        Returns:
            List of conversation messages
        """
        try:
            history = []

            # Get all sessions for user
            sessions = self._sessions.get(user_id, [])

            # Add messages from all sessions
            for session in sessions:
                if session.messages is None:
                    continue
                for message in session.messages:
                    msg_dict = {
                        "role": message.role,
                        "content": message.content,
                        "timestamp": message.timestamp.isoformat(),
                        "session_id": session.session_id,
                    }

                    if include_metadata:
                        msg_dict["metadata"] = message.metadata

                    history.append(msg_dict)

            # Sort by timestamp
            history.sort(key=lambda x: x["timestamp"])

            # Apply limit
            if limit:
                history = history[-limit:]

            return history

        except Exception as e:
            logger.error(f"Error getting history for user {user_id}: {e}")
            return []

    @handle_errors("getting recent messages", default_return=[])
    def get_recent_messages(
        self, user_id: str, count: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get recent conversation messages for a user

        Args:
            user_id: User ID
            count: Number of recent messages to return

        Returns:
            List of recent conversation messages
        """
        return self.get_history(user_id, limit=count)

    @handle_errors("getting active session", default_return=None)
    def get_active_session(self, user_id: str) -> ConversationSession | None:
        """
        Get the active conversation session for a user

        Args:
            user_id: User ID

        Returns:
            Active conversation session or None
        """
        return self._active_sessions.get(user_id)

    @handle_errors("getting session messages", default_return=[])
    def get_session_messages(
        self, user_id: str, session_id: str
    ) -> list[ConversationMessage]:
        """
        Get all messages from a specific session

        Args:
            user_id: User ID
            session_id: Session ID

        Returns:
            List of messages in the session
        """
        try:
            sessions = self._sessions.get(user_id, [])
            for session in sessions:
                if session.session_id == session_id:
                    if session.messages is None:
                        return []
                    return session.messages.copy()

            return []

        except Exception as e:
            logger.error(
                f"Error getting session messages for user {user_id}, session {session_id}: {e}"
            )
            return []

    @handle_errors("clearing conversation history")
    def clear_history(self, user_id: str) -> bool:
        """
        Clear all conversation history for a user

        Args:
            user_id: User ID

        Returns:
            True if history was cleared successfully
        """
        try:
            # End active session
            if user_id in self._active_sessions:
                self.end_session(user_id)

            # Clear sessions
            if user_id in self._sessions:
                del self._sessions[user_id]

            logger.info(f"Cleared conversation history for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error clearing history for user {user_id}: {e}")
            return False

    @handle_errors("deleting session")
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """
        Delete a specific conversation session

        Args:
            user_id: User ID
            session_id: Session ID to delete

        Returns:
            True if session was deleted successfully
        """
        try:
            sessions = self._sessions.get(user_id, [])

            # Find and remove session
            for i, session in enumerate(sessions):
                if session.session_id == session_id:
                    # If this is the active session, end it
                    if (
                        user_id in self._active_sessions
                        and self._active_sessions[user_id].session_id == session_id
                    ):
                        del self._active_sessions[user_id]

                    # Remove from sessions list
                    sessions.pop(i)
                    logger.info(f"Deleted session {session_id} for user {user_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error deleting session {session_id} for user {user_id}: {e}")
            return False

    @handle_errors("getting conversation summary", default_return="")
    def get_conversation_summary(
        self, user_id: str, session_id: str | None = None
    ) -> str:
        """
        Get a summary of conversation history

        Args:
            user_id: User ID
            session_id: Optional specific session ID

        Returns:
            Conversation summary string
        """
        try:
            if session_id:
                messages = self.get_session_messages(user_id, session_id)
            else:
                messages_data = self.get_recent_messages(user_id, count=20)
                messages = []
                for msg_data in messages_data:
                    messages.append(
                        ConversationMessage(
                            role=msg_data["role"],
                            content=msg_data["content"],
                            timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                        )
                    )

            if not messages:
                return "No conversation history available."

            # Create summary
            summary_parts = []
            summary_parts.append(f"Conversation Summary ({len(messages)} messages):")

            # Group by role
            user_messages = [msg for msg in messages if msg.role == "user"]
            assistant_messages = [msg for msg in messages if msg.role == "assistant"]

            summary_parts.append(f"- User messages: {len(user_messages)}")
            summary_parts.append(f"- Assistant messages: {len(assistant_messages)}")

            # Add recent topics (last few user messages)
            if user_messages:
                recent_topics = [
                    msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                    for msg in user_messages[-3:]
                ]
                summary_parts.append(f"- Recent topics: {', '.join(recent_topics)}")

            return "\n".join(summary_parts)

        except Exception as e:
            logger.error(f"Error getting conversation summary for user {user_id}: {e}")
            return "Error generating conversation summary."

    @handle_errors("cleaning up old sessions", user_friendly=False, default_return=None)
    def _cleanup_old_sessions(self, user_id: str):
        """Clean up old sessions for a user"""
        sessions = self._sessions.get(user_id, [])
        if len(sessions) > self.max_sessions_per_user:
            sessions_to_remove = len(sessions) - self.max_sessions_per_user
            sessions[:sessions_to_remove] = []

            logger.debug(
                f"Cleaned up {sessions_to_remove} old sessions for user {user_id}"
            )

    @handle_errors("getting conversation statistics", default_return={})
    def get_statistics(self, user_id: str) -> dict[str, Any]:
        """
        Get conversation statistics for a user

        Args:
            user_id: User ID

        Returns:
            Dictionary with conversation statistics
        """
        try:
            sessions = self._sessions.get(user_id, [])

            total_messages = sum(len(session.messages) for session in sessions)
            total_sessions = len(sessions)

            # Count messages by role
            user_messages = 0
            assistant_messages = 0

            for session in sessions:
                if session.messages is None:
                    continue
                for message in session.messages:
                    if message.role == "user":
                        user_messages += 1
                    elif message.role == "assistant":
                        assistant_messages += 1

            # Calculate average session length
            avg_session_length = (
                total_messages / total_sessions if total_sessions > 0 else 0
            )

            # Get active session info
            active_session = self._active_sessions.get(user_id)
            active_session_id = active_session.session_id if active_session else None

            return {
                "total_messages": total_messages,
                "total_sessions": total_sessions,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "avg_session_length": avg_session_length,
                "active_session_id": active_session_id,
                "has_active_session": active_session is not None,
            }

        except Exception as e:
            logger.error(f"Error getting statistics for user {user_id}: {e}")
            return {}


# Global conversation history instance
_conversation_history = None


@handle_errors("getting conversation history instance", default_return=None)
def get_conversation_history() -> ConversationHistory:
    """Get the global conversation history instance"""
    global _conversation_history
    if _conversation_history is None:
        _conversation_history = ConversationHistory()
    return _conversation_history
