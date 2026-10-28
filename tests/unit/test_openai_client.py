"""Responses transport contracts, failure handling, and policy boundaries."""

from unittest.mock import Mock, patch

import pytest
import requests

from ai.client import openai_client as client

pytestmark = [pytest.mark.unit, pytest.mark.ai]


@pytest.fixture
def configured(monkeypatch):
    """Use fake credentials and explicit policy for transport tests."""
    monkeypatch.setattr(client, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(client, "OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setattr(client, "OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.setattr(client, "is_ai_usage_allowed", lambda *args: True)


def response_body(text="Hello"):
    """Return a Responses API object with a reasoning item before its text."""
    return {
        "status": "completed",
        "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [{"type": "output_text", "text": text}]},
        ],
    }


def test_responses_contract_and_local_stop(configured):
    """Send supported parameters, avoid storage, and extract message output."""
    messages = [{"role": "system", "content": "You are MHM."}, {"role": "user", "content": "Hi"}]
    with patch.object(client.requests, "post", return_value=Mock(status_code=200, json=lambda: response_body("Hello STOP ignored"))) as post:
        result = client.complete_openai_chat(messages, max_tokens=80, timeout=7, stop=["STOP"])
    assert result.text == "Hello"
    assert result.failure is None
    args, kwargs = post.call_args
    assert args == ("https://api.openai.com/v1/responses",)
    assert kwargs["json"] == {
        "model": "gpt-5.4-mini", "input": messages, "max_output_tokens": 80,
        "store": False, "reasoning": {"effort": "none"},
    }
    assert kwargs["timeout"] == 7
    assert kwargs["allow_redirects"] is False
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"


@pytest.mark.parametrize("status", [401, 403, 429, 500])
def test_http_failures_return_no_text(configured, status):
    """Authentication, quota, and provider failures cannot be consumed as output."""
    with patch.object(client.requests, "post", return_value=Mock(status_code=status)):
        result = client.complete_openai_chat([{"role": "user", "content": "Hi"}])
    assert result.text is None
    assert result.failure == f"HTTP {status}"


@pytest.mark.parametrize("body", [
    [], {}, {"status": "completed", "output": []},
    {"status": "completed", "output": "bad"},
    {"status": "incomplete", "output": response_body()["output"]},
    {"status": "completed", "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "No"}]}]},
])
def test_invalid_incomplete_and_refused_responses_fail_closed(configured, body):
    """Never save or execute partial, malformed, or refused model output."""
    with patch.object(client.requests, "post", return_value=Mock(status_code=200, json=lambda: body)):
        result = client.complete_openai_chat([{"role": "user", "content": "Hi"}])
    assert result.text is None
    assert result.failure


def test_timeout_is_sanitized(configured):
    """Request exception text must not expose credentials in the failure."""
    with patch.object(client.requests, "post", side_effect=requests.Timeout("test-key")):
        result = client.complete_openai_chat([])
    assert result.failure == "Timeout"


@pytest.mark.parametrize("disabled", [True, False])
def test_policy_and_missing_key_never_make_http_requests(configured, monkeypatch, disabled):
    """Unavailable credentials and policy off block readiness and generation."""
    if disabled:
        monkeypatch.setattr(client, "is_ai_usage_allowed", lambda *args: False)
    else:
        monkeypatch.setattr(client, "OPENAI_API_KEY", "")
    with patch.object(client.requests, "get") as get, patch.object(client.requests, "post") as post:
        assert client.test_openai_connection() is False
        assert client.call_openai_api([]) is None
    get.assert_not_called()
    post.assert_not_called()


def test_readiness_checks_configured_model_without_generation(configured):
    """Availability checks use a model GET, never a paid completion."""
    with patch.object(client.requests, "get", return_value=Mock(status_code=200)) as get, patch.object(client.requests, "post") as post:
        assert client.test_openai_connection()
    assert get.call_args.args == ("https://api.openai.com/v1/models/gpt-5.4-mini",)
    post.assert_not_called()


@pytest.mark.parametrize("timeout", [0, -1])
def test_invalid_timeout_does_not_send_request(configured, timeout):
    """Never disable the request deadline through an invalid caller timeout."""
    with patch.object(client.requests, "post") as post:
        result = client.complete_openai_chat([], timeout=timeout)
    assert result.text is None
    assert result.failure == "OpenAI request timeout must be positive"
    post.assert_not_called()
