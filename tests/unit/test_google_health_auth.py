"""Unit tests for Google Health OAuth helpers."""

from unittest.mock import MagicMock, patch

import pytest

from integrations.google_health import auth

pytestmark = [pytest.mark.core]


@pytest.mark.unit
def test_build_authorization_url_excludes_include_granted_scopes():
    with patch.object(auth, "GOOGLE_HEALTH_CLIENT_ID", "cid"), patch(
        "core.config.get_google_health_oauth_scopes", return_value=["scope-a"]
    ):
        url = auth.build_authorization_url(state="user-1")
    assert "include_granted_scopes" not in url
    assert "client_id=cid" in url
    assert "access_type=offline" in url


@pytest.mark.unit
def test_refresh_access_token_skips_in_testing_mode(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "1")
    assert auth.refresh_access_token("refresh") is None


@pytest.mark.unit
def test_exchange_code_skips_in_testing_mode(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "1")
    assert auth.exchange_code_for_tokens("code") is None


@pytest.mark.unit
def test_refresh_access_token_success(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "new", "expires_in": 3600}
    with patch("integrations.google_health.auth.requests.post", return_value=mock_resp):
        data = auth.refresh_access_token("refresh-token")
    assert data["access_token"] == "new"
