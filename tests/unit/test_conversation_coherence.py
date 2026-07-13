"""Unit tests for follow-up conversation alignment."""

import pytest

from ai.chat.conversation_coherence import (
    align_response_to_conversation_topic,
    extract_recent_user_topics,
)


@pytest.mark.unit
@pytest.mark.ai
def test_extract_recent_user_topics_finds_books():
    history = [
        {"user_message": "I love reading books"},
        {"user_message": "Thanks"},
    ]
    assert "books" in extract_recent_user_topics(history)


@pytest.mark.unit
@pytest.mark.ai
def test_align_response_adds_book_context_for_genre_follow_up():
    history = [{"user_message": "I love reading books"}]
    reply = align_response_to_conversation_topic(
        "What genres would I like?",
        "That sounds great! How can I help you today?",
        history,
    )
    assert "book" in reply.lower()


@pytest.mark.unit
@pytest.mark.ai
def test_align_response_leaves_on_topic_reply_unchanged():
    history = [{"user_message": "I love reading books"}]
    reply = align_response_to_conversation_topic(
        "What genres would I like?",
        "Since you enjoy books, you might like mystery or sci-fi.",
        history,
    )
    assert reply.startswith("Since you enjoy books")


@pytest.mark.unit
@pytest.mark.ai
def test_align_response_skips_unrelated_follow_up():
    history = [{"user_message": "I love reading books"}]
    reply = align_response_to_conversation_topic(
        "What tasks do I have today?",
        "You have two tasks due.",
        history,
    )
    assert reply == "You have two tasks due."
