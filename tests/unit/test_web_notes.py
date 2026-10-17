"""Website notes page routes over the canonical notebook service."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from aiohttp import CookieJar

from core.error_handling import error_handler
from core.web_account_service import create_web_app
from core.web_notes import WebNotesRoutes, register_notes_routes
from tests.unit.test_web_account_service import web_client

pytestmark = [pytest.mark.unit, pytest.mark.notebook, pytest.mark.asyncio]
ORIGIN = "http://localhost:8080"


async def test_notes_route_initialization_reports_and_reraises_errors(monkeypatch):
    calls = []
    monkeypatch.setattr(
        error_handler,
        "handle_error",
        lambda error, context, operation, user_friendly=True: calls.append(
            (error, operation, user_friendly)
        )
        or False,
    )

    class BrokenNotesRoutes(WebNotesRoutes):
        def __setattr__(self, _name, _value):
            raise RuntimeError("cannot initialize routes")

    with pytest.raises(RuntimeError, match="cannot initialize routes"):
        BrokenNotesRoutes(object())

    assert len(calls) == 1
    assert calls[0][1:] == ("initializing website notebook routes", False)


async def test_notes_route_registration_reports_and_reraises_errors(monkeypatch):
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
        register_notes_routes(app, object())

    assert len(calls) == 1
    assert calls[0][1:] == ("registering website notebook routes", False)


class Accounts:
    def __init__(self):
        self.user = {"test_label": "river", "email": "river@example.com", "account_status": "active"}

    def by_email(self, email):
        return ("existing", self.user) if email.casefold() == self.user["email"] else None

    def email_exists(self, email): return email.casefold() == self.user["email"]
    def username_exists(self, username): return False
    def get(self, uid): return self.user


@pytest_asyncio.fixture
async def notes_gateway(monkeypatch):
    import notebook.notebook_data_manager as manager
    import core.tags as shared_tags

    entries = []
    sent = []

    def make(kind="note", **values):
        prefix = {"note": "n", "journal_entry": "j", "list": "l"}[kind]
        items = [
            SimpleNamespace(
                id=uuid4(),
                text=item["text"] if isinstance(item, dict) else item,
                done=item.get("done", False) if isinstance(item, dict) else False,
                order=index,
            )
            for index, item in enumerate(values.get("items", []))
        ]
        return SimpleNamespace(id=uuid4(), short_id=f"{prefix}{uuid4().hex[:5]}", kind=kind, title=values["title"], description=values.get("description"), items=items, tags=values.get("tags", []), pinned=False, status="active", submitted_at=None, created_at="2026-09-20 09:00:00", updated_at="2026-09-20 09:00:00")

    def list_recent(uid, n=5, include_archived=False):
        return [entry for entry in entries if include_archived or entry.status == "active"][:n]

    def find(uid, ref):
        return next((entry for entry in entries if str(entry.id) == ref or entry.short_id.casefold() == ref.casefold()), None)

    def update(uid, ref, callback):
        entry = find(uid, ref)
        if not entry or entry.status != "active":
            return None
        callback(entry)
        return entry

    def update_entry(uid, ref, changes):
        def apply(entry):
            for key, value in changes.items():
                if key == "items":
                    value = [
                        SimpleNamespace(
                            id=uuid4(),
                            text=item["text"],
                            done=item["done"],
                            order=index,
                        )
                        for index, item in enumerate(value)
                    ]
                setattr(entry, key, value)

        return update(uid, ref, apply)

    def archive(uid, ref, archived=True):
        entry = find(uid, ref)
        if not entry:
            return None
        entry.status = "archived" if archived else "active"
        return entry

    monkeypatch.setattr(manager, "create_note", lambda uid, **values: (entries.append(make(**values)) or entries[-1]))
    monkeypatch.setattr(manager, "create_journal", lambda uid, **values: (entries.append(make(kind="journal_entry", **values)) or entries[-1]))
    monkeypatch.setattr(manager, "create_list", lambda uid, **values: (entries.append(make(kind="list", **values)) or entries[-1]))
    monkeypatch.setattr(manager, "list_recent", list_recent)
    monkeypatch.setattr(manager, "list_pinned", lambda uid, limit=100: [entry for entry in entries if entry.status == "active" and entry.pinned][:limit])
    monkeypatch.setattr(manager, "list_inbox", lambda uid, days=30, limit=100: [entry for entry in entries if entry.status == "active" and not entry.tags][:limit])
    monkeypatch.setattr(manager, "search_entries", lambda uid, query, limit=100: [entry for entry in list_recent(uid, 100, True) if query.casefold() in (entry.title or "").casefold()])
    monkeypatch.setattr(manager, "set_entry_body", lambda uid, ref, text: update(uid, ref, lambda entry: setattr(entry, "description", text)))
    monkeypatch.setattr(manager, "set_entry_title", lambda uid, ref, text: update(uid, ref, lambda entry: setattr(entry, "title", text.strip())))
    monkeypatch.setattr(manager, "set_list_items", lambda uid, ref, items: update(uid, ref, lambda entry: setattr(entry, "items", [SimpleNamespace(id=uuid4(), text=item["text"], done=item["done"], order=index) for index, item in enumerate(items)])))
    monkeypatch.setattr(manager, "remove_tags", lambda uid, ref, tags: update(uid, ref, lambda entry: setattr(entry, "tags", [tag for tag in entry.tags if tag not in tags])))
    monkeypatch.setattr(manager, "add_tags", lambda uid, ref, tags: update(uid, ref, lambda entry: setattr(entry, "tags", list(dict.fromkeys([*entry.tags, *tags])))))
    monkeypatch.setattr(manager, "pin_entry", lambda uid, ref, pinned: update(uid, ref, lambda entry: setattr(entry, "pinned", pinned)))
    monkeypatch.setattr(manager, "update_entry", update_entry)
    monkeypatch.setattr(manager, "archive_entry", archive)
    monkeypatch.setattr(shared_tags, "get_user_tags", lambda uid: ["work", "personal"])
    entries.extend([
        SimpleNamespace(id=uuid4(), short_id="labc12", kind="list", title="Groceries", description=None, items=[SimpleNamespace(id=uuid4(), text="Oats", done=False, order=0)], tags=["home"], pinned=False, status="active", submitted_at=None, created_at="2026-09-19 09:00:00", updated_at="2026-09-19 09:00:00"),
        SimpleNamespace(id=uuid4(), short_id="jabc12", kind="journal_entry", title="Today", description="A steady day", items=None, tags=["journal"], pinned=False, status="active", submitted_at="2026-09-18 09:00:00", created_at="2026-09-18 09:00:00", updated_at="2026-09-18 09:00:00"),
    ])

    async with web_client(create_web_app(accounts=Accounts(), mailer=lambda email, code: sent.append(code), origin=ORIGIN, proxy_secret=""), cookie_jar=CookieJar(unsafe=True)) as client:
        challenge = (await (await client.post("/api/auth/request-code", json={"email": "river@example.com", "mode": "login"}, headers={"Origin": ORIGIN})).json())["challenge"]
        assert (await client.post("/api/auth/verify", json={"challenge": challenge, "code": sent[-1]}, headers={"Origin": ORIGIN})).status == 200
        yield client


async def test_note_create_edit_search_and_archive(notes_gateway):
    client = notes_gateway
    existing = await (await client.get("/api/notes")).json()
    assert {entry["kind"] for entry in existing["notes"]} == {"list", "journal_entry"}
    assert existing["tags"] == ["home", "journal", "personal", "work"]
    tagged = await (await client.get("/api/notes?tag=journal")).json()
    assert [entry["title"] for entry in tagged["notes"]] == ["Today"]
    created = await client.post("/api/notes", json={"title": "Appointment questions", "description": "Bring the list", "tags": ["Health", "prep"]}, headers={"Origin": ORIGIN})
    assert created.status == 201
    note = (await created.json())["note"]
    assert note["tags"] == ["health", "prep"]
    assert (await client.patch(f"/api/notes/{note['id']}", json={"description": "Bring the updated list", "tags": ["follow-up"]}, headers={"Origin": ORIGIN})).status == 200
    assert (await client.get("/api/notes?q=updated")).status == 200
    assert (await client.post(f"/api/notes/{note['id']}/archive", json={}, headers={"Origin": ORIGIN})).status == 200
    assert (await client.get("/api/notes?status=archived")).status == 200


async def test_note_accepts_maximum_unicode_description(notes_gateway):
    """The gateway byte limit must allow the handler's 10,000-character maximum."""
    response = await notes_gateway.post(
        "/api/notes",
        json={"title": "Unicode", "description": "🙂" * 10_000},
        headers={"Origin": ORIGIN},
    )
    assert response.status == 201


async def test_journal_and_list_create_and_edit(notes_gateway):
    client = notes_gateway
    journal_response = await client.post(
        "/api/notes",
        json={"kind": "journal_entry", "title": "Morning", "description": "Feeling rested", "tags": ["Daily"]},
        headers={"Origin": ORIGIN},
    )
    assert journal_response.status == 201
    journal = (await journal_response.json())["note"]
    assert journal["kind"] == "journal_entry"
    journal_update = await client.patch(
        f"/api/notes/{journal['id']}",
        json={"title": "Monday morning", "description": "Feeling rested and ready"},
        headers={"Origin": ORIGIN},
    )
    assert journal_update.status == 200
    updated_journal = (await journal_update.json())["note"]
    assert updated_journal["title"] == "Monday morning"
    assert updated_journal["description"] == "Feeling rested and ready"

    list_response = await client.post(
        "/api/notes",
        json={"kind": "list", "title": "Weekend", "items": [{"text": "Laundry", "done": False}, {"text": "Walk", "done": True}], "tags": ["home"]},
        headers={"Origin": ORIGIN},
    )
    assert list_response.status == 201
    list_entry = (await list_response.json())["note"]
    assert list_entry["kind"] == "list"
    assert list_entry["items"][1]["done"] is True
    list_update = await client.patch(
        f"/api/notes/{list_entry['id']}",
        json={"title": "Sunday", "items": [{"text": "Fold laundry", "done": True}, {"text": "Long walk", "done": False}]},
        headers={"Origin": ORIGIN},
    )
    assert list_update.status == 200
    updated_list = (await list_update.json())["note"]
    assert updated_list["title"] == "Sunday"
    assert updated_list["items"] == [
        {"id": updated_list["items"][0]["id"], "text": "Fold laundry", "done": True, "order": 0},
        {"id": updated_list["items"][1]["id"], "text": "Long walk", "done": False, "order": 1},
    ]


async def test_list_create_persists_final_items_in_one_operation(
    notes_gateway, monkeypatch
):
    """Completed states are included in the creation write, with no repair save."""
    import notebook.notebook_data_manager as manager

    original_create = manager.create_list
    calls = []

    def tracked_create(uid, **values):
        calls.append(values)
        return original_create(uid, **values)

    monkeypatch.setattr(manager, "create_list", tracked_create)
    monkeypatch.setattr(
        manager,
        "set_list_items",
        lambda *args, **kwargs: pytest.fail("second list save was called"),
    )

    response = await notes_gateway.post(
        "/api/notes",
        json={
            "kind": "list",
            "title": "One write",
            "items": [{"text": "Already done", "done": True}],
        },
        headers={"Origin": ORIGIN},
    )

    assert response.status == 201
    assert calls == [
        {
            "title": "One write",
            "items": [{"text": "Already done", "done": True}],
            "tags": [],
        }
    ]
    assert (await response.json())["note"]["items"][0]["done"] is True


async def test_notes_get_loads_one_notebook_snapshot(notes_gateway, monkeypatch):
    """One GET derives notes and tags from one worker-thread notebook read."""
    import notebook.notebook_data_manager as manager

    original_list_recent = manager.list_recent
    calls = []

    def tracked_list_recent(uid, n=5, include_archived=False):
        calls.append((uid, n, include_archived))
        return original_list_recent(uid, n=n, include_archived=include_archived)

    monkeypatch.setattr(manager, "list_recent", tracked_list_recent)

    response = await notes_gateway.get("/api/notes?status=active&tag=home")

    assert response.status == 200
    assert calls == [("existing", 1000, True)]


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "calendar", "title": "Unsupported"},
        {"kind": "list", "title": "Empty list", "items": []},
        {"kind": "list", "title": "Missing list"},
        {"kind": "list", "title": "Bad state", "items": [{"text": "One", "done": "yes"}]},
        {"kind": "journal_entry", "title": "Bad tags", "description": "Text", "tags": "daily"},
        {"kind": "note", "title": "Extra field", "unexpected": True},
    ],
)
async def test_notebook_create_rejects_invalid_entry_shapes(notes_gateway, payload):
    response = await notes_gateway.post("/api/notes", json=payload, headers={"Origin": ORIGIN})
    assert response.status == 400


async def test_notebook_edit_enforces_kind_and_active_state(notes_gateway):
    client = notes_gateway
    entries = (await (await client.get("/api/notes")).json())["notes"]
    list_entry = next(entry for entry in entries if entry["kind"] == "list")
    journal = next(entry for entry in entries if entry["kind"] == "journal_entry")

    assert (await client.patch(
        f"/api/notes/{list_entry['id']}",
        json={"description": "Lists use items"},
        headers={"Origin": ORIGIN},
    )).status == 400
    assert (await client.patch(
        f"/api/notes/{journal['id']}",
        json={"items": [{"text": "Wrong kind", "done": False}]},
        headers={"Origin": ORIGIN},
    )).status == 400
    assert (await client.patch(
        f"/api/notes/{journal['id']}",
        json={"title": ""},
        headers={"Origin": ORIGIN},
    )).status == 400

    assert (await client.post(
        f"/api/notes/{journal['id']}/archive", json={}, headers={"Origin": ORIGIN}
    )).status == 200
    assert (await client.patch(
        f"/api/notes/{journal['id']}",
        json={"title": "Cannot edit archived"},
        headers={"Origin": ORIGIN},
    )).status == 404
    assert (await client.post(
        f"/api/notes/{journal['id']}/restore", json={}, headers={"Origin": ORIGIN}
    )).status == 200
    restored = (await (await client.get("/api/notes")).json())["notes"]
    assert any(entry["id"] == journal["id"] for entry in restored)


async def test_notebook_queries_validate_status_and_filter_results(notes_gateway):
    client = notes_gateway
    assert (await client.get("/api/notes?status=unknown")).status == 400
    result = await (await client.get("/api/notes?q=grocer")).json()
    assert [entry["title"] for entry in result["notes"]] == ["Groceries"]

    entry_id = result["notes"][0]["id"]
    pinned = await client.patch(
        f"/api/notes/{entry_id}",
        json={"pinned": True, "tags": []},
        headers={"Origin": ORIGIN},
    )
    assert pinned.status == 200
    assert (await pinned.json())["note"]["pinned"] is True
    pinned_view = await (await client.get("/api/notes?status=pinned")).json()
    inbox_view = await (await client.get("/api/notes?status=inbox")).json()
    assert [entry["id"] for entry in pinned_view["notes"]] == [entry_id]
    assert [entry["id"] for entry in inbox_view["notes"]] == [entry_id]
    archived = await client.post(
        f"/api/notes/{entry_id}/archive", json={}, headers={"Origin": ORIGIN}
    )
    assert archived.status == 200
    assert (await archived.json())["note"]["pinned"] is False


async def test_notebook_create_failure_reports_nothing_was_added(
    notes_gateway, monkeypatch
):
    import notebook.notebook_data_manager as manager

    monkeypatch.setattr(manager, "create_note", lambda uid, **values: None)

    response = await notes_gateway.post(
        "/api/notes",
        json={"kind": "note", "title": "Keep this draft"},
        headers={"Origin": ORIGIN},
    )

    assert response.status == 503
    message = (await response.json())["error"]
    assert "Nothing was added" in message
    assert "try again" in message.lower()


async def test_notebook_archive_failure_reports_previous_section(
    notes_gateway, monkeypatch
):
    import notebook.notebook_data_manager as manager

    entries = (await (await notes_gateway.get("/api/notes")).json())["notes"]
    entry_id = entries[0]["id"]
    monkeypatch.setattr(manager, "archive_entry", lambda *args, **kwargs: None)

    response = await notes_gateway.post(
        f"/api/notes/{entry_id}/archive",
        json={},
        headers={"Origin": ORIGIN},
    )

    assert response.status == 503
    message = (await response.json())["error"]
    assert "not archived" in message
    assert "still in active notes" in message


async def test_notebook_edit_failure_explains_how_to_verify_current_version(
    notes_gateway, monkeypatch
):
    import notebook.notebook_data_manager as manager

    entries = (await (await notes_gateway.get("/api/notes")).json())["notes"]
    entry_id = entries[0]["id"]
    monkeypatch.setattr(manager, "update_entry", lambda *args, **kwargs: None)

    response = await notes_gateway.patch(
        f"/api/notes/{entry_id}",
        json={"title": "Updated title"},
        headers={"Origin": ORIGIN},
    )

    assert response.status == 503
    message = (await response.json())["error"]
    assert "could not finish saving" in message
    assert "Refresh the entry" in message


async def test_notebook_tag_removal_failure_is_not_reported_as_saved(
    notes_gateway, monkeypatch
):
    import notebook.notebook_data_manager as manager

    entries = (await (await notes_gateway.get("/api/notes")).json())["notes"]
    entry_id = entries[0]["id"]
    monkeypatch.setattr(manager, "update_entry", lambda *args, **kwargs: None)

    response = await notes_gateway.patch(
        f"/api/notes/{entry_id}",
        json={"tags": ["updated"]},
        headers={"Origin": ORIGIN},
    )

    assert response.status == 503
    message = (await response.json())["error"]
    assert "tag changes" in message
    assert "current tags" in message


async def test_notebook_patch_saves_all_changes_in_one_operation(
    notes_gateway, monkeypatch
):
    import notebook.notebook_data_manager as manager

    entries = (await (await notes_gateway.get("/api/notes")).json())["notes"]
    list_entry = next(entry for entry in entries if entry["kind"] == "list")
    original_update = manager.update_entry
    calls = []

    def tracked_update(uid, ref, changes):
        calls.append((uid, ref, dict(changes)))
        return original_update(uid, ref, changes)

    monkeypatch.setattr(manager, "update_entry", tracked_update)
    monkeypatch.setattr(
        manager,
        "set_entry_title",
        lambda *args, **kwargs: pytest.fail("legacy title save was called"),
    )
    monkeypatch.setattr(
        manager,
        "set_list_items",
        lambda *args, **kwargs: pytest.fail("legacy item save was called"),
    )
    monkeypatch.setattr(
        manager,
        "remove_tags",
        lambda *args, **kwargs: pytest.fail("legacy tag removal was called"),
    )
    monkeypatch.setattr(
        manager,
        "add_tags",
        lambda *args, **kwargs: pytest.fail("legacy tag addition was called"),
    )
    monkeypatch.setattr(
        manager,
        "pin_entry",
        lambda *args, **kwargs: pytest.fail("legacy pin save was called"),
    )

    changes = {
        "title": "Updated groceries",
        "items": [{"text": "Oats", "done": True}],
        "tags": ["errands"],
        "pinned": True,
    }
    response = await notes_gateway.patch(
        f"/api/notes/{list_entry['id']}",
        json=changes,
        headers={"Origin": ORIGIN},
    )

    assert response.status == 200
    assert len(calls) == 1
    assert calls[0][1] == list_entry["id"]
    assert calls[0][2] == changes
