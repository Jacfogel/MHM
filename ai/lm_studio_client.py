# ai/lm_studio_client.py

"""HTTP client helpers for LM Studio (OpenAI-compatible API)."""

import os

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


@handle_errors("testing LM Studio connection", default_return=False)
def test_lm_studio_connection() -> bool:
    """Return True when the LM Studio /models endpoint responds successfully."""
    if os.getenv("MHM_TESTING") == "1":
        logger.info("Skipping LM Studio connection test in testing mode")
        return True

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
) -> str | None:
    """Make a chat/completions request to LM Studio."""
    if timeout is None:
        timeout = AI_API_CALL_TIMEOUT

    payload = {
        "model": LM_STUDIO_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.7,
        "stream": False,
    }
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
