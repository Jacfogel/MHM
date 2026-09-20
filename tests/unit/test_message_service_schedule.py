"""Schedule compatibility tests for predefined messages."""

import pytest

from messages.message_service import message_schedule_matches_current_window

pytestmark = [pytest.mark.unit, pytest.mark.messages]


def test_message_day_matching_is_case_insensitive_across_app_and_website():
    assert message_schedule_matches_current_window(
        ["MONDAY"], ["Morning"], ["Monday"], ["Morning"]
    )
    assert message_schedule_matches_current_window(
        ["monday"], ["ALL"], ["MONDAY"], ["Quiet Window"]
    )
