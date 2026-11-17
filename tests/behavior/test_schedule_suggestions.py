import pytest

from communication.message_processing.interaction_manager import handle_user_message
from tests.test_helpers.test_utilities import setup_test_data_environment, cleanup_test_data_environment, create_test_user


@pytest.mark.tasks
@pytest.mark.behavior
class TestScheduleSuggestions:
    def setup_method(self):
        self.test_dir, self.test_data_dir, _ = setup_test_data_environment()

    def teardown_method(self):
        cleanup_test_data_environment(self.test_dir)

    def test_add_schedule_missing_fields_has_curated_suggestions(self, monkeypatch):
        user_id = "user_sched_add"
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)

        # Intentionally under-specified
        resp = handle_user_message(user_id, "add schedule period", "discord")
        assert not resp.completed
        msg = resp.message.lower()
        assert "please provide all details" in msg or "period" in msg
        # Suggestions should be present and actionable examples
        assert resp.suggestions is not None and len(resp.suggestions) >= 1
        joined = " ".join(resp.suggestions).lower()
        assert ("period" in joined) or ("am" in joined) or ("pm" in joined)

    def test_edit_schedule_missing_times_has_curated_suggestions(self, monkeypatch):
        from core import schedule_runtime

        user_id = "user_sched_edit"
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)
        from communication.command_handlers.schedule_handler import ScheduleManagementHandler

        added = ScheduleManagementHandler()._handle_add_schedule_period(user_id, {
            "category": "tasks", "period_name": "morning", "start_time": "9am", "end_time": "11am",
        })
        assert "Added" in added.message
        period = schedule_runtime.get_schedule_time_periods(user_id, "tasks")["morning"]
        assert (period["start_time"], period["end_time"]) == ("09:00", "11:00")
        resp = handle_user_message(user_id, "edit schedule period morning tasks", "discord")
        assert not resp.completed
        assert "what would you like to update" in resp.message.lower()
        assert resp.suggestions is not None and any(sugg.lower().startswith("from ") for sugg in resp.suggestions)


