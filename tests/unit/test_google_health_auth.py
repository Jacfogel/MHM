"""Unit tests for Google Health OAuth helpers."""

import uuid
from datetime import datetime, timedelta
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


@pytest.mark.unit
def test_build_authorization_url_omits_state_when_empty():
    with patch.object(auth, "GOOGLE_HEALTH_CLIENT_ID", "cid"), patch(
        "core.config.get_google_health_oauth_scopes", return_value=["scope-a"]
    ):
        url = auth.build_authorization_url()
    assert "state=" not in url
    assert "client_id=cid" in url


@pytest.mark.unit
def test_exchange_code_for_tokens_success(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "exchanged", "refresh_token": "r"}
    with patch("integrations.google_health.auth.requests.post", return_value=mock_resp):
        data = auth.exchange_code_for_tokens("auth-code")
    assert data["access_token"] == "exchanged"


@pytest.mark.unit
def test_exchange_code_for_tokens_http_error_returns_none(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = '{"error":"invalid_grant"}'
    with patch("integrations.google_health.auth.requests.post", return_value=mock_resp):
        assert auth.exchange_code_for_tokens("bad-code") is None


@pytest.mark.unit
def test_oauth_error_fields_handles_malformed_bodies():
    assert auth._oauth_error_fields(MagicMock(text=None)) == ("", "")
    assert auth._oauth_error_fields(MagicMock(text="plain failure")) == ("", "")
    assert auth._oauth_error_fields(MagicMock(text="{not-json")) == ("", "")
    assert auth._oauth_error_fields(MagicMock(text='[1, {"x": 1}]')) == ("", "")
    error, description = auth._oauth_error_fields(
        MagicMock(text='{"error":"invalid_client","error_description":"bad client"}')
    )
    assert error == "invalid_client"
    assert description == "bad client"


@pytest.mark.unit
def test_is_dead_refresh_token_failure_uses_status_and_oauth_error():
    assert auth._is_dead_refresh_token_failure(401, "") is True
    assert auth._is_dead_refresh_token_failure(503, "") is False
    assert auth._is_dead_refresh_token_failure(200, "unauthorized_client") is True


@pytest.mark.unit
def test_refresh_access_token_logs_dead_token_on_http_401(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    mock_resp = _token_error_response(401, "not json")
    with patch(
        "integrations.google_health.auth.requests.post", return_value=mock_resp
    ), patch("integrations.google_health.auth.logger") as mock_logger:
        assert auth.refresh_access_token("refresh") is None
    error_text = " ".join(str(call.args[0]) for call in mock_logger.error.call_args_list)
    assert auth.DEAD_REFRESH_TOKEN_ERROR in error_text
    mock_logger.warning.assert_not_called()


@pytest.mark.unit
def test_expires_at_from_token_response():
    stamp = auth._expires_at_from_token_response({"expires_in": 3600})
    datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")
    assert auth._expires_at_from_token_response({}) == ""
    assert auth._expires_at_from_token_response({"expires_in": "soon"}) == ""


@pytest.mark.unit
def test_token_needs_refresh_missing_near_and_valid_expiry():
    assert auth._token_needs_refresh({}) is True
    assert auth._token_needs_refresh({"expires_at": "not-a-timestamp"}) is True
    assert auth._token_needs_refresh({"expires_at": "2099-12-31 23:59:59"}) is False

    fixed_now = datetime(2026, 8, 31, 12, 0, 0)
    soon = (fixed_now + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    with patch.object(auth, "now_datetime_full", return_value=fixed_now), patch.object(
        auth, "GOOGLE_HEALTH_TOKEN_REFRESH_MARGIN_MINUTES", 15
    ):
        assert auth._token_needs_refresh({"expires_at": soon}) is True


@pytest.mark.unit
def test_ensure_valid_access_token_returns_none_without_auth():
    with patch("integrations.google_health.auth.load_auth", return_value=None):
        assert auth.ensure_valid_access_token("missing-user") is None


@pytest.mark.unit
def test_ensure_valid_access_token_returns_current_when_unexpired():
    auth_doc = {
        "access_token": "still-good",
        "refresh_token": "refresh",
        "expires_at": "2099-12-31 23:59:59",
    }
    with patch("integrations.google_health.auth.load_auth", return_value=auth_doc), patch(
        "integrations.google_health.auth.refresh_access_token"
    ) as refresh_mock:
        assert auth.ensure_valid_access_token("user-1") == "still-good"
    refresh_mock.assert_not_called()


@pytest.mark.unit
def test_ensure_valid_access_token_returns_none_without_refresh_token():
    auth_doc = {
        "access_token": "expired",
        "refresh_token": "",
        "expires_at": "2000-01-01 00:00:00",
    }
    with patch("integrations.google_health.auth.load_auth", return_value=auth_doc), patch(
        "integrations.google_health.auth.logger"
    ) as mock_logger:
        assert auth.ensure_valid_access_token("user-1") is None
    warning_text = " ".join(
        str(call.args[0]) for call in mock_logger.warning.call_args_list
    )
    assert "no refresh token" in warning_text


@pytest.mark.unit
@pytest.mark.user
def test_ensure_valid_access_token_persists_refreshed_tokens(test_data_dir, monkeypatch):
    from integrations.google_health.data_handlers import load_auth, save_auth
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    monkeypatch.delenv("MHM_TESTING", raising=False)
    user_id = f"health-auth-refresh-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    save_auth(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-27 12:00:00",
            "access_token": "expired",
            "refresh_token": "refresh-old",
            "expires_at": "2000-01-01 00:00:00",
        },
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "access_token": "fresh-access",
        "refresh_token": "refresh-new",
        "token_type": "Bearer",
        "expires_in": 3600,
    }
    with patch("integrations.google_health.auth.requests.post", return_value=mock_resp):
        token = auth.ensure_valid_access_token(user_id)
    assert token == "fresh-access"
    stored = load_auth(user_id)
    assert stored["access_token"] == "fresh-access"
    assert stored["refresh_token"] == "refresh-new"
    assert stored["expires_at"]
    assert stored["last_refresh_at"]


@pytest.mark.unit
@pytest.mark.user
def test_save_tokens_for_user_keeps_existing_refresh_when_omitted(
    test_data_dir,
):
    from integrations.google_health.data_handlers import load_auth, save_auth
    from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

    user_id = f"health-save-tokens-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    save_auth(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-27 12:00:00",
            "access_token": "old-access",
            "refresh_token": "keep-me",
        },
    )
    assert (
        auth.save_tokens_for_user(
            user_id,
            {"access_token": "new-access", "token_type": "Bearer", "expires_in": 120},
        )
        is True
    )
    stored = load_auth(user_id)
    assert stored["access_token"] == "new-access"
    assert stored["refresh_token"] == "keep-me"
    assert stored["connected_at"]


def _oauth_handler(path: str) -> auth._OAuthCallbackHandler:
    handler = auth._OAuthCallbackHandler.__new__(auth._OAuthCallbackHandler)
    handler.path = path
    handler._respond = MagicMock()
    return handler


@pytest.mark.unit
def test_oauth_callback_handler_stores_code():
    auth._OAuthCallbackHandler.auth_code = None
    auth._OAuthCallbackHandler.error_message = None
    handler = _oauth_handler("/?code=the-code&state=user-1")
    handler.do_GET()
    assert auth._OAuthCallbackHandler.auth_code == "the-code"
    handler._respond.assert_called_once_with(
        200, "Google Health connected. You can close this window."
    )


@pytest.mark.unit
def test_oauth_callback_handler_stores_error():
    auth._OAuthCallbackHandler.auth_code = None
    auth._OAuthCallbackHandler.error_message = None
    handler = _oauth_handler("/?error=access_denied")
    handler.do_GET()
    assert auth._OAuthCallbackHandler.error_message == "access_denied"
    handler._respond.assert_called_once_with(
        400, "Authorization failed. You can close this window."
    )


@pytest.mark.unit
def test_oauth_callback_handler_missing_code():
    auth._OAuthCallbackHandler.auth_code = None
    auth._OAuthCallbackHandler.error_message = None
    handler = _oauth_handler("/")
    handler.do_GET()
    assert auth._OAuthCallbackHandler.auth_code is None
    handler._respond.assert_called_once_with(400, "Missing authorization code.")


@pytest.mark.unit
def test_oauth_callback_handler_log_message_routes_to_logger():
    handler = auth._OAuthCallbackHandler.__new__(auth._OAuthCallbackHandler)
    with patch("integrations.google_health.auth.logger") as mock_logger:
        handler.log_message("%s %s", "GET", "/")
    mock_logger.debug.assert_called_once()
    assert "OAuth callback:" in mock_logger.debug.call_args.args[0]


@pytest.mark.unit
def test_oauth_callback_respond_writes_html():
    handler = auth._OAuthCallbackHandler.__new__(auth._OAuthCallbackHandler)
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = MagicMock()
    handler._respond(200, "ok")
    handler.send_response.assert_called_once_with(200)
    handler.wfile.write.assert_called_once()
    assert b"ok" in handler.wfile.write.call_args.args[0]


@pytest.mark.unit
def test_run_oauth_connect_flow_skips_in_testing_mode(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "1")
    assert auth.run_oauth_connect_flow("user-1") is None


@pytest.mark.unit
def test_run_oauth_connect_flow_timeout_returns_none(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    monkeypatch.setattr(auth, "GOOGLE_HEALTH_OAUTH_CALLBACK_TIMEOUT_SECONDS", 0.05)
    mock_server = MagicMock()
    opened: list[str] = []
    with patch.object(auth, "HTTPServer", return_value=mock_server), patch.object(
        auth, "build_authorization_url", return_value="https://auth.example/connect"
    ):
        result = auth.run_oauth_connect_flow("user-1", on_complete=opened.append)
    assert result is None
    assert opened == ["https://auth.example/connect"]
    mock_server.server_close.assert_called_once()


@pytest.mark.unit
def test_run_oauth_connect_flow_oauth_error_returns_none(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    monkeypatch.setattr(auth, "GOOGLE_HEALTH_OAUTH_CALLBACK_TIMEOUT_SECONDS", 0.05)
    mock_server = MagicMock()

    def _set_error() -> None:
        auth._OAuthCallbackHandler.error_message = "access_denied"

    mock_server.handle_request.side_effect = _set_error
    with patch.object(auth, "HTTPServer", return_value=mock_server), patch.object(
        auth, "build_authorization_url", return_value="https://auth.example/connect"
    ):
        assert auth.run_oauth_connect_flow("user-1") is None


@pytest.mark.unit
def test_run_oauth_connect_flow_exchanges_and_saves(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    monkeypatch.setattr(auth, "GOOGLE_HEALTH_OAUTH_CALLBACK_TIMEOUT_SECONDS", 0.05)
    mock_server = MagicMock()

    def _set_code() -> None:
        auth._OAuthCallbackHandler.auth_code = "auth-code"

    mock_server.handle_request.side_effect = _set_code
    tokens = {"access_token": "a", "refresh_token": "r"}
    with patch.object(auth, "HTTPServer", return_value=mock_server), patch.object(
        auth, "build_authorization_url", return_value="https://auth.example/connect"
    ), patch.object(
        auth, "exchange_code_for_tokens", return_value=tokens
    ) as exchange, patch.object(
        auth, "save_tokens_for_user", return_value=True
    ) as save:
        result = auth.run_oauth_connect_flow("user-1")
    assert result == tokens
    exchange.assert_called_once_with("auth-code")
    save.assert_called_once_with("user-1", tokens)


@pytest.mark.unit
def test_run_oauth_connect_flow_failed_exchange_returns_none(monkeypatch):
    monkeypatch.delenv("MHM_TESTING", raising=False)
    monkeypatch.setattr(auth, "GOOGLE_HEALTH_OAUTH_CALLBACK_TIMEOUT_SECONDS", 0.05)
    mock_server = MagicMock()

    def _set_code() -> None:
        auth._OAuthCallbackHandler.auth_code = "auth-code"

    mock_server.handle_request.side_effect = _set_code
    with patch.object(auth, "HTTPServer", return_value=mock_server), patch.object(
        auth, "build_authorization_url", return_value="https://auth.example/connect"
    ), patch.object(auth, "exchange_code_for_tokens", return_value=None), patch.object(
        auth, "save_tokens_for_user"
    ) as save:
        assert auth.run_oauth_connect_flow("user-1") is None
    save.assert_not_called()
