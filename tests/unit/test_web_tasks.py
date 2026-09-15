"""Website task CRUD routes over an isolated, injectable task service."""

from copy import deepcopy

import pytest
import pytest_asyncio
from aiohttp import CookieJar
from aiohttp.test_utils import TestClient, TestServer

from core.web_account_service import create_web_app

pytestmark = [pytest.mark.unit, pytest.mark.tasks, pytest.mark.asyncio]
ORIGIN = "http://localhost:8080"


class Accounts:
    def __init__(self):
        self.users = {"existing": {"internal_username": "river", "email": "river@example.com", "account_status": "active"}}

    def by_email(self, email):
        for uid, account in self.users.items():
            if account["email"].casefold() == email.casefold():
                return uid, account
        return None

    def email_exists(self, email):
        return any(user["email"].casefold() == email.casefold() for user in self.users.values())

    def username_exists(self, username):
        return False

    def get(self, uid):
        return self.users.get(uid, {})

    def create(self, email, username, timezone):
        self.users["existing"].update(email=email, internal_username=username, timezone=timezone)
        return "existing"


@pytest_asyncio.fixture
async def task_gateway(monkeypatch):
    import tasks.task_service as service
    import tasks.task_data_manager as manager

    active = []
    completed = []
    sent = []

    def create(user_id, **values):
        task = {"id": "task-1", "short_id": "t1", "title": values["title"], "description": values.get("description", ""), "priority": values.get("priority", "medium"), "status": "active", "due": {"date": values.get("due_date"), "time": values.get("due_time")}, "recurrence": {"pattern": values.get("recurrence_pattern"), "interval": values.get("recurrence_interval", 1), "repeat_after_completion": values.get("repeat_after_completion", True)}, "completion": {"completed": False, "completed_at": None, "notes": ""}, "tags": values.get("tags", []), "links": [], "reminders": [{"kind": "scheduled", "period": period} for period in values.get("reminder_periods", [])]}
        active.append(task)
        return task["id"]

    def find(user_id, task_id):
        return next((task for task in active + completed if task["id"] == task_id), None)

    def update(user_id, task_id, updates):
        task = find(user_id, task_id)
        if not task or task["status"] != "active":
            return False
        task.update({key: value for key, value in updates.items() if key not in {"due_date", "due_time"}})
        task["due"]["date"] = updates.get("due_date", task["due"].get("date"))
        task["due"]["time"] = updates.get("due_time", task["due"].get("time"))
        if "reminder_periods" in updates:
            task["reminders"] = [{"kind": "scheduled", "period": period} for period in updates["reminder_periods"]]
        return True

    def complete(user_id, task_id):
        task = find(user_id, task_id)
        if not task or task not in active:
            return False
        active.remove(task)
        task["status"] = "completed"
        task["completion"]["completed"] = True
        completed.append(task)
        return True

    def restore(user_id, task_id):
        task = find(user_id, task_id)
        if not task or task not in completed:
            return False
        completed.remove(task)
        task["status"] = "active"
        task["completion"]["completed"] = False
        active.append(task)
        return True

    def delete(user_id, task_id):
        task = find(user_id, task_id)
        if not task:
            return False
        (active if task in active else completed).remove(task)
        return True

    monkeypatch.setattr(service, "create_task", create)
    monkeypatch.setattr(manager, "get_task_by_id", find)
    monkeypatch.setattr(service, "load_active_tasks", lambda user_id: deepcopy(active))
    monkeypatch.setattr(service, "load_completed_tasks", lambda user_id: deepcopy(completed))
    monkeypatch.setattr(service, "update_task", update)
    monkeypatch.setattr(service, "complete_task", complete)
    monkeypatch.setattr(service, "restore_task", restore)
    monkeypatch.setattr(service, "delete_task", delete)
    accounts = Accounts()
    app = create_web_app(accounts=accounts, mailer=lambda email, code: sent.append(code), origin=ORIGIN, proxy_secret="")
    async with TestClient(TestServer(app), cookie_jar=CookieJar(unsafe=True)) as client:
        token = (await (await client.post("/api/auth/request-code", json={"email": "river@example.com", "mode": "login"}, headers={"Origin": ORIGIN})).json())["challenge"]
        assert (await client.post("/api/auth/verify", json={"challenge": token, "code": sent[-1]}, headers={"Origin": ORIGIN})).status == 200
        yield client, active, completed


async def test_task_crud_lifecycle_and_validation(task_gateway):
    client, active, completed = task_gateway
    assert (await client.get("/api/tasks")).json  # route is authenticated
    created = await client.post("/api/tasks", json={"title": "Plan a gentle start", "description": "One step", "due_date": "2026-09-20", "priority": "high", "tags": ["Health", "morning"], "reminder_periods": [{"date": "2026-09-20", "start_time": "09:00", "end_time": "10:00"}]}, headers={"Origin": ORIGIN})
    assert created.status == 201
    task = (await created.json())["task"]
    assert task["title"] == "Plan a gentle start"
    assert task["tags"] == ["health", "morning"]
    assert task["reminders"][0]["period"]["start_time"] == "09:00"
    assert (await client.patch(f"/api/tasks/{task['id']}", json={"title": "Plan a gentler start", "priority": "medium", "tags": ["home"], "reminder_periods": []}, headers={"Origin": ORIGIN})).status == 200
    assert (await client.post(f"/api/tasks/{task['id']}/complete", json={}, headers={"Origin": ORIGIN})).status == 200
    assert (await client.get("/api/tasks?status=completed")).status == 200
    assert (await client.post(f"/api/tasks/{task['id']}/restore", json={}, headers={"Origin": ORIGIN})).status == 200
    assert (await client.delete(f"/api/tasks/{task['id']}", json={}, headers={"Origin": ORIGIN})).status == 200
    assert (await client.post("/api/tasks", json={"title": "", "due_date": "tomorrow"}, headers={"Origin": ORIGIN})).status == 400
    assert (await client.post("/api/tasks", json={"title": "Bad reminder", "reminder_periods": [{"date": "2026-09-20", "start_time": "10:00", "end_time": "09:00"}]}, headers={"Origin": ORIGIN})).status == 400


async def test_task_routes_require_authentication_and_reject_unknown_fields(task_gateway):
    client, _, _ = task_gateway
    assert (await client.post("/api/tasks", json={"title": "A", "unexpected": True}, headers={"Origin": ORIGIN})).status == 400
    assert (await client.get("/api/tasks?status=unknown")).status == 400
