"""Regressions for honest grading, source attribution and lossless evidence."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ai.client.cache_manager import ResponseCache
from tests.ai.evaluation_contracts import (
    audit_case_input, command_contract_issues, diagnose_case_failure, review_status,
)
from tests.ai.evaluation_evidence import ResponseEvidenceRecorder, source_summary
from tests.ai.evaluation_report import evidence_markdown, write_json_report

pytestmark = [pytest.mark.unit, pytest.mark.ai]


@pytest.mark.parametrize(
    "reply",
    [
        "ACTION: unknown",
        '{"action":"unknown","details":{}}',
        '{"action":"create_task","details":{"title":"wrong task"}}',
        "Sure, I can help with that",
        "[]",
        "ACTION: create_task",
    ],
)
def test_unknown_or_wrong_command_never_satisfies_create_contract(reply):
    assert command_contract_issues(reply, action="create_task", title="buy milk")


@pytest.mark.parametrize(
    "reply",
    [
        "ACTION: create_task\nTITLE: buy milk",
        '{"action":"create_task","details":{"title":"buy milk"}}',
    ],
)
def test_exact_command_contract_accepts_supported_formats(reply):
    assert command_contract_issues(reply, action="create_task", title="buy milk") == []


class ProbeBot:
    """Small caller exercises observation boundaries without contacting a provider."""

    def __init__(self):
        self.cache = ResponseCache()
        self._call_openai_api = Mock(return_value="raw model text")

    def generate_response(self, user_prompt, **kwargs):
        import ai.chat.chatbot as chatbot

        if user_prompt == "cache":
            return self.cache.get("p", "u", "command")
        if user_prompt == "123456":
            if chatbot.is_uninterpretable_user_prompt(user_prompt):
                return chatbot.UNCLEAR_USER_INPUT_REPLY
        if user_prompt == "fallback":
            return chatbot._text_when_model_is_unavailable("chat", user_prompt, None)
        value = self._call_openai_api()
        text, _ = chatbot._text_from_lm_call(value)
        if not text:
            return chatbot._text_when_model_is_unavailable("chat", user_prompt, None)
        if user_prompt == "What is 7+5?":
            return chatbot.repair_simple_arithmetic_reply(user_prompt, text)
        return text

    def generate_contextual_response(self, user_id, user_prompt, **kwargs):
        return self.generate_response(user_prompt, **kwargs)


def test_sources_are_observed_per_turn_and_patches_restore(monkeypatch):
    import ai.chat.chatbot as chatbot

    monkeypatch.setattr(
        chatbot, "_text_when_model_is_unavailable", lambda *a: "fallback text"
    )
    monkeypatch.setattr("ai.client.cache_manager.AI_CACHE_RESPONSES", True)
    bot = ProbeBot()
    bot.cache.set("p", "seeded value", "u", "command")
    original = bot.generate_response
    with ResponseEvidenceRecorder(bot) as recorder:
        assert bot.generate_response("cache") == "seeded value"
        bot.generate_response("123456")
        bot.generate_response("fallback")
        bot.generate_contextual_response("u", "normal")
        turns = recorder.take()
    assert [t["source"] for t in turns] == [
        "cache",
        "deterministic_guard",
        "fallback",
        "mocked_model",
    ]
    assert [t["prompt"] for t in turns] == ["cache", "123456", "fallback", "normal"]
    assert turns[-1]["events"][0]["text"] == "raw model text"
    assert turns[-1]["scenario"] == "mocked"
    assert bot.generate_response == original
    assert recorder.take() == []


def test_simulated_error_and_final_fallback_are_both_preserved(monkeypatch):
    from ai.client.openai_client import OpenAICompletion

    monkeypatch.setattr(
        "ai.chat.chatbot._text_when_model_is_unavailable", lambda *a: "unavailable"
    )
    bot = ProbeBot()
    bot._call_openai_api.return_value = OpenAICompletion(failure="HTTP 500")
    with ResponseEvidenceRecorder(bot) as recorder:
        bot.generate_response("normal")
    turn = recorder.turns[0]
    assert turn["source"] == "fallback"
    assert turn["scenario"] == "simulated_error"
    assert turn["events"][0]["failure"] == "HTTP 500"
    assert turn["events"][-1]["text"] == "unavailable"


def test_repair_is_not_counted_as_model_quality():
    bot = ProbeBot()
    bot._call_openai_api.return_value = "What would you like help with?"
    with ResponseEvidenceRecorder(bot) as recorder:
        result = bot.generate_response("What is 7+5?")
    turn = recorder.turns[0]
    assert "12" in result
    assert turn["source"] == "deterministic_guard"
    assert turn["events"][0]["text"] == "What would you like help with?"


def test_no_transport_evidence_does_not_imply_model(monkeypatch):
    monkeypatch.setattr("requests.post", lambda *a, **kw: None)
    bot = ProbeBot()
    monkeypatch.setattr(bot, "_call_openai_api", lambda: "unobserved text")
    with ResponseEvidenceRecorder(bot) as recorder:
        bot.generate_response("normal")
    assert recorder.turns[0]["source"] == "unknown"


def test_full_evidence_roundtrip_and_pending_semantic_review(tmp_path):
    long_reply = "full text ``` with a fence\n" + "x" * 1900
    result = {
        "test_id": "T-example",
        "status": "PASS",
        "review_status": "pending",
        "context_info": {"tasks_enabled": False, "recent_count": 0, "rows": []},
        "turns": [
            {"prompt": "p", "response": long_reply, "source": "fallback", "events": []}
        ],
    }
    target = tmp_path / "report.json"
    write_json_report(target, [result], model="test-model")
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["results"][0] == result
    rendered = evidence_markdown(result)
    assert long_reply in rendered
    assert '"tasks_enabled": false' in rendered
    assert '"recent_count": 0' in rendered
    assert '"rows": []' in rendered
    assert "````\nfull text" in rendered
    assert saved["summary"]["semantic_review"]["pending"] == 1
    assert source_summary([result])[0]["source"] == "fallback"
    assert review_status(result["turns"], "chat") == "pending"
    assert review_status([], "chat") == "insufficient_evidence"


def test_cache_isolation_harness_detects_cross_user_leak(monkeypatch):
    from tests.ai.test_ai_cache import TestAICache

    suite = object.__new__(TestAICache)
    monkeypatch.setattr(suite, "chatbot", ProbeBot(), raising=False)
    suite.results_collector = SimpleNamespace(results=[], performance_metrics=[])
    original_get = ResponseCache.get

    def faulty_get(cache, prompt, user_id=None, prompt_type="default"):
        return original_get(cache, prompt, "user-A", prompt_type)

    monkeypatch.setattr(ResponseCache, "get", faulty_get)
    suite.test_cache_comprehensive()
    result = next(
        r for r in suite.results_collector.results if r["test_id"] == "T-11.1"
    )
    assert result["status"] == "FAIL"
    assert result["metrics"]["assertions"]["user B retrieves only B"] is False
    assert result["metrics"]["assertions"]["unseeded user misses"] is False


def test_unobserved_handler_reply_is_explicitly_unknown():
    from tests.ai.ai_test_base import AITestBase
    suite = object.__new__(AITestBase)
    suite.results_collector = SimpleNamespace(results=[], performance_metrics=[])
    suite.log_test("T-unobserved", "Unobserved handler", "PASS", prompt="Hello", response="Hello!")
    result = suite.results_collector.results[0]
    assert result["turns"][0]["source"] == "unknown"
    assert result["turns"][0]["response"] == "Hello!"
    assert result["review_status"] == "insufficient_evidence"


def test_missing_context_and_instructions_are_app_input_failures():
    case = {"request": "What color do I like?", "context": "favorite color teal",
            "history": [{"role": "user", "content": "I like teal"}],
            "required_instructions": ["Use provided facts"],
            "conflicting_instructions": ["Always ignore saved facts"]}
    messages = [{"role": "system", "content": "Always ignore saved facts"},
                {"role": "user", "content": case["request"]}]
    audit = audit_case_input(case, messages)
    assert len(audit["context_issues"]) == 2
    assert len(audit["instruction_issues"]) == 2
    result = diagnose_case_failure(case, audit=audit, raw="I don't know", issues=["missing teal"], raw_issues=["missing teal"])
    assert result["origin"] == "application_context"
    audit["context_issues"] = []
    assert diagnose_case_failure(case, audit=audit, raw="I don't know", issues=["missing teal"], raw_issues=["missing teal"])["origin"] == "application_prompt"


@pytest.mark.parametrize("raw,issues,raw_issues,failure,origin", [
    ("", ["request failed"], [], "ConnectionError", "transport_or_configuration"),
    ("Teal", ["postprocessor removed teal"], [], None, "application_postprocessing"),
    ("Blue", ["missing teal"], ["missing teal"], None, "model_output"),
    ("Teal", [], [], None, "none_observed"),
])
def test_failure_attribution_uses_evidence(raw, issues, raw_issues, failure, origin):
    diagnosis = diagnose_case_failure({"request": "What color?"},
        audit={"context_issues": [], "instruction_issues": []},
        raw=raw, issues=issues, raw_issues=raw_issues, failure=failure)
    assert diagnosis["origin"] == origin


def test_rejected_valid_no_action_output_is_a_parser_failure():
    diagnosis = diagnose_case_failure({"kind": "planner", "intent": "answer_only"},
        audit={"context_issues": [], "instruction_issues": []}, raw="ACTION: unknown",
        issues=["parser marked supported output malformed"], raw_issues=[])
    assert diagnosis["origin"] == "application_parser"
