"""Self-service settings validation, ownership, and shared-storage checks."""

from copy import deepcopy

import pytest
import pytest_asyncio
from aiohttp import CookieJar
from aiohttp.test_utils import TestClient, TestServer

from core.web_account_service import create_web_app, MHMAccounts
from core.web_user_settings import build_settings_updates, settings_snapshot
from tests.unit.test_web_account_service import Accounts, ORIGIN, request_code, verify

pytestmark = [pytest.mark.unit, pytest.mark.user_management]

OPTIONS = {
    "timezones": ["America/Regina", "Europe/London"],
    "categories": ["motivational", "health"],
    "questions": {"mood": "Mood", "energy": "Energy", "sleep": "Sleep"},
}
WINDOW = {
    "active": True,
    "days": ["Monday"],
    "start_time": "09:00",
    "end_time": "10:00",
}
ALL = {"active": True, "days": ["ALL"], "start_time": "00:00", "end_time": "23:59"}


@pytest.fixture
def documents():
    return {
        "account": {
            "email": "river@example.com",
            "internal_username": "river",
            "account_status": "active",
            "timezone": "America/Regina",
            "features": {
                "automated_messages": "disabled",
                "checkins": "disabled",
                "task_management": "disabled",
                "google_health": "enabled",
            },
        },
        "context": {
            "preferred_name": "River",
            "goals": ["Rest"],
            "custom_fields": {"private": "keep"},
        },
        "preferences": {
            "categories": ["motivational"],
            "channel": {"type": "email"},
            "natural_language_defaults": {"keep": True},
            "task_settings": {"custom": "keep"},
            "checkin_settings": {
                "custom_questions": {"keep": True},
                "questions": {
                    "mood": {"custom": "keep", "always_include": True},
                    "archived": {"enabled": False},
                },
                "min_questions": 1,
                "max_questions": 1,
            },
        },
        "schedules": {
            "schema_version": 2,
            "categories": {
                category: {
                    "periods": {"ALL": deepcopy(ALL), "Morning": deepcopy(WINDOW)}
                }
                for category in ["motivational", "tasks", "checkin", "health"]
            },
        },
    }


def values(documents, section):
    return deepcopy(settings_snapshot(documents, OPTIONS)["sections"][section])


def test_sections_preserve_unrelated_admin_data_and_reserved_periods(documents):
    original = deepcopy(documents)
    profile = values(documents, "profile")
    profile["preferred_name"] = "  Willow  "
    updates = build_settings_updates(documents, OPTIONS, "profile", profile)
    assert set(updates) == {"context"}
    assert updates["context"]["custom_fields"] == {"private": "keep"}
    assert updates["context"]["preferred_name"] == "Willow"
    tasks = values(documents, "tasks")
    tasks["enabled"] = True
    tasks["recurring"]["default_recurrence_pattern"] = "weekly"
    updates = build_settings_updates(documents, OPTIONS, "tasks", tasks)
    assert updates["account"]["features"]["google_health"] == "enabled"
    assert updates["preferences"]["task_settings"]["custom"] == "keep"
    assert updates["preferences"]["natural_language_defaults"] == {"keep": True}
    assert updates["schedules"]["tasks"]["periods"]["ALL"] == ALL
    assert (
        updates["schedules"]["health"] == original["schedules"]["categories"]["health"]
    )
    assert documents == original


@pytest.mark.parametrize(
    "section,field,bad",
    [
        ("profile", "preferred_name", []),
        ("profile", "goals", [123]),
        ("delivery", "channel", []),
        ("delivery", "timezone", {}),
        ("messages", "categories", ["../private"]),
        ("tasks", "enabled", "true"),
        ("checkins", "questions", {"mood": [], "energy": "off", "sleep": "off"}),
    ],
)
def test_invalid_types_and_categories_are_rejected(documents, section, field, bad):
    draft = values(documents, section)
    draft[field] = bad
    with pytest.raises(ValueError):
        build_settings_updates(documents, OPTIONS, section, draft)


@pytest.mark.parametrize(
    "bad",
    [
        {"days": ["Funday"]},
        {"days": [[]]},
        {"days": ["Monday", "Monday"]},
        {"start_time": "11:00", "end_time": "10:00"},
        {"start_time": "99:00"},
    ],
)
def test_inactive_windows_are_still_validated(documents, bad):
    draft = values(documents, "tasks")
    draft["periods"] = {"Draft": {**WINDOW, "active": False, **bad}}
    with pytest.raises(ValueError):
        build_settings_updates(documents, OPTIONS, "tasks", draft)


def test_feature_requires_active_window_and_discord_requires_link(documents):
    draft = values(documents, "tasks")
    draft["periods"] = {}
    build_settings_updates(documents, OPTIONS, "tasks", draft)
    draft["enabled"] = True
    with pytest.raises(ValueError):
        build_settings_updates(documents, OPTIONS, "tasks", draft)
    delivery = {"channel": "discord", "timezone": "Europe/London"}
    with pytest.raises(ValueError):
        build_settings_updates(documents, OPTIONS, "delivery", delivery)
    documents["account"]["discord_user_id"] = "123456"
    assert (
        build_settings_updates(documents, OPTIONS, "delivery", delivery)["account"][
            "chat_id"
        ]
        == "123456"
    )


def test_checkin_rules_and_custom_metadata_are_preserved(documents):
    draft = values(documents, "checkins")
    draft.update(
        enabled=True,
        questions={"mood": "always", "energy": "sometimes", "sleep": "sometimes"},
        min_questions=1,
        max_questions=2,
    )
    updates = build_settings_updates(documents, OPTIONS, "checkins", draft)
    checkin = updates["preferences"]["checkin_settings"]
    assert checkin["custom_questions"] == {"keep": True}
    assert checkin["questions"]["mood"]["custom"] == "keep"
    assert checkin["questions"]["energy"]["sometimes_include"] is True
    assert "archived" in checkin["questions"]
    draft["max_questions"] = 3
    with pytest.raises(ValueError):
        build_settings_updates(documents, OPTIONS, "checkins", draft)


def test_unselected_message_windows_and_new_question_defaults_are_loaded(documents):
    options = {**OPTIONS, "question_defaults": {"energy": "sometimes"}}
    documents["preferences"]["checkin_settings"]["custom_questions"]["sleep"] = {
        "question_text": "Custom sleep",
        "always_include": True,
    }
    snapshot = settings_snapshot(documents, options)
    assert snapshot["sections"]["checkins"]["questions"]["energy"] == "sometimes"
    assert snapshot["sections"]["checkins"]["questions"]["sleep"] == "always"
    assert snapshot["available_message_periods"]["health"] == {"Morning": WINDOW}
    documents["schedules"]["categories"]["health"]["periods"]["Morning"][
        "start_time"
    ] = "08:00"
    assert (
        settings_snapshot(documents, options)["revisions"]["messages"]
        != snapshot["revisions"]["messages"]
    )


class SettingsAccounts(Accounts):
    def __init__(self, docs):
        super().__init__()
        self.docs = {"existing": deepcopy(docs), "other": deepcopy(docs)}
        self.users["existing"] = self.docs["existing"]["account"]
        self.saved = []

    def documents(self, uid):
        return deepcopy(self.docs[uid])

    def settings_options(self, uid):
        return deepcopy(OPTIONS)

    def save_settings(self, uid, updates):
        self.saved.append(uid)
        self.docs[uid].update(deepcopy(updates))
        self.users[uid] = self.docs[uid]["account"]
        return True


@pytest_asyncio.fixture
async def settings_gateway(documents):
    accounts, sent = SettingsAccounts(documents), []
    app = create_web_app(
        accounts=accounts,
        mailer=lambda email, code: sent.append(code),
        origin=ORIGIN,
        proxy_secret="",
    )
    async with TestClient(TestServer(app), cookie_jar=CookieJar(unsafe=True)) as client:
        yield client, accounts, sent


@pytest.mark.asyncio
async def test_api_session_ownership_csrf_conflicts_and_injected_fields(
    settings_gateway,
):
    client, accounts, sent = settings_gateway
    assert (await client.get("/api/settings")).status == 401
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1])).status == 200
    snapshot = await (await client.get("/api/settings")).json()
    assert "email" not in snapshot["sections"]["profile"]
    payload = {
        "section": "profile",
        "values": snapshot["sections"]["profile"],
        "revision": snapshot["revisions"]["profile"],
    }
    payload["values"]["preferred_name"] = "Willow"
    assert (await client.post("/api/settings", json=payload)).status == 403
    payload["user_id"] = "other"
    assert (
        await client.post("/api/settings", json=payload, headers={"Origin": ORIGIN})
    ).status == 400
    del payload["user_id"]
    payload["values"]["account_status"] = "active"
    assert (
        await client.post("/api/settings", json=payload, headers={"Origin": ORIGIN})
    ).status == 400
    del payload["values"]["account_status"]
    response = await client.post(
        "/api/settings", json=payload, headers={"Origin": ORIGIN}
    )
    assert response.status == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert accounts.saved == ["existing"]
    assert accounts.docs["other"]["context"]["preferred_name"] == "River"
    assert accounts.docs["existing"]["context"]["preferred_name"] == "Willow"
    assert (
        await client.post("/api/settings", json=payload, headers={"Origin": ORIGIN})
    ).status == 409
    assert (await client.get("/settings.js")).status == 200
    accounts.users["existing"]["account_status"] = "suspended"
    assert (await client.get("/api/settings")).status == 401


@pytest.mark.file_io
def test_saved_settings_use_existing_v2_profile_and_schedule_storage(test_data_dir):
    from core.profile_v2_io import schedule_categories
    from tests.test_helpers.test_utilities import TestUserFactory

    uid = "test_web_settings_storage"
    assert TestUserFactory.create_basic_user(
        uid, enable_checkins=False, test_data_dir=test_data_dir
    )
    adapter = MHMAccounts()
    uid = adapter.by_email(f"{uid}@example.com")[0]
    docs = adapter.documents(uid)
    profile = values(docs, "profile")
    profile["preferred_name"] = "Web profile"
    assert adapter.save_settings(
        uid, build_settings_updates(docs, OPTIONS, "profile", profile)
    )
    docs = adapter.documents(uid)
    assert docs["context"]["preferred_name"] == "Web profile"
    tasks = values(docs, "tasks")
    tasks.update(enabled=True, periods={"Morning": deepcopy(WINDOW)})
    tasks["recurring"]["default_recurrence_pattern"] = "weekly"
    assert adapter.save_settings(
        uid, build_settings_updates(docs, OPTIONS, "tasks", tasks)
    )
    saved = adapter.documents(uid)
    assert saved["account"]["features"]["task_management"] == "enabled"
    assert (
        schedule_categories(saved["schedules"])["tasks"]["periods"]["Morning"] == WINDOW
    )
    assert (
        saved["preferences"]["task_settings"]["recurring_settings"][
            "default_recurrence_pattern"
        ]
        == "weekly"
    )
    assert adapter.save_settings(
        uid,
        build_settings_updates(
            saved,
            OPTIONS,
            "delivery",
            {"channel": "email", "timezone": "Europe/London"},
        ),
    )
    saved = adapter.documents(uid)
    assert saved["account"]["chat_id"] == saved["account"]["email"]
    assert saved["preferences"]["channel"]["type"] == "email"
    messages = values(saved, "messages")
    messages.update(
        enabled=True,
        categories=["motivational"],
        periods={"motivational": {"Morning": deepcopy(WINDOW)}},
    )
    assert adapter.save_settings(
        uid, build_settings_updates(saved, OPTIONS, "messages", messages)
    )
    saved = adapter.documents(uid)
    assert saved["preferences"]["categories"] == ["motivational"]
    options = adapter.settings_options(uid)
    checkins = deepcopy(settings_snapshot(saved, options)["sections"]["checkins"])
    checkins.update(
        enabled=True,
        periods={"Morning": deepcopy(WINDOW)},
        questions={key: "off" for key in options["questions"]},
        min_questions=1,
        max_questions=1,
    )
    checkins["questions"][next(iter(options["questions"]))] = "always"
    assert adapter.save_settings(
        uid, build_settings_updates(saved, options, "checkins", checkins)
    )
    saved = adapter.documents(uid)
    assert saved["account"]["features"]["checkins"] == "enabled"
    assert (
        schedule_categories(saved["schedules"])["checkin"]["periods"]["Morning"]
        == WINDOW
    )
    assert saved["context"]["preferred_name"] == "Web profile"
