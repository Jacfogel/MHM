"""Unit tests for follow-up conversation alignment."""

import pytest
from typing import cast

from ai.chat.action_boundaries import UNCLEAR_USER_INPUT_REPLY
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
def test_align_response_repairs_unclear_book_genre_follow_up():
    history = [{"user_message": "I love reading books"}]
    reply = align_response_to_conversation_topic(
        "What genres do you think I'd like?",
        UNCLEAR_USER_INPUT_REPLY,
        history,
    )
    assert "books" in reply.lower()
    assert "mystery" in reply.lower()


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
def test_reinforce_keeps_only_grounded_fact_when_model_adds_provenance():
    history = [{"user_message": "My favorite color is blue"}]
    reply = reinforce_stated_facts_if_needed(
        "What's my favorite color?",
        "Your favorite color is blue. This was confirmed by a check-in.",
        history,
    )
    assert reply == "Your favorite color is blue."
    assert "check-in" not in reply


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


@pytest.mark.unit
@pytest.mark.ai
def test_align_response_acknowledges_newly_stated_favorite_color():
    reply = align_response_to_conversation_topic(
        "My favorite color is blue",
        "I cannot see your preferences. Click the chat button.",
        [],
    )
    assert reply == "Got it - your favorite color is blue."


@pytest.mark.unit
@pytest.mark.ai
def test_align_response_acknowledges_reading_interest():
    reply = align_response_to_conversation_topic(
        "I love reading books",
        UNCLEAR_USER_INPUT_REPLY,
        [],
    )
    assert "what kinds of books" in reply.lower()


@pytest.mark.unit
@pytest.mark.ai
@pytest.mark.parametrize("prompt,response,history", [
    ("My favorite color is blue", "Got it — I’ll remember that your favorite color is blue.", []),
    ("I love reading books", "That’s a great way to unwind. What kind of books do you like most right now—fiction, non-fiction, fantasy, memoir, or something else?", []),
    ("What genres do you think I'd like?", "I don’t have enough about your reading tastes yet to guess confidently. If you tell me a few books you’ve liked, or even books you’ve quit halfway through, I can suggest genres that fit.", [{"user_message": "I love reading books"}]),
    ("What's my favorite color?", "You told me your favorite color is blue. What do you like about it?", [{"user_message": "My favorite color is blue"}]),
    ("My favorite color is blue. What colors go well with it?", "Blue pairs nicely with cream, orange, or warm gray.", []),
])
def test_alignment_preserves_relevant_model_replies(prompt, response, history):
    assert align_response_to_conversation_topic(prompt, response, history) == response


@pytest.mark.unit
@pytest.mark.ai
@pytest.mark.parametrize("response", ["Your favorite color is green.", "Your favorite color is not blue."])
def test_known_fact_contradictions_are_still_repaired(response):
    assert reinforce_stated_facts_if_needed(
        "What's my favorite color?", response, [{"user_message": "My favorite color is blue"}]
    ) == "Your favorite color is blue."


@pytest.mark.unit
@pytest.mark.ai
def test_conversation_repair_check_preserves_reply_on_invalid_internal_input():
    from ai.chat.conversation_coherence import _needs_conversation_repair

    assert _needs_conversation_repair(cast(str, object())) is False
