import os

from communication.message_processing.interaction_manager import handle_user_message
from tests.test_utilities import setup_test_data_environment, cleanup_test_data_environment, create_test_user


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
        user_id = "user_sched_edit"
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)
        # Request editing a known period name/category without times
        resp = handle_user_message(user_id, "edit schedule period morning tasks", "discord")
        # With improved parser, this should hit the curated suggestions path
        assert not resp.completed
        msg = resp.message.lower()
        assert "what times should" in msg or "from" in " ".join((resp.suggestions or [])).lower()
        assert resp.suggestions is not None and any(sugg.lower().startswith("from ") for sugg in resp.suggestions)


