"""Shared check-in analysis for AI context, fallback, and product analytics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import parse_time_only_minute

logger = get_component_logger("user_activity")

MIN_CHECKINS_FOR_NAMED_SCORE = 3
WELLNESS_WEIGHTS = {
    "mood": 0.30,
    "energy": 0.20,
    "habits": 0.30,
    "sleep": 0.20,
}
WELLNESS_HABITS = (
    "ate_breakfast",
    "brushed_teeth",
    "medication_taken",
    "exercise",
    "hydration",
)
RESERVED_CHECKIN_KEYS = {
    "submitted_at",
    "timestamp",
    "date",
    "user_id",
    "completed",
    "responses",
    "questions_asked",
}
_YES_TEXTS = {
    "yes",
    "y",
    "yeah",
    "yep",
    "true",
    "1",
    "absolutely",
    "definitely",
    "sure",
    "of course",
    "i did",
    "i have",
    "100",
    "100%",
    "correct",
    "affirmative",
    "indeed",
    "certainly",
    "positively",
}
_NO_TEXTS = {
    "no",
    "n",
    "nope",
    "false",
    "0",
    "not",
    "never",
    "i didn't",
    "i did not",
    "i haven't",
    "i have not",
    "no way",
    "absolutely not",
    "definitely not",
    "negative",
    "incorrect",
    "wrong",
    "0%",
}


@dataclass
class CheckinAnalysis:
    """Canonical check-in metrics from recent response rows."""

    total_entries: int = 0
    breakfast_count: int = 0
    teeth_brushed_count: int = 0
    breakfast_rate: float = 0.0
    avg_mood: float | None = None
    avg_energy: float | None = None
    teeth_brushing_rate: float = 0.0
    mood_trend: str = "stable"
    energy_trend: str = "stable"
    mood_score: float | None = None
    energy_score: float | None = None
    habit_score: float | None = None
    sleep_score: float | None = None
    overall_wellness_score: float = 0.0
    wellness_level: str = "unknown"
    insights: list[str] | None = None

    @handle_errors("post-initializing check-in analysis", default_return=None)
    def __post_init__(self):
        if self.insights is None:
            self.insights = []


ContextAnalysis = CheckinAnalysis


@handle_errors("listing questions asked on a check-in", default_return=[])
def get_questions_asked(checkin: dict[str, Any]) -> list[str]:
    """Return the list of questions asked for a check-in."""
    questions_asked = checkin.get("questions_asked")
    if isinstance(questions_asked, list):
        return [q for q in questions_asked if isinstance(q, str) and q]
    responses = checkin.get("responses")
    if isinstance(responses, dict):
        return [key for key in responses if isinstance(key, str) and key]
    return [
        key
        for key in checkin
        if isinstance(key, str) and key not in RESERVED_CHECKIN_KEYS
    ]


@handle_errors("checking whether a check-in question was asked", default_return=False)
def is_question_asked(checkin: dict[str, Any], question_key: str) -> bool:
    """Return True when a question was asked or is present on the row."""
    questions_asked = checkin.get("questions_asked")
    if isinstance(questions_asked, list):
        return question_key in questions_asked
    responses = checkin.get("responses")
    if isinstance(responses, dict) and question_key in responses:
        return True
    return question_key not in RESERVED_CHECKIN_KEYS and question_key in checkin


@handle_errors("getting check-in response value", default_return=None)
def response_value(checkin: dict[str, Any], key: str) -> Any:
    """Read a check-in answer from nested responses or a flattened top-level key."""
    responses = checkin.get("responses")
    if isinstance(responses, dict) and key in responses:
        return responses.get(key)
    if key not in RESERVED_CHECKIN_KEYS and key in checkin:
        return checkin.get(key)
    return None


@handle_errors("checking answered value", default_return=False)
def is_answered_value(value: Any) -> bool:
    """Return True if the value counts as answered."""
    if value is None:
        return False
    if value == "SKIPPED":
        return True
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


@handle_errors("coercing yes/no value", default_return=None)
def coerce_yes_no(value: Any) -> bool | None:
    """Convert yes/no-like values to bool."""
    if value is None or value == "SKIPPED":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value in (0, 1):
            return bool(value)
        return None
    if isinstance(value, str):
        text = value.strip().lower()
        if text in _YES_TEXTS:
            return True
        if text in _NO_TEXTS:
            return False
    return None


@handle_errors("coercing numeric value", default_return=None)
def coerce_numeric(value: Any) -> float | None:
    """Convert numeric-like values to float, skipping invalid or skipped entries."""
    if value is None or value == "SKIPPED":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value_str = value.strip()
        if not value_str:
            return None
        try:
            return float(value_str)
        except ValueError:
            return None
    return None


@handle_errors("calculating sleep duration", default_return=None)
def calculate_sleep_duration(sleep_time: str, wake_time: str) -> float | None:
    """Calculate sleep duration in hours from HH:MM sleep and wake times."""
    try:
        sleep_dt = parse_time_only_minute(sleep_time)
        wake_dt = parse_time_only_minute(wake_time)
        if sleep_dt is None or wake_dt is None:
            return None
        if wake_dt < sleep_dt:
            duration = (wake_dt + timedelta(days=1) - sleep_dt).total_seconds() / 3600
        else:
            duration = (wake_dt - sleep_dt).total_seconds() / 3600
        return round(duration, 1)
    except (ValueError, TypeError):
        return None


@handle_errors("coercing sleep hours", default_return=None)
def coerce_sleep_hours(value: Any) -> float | None:
    """Convert sleep schedule values into hours."""
    if value is None or value == "SKIPPED":
        return None
    if isinstance(value, dict):
        total_sleep_hours = value.get("total_sleep_hours")
        if isinstance(total_sleep_hours, (int, float)):
            return float(total_sleep_hours)
        sleep_chunks = value.get("sleep_chunks")
        if isinstance(sleep_chunks, list) and sleep_chunks:
            chunk_total = 0.0
            for chunk in sleep_chunks:
                if not isinstance(chunk, dict):
                    return None
                duration = chunk.get("duration_hours")
                if isinstance(duration, (int, float)):
                    chunk_total += float(duration)
                    continue
                sleep_time = chunk.get("sleep_time")
                wake_time = chunk.get("wake_time")
                if sleep_time and wake_time:
                    chunk_duration = calculate_sleep_duration(sleep_time, wake_time)
                    if chunk_duration is None:
                        return None
                    chunk_total += chunk_duration
                    continue
                return None
            return round(chunk_total, 1)
        sleep_time = value.get("sleep_time")
        wake_time = value.get("wake_time")
        if sleep_time and wake_time:
            return calculate_sleep_duration(sleep_time, wake_time)
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        if "-" in cleaned:
            parts = cleaned.split("-", 1)
            return calculate_sleep_duration(parts[0].strip(), parts[1].strip())
    return None


@handle_errors("converting score from 1-5 to 0-100 scale", default_return=0.0)
def convert_score_5_to_100(score_5: float) -> float:
    """Convert a score from 1-5 scale to 0-100 scale."""
    if score_5 <= 0:
        return 0.0
    return (score_5 - 1) * 25


@handle_errors("converting score from 0-100 to 1-5 scale", default_return=0.0)
def convert_score_100_to_5(score_100: float) -> float:
    """Convert a score from 0-100 scale to 1-5 scale."""
    if score_100 <= 0:
        return 0.0
    return round((score_100 / 25) + 1, 1)


@handle_errors("determining numeric trend", default_return="stable")
def determine_numeric_trend(
    values: list[float], recent_count: int | None = None
) -> str:
    """Return improving, declining, or stable from a numeric series."""
    if recent_count is not None:
        recent_values = values[:recent_count] if len(values) >= recent_count else values
        older_values = (
            values[recent_count : recent_count * 2] if len(values) >= recent_count * 2 else []
        )
        if not older_values:
            return "stable"
        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)
        if recent_avg > older_avg + 0.5:
            return "improving"
        if recent_avg < older_avg - 0.5:
            return "declining"
        return "stable"

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


_determine_trend = determine_numeric_trend


@handle_errors("calculating wellness score", default_return=0.0)
def calculate_wellness_score(
    mood_score: float | None = None,
    energy_score: float | None = None,
    habit_score: float | None = None,
    sleep_score: float | None = None,
) -> float:
    """Weighted wellness score; missing components are omitted and weights renormalized."""
    components = {
        "mood": mood_score,
        "energy": energy_score,
        "habits": habit_score,
        "sleep": sleep_score,
    }
    present = {key: value for key, value in components.items() if value is not None}
    if not present:
        return 0.0
    total_weight = sum(WELLNESS_WEIGHTS[key] for key in present)
    if total_weight <= 0:
        return 0.0
    return sum(present[key] * WELLNESS_WEIGHTS[key] for key in present) / total_weight


_calculate_wellness_score = calculate_wellness_score


@handle_errors("determining wellness score level", default_return="unknown")
def wellness_score_level(score: float) -> str:
    """Get wellness score level description."""
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 50:
        return "Fair"
    return "Needs Attention"


@handle_errors("generating wellness recommendations", default_return=[])
def wellness_recommendations(
    mood_score: float | None,
    energy_score: float | None,
    habit_score: float | None,
    sleep_score: float | None,
) -> list[str]:
    """Generate wellness recommendations from present component scores."""
    if all(score is None for score in (mood_score, energy_score, habit_score, sleep_score)):
        return ["Complete more detailed check-ins to see wellness insights."]

    recommendations: list[str] = []
    if mood_score is not None and mood_score < 60:
        recommendations.append("Focus on activities that boost your mood")
    if energy_score is not None and energy_score < 60:
        recommendations.append(
            "Consider rest, nutrition, and gentle movement to boost energy"
        )
    if habit_score is not None and habit_score < 60:
        recommendations.append("Work on building consistent daily habits")
    if sleep_score is not None and sleep_score < 60:
        recommendations.append("Prioritize improving your sleep routine")
    if not recommendations:
        recommendations.append("Your wellness is looking good! Keep up the great work!")
    return recommendations


@handle_errors("generating check-in insights", default_return=[])
def generate_insights(
    breakfast_rate: float,
    avg_mood: float | None,
    avg_energy: float | None,
    teeth_brushing_rate: float,
    mood_trend: str,
    energy_trend: str,
) -> list[str]:
    """Phrase compact check-in insights for prompts and fallback copy."""
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


_generate_insights = generate_insights


@handle_errors("collecting numeric check-in values", default_return=[])
def collect_numeric_values(checkins: list[dict[str, Any]], key: str) -> list[float]:
    """Collect asked-and-answered numeric values for one check-in field."""
    values: list[float] = []
    for checkin in checkins:
        if not is_question_asked(checkin, key):
            continue
        number = coerce_numeric(response_value(checkin, key))
        if number is not None:
            values.append(number)
    return values


@handle_errors("calculating habit completion score", default_return=None)
def calculate_habit_score(checkins: list[dict[str, Any]]) -> float | None:
    """Return 0-100 habit completion among asked wellness habits, or None if none asked."""
    total_completion = 0
    total_possible = 0
    for checkin in checkins:
        for habit in WELLNESS_HABITS:
            if not is_question_asked(checkin, habit):
                continue
            value = coerce_yes_no(response_value(checkin, habit))
            if value is None:
                continue
            total_possible += 1
            if value:
                total_completion += 1
    if total_possible == 0:
        return None
    return (total_completion / total_possible) * 100


@handle_errors("calculating sleep score", default_return=None)
def calculate_sleep_score(checkins: list[dict[str, Any]]) -> float | None:
    """Return 0-100 sleep score from hours plus quality, or None if incomplete."""
    sleep_records: list[float] = []
    for checkin in checkins:
        hours = None
        quality = None
        if is_question_asked(checkin, "sleep_quality"):
            quality = coerce_numeric(response_value(checkin, "sleep_quality"))
        if is_question_asked(checkin, "sleep_schedule"):
            hours = coerce_sleep_hours(response_value(checkin, "sleep_schedule"))
        if hours is None or quality is None:
            continue
        if 7 <= hours <= 9:
            hour_score = 100.0
        elif 6 <= hours <= 10:
            hour_score = 80.0
        else:
            hour_score = 40.0
        quality_score = convert_score_5_to_100(quality)
        sleep_records.append((hour_score + quality_score) / 2)
    if not sleep_records:
        return None
    return sum(sleep_records) / len(sleep_records)


@handle_errors("formatting wellness score report", default_return={})
def format_wellness_score_report(
    analysis: CheckinAnalysis, *, period_days: int
) -> dict[str, Any]:
    """Shape CheckinAnalysis into the UI/command wellness-score payload."""
    components: dict[str, float] = {}
    if analysis.mood_score is not None:
        components["mood_score"] = round(analysis.mood_score, 1)
    if analysis.energy_score is not None:
        components["energy_score"] = round(analysis.energy_score, 1)
    if analysis.habit_score is not None:
        components["habit_score"] = round(analysis.habit_score, 1)
    if analysis.sleep_score is not None:
        components["sleep_score"] = round(analysis.sleep_score, 1)
    return {
        "score": round(analysis.overall_wellness_score, 1),
        "level": analysis.wellness_level,
        "components": components,
        "period_days": period_days,
        "recommendations": wellness_recommendations(
            analysis.mood_score,
            analysis.energy_score,
            analysis.habit_score,
            analysis.sleep_score,
        ),
        "total_checkins": analysis.total_entries,
    }


@handle_errors(
    "reading check-in analysis from structured context",
    default_return=CheckinAnalysis(),
)
def analysis_from_structured(structured: dict[str, Any] | None) -> CheckinAnalysis:
    """Return envelope analytics when present, otherwise analyze recent check-in rows."""
    payload = structured or {}
    analytics = payload.get("analytics") or {}
    analysis = analytics.get("checkin_analysis")
    if isinstance(analysis, CheckinAnalysis):
        return analysis
    checkins = payload.get("checkins") or {}
    return analyze_checkin_entries(list(checkins.get("recent") or []))


@handle_errors("analyzing check-in entries", default_return=CheckinAnalysis())
def analyze_checkin_entries(
    recent_checkins: list[dict[str, Any]] | None,
) -> CheckinAnalysis:
    """Compute check-in metrics from raw recent-response rows."""
    entries = [entry for entry in list(recent_checkins or []) if isinstance(entry, dict)]
    if not entries:
        logger.debug("No recent check-ins available for analysis")
        return CheckinAnalysis()

    total_entries = len(entries)
    logger.debug(f"Analyzing {total_entries} recent check-ins")

    breakfast_count = sum(
        1 for entry in entries if coerce_yes_no(response_value(entry, "ate_breakfast")) is True
    )
    breakfast_rate = (breakfast_count / total_entries) * 100 if total_entries else 0.0

    moods = collect_numeric_values(entries, "mood")
    avg_mood = sum(moods) / len(moods) if moods else None

    energies = collect_numeric_values(entries, "energy")
    avg_energy = sum(energies) / len(energies) if energies else None

    teeth_brushed_count = sum(
        1 for entry in entries if coerce_yes_no(response_value(entry, "brushed_teeth")) is True
    )
    teeth_brushing_rate = (
        (teeth_brushed_count / total_entries) * 100 if total_entries else 0.0
    )

    mood_trend = determine_numeric_trend(moods)
    energy_trend = determine_numeric_trend(energies)
    mood_score = convert_score_5_to_100(avg_mood) if avg_mood is not None else None
    energy_score = convert_score_5_to_100(avg_energy) if avg_energy is not None else None
    habit_score = calculate_habit_score(entries)
    sleep_score = calculate_sleep_score(entries)
    wellness_score = calculate_wellness_score(
        mood_score=mood_score,
        energy_score=energy_score,
        habit_score=habit_score,
        sleep_score=sleep_score,
    )
    insights = generate_insights(
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

    return CheckinAnalysis(
        total_entries=total_entries,
        breakfast_count=breakfast_count,
        teeth_brushed_count=teeth_brushed_count,
        breakfast_rate=breakfast_rate,
        avg_mood=avg_mood,
        avg_energy=avg_energy,
        teeth_brushing_rate=teeth_brushing_rate,
        mood_trend=mood_trend,
        energy_trend=energy_trend,
        mood_score=mood_score,
        energy_score=energy_score,
        habit_score=habit_score,
        sleep_score=sleep_score,
        overall_wellness_score=wellness_score,
        wellness_level=wellness_score_level(wellness_score),
        insights=insights,
    )
