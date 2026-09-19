from unittest.mock import patch

import pytest

from communication.message_processing.flows.checkin_flow import CheckinFlowMixin


pytestmark = [pytest.mark.unit, pytest.mark.checkins]


def _questions():
    return {
        "mood": {"enabled": True, "always_include": True},
        "energy": {"enabled": True, "sometimes_include": True},
        "hydration": {"enabled": True, "sometimes_include": True},
    }


@pytest.mark.parametrize("target_count", [2, 3])
def test_default_checkin_question_count_can_vary_between_two_and_three(target_count):
    flow = CheckinFlowMixin()
    with (
        patch(
            "communication.message_processing.flows.checkin_flow.get_user_data",
            return_value={"preferences": {"checkin_settings": {}}},
        ),
        patch(
            "communication.message_processing.flows.checkin_flow.get_recent_checkins",
            return_value=[],
        ),
        patch(
            "communication.message_processing.flows.checkin_flow.random.randint",
            return_value=target_count,
        ) as choose_count,
        patch(
            "communication.message_processing.flows.checkin_flow.random.uniform",
            return_value=1.0,
        ),
        patch("communication.message_processing.flows.checkin_flow.random.shuffle"),
    ):
        selected = flow._select_checkin_questions_with_weighting("user", _questions())

    choose_count.assert_called_once_with(2, 3)
    assert len(selected) == target_count
    assert "mood" in selected
