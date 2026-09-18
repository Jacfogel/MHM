"""Self-service settings validation, ownership, and shared-storage checks."""

from copy import deepcopy

import pytest
import pytest_asyncio
from aiohttp import CookieJar

from core.error_handling import ValidationError
from core.web_account_service import create_web_app, MHMAccounts
from core.web_user_settings import (
    _available_message_categories,
    _editable_custom_questions,
    build_settings_updates,
    settings_snapshot,
)
from tests.unit.test_web_account_service import Accounts, ORIGIN, request_code, verify, web_client

pytestmark = [pytest.mark.unit, pytest.mark.user]

OPTIONS = {
    "timezones": ["America/Regina", "Europe/London"],
    "categories": ["motivational", "health"],
    "questions": {"mood": "Mood", "energy": "Energy", "sleep": "Sleep"},
    "question_category_map": {"mood": "mood", "energy": "energy", "sleep": "energy"},
    "question_categories": {
        "mood": {"name": "Mood"},
        "energy": {"name": "Energy"},
        "health": {"name": "Health"},
        "activities": {"name": "Activities"},
    },
    "question_templates": {},
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
                "custom_questions": {},
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


def test_settings_helpers_reject_invalid_current_schema_inputs():
    assert _available_message_categories(None, {}) == []
    with pytest.raises(ValidationError):
        _editable_custom_questions(None)


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


def test_extended_profile_and_phrase_settings_round_trip_without_losing_private_data(
    documents,
):
    assert values(documents, "phrases")["time_of_day_defaults"]["morning"] == "09:00"
    profile = values(documents, "profile")
    profile.update(
        date_of_birth="1990-02-28",
        gender_identity=["non-binary"],
        health_conditions=["Migraine"],
        medications_treatments=["Daily medication"],
        reminders_needed=["Refill prescription"],
        allergies_sensitivities=["Latex"],
        loved_ones=[
            {
                "name": "Sam",
                "type": "friend",
                "relationships": ["walking buddy", "emergency contact"],
            }
        ],
    )
    updates = build_settings_updates(documents, OPTIONS, "profile", profile)
    assert updates["context"]["date_of_birth"] == "1990-02-28"
    assert updates["context"]["gender_identity"] == ["non-binary"]
    assert updates["context"]["loved_ones"] == [
        {
            "name": "Sam",
            "type": "friend",
            "relationships": ["walking buddy", "emergency contact"],
        }
    ]
    assert updates["context"]["custom_fields"] == {
        "private": "keep",
        "health_conditions": ["Migraine"],
        "medications_treatments": ["Daily medication"],
        "reminders_needed": ["Refill prescription"],
        "allergies_sensitivities": ["Latex"],
    }

    phrases = values(documents, "phrases")
    phrases.update(
        tonight_start_time="19:30",
        after_work_school_time="16:45",
        time_of_day_defaults={
            "morning": "08:00",
            "afternoon": "13:30",
            "evening": "18:30",
            "night": "22:00",
        },
        weekend_this_week_means_coming_week=False,
    )
    phrase_updates = build_settings_updates(documents, OPTIONS, "phrases", phrases)
    assert phrase_updates["preferences"]["natural_language_defaults"] == phrases
    assert phrase_updates["preferences"]["task_settings"] == {"custom": "keep"}


@pytest.mark.parametrize("invalid", ["1990-02-30", "2999-01-01", "02/28/1990"])
def test_profile_rejects_invalid_or_future_birth_dates(documents, invalid):
    profile = values(documents, "profile")
    profile["date_of_birth"] = invalid
    with pytest.raises(ValidationError):
        build_settings_updates(documents, OPTIONS, "profile", profile)


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
    with pytest.raises(ValidationError):
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
    with pytest.raises(ValidationError):
        build_settings_updates(documents, OPTIONS, "tasks", draft)


def test_feature_requires_active_window_and_discord_requires_link(documents):
    draft = values(documents, "tasks")
    draft["periods"] = {}
    build_settings_updates(documents, OPTIONS, "tasks", draft)
    draft["enabled"] = True
    with pytest.raises(ValidationError):
        build_settings_updates(documents, OPTIONS, "tasks", draft)
    delivery = {"channel": "discord", "timezone": "Europe/London"}
    with pytest.raises(ValidationError):
        build_settings_updates(documents, OPTIONS, "delivery", delivery)
    documents["account"]["discord_user_id"] = "123456"
    assert (
        build_settings_updates(documents, OPTIONS, "delivery", delivery)["account"][
            "chat_id"
        ]
        == "123456"
    )


def test_checkin_rules_and_question_metadata_are_preserved(documents):
    draft = values(documents, "checkins")
    draft.update(
        enabled=True,
        questions={"mood": "always", "energy": "sometimes", "sleep": "sometimes"},
        min_questions=1,
        max_questions=2,
    )
    updates = build_settings_updates(documents, OPTIONS, "checkins", draft)
    checkin = updates["preferences"]["checkin_settings"]
    assert checkin["custom_questions"] == {}
    assert checkin["questions"]["mood"]["custom"] == "keep"
    assert checkin["questions"]["energy"]["sometimes_include"] is True
    assert "archived" in checkin["questions"]
    draft["max_questions"] = 3
    with pytest.raises(ValidationError):
        build_settings_updates(documents, OPTIONS, "checkins", draft)


def test_custom_checkin_question_can_be_added_loaded_and_removed(documents):
    question_key = "custom_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    draft = values(documents, "checkins")
    draft.update(enabled=True, min_questions=2, max_questions=2)
    draft["custom_questions"] = {
        question_key: {
            "question_text": "Did you spend time outside?",
            "ui_display_name": "Time outside",
            "type": "yes_no",
            "category": "activities",
            "validation": {"error_message": "Please answer yes or no."},
        }
    }
    draft["questions"][question_key] = "always"

    updates = build_settings_updates(documents, OPTIONS, "checkins", draft)
    checkin = updates["preferences"]["checkin_settings"]
    assert checkin["custom_questions"][question_key] == {
        "question_text": "Did you spend time outside?",
        "ui_display_name": "Time outside",
        "type": "yes_no",
        "category": "activities",
        "enabled": True,
        "always_include": True,
        "sometimes_include": False,
        "validation": {"error_message": "Please answer yes or no."},
    }
    assert checkin["questions"][question_key]["always_include"] is True

    saved = deepcopy(documents)
    saved.update(deepcopy(updates))
    loaded = values(saved, "checkins")
    assert loaded["custom_questions"][question_key]["question_text"] == (
        "Did you spend time outside?"
    )
    assert loaded["questions"][question_key] == "always"

    loaded["custom_questions"].pop(question_key)
    loaded["questions"].pop(question_key)
    loaded.update(enabled=True, min_questions=1, max_questions=1)
    removed = build_settings_updates(saved, OPTIONS, "checkins", loaded)
    removed_checkin = removed["preferences"]["checkin_settings"]
    assert question_key not in removed_checkin["custom_questions"]
    assert question_key not in removed_checkin["questions"]
    assert removed_checkin["custom_questions"] == {}


def test_custom_checkin_question_rejects_untrusted_definition(documents):
    draft = values(documents, "checkins")
    draft["custom_questions"] = {
        "custom_not-a-safe-id": {
            "question_text": "Unsafe question",
            "type": "html",
        }
    }
    draft["questions"]["custom_not-a-safe-id"] = "off"

    with pytest.raises(ValidationError):
        build_settings_updates(documents, OPTIONS, "checkins", draft)


def test_settings_snapshot_rejects_obsolete_saved_custom_question_shape(documents):
    documents["preferences"]["checkin_settings"]["custom_questions"] = {
        "custom_old": {"question_text": "Old incomplete definition"}
    }

    with pytest.raises(ValidationError):
        settings_snapshot(documents, OPTIONS)


def test_unselected_message_windows_and_new_question_defaults_are_loaded(documents):
    options = {**OPTIONS, "question_defaults": {"energy": "sometimes"}}
    snapshot = settings_snapshot(documents, options)
    assert snapshot["sections"]["checkins"]["questions"]["energy"] == "sometimes"
    assert snapshot["available_message_periods"]["health"] == {"Morning": WINDOW}
    documents["schedules"]["categories"]["health"]["periods"]["Morning"][
        "start_time"
    ] = "08:00"
    assert (
        settings_snapshot(documents, options)["revisions"]["messages"]
        != snapshot["revisions"]["messages"]
    )


@pytest.mark.parametrize("feature", ["checkins", "google_health"])
def test_personalized_messages_are_available_with_a_health_data_source(
    documents, feature
):
    options = {
        **OPTIONS,
        "categories": [
            *OPTIONS["categories"],
            "personalized_checkin",
            "personalized_google_health",
            "personalized_profile",
        ],
    }
    documents["account"]["features"].update(
        {"checkins": "disabled", "google_health": "disabled", feature: "enabled"}
    )

    snapshot = settings_snapshot(documents, options)

    expected = (
        "personalized_checkin"
        if feature == "checkins"
        else "personalized_google_health"
    )
    assert expected in snapshot["options"]["categories"]
    assert expected in snapshot["available_message_periods"]
    assert "personalized_profile" in snapshot["options"]["categories"]


def test_personalized_messages_are_hidden_and_rejected_without_health_data(documents):
    options = {
        **OPTIONS,
        "categories": [
            *OPTIONS["categories"],
            "personalized_checkin",
            "personalized_google_health",
            "personalized_profile",
        ],
    }
    documents["account"]["features"].update(
        {"checkins": "disabled", "google_health": "disabled"}
    )
    documents["preferences"]["categories"].append("personalized_checkin")

    snapshot = settings_snapshot(documents, options)

    assert "personalized_checkin" not in snapshot["options"]["categories"]
    assert "personalized_google_health" not in snapshot["options"]["categories"]
    assert "personalized_profile" in snapshot["options"]["categories"]
    assert "personalized_checkin" not in snapshot["sections"]["messages"]["categories"]
    forged = deepcopy(snapshot["sections"]["messages"])
    forged["categories"].append("personalized_checkin")
    forged["periods"]["personalized_checkin"] = {"Morning": deepcopy(WINDOW)}
    with pytest.raises(ValidationError):
        build_settings_updates(documents, options, "messages", forged)


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
    async with web_client(app, cookie_jar=CookieJar(unsafe=True)) as client:
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


@pytest.mark.asyncio
async def test_personal_message_library_crud_uses_allowed_categories_and_periods(
    settings_gateway, monkeypatch
):
    from messages import message_data_manager as manager

    client, _, sent = settings_gateway
    stored = []
    monkeypatch.setattr(manager, "load_user_messages", lambda uid, category: deepcopy(stored))
    monkeypatch.setattr(manager, "is_ai_generated_message_category", lambda category: False)
    monkeypatch.setattr(manager, "add_message", lambda uid, category, message: stored.append(deepcopy(message)))

    def edit(uid, category, message_id, values):
        target = next(item for item in stored if item["id"] == message_id)
        target.update(deepcopy(values))

    monkeypatch.setattr(manager, "edit_message", edit)
    monkeypatch.setattr(manager, "delete_message", lambda uid, category, message_id: stored.remove(next(item for item in stored if item["id"] == message_id)))
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1])).status == 200

    payload = {
        "text": "Take one gentle step.",
        "active": True,
        "days": ["MONDAY"],
        "periods": ["Morning"],
    }
    created = await client.post(
        "/api/messages?category=motivational",
        json=payload,
        headers={"Origin": ORIGIN},
    )
    assert created.status == 201
    message = (await created.json())["message"]
    assert message["text"] == payload["text"]
    assert message["periods"] == ["Morning"]

    changed = {**payload, "text": "Pause, then take one gentle step.", "active": False}
    edited = await client.patch(
        f"/api/messages/motivational/{message['id']}",
        json=changed,
        headers={"Origin": ORIGIN},
    )
    assert edited.status == 200
    assert (await edited.json())["message"]["active"] is False
    assert (await client.post(
        "/api/messages?category=motivational",
        json={**payload, "periods": ["Unknown"]},
        headers={"Origin": ORIGIN},
    )).status == 400
    assert (await client.delete(
        f"/api/messages/motivational/{message['id']}",
        json={},
        headers={"Origin": ORIGIN},
    )).status == 200
    assert stored == []


@pytest.mark.asyncio
async def test_authenticated_delivery_actions_write_scoped_service_requests(
    settings_gateway, monkeypatch, tmp_path
):
    from core import service_utilities
    client, accounts, sent = settings_gateway
    accounts.docs["existing"]["preferences"]["channel"] = {"type": "email"}
    accounts.docs["existing"]["account"]["features"]["checkins"] = "enabled"
    monkeypatch.setattr(service_utilities, "get_flags_dir", lambda: tmp_path)
    token = (await (await request_code(client)).json())["challenge"]
    assert (await verify(client, token, sent[-1])).status == 200

    for payload, filename in (
        (
            {"action": "test_message", "category": "motivational"},
            "test_message_request_existing_motivational.flag",
        ),
        ({"action": "checkin_prompt"}, "checkin_prompt_request_existing.flag"),
    ):
        response = await client.post(
            "/api/actions", json=payload, headers={"Origin": ORIGIN}
        )
        assert response.status == 200
        assert (tmp_path / filename).exists()

    removed = await client.post(
        "/api/actions",
        json={"action": "task_reminder", "task_id": "task-1"},
        headers={"Origin": ORIGIN},
    )
    assert removed.status == 400


@pytest.mark.file_io
@pytest.mark.no_parallel  # shared user index and test_data_dir under xdist
def test_saved_settings_use_existing_v2_profile_and_schedule_storage(test_data_dir):
    from core.profile_v2_io import schedule_categories
    from tests.test_helpers.test_utilities import TestUserFactory

    uid = "test_web_settings_storage"
    assert TestUserFactory.create_basic_user(
        uid, enable_checkins=False, test_data_dir=test_data_dir
    )
    adapter = MHMAccounts()
    match = adapter.by_email(f"{uid}@example.com")
    assert match is not None
    uid = match[0]
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
    assert set(options["question_category_map"]) == set(options["questions"])
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
