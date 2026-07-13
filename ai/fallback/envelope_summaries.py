"""Deterministic fallback answers from AIContextEnvelope structured data."""

from __future__ import annotations

from ai.fallback.categories import FallbackCategory
from ai.fallback.context import FallbackContext, analyze_fallback_checkins
from ai.fallback.checkin_summary import try_checkin_summary_response
from core.error_handling import handle_errors

_TASK_PROMPT_MARKERS = (
    "task",
    "to-do",
    "todo",
    "to do",
    "due soon",
    "overdue",
    "reminder",
)

_CAPABILITY_PROMPT_MARKERS = (
    "what can you do",
    "what do you do",
    "what commands",
    "available commands",
    "help me with",
    "how do i use",
)

_PROFILE_NAME_MARKERS = (
    "my name",
    "what's my name",
    "whats my name",
    "what is my name",
    "call me",
)

_SCHEDULE_PROMPT_MARKERS = (
    "my schedule",
    "when are my",
    "schedule for",
    "message schedule",
    "check-in schedule",
    "checkin schedule",
)


@handle_errors("building envelope summary fallback", default_return=None)
def try_envelope_summary_response(
    prompt_lower: str,
    context: FallbackContext | None,
) -> tuple[str, FallbackCategory] | None:
    """Return a data-backed fallback when envelope sections answer the prompt."""
    if context is None:
        return None

    name_prefix = context.name_prefix
    raw_health_summary = str(
        (context.structured.get("health") or {}).get("guidance_summary") or ""
    )
    from core.health_context_builder import health_wellness_snippet_from_context

    health_wellness_text = health_wellness_snippet_from_context(
        {"health_guidance_summary": raw_health_summary},
        user_id=context.user_id,
    )
    analysis = analyze_fallback_checkins(context)
    if analysis is not None:
        checkin_result = try_checkin_summary_response(
            prompt_lower,
            analysis,
            name_prefix,
            health_guidance_summary=health_wellness_text or raw_health_summary,
        )
        if checkin_result:
            return checkin_result

    capability = _try_capability_summary(prompt_lower, context)
    if capability:
        return capability

    profile = _try_profile_summary(prompt_lower, context)
    if profile:
        return profile

    task = _try_task_summary(prompt_lower, context)
    if task:
        return task

    schedule = _try_schedule_summary(prompt_lower, context)
    if schedule:
        return schedule

    messages = _try_messages_summary(prompt_lower, context)
    if messages:
        return messages

    return None


@handle_errors("building capability summary fallback", default_return=None)
def _try_capability_summary(
    prompt_lower: str, context: FallbackContext
) -> tuple[str, FallbackCategory] | None:
    if not any(marker in prompt_lower for marker in _CAPABILITY_PROMPT_MARKERS):
        return None
    summary = context.action_catalog_summary
    return (
        f"{context.name_prefix}I'm offline for AI chat right now, but here is what I can "
        f"help with when connected: {summary} "
        f"Some commands also work without AI — try `help` or `commands` for examples.",
        FallbackCategory.ENVELOPE_SUMMARY,
    )


@handle_errors("building profile summary fallback", default_return=None)
def _try_profile_summary(
    prompt_lower: str, context: FallbackContext
) -> tuple[str, FallbackCategory] | None:
    if not any(marker in prompt_lower for marker in _PROFILE_NAME_MARKERS):
        return None
    personal = context.structured.get("personal_context") or {}
    preferred = (personal.get("preferred_name") or "").strip()
    if preferred:
        return (
            f"{context.name_prefix}Your preferred name in MHM is {preferred}.",
            FallbackCategory.ENVELOPE_SUMMARY,
        )
    return (
        f"{context.name_prefix}I don't have a preferred name saved yet. "
        f"You can set one with a profile update when AI or commands are available.",
        FallbackCategory.DATA_UNAVAILABLE,
    )


@handle_errors("building task summary fallback", default_return=None)
def _try_task_summary(
    prompt_lower: str, context: FallbackContext
) -> tuple[str, FallbackCategory] | None:
    if not any(marker in prompt_lower for marker in _TASK_PROMPT_MARKERS):
        return None

    tasks = context.structured.get("tasks") or {}
    if not tasks.get("enabled"):
        return (
            f"{context.name_prefix}Task management is not enabled on your account.",
            FallbackCategory.DATA_UNAVAILABLE,
        )

    active = tasks.get("active") or []
    due_soon = tasks.get("due_soon") or []
    stats = tasks.get("stats") or {}
    active_count = len(active)
    due_count = len(due_soon)

    if "due soon" in prompt_lower or "overdue" in prompt_lower:
        if not due_soon:
            return (
                f"{context.name_prefix}You have no tasks due in the next week.",
                FallbackCategory.ENVELOPE_SUMMARY,
            )
        titles = [
            str(task.get("title") or task.get("name") or "Untitled").strip()
            for task in due_soon[:5]
            if isinstance(task, dict)
        ]
        title_text = ", ".join(title for title in titles if title) or "your due tasks"
        suffix = f" (and {due_count - 5} more)" if due_count > 5 else ""
        return (
            f"{context.name_prefix}You have {due_count} task(s) due soon: {title_text}{suffix}.",
            FallbackCategory.ENVELOPE_SUMMARY,
        )

    completion_rate = stats.get("completion_rate")
    rate_text = (
        f" Completion rate: {float(completion_rate):.0f}%."
        if completion_rate is not None
        else ""
    )
    if active_count == 0:
        return (
            f"{context.name_prefix}You have no active tasks right now.{rate_text}",
            FallbackCategory.ENVELOPE_SUMMARY,
        )

    titles = [
        str(task.get("title") or task.get("name") or "Untitled").strip()
        for task in active[:5]
        if isinstance(task, dict)
    ]
    sample = ", ".join(title for title in titles if title) or "your active tasks"
    suffix = f" (and {active_count - 5} more)" if active_count > 5 else ""
    return (
        f"{context.name_prefix}You have {active_count} active task(s): {sample}{suffix}.{rate_text}",
        FallbackCategory.ENVELOPE_SUMMARY,
    )


@handle_errors("building schedule summary fallback", default_return=None)
def _try_schedule_summary(
    prompt_lower: str, context: FallbackContext
) -> tuple[str, FallbackCategory] | None:
    if not any(marker in prompt_lower for marker in _SCHEDULE_PROMPT_MARKERS):
        return None

    schedules = context.structured.get("schedules") or {}
    active = schedules.get("active_schedules") or []
    if context.envelope is not None:
        schedule_text = context.envelope.prompt_sections.get("schedules")
        if schedule_text:
            return (
                f"{context.name_prefix}{schedule_text}",
                FallbackCategory.ENVELOPE_SUMMARY,
            )

    if not active:
        return (
            f"{context.name_prefix}I don't see any active schedule periods configured.",
            FallbackCategory.DATA_UNAVAILABLE,
        )

    detail = ", ".join(str(item) for item in active[:5])
    suffix = f" (and {len(active) - 5} more)" if len(active) > 5 else ""
    return (
        f"{context.name_prefix}Active schedule periods: {detail}{suffix}.",
        FallbackCategory.ENVELOPE_SUMMARY,
    )


@handle_errors("building messages summary fallback", default_return=None)
def _try_messages_summary(
    prompt_lower: str, context: FallbackContext
) -> tuple[str, FallbackCategory] | None:
    if "message" not in prompt_lower and "messages" not in prompt_lower:
        return None

    messages = context.structured.get("messages") or {}
    if messages.get("enabled") is False:
        return (
            f"{context.name_prefix}Automated messages are not enabled on your account.",
            FallbackCategory.DATA_UNAVAILABLE,
        )

    categories = messages.get("categories") or []
    recent = messages.get("recent_sent") or []
    category_text = ", ".join(str(item) for item in categories[:5]) or "none"
    return (
        f"{context.name_prefix}Message categories: {category_text}. "
        f"Recent sent messages on file: {len(recent)}.",
        FallbackCategory.ENVELOPE_SUMMARY,
    )
