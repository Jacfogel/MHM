# ai/lm_studio_client.py

"""HTTP client helpers for LM Studio (OpenAI-compatible API)."""

import requests

from core.config import (
    AI_API_CALL_TIMEOUT,
    AI_CONNECTION_TEST_TIMEOUT,
    LM_STUDIO_API_KEY,
    LM_STUDIO_BASE_URL,
    LM_STUDIO_MODEL,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("ai")
# Why the latest chat/completions call returned no text. None after a success.
last_call_failure: str | None = None

# The loaded local model rejects prompts above this window. Measured English
# in these prompts is about 2.3 characters per token; 2 keeps the request under.
_MODEL_CONTEXT_TOKENS = 2048
_CHARS_PER_TOKEN = 2
_CONTEXT_MARKER = "[selected_user_context]"


@handle_errors("measuring the LM Studio character budget", default_return=512)
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


@handle_errors("fitting LM Studio messages to the context window", default_return=[])
def fit_messages_to_context(
    messages: list, completion_tokens: int
) -> list:
    """Shrink system and user text so the request stays inside the 2048-token window.

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


@handle_errors("shrinking an LM Studio system prompt", default_return="")
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


@handle_errors("testing LM Studio connection", default_return=False)
def test_lm_studio_connection() -> bool:
    """Return True when the LM Studio /models endpoint responds successfully."""
    response = requests.get(
        f"{LM_STUDIO_BASE_URL}/models",
        headers={"Authorization": f"Bearer {LM_STUDIO_API_KEY}"},
        timeout=AI_CONNECTION_TEST_TIMEOUT,
    )

    if response.status_code != 200:
        logger.warning(
            f"LM Studio connection test failed: HTTP {response.status_code}"
        )
        return False

    models = response.json().get("data", [])
    logger.info(f"LM Studio connection successful. Available models: {len(models)}")
    if models:
        model_names = [model.get("id", "unknown") for model in models[:3]]
        logger.debug(f"Available models (first 3): {model_names}")
    else:
        logger.warning("LM Studio is running but no models are loaded")
    return True


@handle_errors("calling LM Studio API", default_return=None)
def call_lm_studio_api(
    messages: list,
    max_tokens: int = 100,
    temperature: float = 0.2,
    timeout: int | None = None,
    *,
    stop: list[str] | None = None,
) -> str | None:
    """Make a chat/completions request to LM Studio."""
    global last_call_failure
    last_call_failure = None
    if timeout is None:
        timeout = AI_API_CALL_TIMEOUT

    messages = fit_messages_to_context(messages, max_tokens)
    payload = {
        "model": LM_STUDIO_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.7,
        "stream": False,
    }
    if stop:
        payload["stop"] = stop
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LM_STUDIO_API_KEY}",
    }

    try:
        response = requests.post(
            f"{LM_STUDIO_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        last_call_failure = f"{type(exc).__name__}: {exc}"
        logger.warning(f"LM Studio API request failed: {last_call_failure}")
        return None

    if response.status_code != 200:
        last_call_failure = f"HTTP {response.status_code}"
        logger.warning(
            f"LM Studio API error: HTTP {response.status_code} - {response.text}"
        )
        return None

    data = response.json()
    if "choices" not in data or not data["choices"]:
        last_call_failure = "empty choices"
        logger.warning("LM Studio API returned empty choices")
        return None

    content = data["choices"][0]["message"]["content"]
    if not content:
        last_call_failure = "empty content"
        return None
    return content.strip()
