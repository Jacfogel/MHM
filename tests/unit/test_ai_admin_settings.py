"""Shared storage and execution enforcement for desktop administrator controls."""

import json
import subprocess
import sys
from unittest.mock import patch

import pytest

from core import config
from core.ai_usage_settings import (
    AI_FEATURE_LABELS,
    AI_SETTINGS_FILE,
    read_ai_usage_settings,
    save_ai_usage_settings,
)
from ai.usage_policy import AIUsageFeature, is_ai_usage_allowed
from ai.client.lm_studio_client import complete_lm_studio_chat

pytestmark = [pytest.mark.unit, pytest.mark.ai]


@pytest.fixture(autouse=True)
def isolated_admin_settings(tmp_path, monkeypatch):
    """Keep administrator settings isolated from the running installation."""
    monkeypatch.setattr(config, "BASE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(config, "AI_USAGE_MODE", "automatic")
    monkeypatch.setattr(config, "AI_DISABLED_FEATURES", "")
    return tmp_path


def test_saved_switches_override_environment_and_block_http(isolated_admin_settings):
    assert set(AI_FEATURE_LABELS) == {
        item.value for item in AIUsageFeature if item is not AIUsageFeature.GENERIC
    }
    assert save_ai_usage_settings("automatic", ["conversation", "task_breakdown"])
    assert read_ai_usage_settings()["source"] == "desktop"
    assert is_ai_usage_allowed(AIUsageFeature.TASK_EFFORT)
    with patch("ai.client.lm_studio_client.requests.post") as request:
        result = complete_lm_studio_chat(
            [{"role": "user", "content": "Hello"}],
            usage_feature=AIUsageFeature.CONVERSATION,
        )
    assert result.text is None
    request.assert_not_called()
    assert save_ai_usage_settings("off", ["conversation", "task_breakdown"])
    assert all(not is_ai_usage_allowed(feature) for feature in AIUsageFeature)
    assert save_ai_usage_settings("automatic", ["conversation", "task_breakdown"])
    assert not is_ai_usage_allowed(AIUsageFeature.TASK_BREAKDOWN)
    assert is_ai_usage_allowed(AIUsageFeature.TASK_EFFORT)


def test_saved_change_is_seen_by_another_process(isolated_admin_settings):
    assert save_ai_usage_settings("off", [])
    script = (
        "import sys; from core import config; config.BASE_DATA_DIR = sys.argv[1]; "
        "from ai.usage_policy import is_ai_usage_allowed; "
        "assert not is_ai_usage_allowed()"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(isolated_admin_settings)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr


def test_environment_defaults_can_be_restored_and_remain_live(monkeypatch):
    monkeypatch.setattr(config, "AI_USAGE_MODE", "off")
    assert not is_ai_usage_allowed()
    assert save_ai_usage_settings("automatic", [])
    assert is_ai_usage_allowed()
    assert save_ai_usage_settings("automatic", [], use_environment=True)
    assert read_ai_usage_settings()["source"] == "environment"
    assert not is_ai_usage_allowed()
    monkeypatch.setattr(config, "AI_USAGE_MODE", "automatic")
    assert is_ai_usage_allowed()


@pytest.mark.parametrize(
    "content",
    [
        "{broken",
        "[]",
        "{}",
        '{"schema_version":1,"use_environment":false,"mode":"sometimes","disabled_features":[]}',
        '{"schema_version":1,"use_environment":false,"mode":"automatic","disabled_features":["unknown"]}',
    ],
)
def test_bad_saved_controls_fail_closed(isolated_admin_settings, content):
    (isolated_admin_settings / AI_SETTINGS_FILE).write_text(content, encoding="utf-8")
    assert read_ai_usage_settings()["source"] == "invalid"
    assert not is_ai_usage_allowed()
    valid, errors, _warnings = config.validate_ai_configuration()
    assert not valid
    assert any("Desktop AI controls" in error for error in errors)


def test_invalid_or_failed_save_keeps_last_working_policy(isolated_admin_settings):
    assert save_ai_usage_settings("off", [])
    assert not save_ai_usage_settings("automatic", ["unknown"])
    with patch("core.ai_usage_settings.save_runtime_state_json", return_value=False):
        assert not save_ai_usage_settings("automatic", [])
    assert not is_ai_usage_allowed()
    saved = json.loads(
        (isolated_admin_settings / AI_SETTINGS_FILE).read_text(encoding="utf-8")
    )
    assert saved["mode"] == "off"


def test_global_off_override_does_not_require_model_configuration(monkeypatch):
    assert save_ai_usage_settings("off", [])
    monkeypatch.setattr(config, "LM_STUDIO_BASE_URL", "")
    valid, errors, _warnings = config.validate_ai_configuration()
    assert valid
    assert not errors


def test_enabling_ai_in_desktop_requires_model_configuration(monkeypatch):
    monkeypatch.setattr(config, "AI_USAGE_MODE", "off")
    monkeypatch.setattr(config, "LM_STUDIO_BASE_URL", "")
    assert save_ai_usage_settings("automatic", [])
    valid, errors, _warnings = config.validate_ai_configuration()
    assert not valid
    assert "LM_STUDIO_BASE_URL is not configured" in errors
