"""Check-in analytics for product-AI context and fallback routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("ai_context")


@dataclass
class ContextAnalysis:
    """Canonical check-in analytics from recent response rows."""

    total_entries: int = 0
    breakfast_count: int = 0
    teeth_brushed_count: int = 0
    breakfast_rate: float = 0.0
    avg_mood: float | None = None
    avg_energy: float | None = None
    teeth_brushing_rate: float = 0.0
    mood_trend: str = "stable"
    energy_trend: str = "stable"
    overall_wellness_score: float = 0.0
    insights: list[str] | None = None

    # not_duplicate: dataclass_post_init_defaults
    @handle_errors("post-initializing context analysis", default_return=None)
    def __post_init__(self):
        if self.insights is None:
            self.insights = []


@handle_errors("determining check-in trend", default_return="stable")
def _determine_trend(values: list[float]) -> str:
    if len(values) < 3:
        return "stable"

    mid_point = len(values) // 2
    first_half = values[:mid_point]
    second_half = values[mid_point:]

    first_avg = sum(first_half) / len(first_half)
    second_avg = sum(second_half) / len(second_half)

    if second_avg > first_avg + 0.5:
        return "improving"
    if second_avg < first_avg - 0.5:
        return "declining"
    return "stable"


@handle_errors("calculating wellness score", default_return=0.0)
def _calculate_wellness_score(
    breakfast_rate: float,
    avg_mood: float | None,
    avg_energy: float | None,
    teeth_brushing_rate: float,
) -> float:
    score = 0.0
    factors = 0

    if breakfast_rate > 0:
        score += (breakfast_rate / 100) * 25
        factors += 1

    if avg_mood is not None:
        score += (avg_mood / 5) * 30
        factors += 1

    if avg_energy is not None:
        score += (avg_energy / 5) * 30
        factors += 1

    if teeth_brushing_rate > 0:
        score += (teeth_brushing_rate / 100) * 15
        factors += 1

    return score if factors > 0 else 0.0


@handle_errors("generating check-in insights", default_return=[])
def _generate_insights(
    breakfast_rate: float,
    avg_mood: float | None,
    avg_energy: float | None,
    teeth_brushing_rate: float,
    mood_trend: str,
    energy_trend: str,
) -> list[str]:
    insights: list[str] = []

    if breakfast_rate >= 80:
        insights.append("excellent breakfast habits")
    elif breakfast_rate >= 60:
        insights.append("good breakfast consistency")
    elif breakfast_rate <= 30:
        insights.append("room for improvement in breakfast habits")

    if avg_mood is not None:
        if avg_mood >= 4:
            insights.append("generally positive mood")
        elif avg_mood <= 2:
            insights.append("challenging mood patterns")

        if mood_trend == "improving":
            insights.append("mood is trending upward")
        elif mood_trend == "declining":
            insights.append("mood is trending downward")

    if avg_energy is not None:
        if avg_energy >= 4:
            insights.append("good energy levels")
        elif avg_energy <= 2:
            insights.append("low energy patterns")

        if energy_trend == "improving":
            insights.append("energy is trending upward")
        elif energy_trend == "declining":
            insights.append("energy is trending downward")

    if teeth_brushing_rate >= 90:
        insights.append("excellent dental hygiene")
    elif teeth_brushing_rate <= 50:
        insights.append("room for improvement in dental hygiene")

    return insights


@handle_errors("analyzing check-in entries", default_return=ContextAnalysis())
def analyze_checkin_entries(
    recent_checkins: list[dict[str, Any]] | None,
) -> ContextAnalysis:
    """Compute check-in metrics from raw recent-response rows."""
    entries = list(recent_checkins or [])
    if not entries:
        logger.debug("No recent check-ins available for analysis")
        return ContextAnalysis()

    total_entries = len(entries)
    logger.debug(f"Analyzing {total_entries} recent check-ins")

    breakfast_count = sum(
        1 for entry in entries if entry.get("ate_breakfast") is True
    )
    breakfast_rate = (breakfast_count / total_entries) * 100 if total_entries else 0.0

    moods: list[float] = []
    for entry in entries:
        mood = entry.get("mood")
        if mood is not None:
            moods.append(float(mood))
    avg_mood = sum(moods) / len(moods) if moods else None

    energies: list[float] = []
    for entry in entries:
        energy = entry.get("energy")
        if energy is not None:
            energies.append(float(energy))
    avg_energy = sum(energies) / len(energies) if energies else None

    teeth_brushed_count = sum(
        1 for entry in entries if entry.get("brushed_teeth") is True
    )
    teeth_brushing_rate = (
        (teeth_brushed_count / total_entries) * 100 if total_entries else 0.0
    )

    mood_trend = _determine_trend(moods)
    energy_trend = _determine_trend(energies)
    wellness_score = _calculate_wellness_score(
        breakfast_rate, avg_mood, avg_energy, teeth_brushing_rate
    )
    insights = _generate_insights(
        breakfast_rate,
        avg_mood,
        avg_energy,
        teeth_brushing_rate,
        mood_trend,
        energy_trend,
    )

    logger.debug(
        f"Check-in analysis completed: wellness_score={wellness_score:.1f}, "
        f"mood_trend={mood_trend}, energy_trend={energy_trend}, "
        f"insights_count={len(insights)}"
    )

    return ContextAnalysis(
        total_entries=total_entries,
        breakfast_count=breakfast_count,
        teeth_brushed_count=teeth_brushed_count,
        breakfast_rate=breakfast_rate,
        avg_mood=avg_mood,
        avg_energy=avg_energy,
        teeth_brushing_rate=teeth_brushing_rate,
        mood_trend=mood_trend,
        energy_trend=energy_trend,
        overall_wellness_score=wellness_score,
        insights=insights,
    )
