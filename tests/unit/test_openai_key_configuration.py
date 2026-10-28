"""Project OpenAI credentials must survive stale Windows parent environments."""

from unittest.mock import patch

import pytest

from core import config

pytestmark = [pytest.mark.unit, pytest.mark.core, pytest.mark.ai]


@pytest.mark.parametrize("local_key, expected", [("new-local-key", "new-local-key"), ("", ""), (None, "")])
def test_local_key_is_authoritative(monkeypatch, local_key, expected):
    """A local replacement or explicit disable wins over a stale inherited key."""
    monkeypatch.setenv("OPENAI_API_KEY", "stale-parent-key")
    with patch.object(config, "dotenv_values", return_value={"OPENAI_API_KEY": local_key}):
        assert config._resolve_openai_api_key() == expected


def test_environment_key_used_without_local_setting(monkeypatch):
    """Server deployments can still supply credentials entirely through the environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")
    with patch.object(config, "dotenv_values", return_value={}):
        assert config._resolve_openai_api_key() == "environment-key"


def test_local_file_failure_does_not_restore_stale_credential(monkeypatch):
    """An unreadable credential file fails closed instead of reviving an older key."""
    monkeypatch.setenv("OPENAI_API_KEY", "stale-parent-key")
    with patch.object(config, "dotenv_values", side_effect=OSError("cannot read local settings")):
        assert config._resolve_openai_api_key() == ""
