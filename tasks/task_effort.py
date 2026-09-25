"""Ask the model how many minutes an open task is likely to take."""

from __future__ import annotations

import re
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger(__name__)

_MINUTES_RE = re.compile(r"^(\S+)\s+(\d{1,3})\b")
_effort_cache: dict[str, int] = {}


@handle_errors("parsing task effort estimates", default_return=[])
def parse_task_effort_lines(text: str, allowed_ids: set[str]) -> list[dict[str, Any]]:
    """Read `id minutes` lines and keep only ids from this request."""
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_line in str(text or "").splitlines():
        match = _MINUTES_RE.match(raw_line.strip())
        if not match:
            continue
        task_id, minutes_text = match.group(1), match.group(2)
        if task_id not in allowed_ids or task_id in seen:
            continue
        minutes = int(minutes_text)
        if minutes < 1 or minutes > 480:
            continue
        seen.add(task_id)
        found.append({"id": task_id, "minutes": minutes})
    return found


@handle_errors("building a task effort cache key", default_return="")
def _cache_key(task: dict[str, Any]) -> str:
    """Build a cache key from the task title and description."""
    title = str(task.get("title") or "").strip().casefold()
    description = str(task.get("description") or "").strip().casefold()
    return f"{title}\n{description}"


@handle_errors("estimating how long tasks take", default_return=[])
def estimate_task_efforts(tasks: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Return minute estimates for active tasks. Missing estimates are omitted."""
    pending = []
    estimates: list[dict[str, Any]] = []
    for task in tasks or []:
        task_id = str(task.get("id") or "").strip()
        if not task_id or not str(task.get("title") or "").strip():
            continue
        cache_key = _cache_key(task)
        cached = _effort_cache.get(cache_key) if cache_key else None
        if cached:
            estimates.append({"id": task_id, "minutes": cached})
        else:
            pending.append(task)
    if not pending:
        return estimates
    from ai.chat.chatbot import get_ai_chatbot
    from ai.client.lm_studio_client import call_lm_studio_api
    from core.config import AI_COMMAND_PARSING_TIMEOUT

    if not get_ai_chatbot().is_ai_available():
        logger.info("Skipping task effort estimates because the model is unavailable")
        return estimates
    lines = []
    allowed_ids = set()
    for task in pending[:20]:
        task_id = str(task.get("id"))
        allowed_ids.add(task_id)
        title = str(task.get("title") or "").replace("\n", " ").strip()
        description = str(task.get("description") or "").replace("\n", " ").strip()
        detail = f" | {description}" if description else ""
        lines.append(f"{task_id} | {title}{detail}")
    messages = [
        {
            "role": "system",
            "content": (
                "Estimate how many minutes one person needs for each task. "
                "Reply with one line per task: id minutes. No other words."
            ),
        },
        {"role": "user", "content": "\n".join(lines)},
    ]
    raw = call_lm_studio_api(
        messages=messages,
        max_tokens=220,
        temperature=0.2,
        timeout=AI_COMMAND_PARSING_TIMEOUT,
    )
    parsed = parse_task_effort_lines(raw or "", allowed_ids)
    by_id = {str(task.get("id")): task for task in pending}
    for item in parsed:
        task = by_id.get(item["id"])
        cache_key = _cache_key(task) if task else ""
        if cache_key:
            _effort_cache[cache_key] = item["minutes"]
        estimates.append(item)
    return estimates
