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

# The loaded local model rejects prompts above this window. Measured English
# in these prompts is about 2.3 characters per token; 2 keeps the request under.
_MODEL_CONTEXT_TOKENS = 2048
_CHARS_PER_TOKEN = 2
_CONTEXT_MARKER = "[selected_user_context]"


@handle_errors("fitting LM Studio messages to the context window", default_return=[])
def fit_messages_to_context(
    messages: list, completion_tokens: int
) -> list:
    """Shrink the system prompt so the request fits a 2048-token local model.

    The user message is kept. Extra instruction text is shortened before the
    selected user context, and that context keeps its opening lines.
    """
    if not isinstance(messages, list):
        return []
    reserve = max(int(completion_tokens or 0), 0) + 32
    input_tokens = max(256, _MODEL_CONTEXT_TOKENS - reserve)
    budget = input_tokens * _CHARS_PER_TOKEN
    fitted = []
    for message in messages:
        if isinstance(message, dict):
            fitted.append(dict(message))
    total = sum(len(str(message.get("content") or "")) for message in fitted)
    if total <= budget:
        return fitted

    user_len = sum(
        len(str(message.get("content") or ""))
        for message in fitted
        if message.get("role") != "system"
    )
    system_budget = max(400, budget - user_len)
    for message in fitted:
        if message.get("role") != "system":
            continue
        content = str(message.get("content") or "")
        if len(content) <= system_budget:
            continue
        message["content"] = _shrink_system_prompt(content, system_budget)
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

    response = requests.post(
        f"{LM_STUDIO_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=timeout,
    )

    if response.status_code != 200:
        logger.warning(
            f"LM Studio API error: HTTP {response.status_code} - {response.text}"
        )
        return None

    data = response.json()
    if "choices" not in data or not data["choices"]:
        logger.warning("LM Studio API returned empty choices")
        return None

    content = data["choices"][0]["message"]["content"]
    return content.strip() if content else None
