# ai/fallback_responses/checkin_summary.py

"""Check-in data-aware fallback responses (separate from generic keyword support)."""

import re

from ai.context.analytics import ContextAnalysis
from ai.fallback.categories import FallbackCategory
from core.error_handling import handle_errors
from core.health_context_builder import format_health_guidance_for_user_reply

_WELLNESS_PROGRESS_PROMPT_WORDS = (
    "how am i",
    "how have i been",
    "doing lately",
    "progress",
)

_BREAKFAST_WORD_PATTERNS = (
    re.compile(r"\bbreakfast\b"),
    re.compile(r"\beat(?:ing|s)?\b"),
    re.compile(r"\bate\b"),
)


@handle_errors("checking breakfast mention in prompt", default_return=False)
def _prompt_mentions_breakfast(prompt_lower: str) -> bool:
    """Return True when the prompt asks about breakfast/eating, not substring noise."""
    return any(pattern.search(prompt_lower) for pattern in _BREAKFAST_WORD_PATTERNS)


@handle_errors("building health-guidance wellness fallback", default_return=None)
def try_health_guidance_wellness_response(
    prompt_lower: str,
    name_prefix: str,
    health_guidance_summary: str,
) -> tuple[str, FallbackCategory] | None:
    """Return a wellness reply from recent Google Health guidance when check-ins are absent."""
    if not any(word in prompt_lower for word in _WELLNESS_PROGRESS_PROMPT_WORDS):
        return None
    health_text = format_health_guidance_for_user_reply(health_guidance_summary)
    if not health_text:
        return None
    return (
        f"{name_prefix}From your recent wellness data: {health_text}",
        FallbackCategory.CHECKIN_SUMMARY,
    )


@handle_errors("building health guidance fallback reply", default_return=None)
def _health_guidance_fallback(
    name_prefix: str,
    health_guidance_summary: str | None,
) -> tuple[str, FallbackCategory] | None:
    """Return a wellness fallback from Google Health guidance text when available."""
    health_text = format_health_guidance_for_user_reply(health_guidance_summary or "")
    if not health_text:
        return None
    return (
        f"{name_prefix}From your recent wellness data: {health_text}",
        FallbackCategory.CHECKIN_SUMMARY,
    )


@handle_errors("building partial check-in wellness fallback", default_return=None)
def _partial_checkin_wellness_reply(
    name_prefix: str,
    analysis: ContextAnalysis,
) -> tuple[str, FallbackCategory] | None:
    """Cite available check-in metrics when they are below strong-insight thresholds."""
    parts: list[str] = []
    if analysis.avg_mood is not None:
        parts.append(f"your average mood is around {analysis.avg_mood:.1f}/5")
    if analysis.avg_energy is not None:
        parts.append(f"your average energy is around {analysis.avg_energy:.1f}/5")
    if analysis.total_entries and analysis.breakfast_rate is not None:
        parts.append(
            f"you've had breakfast about {analysis.breakfast_rate:.0f}% of the time "
            f"in your recent check-ins"
        )
    if not parts:
        return None
    joined = ", and ".join(parts) if len(parts) == 2 else ", ".join(parts)
    return (
        f"{name_prefix}From your recent check-ins: {joined}.",
        FallbackCategory.CHECKIN_SUMMARY,
    )


@handle_errors("building check-in summary fallback", default_return=None)
def try_checkin_summary_response(
    prompt_lower: str,
    analysis: ContextAnalysis,
    name_prefix: str,
    *,
    health_guidance_summary: str | None = None,
) -> tuple[str, FallbackCategory] | None:
    """Return a check-in summary fallback when prompt and data align.

    ``analysis`` must come from ``analyze_checkin_entries`` so metrics match conversational context.
    """
    if _prompt_mentions_breakfast(prompt_lower):
        if analysis.breakfast_rate >= 80:
            return (
                f"{name_prefix}Great news! You've been eating breakfast {analysis.breakfast_rate:.0f}% of the time in your recent check-ins. "
                f"That's a really healthy habit to maintain!",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        if analysis.breakfast_rate >= 50:
            return (
                f"{name_prefix}You've been eating breakfast {analysis.breakfast_rate:.0f}% of the time recently. "
                f"Breakfast can really help with energy and focus throughout the day!",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        return (
            f"{name_prefix}I notice you've been eating breakfast {analysis.breakfast_rate:.0f}% of the time in your recent check-ins. "
            f"Starting the day with a good breakfast can help with energy and mood!",
            FallbackCategory.CHECKIN_SUMMARY,
        )

    if (
        any(
            word in prompt_lower
            for word in ["mood", "feeling", "how have i been", "lately"]
        )
        and analysis.avg_mood
        and analysis.avg_energy
    ):
        if analysis.avg_mood >= 4 and analysis.avg_energy >= 4:
            return (
                f"{name_prefix}Looking at your recent check-ins, you've been doing really well! "
                f"Your average mood has been {analysis.avg_mood:.1f}/5 and energy {analysis.avg_energy:.1f}/5. "
                f"Keep up those positive patterns!",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        if analysis.avg_mood <= 2 or analysis.avg_energy <= 2:
            return (
                f"{name_prefix}I've noticed from your recent check-ins that things might be challenging lately. "
                f"Your average mood is {analysis.avg_mood:.1f}/5 and energy {analysis.avg_energy:.1f}/5. "
                f"Remember that tough periods are temporary, and it's okay to take things one step at a time.",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        return (
            f"{name_prefix}Based on your recent check-ins, you're doing okay! "
            f"Your average mood is {analysis.avg_mood:.1f}/5 and energy {analysis.avg_energy:.1f}/5. "
            f"Small improvements each day add up to big changes over time.",
            FallbackCategory.CHECKIN_SUMMARY,
        )

    if any(word in prompt_lower for word in _WELLNESS_PROGRESS_PROMPT_WORDS):
        insights = []
        if analysis.breakfast_rate >= 70:
            insights.append("great breakfast habits")
        if analysis.avg_mood and analysis.avg_mood >= 3.5:
            insights.append("generally positive mood")
        if analysis.avg_energy and analysis.avg_energy >= 3:
            insights.append("decent energy levels")

        if insights:
            return (
                f"{name_prefix}You're doing well in several areas: {', '.join(insights)}. Keep up the good work!",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        partial = _partial_checkin_wellness_reply(name_prefix, analysis)
        health_fallback = _health_guidance_fallback(name_prefix, health_guidance_summary)
        if partial and health_fallback:
            checkin_part = partial[0][len(name_prefix) :].strip()
            health_part = health_fallback[0][len(name_prefix) :].strip()
            return (
                f"{name_prefix}{checkin_part} {health_part}",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        if partial:
            return partial
        if health_fallback:
            return health_fallback
        return (
            f"{name_prefix}There's room for improvement, but that's normal! Every small step counts.",
            FallbackCategory.CHECKIN_SUMMARY,
        )

    if any(
        word in prompt_lower
        for word in ["how many", "times", "count", "frequency"]
    ):
        if "breakfast" in prompt_lower:
            return (
                f"{name_prefix}You ate breakfast {analysis.breakfast_count}/{analysis.total_entries} times ({analysis.breakfast_rate:.0f}%).",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        if "mood" in prompt_lower:
            if analysis.avg_mood is not None:
                tone = (
                    "positive"
                    if analysis.avg_mood >= 4
                    else "neutral"
                    if analysis.avg_mood >= 3
                    else "challenging"
                )
                return (
                    f"{name_prefix}Your average mood was {analysis.avg_mood:.1f}/5 - {tone}.",
                    FallbackCategory.CHECKIN_SUMMARY,
                )
            return (
                f"{name_prefix}I don't have enough mood data to calculate an average yet.",
                FallbackCategory.DATA_UNAVAILABLE,
            )
        if "energy" in prompt_lower:
            if analysis.avg_energy is not None:
                tone = (
                    "high"
                    if analysis.avg_energy >= 4
                    else "moderate"
                    if analysis.avg_energy >= 3
                    else "low"
                )
                return (
                    f"{name_prefix}Your average energy was {analysis.avg_energy:.1f}/5 - {tone}.",
                    FallbackCategory.CHECKIN_SUMMARY,
                )
            return (
                f"{name_prefix}I don't have enough energy data to calculate an average yet.",
                FallbackCategory.DATA_UNAVAILABLE,
            )

    return None
