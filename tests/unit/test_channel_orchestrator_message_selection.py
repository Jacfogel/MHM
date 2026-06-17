from unittest.mock import patch

import pytest

from communication.core.channel_orchestrator import CommunicationManager


def _runtime_template(text: str, days: list[str], periods: list[str], mid: str = "m1") -> dict:
    """v2 runtime template shape from load_user_messages."""
    return {
        "id": mid,
        "text": text,
        "category": "motivation",
        "schedule": {"days": days, "periods": periods},
        "created_at": None,
        "updated_at": None,
        "active": True,
    }


@pytest.mark.unit
@pytest.mark.communication
class TestChannelOrchestratorMessageSelectionHelpers:
    def setup_method(self):
        CommunicationManager._instance = None
        setattr(CommunicationManager, "_initialized", False)  # noqa: B010
        self.manager = CommunicationManager()
        self.dispatcher = self.manager.predefined_dispatcher

    def test_normalize_periods_removes_all_when_specific_periods_exist(self):
        result = self.dispatcher.normalize_message_selection_periods(
            ["ALL", "morning", "evening"], ["ALL", "morning", "evening"]
        )
        assert result == ["morning", "evening"]

    def test_normalize_periods_falls_back_to_all(self):
        result = self.dispatcher.normalize_message_selection_periods([], ["ALL", "morning"])
        assert result == ["ALL"]

    def test_load_predefined_messages_library_returns_none_when_missing_messages(self):
        with patch(
            "communication.delivery.message_dispatcher.load_user_messages",
            return_value=[],
        ):
            assert self.dispatcher.load_predefined_messages_library("u1", "motivation") is None

    def test_load_predefined_messages_library_uses_runtime_messages_loader(self):
        runtime_messages = [_runtime_template("normalized", ["ALL"], ["ALL"])]
        with patch(
            "communication.delivery.message_dispatcher.load_user_messages",
            return_value=runtime_messages,
        ):
            result = self.dispatcher.load_predefined_messages_library("u1", "motivation")

        assert result == {"messages": runtime_messages}

    def test_filter_messages_by_day_and_period(self):
        messages = [
            _runtime_template("a", ["MONDAY"], ["morning"], "1"),
            _runtime_template("b", ["TUESDAY"], ["morning"], "2"),
            _runtime_template("c", ["MONDAY"], ["evening"], "3"),
        ]
        result = self.dispatcher.filter_messages_by_day_and_period(messages, ["MONDAY"], ["morning"])
        assert result == [messages[0]]

    def test_filter_messages_treats_all_days_and_periods_as_wildcards(self):
        messages = [
            _runtime_template("all", ["ALL"], ["ALL"], "all"),
            _runtime_template("all-day", ["ALL"], ["morning"], "all-day"),
            _runtime_template("all-period", ["MONDAY"], ["ALL"], "all-period"),
            _runtime_template("wrong-day", ["TUESDAY"], ["morning"], "wrong-day"),
            _runtime_template("wrong-period", ["MONDAY"], ["evening"], "wrong-period"),
        ]

        result = self.dispatcher.filter_messages_by_day_and_period(
            messages, ["MONDAY"], ["morning"]
        )

        assert result == messages[:3]

    def test_deduplicate_candidate_messages_filters_recent_duplicates(self):
        all_messages = [
            _runtime_template("Hello there", ["ALL"], ["ALL"], "a"),
            _runtime_template("Unique message", ["ALL"], ["ALL"], "b"),
        ]
        with patch(
            "communication.delivery.message_dispatcher.get_recent_messages",
            return_value=[{"sent_text": "hello there", "sent_at": "2026-01-01 12:00:00"}],
        ):
            result = self.dispatcher.deduplicate_candidate_messages("u1", "motivation", all_messages)

        assert result == [all_messages[1]]

    def test_deduplicate_candidate_messages_falls_back_to_all_when_empty(self):
        all_messages = [_runtime_template("Repeated", ["ALL"], ["ALL"])]
        with patch(
            "communication.delivery.message_dispatcher.get_recent_messages",
            return_value=[{"sent_text": " repeated ", "sent_at": "2026-01-01 12:00:00"}],
        ):
            result = self.dispatcher.deduplicate_candidate_messages("u1", "motivation", all_messages)

        assert result == all_messages

    def test_send_and_store_predefined_message_does_not_store_failed_send(self):
        message = {"id": "m1", "text": "Hello world"}
        with (
            patch.object(self.manager, "send_message_sync", return_value=False),
            patch(
                "communication.delivery.message_dispatcher.store_sent_message"
            ) as mock_store,
        ):
            success, content = self.dispatcher.send_and_store_predefined_message(
                "u1", "motivation", "email", "u@example.com", message, ["morning"]
            )

        assert success is False
        assert content is None
        mock_store.assert_not_called()

    def test_send_predefined_message_returns_false_when_library_missing(self):
        with (
            patch(
                "communication.delivery.message_dispatcher.get_current_time_periods_with_validation",
                return_value=(["morning"], ["ALL", "morning"]),
            ),
            patch.object(
                self.manager.predefined_dispatcher,
                "load_predefined_messages_library",
                return_value=None,
            ),
        ):
            success, content = self.dispatcher.send_predefined_message("u1", "motivation", "email", "u@example.com")

        assert success is False
        assert content is None

    def test_send_predefined_message_handles_no_matching_messages(self):
        data = {"messages": [_runtime_template("x", ["SUNDAY"], ["night"])]}
        with (
            patch(
                "communication.delivery.message_dispatcher.get_current_time_periods_with_validation",
                return_value=(["morning"], ["ALL", "morning"]),
            ),
            patch(
                "communication.delivery.message_dispatcher.get_current_day_names",
                return_value=["MONDAY"],
            ),
            patch.object(
                self.manager.predefined_dispatcher,
                "load_predefined_messages_library",
                return_value=data,
            ),
        ):
            success, content = self.dispatcher.send_predefined_message("u1", "motivation", "email", "u@example.com")

        assert success is False
        assert content is None

    def test_send_predefined_message_success_path(self):
        msg0 = _runtime_template("x", ["MONDAY"], ["morning"], "m1")
        data = {"messages": [msg0]}
        with (
            patch(
                "communication.delivery.message_dispatcher.get_current_time_periods_with_validation",
                return_value=(["morning"], ["ALL", "morning"]),
            ),
            patch(
                "communication.delivery.message_dispatcher.get_current_day_names",
                return_value=["MONDAY"],
            ),
            patch.object(
                self.manager.predefined_dispatcher,
                "load_predefined_messages_library",
                return_value=data,
            ),
            patch.object(
                self.manager.predefined_dispatcher,
                "deduplicate_candidate_messages",
                return_value=data["messages"],
            ),
            patch.object(
                self.manager.predefined_dispatcher,
                "select_weighted_message",
                return_value=data["messages"][0],
            ),
            patch.object(
                self.manager.predefined_dispatcher,
                "send_and_store_predefined_message",
                return_value=(True, "x"),
            ),
        ):
            success, content = self.dispatcher.send_predefined_message("u1", "motivation", "email", "u@example.com")

        assert success is True
        assert content == "x"

    def test_send_predefined_message_send_exception_returns_false(self):
        msg0 = _runtime_template("x", ["MONDAY"], ["morning"], "m1")
        data = {"messages": [msg0]}
        with (
            patch(
                "communication.delivery.message_dispatcher.get_current_time_periods_with_validation",
                return_value=(["morning"], ["ALL", "morning"]),
            ),
            patch(
                "communication.delivery.message_dispatcher.get_current_day_names",
                return_value=["MONDAY"],
            ),
            patch.object(
                self.manager.predefined_dispatcher,
                "load_predefined_messages_library",
                return_value=data,
            ),
            patch.object(
                self.manager.predefined_dispatcher,
                "deduplicate_candidate_messages",
                return_value=data["messages"],
            ),
            patch.object(
                self.manager.predefined_dispatcher,
                "select_weighted_message",
                return_value=data["messages"][0],
            ),
            patch.object(
                self.manager.predefined_dispatcher,
                "send_and_store_predefined_message",
                side_effect=RuntimeError("send boom"),
            ),
        ):
            success, content = self.dispatcher.send_predefined_message("u1", "motivation", "email", "u@example.com")

        assert success is False
        assert content is None
