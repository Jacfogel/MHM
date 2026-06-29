"""Unit tests for Google Health configuration."""

import importlib

import pytest

from core import config


pytestmark = [pytest.mark.core]


@pytest.mark.unit
def test_google_health_disabled_by_default(monkeypatch, request):
    """Env false resolves to disabled (isolated from project .env)."""
    monkeypatch.setenv("GOOGLE_HEALTH_ENABLED", "false")
    importlib.reload(config)
    request.addfinalizer(lambda: importlib.reload(config))
    assert config.GOOGLE_HEALTH_ENABLED is False


@pytest.mark.unit
def test_validate_google_health_when_disabled(monkeypatch, request):
    monkeypatch.setenv("GOOGLE_HEALTH_ENABLED", "false")
    importlib.reload(config)
    request.addfinalizer(lambda: importlib.reload(config))
    ok, errors, warnings = config.validate_google_health_configuration()
    assert ok is True
    assert not errors


@pytest.mark.unit
def test_parse_sync_times_default():
    times = config.parse_google_health_sync_times()
    assert "06:30" in times
    assert "18:00" in times


@pytest.mark.unit
def test_oauth_scopes_normalized():
    scopes = config.get_google_health_oauth_scopes()
    assert scopes
    assert all(s.startswith("https://www.googleapis.com/auth/") for s in scopes)


@pytest.mark.unit
def test_validate_warns_when_encryption_key_missing(monkeypatch, request):
    monkeypatch.setenv("GOOGLE_HEALTH_ENABLED", "true")
    monkeypatch.setenv("GOOGLE_HEALTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("GOOGLE_HEALTH_CLIENT_SECRET", "test-secret")
    monkeypatch.delenv("GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY", raising=False)
    importlib.reload(config)
    request.addfinalizer(lambda: importlib.reload(config))

    ok, errors, warnings = config.validate_google_health_configuration()
    assert ok is True
    assert not errors
    assert any("TOKEN_ENCRYPTION_KEY" in w for w in warnings)


@pytest.mark.unit
def test_validate_rejects_invalid_encryption_key(monkeypatch, request):
    monkeypatch.setenv("GOOGLE_HEALTH_ENABLED", "true")
    monkeypatch.setenv("GOOGLE_HEALTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("GOOGLE_HEALTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("GOOGLE_HEALTH_TOKEN_ENCRYPTION_KEY", "invalid-key")
    importlib.reload(config)
    request.addfinalizer(lambda: importlib.reload(config))

    ok, errors, _warnings = config.validate_google_health_configuration()
    assert ok is False
    assert any("TOKEN_ENCRYPTION_KEY" in err for err in errors)
