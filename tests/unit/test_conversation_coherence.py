"""Unit tests for follow-up conversation alignment."""

import pytest

from ai.chat.conversation_coherence import (
    align_response_to_conversation_topic,
    detect_fact_follow_up_keys,
    extract_recent_user_topics,
    extract_stated_conversation_facts,
    reinforce_stated_facts_if_needed,
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


@pytest.mark.unit
@pytest.mark.ai
def test_extract_stated_favorite_color_fact():
    history = [{"user_message": "My favorite color is blue"}]
    facts = extract_stated_conversation_facts(history)
    assert facts.get("favorite_color") == "blue"


@pytest.mark.unit
@pytest.mark.ai
def test_detect_favorite_color_follow_up():
    assert "favorite_color" in detect_fact_follow_up_keys("What's my favorite color?")
    assert "favorite_color" in detect_fact_follow_up_keys(
        "Do you remember my favorite color?"
    )


@pytest.mark.unit
@pytest.mark.ai
def test_reinforce_stated_color_when_model_forgets():
    history = [{"user_message": "My favorite color is blue"}]
    reply = reinforce_stated_facts_if_needed(
        "What's my favorite color?",
        "I'm not sure what your favorite color is.",
        history,
    )
    assert "blue" in reply.lower()


@pytest.mark.unit
@pytest.mark.ai
def test_reinforce_leaves_reply_that_already_has_fact():
    history = [{"user_message": "My favorite color is blue"}]
    original = "You told me your favorite color is blue!"
    reply = reinforce_stated_facts_if_needed(
        "What's my favorite color?",
        original,
        history,
    )
    assert reply == original


@pytest.mark.unit
@pytest.mark.ai
def test_align_response_recalls_favorite_color_fact():
    history = [{"user_message": "My favorite color is blue"}]
    reply = align_response_to_conversation_topic(
        "What's my favorite color?",
        "Hmm, I don't think I know that yet.",
        history,
    )
    assert "blue" in reply.lower()
