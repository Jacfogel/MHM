# ai/client/openai_client.py

"""OpenAI Responses API transport with policy checks and deterministic failures."""

from dataclasses import dataclass

import requests

from core.config import (
    AI_API_CALL_TIMEOUT,
    AI_CONNECTION_TEST_TIMEOUT,
    AI_CONTEXT_TOKENS,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger
from ai.usage_policy import AIUsageFeature, is_ai_usage_allowed

logger = get_component_logger("ai")


@dataclass(frozen=True)
class OpenAICompletion:
    """Text from one Responses API call, and why the text is missing."""

    text: str | None = None
    failure: str | None = None

# Conservative character estimate for the app's bounded input budget.
_MODEL_CONTEXT_TOKENS = AI_CONTEXT_TOKENS
_CHARS_PER_TOKEN = 2
_CONTEXT_MARKER = "[selected_user_context]"


@handle_errors("measuring the OpenAI character budget", default_return=512)
def _context_char_budget(completion_tokens: int) -> int:
    """Return how many prompt characters fit beside the reserved completion."""
    reserve = max(int(completion_tokens or 0), 0) + 32
    input_tokens = max(256, _MODEL_CONTEXT_TOKENS - reserve)
    return input_tokens * _CHARS_PER_TOKEN


@handle_errors("keeping the tail of a prompt", default_return="")
def _keep_text_tail(content: str, budget: int) -> str:
    """Keep the end of text, starting on the next line when a cut lands mid-line."""
    if budget < 1 or not content:
        return ""
    if len(content) <= budget:
        return content
    tail = content[-budget:]
    newline = tail.find("\n")
    if newline != -1 and newline < len(tail) - 1:
        trimmed = tail[newline + 1 :]
        if trimmed:
            return trimmed
    return tail


@handle_errors("fitting prompt texts into a character budget", default_return=None)
def _apply_text_budget(
    messages: list, indexes: list[int], budget: int, *, keep_tail: bool
) -> None:
    """Write each selected message so their combined text stays within budget."""
    remaining = max(int(budget or 0), 0)
    order = list(reversed(indexes)) if keep_tail else list(indexes)
    assigned = {index: "" for index in indexes}
    for index in order:
        content = str(messages[index].get("content") or "")
        if remaining <= 0 or not content:
            continue
        if len(content) <= remaining:
            assigned[index] = content
            remaining -= len(content)
            continue
        piece = (
            _keep_text_tail(content, remaining)
            if keep_tail
            else _shrink_system_prompt(content, remaining)
        )
        assigned[index] = piece
        remaining -= len(piece)
    for index, text in assigned.items():
        messages[index]["content"] = text


@handle_errors("fitting OpenAI messages to the context window", default_return=[])
def fit_messages_to_context(
    messages: list, completion_tokens: int
) -> list:
    """Shrink system and user text so the request stays inside the configured app input budget.

    The start of the instructions is kept. The end of the user message is kept.
    The combined text never exceeds the character budget.
    """
    if not isinstance(messages, list):
        return []
    budget = _context_char_budget(completion_tokens)
    fitted = []
    for message in messages:
        if isinstance(message, dict):
            fitted.append(dict(message))
    total = sum(len(str(message.get("content") or "")) for message in fitted)
    if total <= budget:
        return fitted

    system_indexes = [
        index for index, message in enumerate(fitted) if message.get("role") == "system"
    ]
    other_indexes = [
        index for index, message in enumerate(fitted) if message.get("role") != "system"
    ]
    user_len = sum(len(str(fitted[index].get("content") or "")) for index in other_indexes)
    system_len = sum(
        len(str(fitted[index].get("content") or "")) for index in system_indexes
    )
    if user_len < budget:
        system_budget = budget - user_len
        user_budget = user_len
    else:
        system_budget = min(system_len, budget // 3)
        user_budget = budget - system_budget
    _apply_text_budget(fitted, system_indexes, system_budget, keep_tail=False)
    _apply_text_budget(fitted, other_indexes, user_budget, keep_tail=True)
    return fitted


@handle_errors("shrinking an OpenAI system prompt", default_return="")
def _shrink_system_prompt(content: str, budget: int) -> str:
    """Keep the start of the instructions and the start of the user context."""
    if budget < 1:
        return ""
    if _CONTEXT_MARKER not in content:
        return content[:budget]
    head, context = content.split(_CONTEXT_MARKER, 1)
    context_budget = min(900, max(200, budget // 3))
    head_budget = budget - len(_CONTEXT_MARKER) - context_budget
    if head_budget < 200:
        return content[:budget]
    if len(head) > head_budget:
        head = head[:head_budget].rsplit("\n", 1)[0]
    if len(context) > context_budget:
        context = context[:context_budget].rsplit("\n", 1)[0]
    shrunk = f"{head}{_CONTEXT_MARKER}{context}"
    if len(shrunk) > budget:
        return shrunk[:budget]
    return shrunk


@handle_errors("testing OpenAI connection", default_return=False)
def test_openai_connection() -> bool:
    """Check model access without generating or paying for a test completion."""
    if not is_ai_usage_allowed() or not OPENAI_API_KEY or not OPENAI_MODEL:
        return False
    try:
        response = requests.get(
            f"{OPENAI_BASE_URL}/models/{OPENAI_MODEL}",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            timeout=AI_CONNECTION_TEST_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException:
        logger.warning("OpenAI connection check failed")
        return False
    if response.status_code != 200:
        logger.warning("OpenAI model access check failed", status_code=response.status_code)
        return False
    return True


@handle_errors(
    "completing an OpenAI response",
    default_return=OpenAICompletion(text=None, failure="OpenAI call failed"),
)
def complete_openai_chat(
    messages: list,
    max_tokens: int = 100,
    temperature: float = 0.2,
    timeout: int | None = None,
    *,
    stop: list[str] | None = None,
    usage_feature: AIUsageFeature | str = AIUsageFeature.GENERIC,
) -> OpenAICompletion:
    """Request bounded text; keep errors on this call and never log credentials.

    Temperature is retained in the application interface, but omitted from the
    wire request so sampling uses the model defaults. Stop sequences are applied locally.
    """
    if not is_ai_usage_allowed(usage_feature):
        return OpenAICompletion(failure=f"AI usage disabled for feature: {usage_feature}")
    if not OPENAI_API_KEY:
        return OpenAICompletion(failure="OpenAI API key is not configured")
    if not OPENAI_MODEL:
        return OpenAICompletion(failure="OpenAI model is not configured")
    payload: dict = {
        "model": OPENAI_MODEL,
        "input": fit_messages_to_context(messages, max_tokens),
        "max_output_tokens": max(16, int(max_tokens)),
        "store": False,
    }
    # This default model supports no reasoning. Other configured models use
    # their own server defaults instead of inheriting incompatible parameters.
    if OPENAI_MODEL.startswith("gpt-5.4-mini"):
        payload["reasoning"] = {"effort": "none"}
    request_timeout = AI_API_CALL_TIMEOUT if timeout is None else timeout
    if request_timeout <= 0:
        return OpenAICompletion(failure="OpenAI request timeout must be positive")
    try:
        response = requests.post(
            f"{OPENAI_BASE_URL}/responses",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}",
            },
            json=payload,
            timeout=request_timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        # Exception messages can include request URLs or secrets; log type only.
        failure = type(exc).__name__
        logger.warning("OpenAI request failed", failure=failure)
        return OpenAICompletion(failure=failure)
    if response.status_code != 200:
        logger.warning("OpenAI API returned an error", status_code=response.status_code)
        return OpenAICompletion(failure=f"HTTP {response.status_code}")
    try:
        data = response.json()
    except ValueError:
        return OpenAICompletion(failure="invalid JSON")
    if not isinstance(data, dict):
        return OpenAICompletion(failure="invalid response")
    # Partial output must not become an executable action or saved task plan.
    if data.get("status") != "completed":
        return OpenAICompletion(failure="OpenAI response did not complete")
    output = data.get("output")
    if not isinstance(output, list):
        return OpenAICompletion(failure="missing output")
    pieces = []
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        contents = item.get("content", [])
        if not isinstance(contents, list):
            continue
        for content in contents:
            if not isinstance(content, dict):
                continue
            if content.get("type") == "refusal":
                return OpenAICompletion(failure="OpenAI declined the request")
            text = content.get("text")
            if content.get("type") == "output_text" and isinstance(text, str):
                pieces.append(text)
    text = "".join(pieces).strip()
    for sequence in stop or []:
        if sequence and sequence in text:
            text = text.split(sequence, 1)[0].strip()
    if not text:
        return OpenAICompletion(failure="empty content")
    return OpenAICompletion(text=text)


@handle_errors("calling OpenAI API", default_return=None)
def call_openai_api(
    messages: list,
    max_tokens: int = 100,
    temperature: float = 0.2,
    timeout: int | None = None,
    *,
    stop: list[str] | None = None,
    usage_feature: AIUsageFeature | str = AIUsageFeature.GENERIC,
) -> str | None:
    """Return text from one policy-controlled Responses request."""
    completion = complete_openai_chat(
        messages, max_tokens=max_tokens, temperature=temperature, timeout=timeout,
        stop=stop, usage_feature=usage_feature,
    )
    return completion.text if isinstance(completion, OpenAICompletion) else None
