"""Unit tests for Google Health OAuth helpers."""

from unittest.mock import MagicMock, patch

import pytest

from integrations.google_health import auth
from integrations.google_health.testing import is_google_health_testing_mode

pytestmark = [pytest.mark.core, pytest.mark.integrations]


def _token_error_response(status_code: int, body: str) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = body
    return mock_resp


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
def test_is_google_health_testing_mode_reads_env(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "1")
    assert is_google_health_testing_mode() is True
    monkeypatch.setenv("MHM_TESTING", "0")
    assert is_google_health_testing_mode() is False


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


@pytest.mark.unit
def test_refresh_access_token_logs_dead_token_on_http_400(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    mock_resp = _token_error_response(
        400,
        '{"error":"invalid_grant","error_description":"Token has been expired or revoked."}',
    )
    with patch(
        "integrations.google_health.auth.requests.post", return_value=mock_resp
    ), patch("integrations.google_health.auth.logger") as mock_logger:
        assert auth.refresh_access_token("dead-refresh", user_id="user-1") is None
    error_text = " ".join(str(call.args[0]) for call in mock_logger.error.call_args_list)
    assert auth.DEAD_REFRESH_TOKEN_ERROR in error_text
    assert "invalid_grant" in error_text
    assert "user-1" in error_text
    assert "connect google health" in error_text
    mock_logger.warning.assert_not_called()


@pytest.mark.unit
def test_refresh_access_token_logs_transient_on_http_500(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    mock_resp = _token_error_response(500, '{"error":"server_error"}')
    with patch(
        "integrations.google_health.auth.requests.post", return_value=mock_resp
    ), patch("integrations.google_health.auth.logger") as mock_logger:
        assert auth.refresh_access_token("refresh") is None
    warning_text = " ".join(
        str(call.args[0]) for call in mock_logger.warning.call_args_list
    )
    assert "may be transient" in warning_text
    assert auth.DEAD_REFRESH_TOKEN_ERROR not in warning_text
    mock_logger.error.assert_not_called()


@pytest.mark.unit
def test_ensure_valid_access_token_returns_none_on_dead_refresh(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    auth_doc = {
        "access_token": "expired",
        "refresh_token": "dead-refresh",
        "expires_at": "2000-01-01 00:00:00",
    }
    mock_resp = _token_error_response(
        400,
        '{"error":"invalid_grant","error_description":"Token has been expired or revoked."}',
    )
    with patch(
        "integrations.google_health.auth.load_auth", return_value=auth_doc
    ), patch(
        "integrations.google_health.auth.requests.post", return_value=mock_resp
    ), patch("integrations.google_health.auth.logger") as mock_logger:
        assert auth.ensure_valid_access_token("user-1") is None
    error_text = " ".join(str(call.args[0]) for call in mock_logger.error.call_args_list)
    assert auth.DEAD_REFRESH_TOKEN_ERROR in error_text
    assert "invalid_grant" in error_text
