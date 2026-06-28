"""Unit tests for corrupt health JSON recovery."""

import pytest

from integrations.google_health.data_handlers import load_daily_summaries, save_daily_summaries
from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory


@pytest.mark.unit
@pytest.mark.user
def test_corrupt_daily_summaries_returns_empty_document(test_data_dir):
    from pathlib import Path

    from core.config import get_user_data_dir

    user_id = "health-corrupt-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    health_dir = Path(get_user_data_dir(user_id)) / "health"
    health_dir.mkdir(parents=True, exist_ok=True)
    (health_dir / "daily_summaries.json").write_text("{not valid json", encoding="utf-8")

    doc = load_daily_summaries(user_id)
    assert doc is not None
    assert doc.get("schema_version") == 2
    assert doc.get("summaries") == []


@pytest.mark.unit
@pytest.mark.user
def test_schema_round_trip(test_data_dir):
    user_id = "health-roundtrip-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    payload = {
        "schema_version": 2,
        "updated_at": "2026-06-27 12:00:00",
        "summaries": [
            {
                "date": "2026-06-27",
                "sleep_duration_minutes": 420,
                "steps": 5000,
                "completeness": ["sleep", "activity"],
            }
        ],
    }
    assert save_daily_summaries(user_id, payload) is True
    loaded = load_daily_summaries(user_id)
    assert loaded["summaries"][0]["steps"] == 5000
