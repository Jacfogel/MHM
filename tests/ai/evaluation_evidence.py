"""Test-only observation of response paths; never infer provenance from wording."""

from collections import Counter
from contextlib import ExitStack
from functools import wraps
from unittest.mock import Mock, patch


class ResponseEvidenceRecorder:
    """Observe synchronous chatbot turns without changing their return values.

    Scoped to one functionality-test method. Unknown paths stay unknown. Events
    retain raw model output and deterministic replacements as well as final text.
    No request headers, credentials, or arbitrary user stores are captured.
    """

    def __init__(self, bot):
        self.bot = bot
        self.turns = []
        self.active = None
        self.stack = ExitStack()

    def _event(self, source, **details):
        if self.active is not None:
            self.active["events"].append({"source": source, **details})

    def __enter__(self):
        import ai.chat.chatbot as chatbot
        from ai.client.cache_manager import ResponseCache
        from ai.fallback import get_fallback_responses
        import requests

        def observe_call(original, source, *, predicate=lambda value: True):
            @wraps(original)
            def observed(*args, **kwargs):
                value = original(*args, **kwargs)
                if predicate(value):
                    self._event(source, text=value if isinstance(value, str) else None)
                return value

            return observed

        def wrap_turn(original, contextual):
            @wraps(original)
            def observed(*args, **kwargs):
                if self.active is not None:
                    return original(*args, **kwargs)
                prompt = (
                    args[1]
                    if contextual and len(args) > 1
                    else kwargs.get(
                        "user_prompt", args[0] if args and not contextual else ""
                    )
                )
                turn = {
                    "prompt": prompt,
                    "response": "",
                    "events": [],
                    "source": "unknown",
                    "error": None,
                }
                self.active = turn
                try:
                    turn["response"] = original(*args, **kwargs)
                    return turn["response"]
                except Exception as exc:
                    turn["error"] = type(exc).__name__
                    raise
                finally:
                    producing = [
                        e for e in turn["events"] if e["source"] != "model_error"
                    ]
                    if producing:
                        turn["source"] = producing[-1]["source"]
                    mocked = [
                        e for e in turn["events"] if e["source"] == "mocked_model"
                    ]
                    turn["scenario"] = (
                        "simulated_error"
                        if any(e.get("failure") for e in mocked)
                        else "mocked"
                        if mocked
                        else "observed"
                    )
                    self.turns.append(turn)
                    self.active = None

            return observed

        try:
            original_post = requests.post
            transport_observations = []

            def transport(*args, **kwargs):
                result = original_post(*args, **kwargs)
                transport_observations.append(
                    isinstance(result, requests.Response)
                    and not isinstance(original_post, Mock)
                    and getattr(original_post, "__module__", "") == "requests.api"
                )
                return result

            self.stack.enter_context(patch.object(requests, "post", transport))
            for name in ("generate_response", "generate_contextual_response"):
                original = getattr(self.bot, name)
                self.stack.enter_context(
                    patch.object(
                        self.bot,
                        name,
                        wrap_turn(original, name == "generate_contextual_response"),
                    )
                )

            original_call = self.bot._call_openai_api

            def provider(*args, **kwargs):
                from ai.chat.chatbot import _text_from_lm_call

                start = len(transport_observations)
                simulated = (
                    isinstance(requests.post, Mock)
                    or isinstance(original_call, Mock)
                    or isinstance(original_post, Mock)
                )
                result = original_call(*args, **kwargs)
                text, failure = _text_from_lm_call(result)
                real_http = any(transport_observations[start:])
                self._event(
                    "mocked_model"
                    if simulated
                    else (
                        "model"
                        if text and real_http
                        else "model_error"
                        if failure
                        else "unknown"
                    ),
                    text=text,
                    failure=failure,
                    real_http=real_http,
                    messages=kwargs.get("messages", args[0] if args else []),
                )
                return result

            self.stack.enter_context(
                patch.object(self.bot, "_call_openai_api", provider)
            )
            self.stack.enter_context(
                patch.object(
                    ResponseCache,
                    "get",
                    observe_call(ResponseCache.get, "cache", predicate=bool),
                )
            )
            fallback = get_fallback_responses()
            for name in ("contextual", "personalized"):
                self.stack.enter_context(
                    patch.object(
                        fallback,
                        name,
                        observe_call(getattr(fallback, name), "fallback"),
                    )
                )
            self.stack.enter_context(
                patch.object(
                    chatbot,
                    "_text_when_model_is_unavailable",
                    observe_call(chatbot._text_when_model_is_unavailable, "fallback"),
                )
            )
            self.stack.enter_context(
                patch.object(
                    chatbot,
                    "build_honest_wellness_status_reply",
                    observe_call(
                        chatbot.build_honest_wellness_status_reply,
                        "deterministic_guard",
                    ),
                )
            )
            self.stack.enter_context(
                patch.object(
                    chatbot,
                    "is_uninterpretable_user_prompt",
                    observe_call(
                        chatbot.is_uninterpretable_user_prompt,
                        "deterministic_guard",
                        predicate=bool,
                    ),
                )
            )
            # Content repair is a different source from the model text it replaces.
            for name in dir(chatbot):
                if not (
                    name.startswith("repair_")
                    or name
                    in (
                        "align_response_to_conversation_topic",
                        "reinforce_wellness_honesty_if_needed",
                    )
                ):
                    continue
                original = getattr(chatbot, name)

                def repair(*args, _original=original, _name=name, **kwargs):
                    value = _original(*args, **kwargs)
                    before = kwargs.get("response", args[1] if len(args) > 1 else None)
                    if value != before:
                        self._event("deterministic_guard", function=_name, text=value)
                    return value

                self.stack.enter_context(patch.object(chatbot, name, repair))
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *exc):
        return self.stack.__exit__(*exc)

    def take(self):
        turns, self.turns = self.turns, []
        return turns


def source_summary(results):
    """Count observed turns by final source and contract status, not model quality."""
    counts = Counter()
    for result in results:
        for turn in result.get("turns", []):
            counts[
                (turn["source"], turn.get("scenario", "fixture"), result["status"])
            ] += 1
    return [
        dict(source=source, scenario=scenario, status=status, turns=count)
        for (source, scenario, status), count in sorted(counts.items())
    ]
