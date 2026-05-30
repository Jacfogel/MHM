"""Unit coverage for schedule document defaults and legacy migration."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from core.schedule_document_defaults import (
    create_default_schedule_periods,
    ensure_category_has_default_schedule,
    migrate_legacy_schedules_structure,
)


@pytest.mark.unit
@pytest.mark.core
def test_migrate_legacy_schedules_structure_wraps_flat_periods():
    legacy = {
        "motivational": {
            "Morning Message Default": {
                "active": True,
                "start_time": "09:00",
                "end_time": "12:00",
            }
        }
    }
    migrated = migrate_legacy_schedules_structure(legacy)

    assert "periods" in migrated["motivational"]
    assert "Morning Message Default" in migrated["motivational"]["periods"]
    assert migrated["motivational"]["periods"]["Morning Message Default"]["days"] == ["ALL"]


@pytest.mark.unit
@pytest.mark.core
def test_migrate_legacy_schedules_structure_preserves_new_format():
    modern = {
        "checkin": {
            "periods": {
                "Check-in Reminder Default": {
                    "active": True,
                    "days": ["ALL"],
                    "start_time": "18:00",
                    "end_time": "20:00",
                }
            }
        }
    }
    migrated = migrate_legacy_schedules_structure(modern)
    assert migrated == modern


@pytest.mark.unit
@pytest.mark.core
def test_migrate_legacy_schedules_structure_replaces_non_dict_category():
    legacy = {"health": "invalid"}
    migrated = migrate_legacy_schedules_structure(legacy)

    assert "periods" in migrated["health"]
    assert "Health Message Default" in migrated["health"]["periods"]


@pytest.mark.unit
@pytest.mark.core
def test_ensure_category_has_default_schedule_migrates_and_creates_periods():
    legacy_schedules = {
        "motivational": {
            "Morning Message Default": {
                "active": True,
                "start": "09:00",
                "end": "12:00",
            }
        }
    }

    with (
        patch(
            "core.schedule_document_defaults._get_user_data__load_schedules",
            return_value=legacy_schedules,
        ) as load_schedules,
        patch(
            "core.schedule_document_defaults._save_user_data__save_schedules"
        ) as save_schedules,
    ):
        result = ensure_category_has_default_schedule("user-1", "tasks")

    assert result is True
    load_schedules.assert_called_once_with("user-1")
    save_schedules.assert_called()
    saved_payload = save_schedules.call_args[0][1]
    assert "tasks" in saved_payload
    assert "Task Reminder Default" in saved_payload["tasks"]["periods"]


@pytest.mark.unit
@pytest.mark.core
def test_ensure_category_has_default_schedule_rejects_invalid_inputs():
    assert ensure_category_has_default_schedule("", "tasks") is False
    assert ensure_category_has_default_schedule("user-1", "") is False


@pytest.mark.unit
@pytest.mark.core
def test_create_default_schedule_periods_named_defaults():
    tasks = create_default_schedule_periods("tasks")
    checkin = create_default_schedule_periods("checkin")
    health = create_default_schedule_periods("health_and_wellness")

    assert "Task Reminder Default" in tasks
    assert "Check-in Reminder Default" in checkin
    assert "Health And Wellness Message Default" in health
