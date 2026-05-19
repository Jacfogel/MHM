# ai/fallback_responses/checkin_summary.py

"""Check-in data-aware fallback responses (separate from generic keyword support)."""

from dataclasses import dataclass

from ai.fallback_responses.categories import FallbackCategory
from core.error_handling import handle_errors


@dataclass(frozen=True)
class CheckinMetrics:
    breakfast_count: int
    total_entries: int
    breakfast_rate: float
    avg_mood: float | None
    avg_energy: float | None


_EMPTY_CHECKIN_METRICS = CheckinMetrics(
    breakfast_count=0,
    total_entries=0,
    breakfast_rate=0.0,
    avg_mood=None,
    avg_energy=None,
)


@handle_errors("computing check-in metrics for fallback", default_return=_EMPTY_CHECKIN_METRICS)
def compute_checkin_metrics(recent_data: list[dict]) -> CheckinMetrics:
    breakfast_count = sum(
        1 for entry in recent_data if entry.get("ate_breakfast") is True
    )
    total_entries = len(recent_data)
    breakfast_rate = (
        (breakfast_count / total_entries) * 100 if total_entries > 0 else 0.0
    )

    moods: list[float] = []
    for entry in recent_data:
        mood = entry.get("mood")
        if mood is not None:
            moods.append(float(mood))

    avg_mood = sum(moods) / len(moods) if moods else None

    energies: list[float] = []
    for entry in recent_data:
        energy = entry.get("energy")
        if energy is not None:
            energies.append(float(energy))

    avg_energy = sum(energies) / len(energies) if energies else None

    return CheckinMetrics(
        breakfast_count=breakfast_count,
        total_entries=total_entries,
        breakfast_rate=breakfast_rate,
        avg_mood=avg_mood,
        avg_energy=avg_energy,
    )


@handle_errors("building check-in summary fallback", default_return=None)
def try_checkin_summary_response(
    prompt_lower: str, metrics: CheckinMetrics, name_prefix: str
) -> tuple[str, FallbackCategory] | None:
    """Return a check-in summary fallback when prompt and data align."""
    if any(word in prompt_lower for word in ["breakfast", "eat", "ate"]):
        if metrics.breakfast_rate >= 80:
            return (
                f"{name_prefix}Great news! You've been eating breakfast {metrics.breakfast_rate:.0f}% of the time in your recent check-ins. "
                f"That's a really healthy habit to maintain!",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        if metrics.breakfast_rate >= 50:
            return (
                f"{name_prefix}You've been eating breakfast {metrics.breakfast_rate:.0f}% of the time recently. "
                f"Breakfast can really help with energy and focus throughout the day!",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        return (
            f"{name_prefix}I notice you've been eating breakfast {metrics.breakfast_rate:.0f}% of the time in your recent check-ins. "
            f"Starting the day with a good breakfast can help with energy and mood!",
            FallbackCategory.CHECKIN_SUMMARY,
        )

    if (
        any(
            word in prompt_lower
            for word in ["mood", "feeling", "how have i been", "lately"]
        )
        and metrics.avg_mood
        and metrics.avg_energy
    ):
        if metrics.avg_mood >= 4 and metrics.avg_energy >= 4:
            return (
                f"{name_prefix}Looking at your recent check-ins, you've been doing really well! "
                f"Your average mood has been {metrics.avg_mood:.1f}/5 and energy {metrics.avg_energy:.1f}/5. "
                f"Keep up those positive patterns!",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        if metrics.avg_mood <= 2 or metrics.avg_energy <= 2:
            return (
                f"{name_prefix}I've noticed from your recent check-ins that things might be challenging lately. "
                f"Your average mood is {metrics.avg_mood:.1f}/5 and energy {metrics.avg_energy:.1f}/5. "
                f"Remember that tough periods are temporary, and it's okay to take things one step at a time.",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        return (
            f"{name_prefix}Based on your recent check-ins, you're doing okay! "
            f"Your average mood is {metrics.avg_mood:.1f}/5 and energy {metrics.avg_energy:.1f}/5. "
            f"Small improvements each day add up to big changes over time.",
            FallbackCategory.CHECKIN_SUMMARY,
        )

    if any(
        word in prompt_lower
        for word in [
            "how am i",
            "how have i been",
            "doing lately",
            "progress",
        ]
    ):
        insights = []
        if metrics.breakfast_rate >= 70:
            insights.append("great breakfast habits")
        if metrics.avg_mood and metrics.avg_mood >= 3.5:
            insights.append("generally positive mood")
        if metrics.avg_energy and metrics.avg_energy >= 3:
            insights.append("decent energy levels")

        if insights:
            return (
                f"{name_prefix}You're doing well in several areas: {', '.join(insights)}. Keep up the good work!",
                FallbackCategory.CHECKIN_SUMMARY,
            )
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
                f"{name_prefix}You ate breakfast {metrics.breakfast_count}/{metrics.total_entries} times ({metrics.breakfast_rate:.0f}%).",
                FallbackCategory.CHECKIN_SUMMARY,
            )
        if "mood" in prompt_lower:
            if metrics.avg_mood is not None:
                tone = (
                    "positive"
                    if metrics.avg_mood >= 4
                    else "neutral"
                    if metrics.avg_mood >= 3
                    else "challenging"
                )
                return (
                    f"{name_prefix}Your average mood was {metrics.avg_mood:.1f}/5 - {tone}.",
                    FallbackCategory.CHECKIN_SUMMARY,
                )
            return (
                f"{name_prefix}I don't have enough mood data to calculate an average yet.",
                FallbackCategory.DATA_UNAVAILABLE,
            )
        if "energy" in prompt_lower:
            if metrics.avg_energy is not None:
                tone = (
                    "high"
                    if metrics.avg_energy >= 4
                    else "moderate"
                    if metrics.avg_energy >= 3
                    else "low"
                )
                return (
                    f"{name_prefix}Your average energy was {metrics.avg_energy:.1f}/5 - {tone}.",
                    FallbackCategory.CHECKIN_SUMMARY,
                )
            return (
                f"{name_prefix}I don't have enough energy data to calculate an average yet.",
                FallbackCategory.DATA_UNAVAILABLE,
            )

    return None
