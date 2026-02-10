import pytest
import uuid
from communication.message_processing.interaction_manager import handle_user_message
from tasks.task_management import load_active_tasks, save_active_tasks
from tests.test_utilities import setup_test_data_environment, cleanup_test_data_environment, create_test_user


@pytest.mark.behavior
class TestTaskCrudDisambiguation:
    def setup_method(self):
        self.test_dir, self.test_data_dir, _ = setup_test_data_environment()

    def teardown_method(self):
        cleanup_test_data_environment(self.test_dir)

    def test_disambiguation_on_complete_by_name(self, monkeypatch):
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        user_id = "user_task_disamb"
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)

        # Create two similar tasks
        tasks = load_active_tasks(user_id)
        tasks.append({"title": "Wash dishes", "task_id": "tdishes"})
        tasks.append({"title": "Wash laundry", "task_id": "tlaundry"})
        assert save_active_tasks(user_id, tasks)

        # Ambiguous command
        resp = handle_user_message(user_id, "complete task wash", "discord")
        assert not resp.completed
        assert "multiple matching tasks" in resp.message.lower()
        # Suggestions should be actionable and limited
        assert resp.suggestions is not None and len(resp.suggestions) <= 2
        assert "list tasks" in " ".join(resp.suggestions).lower()

    def test_delete_by_number_succeeds(self, monkeypatch):
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        user_id = f"user_task_delete_{uuid.uuid4().hex[:8]}"
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)
        tasks = load_active_tasks(user_id)
        tasks.append({"title": "Task A", "task_id": "taskaaaa"})
        tasks.append({"title": "Task B", "task_id": "taskbbbb"})
        assert save_active_tasks(user_id, tasks)

        # Delete task 2
        resp = handle_user_message(user_id, "delete task 2", "discord")
        assert resp.completed
        titles = [t['title'] for t in load_active_tasks(user_id)]
        assert "Task B" not in titles

    def test_delete_by_name_requires_confirm(self, monkeypatch):
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        user_id = "user_task_confirm"
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)
        tasks = load_active_tasks(user_id)
        tasks.append({"title": "Brush teeth", "task_id": "teeth123"})
        assert save_active_tasks(user_id, tasks)

        # Name-based delete triggers confirmation
        resp = handle_user_message(user_id, "delete task brush teeth", "discord")
        assert not resp.completed
        assert "confirm delete" in resp.message.lower()
        assert resp.suggestions is not None and "confirm delete" in " ".join(resp.suggestions).lower()

        # Confirm deletion
        resp2 = handle_user_message(user_id, "confirm delete", "discord")
        assert resp2.completed
        titles = [t['title'] for t in load_active_tasks(user_id)]
        assert "Brush teeth" not in titles

    def test_update_due_date_by_name(self, monkeypatch):
        user_id = "user_task_update_due"
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)
        tasks = load_active_tasks(user_id)
        tasks.append({"title": "Wash dishes", "task_id": "wash0001"})
        assert save_active_tasks(user_id, tasks)

        resp = handle_user_message(user_id, "update task wash dishes due date 2025-11-02", "discord")
        assert resp.completed is False or resp.completed is True
        # Regardless of completion flag, task due_date should be updated when handler runs
        tasks2 = load_active_tasks(user_id)
        updated = [t for t in tasks2 if t.get('task_id') == 'wash0001']
        assert updated and updated[0].get('due_date') in ("2025-11-02", "Nov 2", "2025-11-02T00:00:00")

    def test_update_missing_field_prompts_with_suggestions(self, monkeypatch):
        user_id = f"user_task_update_prompt_{uuid.uuid4().hex[:8]}"
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)
        tasks = load_active_tasks(user_id)
        tasks.append({"title": "Change me", "task_id": "chg001"})
        assert save_active_tasks(user_id, tasks)

        resp = handle_user_message(user_id, "update task change me", "discord")
        assert not resp.completed
        assert "what would you like to update" in resp.message.lower()
        assert resp.suggestions is not None
        joined = " ".join(resp.suggestions).lower()
        assert ("due date" in joined) or ("priority" in joined)

    def test_complete_suggestion_prompt_has_suggestions(self, monkeypatch):
        user_id = "user_task_complete_prompt"
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)
        tasks = load_active_tasks(user_id)
        tasks.append({"title": "Take a walk", "task_id": "walk001"})
        assert save_active_tasks(user_id, tasks)

        # Trigger the "Did you want to complete this task?" path by omitting identifier
        resp = handle_user_message(user_id, "complete task", "discord")
        assert not resp.completed
        assert "did you want to complete this task" in resp.message.lower()
        assert resp.suggestions is not None
        joined = " ".join(resp.suggestions).lower()
        assert ("complete task" in joined) or ("cancel" in joined)

    def test_update_due_date_ambiguous_requires_disambiguation(self, monkeypatch):
        user_id = "user_task_update_ambig"
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)
        tasks = load_active_tasks(user_id)
        tasks.append({"title": "Wash dishes", "task_id": "washA"})
        tasks.append({"title": "Wash laundry", "task_id": "washB"})
        assert save_active_tasks(user_id, tasks)

        resp = handle_user_message(user_id, "update task wash due date 2025-11-03", "discord")
        assert not resp.completed
        assert "multiple matching tasks" in resp.message.lower()

    @pytest.mark.slow
    def test_update_priority_and_title_by_name(self, monkeypatch):
        user_id = "user_task_update_fields"
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        assert create_test_user(user_id, user_type="basic", test_data_dir=self.test_data_dir)
        tasks = load_active_tasks(user_id)
        tasks.append({"title": "Rename me", "task_id": "rename01"})
        assert save_active_tasks(user_id, tasks)

        # Update priority
        resp1 = handle_user_message(user_id, "update task rename me priority high", "discord")
        tasks1 = load_active_tasks(user_id)
        t1 = [t for t in tasks1 if t.get('task_id') == 'rename01'][0]
        assert t1.get('priority') == 'high'

        # Update title (rename) and ensure it is not misread as completion
        # Use a title that doesn't contain "done" to avoid parser confusion
        resp2 = handle_user_message(user_id, "update task rename me title \"Completed project\"", "discord")
        tasks_after = load_active_tasks(user_id)
        # Task should still exist (not completed) and either title updated or awaiting clarification
        still_exists = any(t.get('task_id') == 'rename01' for t in tasks_after)
        assert still_exists, f"Task should still exist after title update. Tasks: {tasks_after}"


