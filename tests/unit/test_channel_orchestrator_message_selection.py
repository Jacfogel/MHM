from unittest.mock import patch

import pytest

from communication.core.channel_orchestrator import CommunicationManager


@pytest.mark.unit
@pytest.mark.communication
class TestChannelOrchestratorMessageSelectionHelpers:
    def setup_method(self):
        CommunicationManager._instance = None
        setattr(CommunicationManager, "_initialized", False)  # noqa: B010
        self.manager = CommunicationManager()

    def test_normalize_periods_removes_all_when_specific_periods_exist(self):
        result = self.manager._normalize_message_selection_periods(
            ["ALL", "morning", "evening"], ["ALL", "morning", "evening"]
        )
        assert result == ["morning", "evening"]

    def test_normalize_periods_falls_back_to_all(self):
        result = self.manager._normalize_message_selection_periods([], ["ALL", "morning"])
        assert result == ["ALL"]

    def test_load_predefined_messages_library_returns_none_when_missing_messages(self):
        with patch("core.message_management.load_user_messages", return_value=[]):
            assert self.manager._load_predefined_messages_library("u1", "motivation") is None

    def test_load_predefined_messages_library_uses_runtime_messages_loader(self):
        runtime_messages = [{"message": "normalized", "days": ["ALL"], "time_periods": ["ALL"]}]
        with patch("core.message_management.load_user_messages", return_value=runtime_messages):
            result = self.manager._load_predefined_messages_library("u1", "motivation")

        assert result == {"messages": runtime_messages}

    def test_filter_messages_by_day_and_period(self):
        messages = [
            {"message": "a", "days": ["MONDAY"], "time_periods": ["morning"]},
            {"message": "b", "days": ["TUESDAY"], "time_periods": ["morning"]},
            {"message": "c", "days": ["MONDAY"], "time_periods": ["evening"]},
        ]
        result = self.manager._filter_messages_by_day_and_period(messages, ["MONDAY"], ["morning"])
        assert result == [{"message": "a", "days": ["MONDAY"], "time_periods": ["morning"]}]

    def test_deduplicate_candidate_messages_filters_recent_duplicates(self):
        all_messages = [
            {"message": "Hello there"},
            {"message": "Unique message"},
        ]
        with patch("core.message_management.get_recent_messages", return_value=[{"message": "hello there"}]):
            result = self.manager._deduplicate_candidate_messages("u1", "motivation", all_messages)

        assert result == [{"message": "Unique message"}]

    def test_deduplicate_candidate_messages_falls_back_to_all_when_empty(self):
        all_messages = [{"message": "Repeated"}]
        with patch("core.message_management.get_recent_messages", return_value=[{"message": " repeated "}]):
            result = self.manager._deduplicate_candidate_messages("u1", "motivation", all_messages)

        assert result == all_messages

    def test_send_and_store_predefined_message_treats_send_false_as_success(self):
        message = {"message_id": "m1", "message": "Hello world"}
        with (
            patch.object(self.manager, "send_message_sync", return_value=False),
            patch("core.message_management.store_sent_message") as mock_store,
        ):
            success, content = self.manager._send_and_store_predefined_message(
                "u1", "motivation", "email", "u@example.com", message, ["morning"]
            )

        assert success is True
        assert content == "Hello world"
        mock_store.assert_called_once()

    def test_send_predefined_message_returns_false_when_library_missing(self):
        with (
            patch("communication.core.channel_orchestrator.get_current_time_periods_with_validation", return_value=(["morning"], ["ALL", "morning"])),
            patch.object(self.manager, "_load_predefined_messages_library", return_value=None),
        ):
            success, content = self.manager._send_predefined_message("u1", "motivation", "email", "u@example.com")

        assert success is False
        assert content is None

    def test_send_predefined_message_handles_no_matching_messages(self):
        data = {"messages": [{"message": "x", "days": ["SUNDAY"], "time_periods": ["night"]}]}
        with (
            patch("communication.core.channel_orchestrator.get_current_time_periods_with_validation", return_value=(["morning"], ["ALL", "morning"])),
            patch("communication.core.channel_orchestrator.get_current_day_names", return_value=["MONDAY"]),
            patch.object(self.manager, "_load_predefined_messages_library", return_value=data),
        ):
            success, content = self.manager._send_predefined_message("u1", "motivation", "email", "u@example.com")

        assert success is False
        assert content is None

    def test_send_predefined_message_success_path(self):
        data = {"messages": [{"message": "x", "message_id": "m1", "days": ["MONDAY"], "time_periods": ["morning"]}]}
        with (
            patch("communication.core.channel_orchestrator.get_current_time_periods_with_validation", return_value=(["morning"], ["ALL", "morning"])),
            patch("communication.core.channel_orchestrator.get_current_day_names", return_value=["MONDAY"]),
            patch.object(self.manager, "_load_predefined_messages_library", return_value=data),
            patch.object(self.manager, "_deduplicate_candidate_messages", return_value=data["messages"]),
            patch.object(self.manager, "_select_weighted_message", return_value=data["messages"][0]),
            patch.object(self.manager, "_send_and_store_predefined_message", return_value=(True, "x")),
        ):
            success, content = self.manager._send_predefined_message("u1", "motivation", "email", "u@example.com")

        assert success is True
        assert content == "x"

    def test_send_predefined_message_send_exception_returns_false(self):
        data = {"messages": [{"message": "x", "message_id": "m1", "days": ["MONDAY"], "time_periods": ["morning"]}]}
        with (
            patch("communication.core.channel_orchestrator.get_current_time_periods_with_validation", return_value=(["morning"], ["ALL", "morning"])),
            patch("communication.core.channel_orchestrator.get_current_day_names", return_value=["MONDAY"]),
            patch.object(self.manager, "_load_predefined_messages_library", return_value=data),
            patch.object(self.manager, "_deduplicate_candidate_messages", return_value=data["messages"]),
            patch.object(self.manager, "_select_weighted_message", return_value=data["messages"][0]),
            patch.object(self.manager, "_send_and_store_predefined_message", side_effect=RuntimeError("send boom")),
        ):
            success, content = self.manager._send_predefined_message("u1", "motivation", "email", "u@example.com")

        assert success is False
        assert content is None
