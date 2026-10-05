"""Website task CRUD routes over an isolated, injectable task service."""

from copy import deepcopy
from types import SimpleNamespace

import pytest
import pytest_asyncio
from aiohttp import CookieJar

from core.error_handling import error_handler
from core.web_account_service import create_web_app
from core.web_tasks import WebTaskRoutes, register_task_routes
from tests.unit.test_web_account_service import web_client

pytestmark = [pytest.mark.unit, pytest.mark.tasks, pytest.mark.asyncio]
ORIGIN = "http://localhost:8080"


class Accounts:
    def __init__(self):
        self.users = {"existing": {"test_label": "river", "email": "river@example.com", "account_status": "active"}}

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
        self.users["existing"].update(email=email, test_label=username, timezone=timezone)
        return "existing"


@pytest_asyncio.fixture
async def task_gateway(monkeypatch):
    import core.tags as tags_module
    import tasks.task_service as service
    import tasks.task_data_manager as manager
    import tasks.task_occurrence_skip as skip_module
    import tasks.task_reminder_snooze as snooze_module
    import tasks.task_simplify as simplify_module

    active = []
    completed = []
    sent = []

    def create(user_id, **values):
        task_number = len(active) + len(completed) + 1
        task = {"id": f"task-{task_number}", "short_id": f"t{task_number}", "title": values["title"], "description": values.get("description", ""), "priority": values.get("priority", "medium"), "status": "active", "due": {"date": values.get("due_date"), "time": values.get("due_time")}, "recurrence": {"pattern": values.get("recurrence_pattern"), "interval": values.get("recurrence_interval", 1), "repeat_after_completion": values.get("repeat_after_completion", True)}, "completion": {"completed": False, "completed_at": None, "notes": ""}, "tags": values.get("tags", []), "parent_id": values.get("parent_id"), "reminders": [{"kind": "scheduled", "period": period} for period in values.get("reminder_periods", [])] + [{"kind": "quick", "value": value} for value in values.get("quick_reminders", [])]}
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
            task["reminders"] = [item for item in task["reminders"] if item["kind"] != "scheduled"] + [{"kind": "scheduled", "period": period} for period in updates["reminder_periods"]]
        if "quick_reminders" in updates:
            task["reminders"] = [item for item in task["reminders"] if item["kind"] != "quick"] + [{"kind": "quick", "value": value} for value in updates["quick_reminders"]]
        return True

    def complete(user_id, task_id, completion_data=None):
        task = find(user_id, task_id)
        if not task or task not in active:
            return False
        active.remove(task)
        task["status"] = "completed"
        task["completion"] = {
            "completed": True,
            "completed_at": (
                f"{completion_data['completion_date']} {completion_data['completion_time']}:00"
                if completion_data
                else "2026-09-20 10:00:00"
            ),
            "notes": completion_data.get("completion_notes", "") if completion_data else "",
        }
        completed.append(task)
        return True

    def restore(user_id, task_id, restore_steps=False):
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
    monkeypatch.setattr(tags_module, "get_user_tags", lambda user_id: ["existing", "health"])
    monkeypatch.setattr(manager, "get_task_by_id", find)
    monkeypatch.setattr(service, "load_active_tasks", lambda user_id: deepcopy(active))
    monkeypatch.setattr(service, "load_completed_tasks", lambda user_id: deepcopy(completed))
    monkeypatch.setattr(service, "get_tasks_due_soon", lambda user_id, days_ahead=7: deepcopy(active))
    monkeypatch.setattr(service, "update_task", update)
    monkeypatch.setattr(service, "complete_task", complete)
    monkeypatch.setattr(service, "restore_task", restore)
    monkeypatch.setattr(service, "delete_task", delete)
    monkeypatch.setattr(
        service,
        "get_custom_task_template_records",
        lambda user_id: {
            "custom_abc123": {
                "display_name": "Morning routine",
                "title": "Start morning routine",
                "description": "Begin with water.",
                "priority": "high",
                "tags": ["routine"],
                "default_due_time": "08:30",
                "recurrence_pattern": "daily",
                "recurrence_interval": 1,
            }
        },
    )
    monkeypatch.setattr(
        snooze_module,
        "snooze_task_reminder",
        lambda user_id, task_id, option, custom_when=None: SimpleNamespace(
            success=True, message=f"Snoozed {option}."
        ),
    )
    monkeypatch.setattr(
        skip_module,
        "skip_task_occurrence",
        lambda user_id, task_id: SimpleNamespace(success=True, message="Skipped."),
    )
    def simplify(user_id, task_id, new_title):
        task = find(user_id, task_id)
        assert task is not None
        task["title"] = new_title
        return SimpleNamespace(success=True, message="Simplified.", needs_title=False)
    monkeypatch.setattr(simplify_module, "simplify_task", simplify)
    accounts = Accounts()
    app = create_web_app(accounts=accounts, mailer=lambda email, code: sent.append(code), origin=ORIGIN, proxy_secret="")
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
        token = (await (await client.post("/api/auth/request-code", json={"email": "river@example.com", "mode": "login"}, headers={"Origin": ORIGIN})).json())["challenge"]
        assert (await client.post("/api/auth/verify", json={"challenge": token, "code": sent[-1]}, headers={"Origin": ORIGIN})).status == 200
        yield client, active, completed


async def test_task_crud_lifecycle_and_validation(task_gateway):
    client, active, completed = task_gateway
    assert (await client.get("/api/tasks")).json  # route is authenticated
    created = await client.post("/api/tasks", json={"title": "Plan a gentle start", "description": "One step", "due_date": "2026-09-20", "priority": "high", "recurrence_pattern": "weekly", "recurrence_interval": 2, "repeat_after_completion": False, "tags": ["Health", "morning"], "reminder_periods": [{"date": "2026-09-20", "start_time": "09:00", "end_time": "10:00"}], "quick_reminders": ["1-2hour"]}, headers={"Origin": ORIGIN})
    assert created.status == 201
    task = (await created.json())["task"]
    assert task["title"] == "Plan a gentle start"
    assert task["tags"] == ["health", "morning"]
    assert "links" not in task
    assert task["reminders"][0]["period"]["start_time"] == "09:00"
    assert task["reminders"][1] == {"kind": "quick", "value": "1-2hour"}
    assert task["recurrence"] == {"pattern": "weekly", "interval": 2, "repeat_after_completion": False, "next_due_date": None}
    task_list = await (await client.get("/api/tasks")).json()
    assert task_list["due_soon_count"] == 1
    assert task_list["tags"] == ["existing", "health", "morning"]
    templates = await (await client.get("/api/task-templates")).json()
    assert {template["id"] for template in templates["templates"]} >= {
        "medication",
        "appointment",
        "custom_abc123",
    }
    custom_template = next(
        template for template in templates["templates"] if template["id"] == "custom_abc123"
    )
    assert custom_template["custom"] is True
    snoozed = await client.post(
        f"/api/tasks/{task['id']}/snooze",
        json={"option": "1_hour"},
        headers={"Origin": ORIGIN},
    )
    assert snoozed.status == 200
    assert (await snoozed.json())["message"] == "Snoozed 1_hour."
    assert (await client.post(f"/api/tasks/{task['id']}/skip", json={}, headers={"Origin": ORIGIN})).status == 200
    simplified = await client.post(
        f"/api/tasks/{task['id']}/simplify",
        json={"new_title": "Open the plan"},
        headers={"Origin": ORIGIN},
    )
    assert simplified.status == 200
    assert (await simplified.json())["task"]["title"] == "Open the plan"
    assert (await client.patch(f"/api/tasks/{task['id']}", json={"title": "Plan a gentler start", "priority": "medium", "tags": ["home"], "reminder_periods": []}, headers={"Origin": ORIGIN})).status == 200
    assert (await client.post(f"/api/tasks/{task['id']}/complete", json={"completion_date": "2026-09-21", "completion_time": "14:30", "completion_notes": "Finished gently"}, headers={"Origin": ORIGIN})).status == 200
    completed_view = await (await client.get("/api/tasks?status=completed")).json()
    assert completed_view["tasks"][0]["completion"]["notes"] == "Finished gently"
    assert (await client.post(f"/api/tasks/{task['id']}/restore", json={}, headers={"Origin": ORIGIN})).status == 200
    assert (await client.delete(f"/api/tasks/{task['id']}", json={}, headers={"Origin": ORIGIN})).status == 200
    point_reminder = await client.post(
        "/api/tasks",
        json={
            "title": "Point reminder",
            "reminder_periods": [{"date": "2026-09-22", "start_time": "09:15"}],
        },
        headers={"Origin": ORIGIN},
    )
    assert point_reminder.status == 201
    assert (await point_reminder.json())["task"]["reminders"][0]["period"] == {
        "date": "2026-09-22",
        "start_time": "09:15",
        "end_time": None,
    }
    assert (
        await client.post(
            "/api/tasks",
            json={"title": "Missing due date", "quick_reminders": ["1-2hour"]},
            headers={"Origin": ORIGIN},
        )
    ).status == 400
    relative_task = await client.post(
        "/api/tasks",
        json={
            "title": "Relative reminder",
            "due_date": "2026-09-23",
            "quick_reminders": ["1-2hour"],
        },
        headers={"Origin": ORIGIN},
    )
    relative_task_id = (await relative_task.json())["task"]["id"]
    assert (
        await client.patch(
            f"/api/tasks/{relative_task_id}",
            json={"due_date": None},
            headers={"Origin": ORIGIN},
        )
    ).status == 400
    assert (await client.post("/api/tasks", json={"title": "", "due_date": "tomorrow"}, headers={"Origin": ORIGIN})).status == 400
    assert (await client.post("/api/tasks", json={"title": "Bad reminder", "reminder_periods": [{"date": "2026-09-20", "start_time": "10:00", "end_time": "09:00"}]}, headers={"Origin": ORIGIN})).status == 400
    assert (await client.post("/api/tasks", json={"title": "Old task shape", "links": []}, headers={"Origin": ORIGIN})).status == 400
    assert (await client.post(f"/api/tasks/{task['id']}/snooze", json={"option": "later"}, headers={"Origin": ORIGIN})).status == 400
    assert (await client.post(f"/api/tasks/{task['id']}/simplify", json={"new_title": ""}, headers={"Origin": ORIGIN})).status == 400


async def test_task_routes_require_authentication_and_reject_unknown_fields(task_gateway):
    client, _, _ = task_gateway
    assert (await client.post("/api/tasks", json={"title": "A", "unexpected": True}, headers={"Origin": ORIGIN})).status == 400
    assert (await client.get("/api/tasks?status=unknown")).status == 400


async def test_task_bulk_actions(task_gateway):
    client, _, _ = task_gateway
    ids = []
    for title in ("First", "Second"):
        response = await client.post(
            "/api/tasks", json={"title": title}, headers={"Origin": ORIGIN}
        )
        ids.append((await response.json())["task"]["id"])
    prioritized = await client.post(
        "/api/tasks/bulk/priority",
        json={"task_ids": ids, "priority": "HIGH"},
        headers={"Origin": ORIGIN},
    )
    assert prioritized.status == 200
    assert (await prioritized.json())["changed"] == ids
    active_tasks = (await (await client.get("/api/tasks")).json())["tasks"]
    assert {task["priority"] for task in active_tasks if task["id"] in ids} == {"high"}
    completed = await client.post(
        "/api/tasks/bulk/complete",
        json={"task_ids": ids},
        headers={"Origin": ORIGIN},
    )
    assert completed.status == 200
    assert (await completed.json())["changed"] == ids
    restored = await client.post(
        "/api/tasks/bulk/restore",
        json={"task_ids": ids},
        headers={"Origin": ORIGIN},
    )
    assert restored.status == 200
    deleted = await client.post(
        "/api/tasks/bulk/delete",
        json={"task_ids": ids},
        headers={"Origin": ORIGIN},
    )
    assert deleted.status == 200


@pytest.mark.parametrize("priority", [None, "later", 3])
async def test_task_bulk_priority_rejects_invalid_values(task_gateway, priority):
    client, _, _ = task_gateway
    created = await client.post(
        "/api/tasks", json={"title": "Choose me"}, headers={"Origin": ORIGIN}
    )
    task_id = (await created.json())["task"]["id"]
    response = await client.post(
        "/api/tasks/bulk/priority",
        json={"task_ids": [task_id], "priority": priority},
        headers={"Origin": ORIGIN},
    )
    assert response.status == 400


async def test_breakdown_adds_subtasks_and_keeps_the_original_title(task_gateway, monkeypatch):
    import tasks.task_breakdown as breakdown
    from tasks.task_breakdown import TaskBreakdownResult

    monkeypatch.setattr(
        breakdown,
        "suggest_breakdown",
        lambda user_id, task_id: TaskBreakdownResult(
            True,
            "Here are a few smaller steps.",
            steps=["Find the phone number", "Ask for the next opening"],
        ),
    )
    client, _active, _completed = task_gateway
    created = await client.post(
        "/api/tasks",
        json={"title": "Call the dentist", "due_date": "2026-09-20"},
        headers={"Origin": ORIGIN},
    )
    task = (await created.json())["task"]
    suggested = await client.post(
        f"/api/tasks/{task['id']}/breakdown",
        json={},
        headers={"Origin": ORIGIN},
    )
    assert suggested.status == 200
    assert (await suggested.json())["steps"] == [
        "Find the phone number",
        "Ask for the next opening",
    ]
    added = await client.post(
        f"/api/tasks/{task['id']}/subtasks",
        json={"titles": ["Find the phone number", "Ask for the next opening"]},
        headers={"Origin": ORIGIN},
    )
    assert added.status == 200
    body = await added.json()
    assert body["task"]["title"] == "Call the dentist"
    assert "original task stays" in body["message"]
    listed = await (await client.get("/api/tasks")).json()
    children = [item for item in listed["tasks"] if item.get("parent_id") == task["id"]]
    assert [item["title"] for item in children] == [
        "Find the phone number",
        "Ask for the next opening",
    ]
    nested = await client.post(
        f"/api/tasks/{children[0]['id']}/subtasks",
        json={"titles": ["Look up the number"]},
        headers={"Origin": ORIGIN},
    )
    assert nested.status == 400


async def test_task_route_initialization_reports_and_reraises_errors(monkeypatch):
    calls = []
    monkeypatch.setattr(
        error_handler,
        "handle_error",
        lambda error, context, operation, user_friendly=True: calls.append(
            (error, operation, user_friendly)
        )
        or False,
    )

    class BrokenTaskRoutes(WebTaskRoutes):
        def __setattr__(self, _name, _value):
            raise RuntimeError("cannot initialize routes")

    with pytest.raises(RuntimeError, match="cannot initialize routes"):
        BrokenTaskRoutes(object())

    assert len(calls) == 1
    assert calls[0][1:] == ("initializing website task routes", False)


async def test_task_route_registration_reports_and_reraises_errors(monkeypatch):
    calls = []
    monkeypatch.setattr(
        error_handler,
        "handle_error",
        lambda error, context, operation, user_friendly=True: calls.append(
            (error, operation, user_friendly)
        )
        or False,
    )

    class BrokenRouter:
        def add_get(self, *_args, **_kwargs):
            raise RuntimeError("cannot register routes")

    app = SimpleNamespace(router=BrokenRouter())
    with pytest.raises(RuntimeError, match="cannot register routes"):
        register_task_routes(app, object())

    assert len(calls) == 1
    assert calls[0][1:] == ("registering website task routes", False)
