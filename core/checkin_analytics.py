# core/checkin_analytics.py

"""
Check-in Analytics Module

Provides insights and analysis from check-in data to help users
understand their patterns and progress over time.
"""

import statistics
from datetime import datetime
from typing import Dict, List, Optional
from core.logger import get_component_logger
from core.response_tracking import get_checkins_by_days
from core.error_handling import handle_errors
from core.time_utilities import TIMESTAMP_FULL, TIME_ONLY_MINUTE

logger = get_component_logger("user_activity")
analytics_logger = get_component_logger("user_activity")


class CheckinAnalytics:
    @handle_errors("initializing checkin analytics", default_return=None)
    def __init__(self):
        """
        Initialize the CheckinAnalytics instance.

        This class provides analytics and insights from check-in data.
        """
        pass

    @handle_errors("analyzing mood trends", default_return={"error": "Analysis failed"})
    def get_mood_trends(self, user_id: str, days: int = 30) -> dict:
        """Analyze mood trends over the specified period"""
        checkins = get_checkins_by_days(user_id, days)
        if not checkins:
            return {"error": "No check-in data available"}

        # Extract mood data with timestamps
        mood_data = []
        for checkin in checkins:
            if "mood" in checkin and "timestamp" in checkin:
                try:
                    timestamp = datetime.strptime(checkin["timestamp"], TIMESTAMP_FULL)
                    mood_data.append(
                        {
                            "date": timestamp.date(),
                            "mood": checkin["mood"],
                            "timestamp": checkin["timestamp"],
                        }
                    )
                except (ValueError, TypeError):
                    continue

        if not mood_data:
            return {"error": "No valid mood data found"}

        moods = [d["mood"] for d in mood_data]
        avg_mood = statistics.mean(moods)
        mood_std = statistics.stdev(moods) if len(moods) > 1 else 0

        # Identify trends
        recent_moods = moods[:7] if len(moods) >= 7 else moods
        older_moods = moods[7:14] if len(moods) >= 14 else []

        trend = "stable"
        if len(older_moods) > 0:
            recent_avg = statistics.mean(recent_moods)
            older_avg = statistics.mean(older_moods)
            if recent_avg > older_avg + 0.5:
                trend = "improving"
            elif recent_avg < older_avg - 0.5:
                trend = "declining"

        # Find best and worst days
        best_day = max(mood_data, key=lambda x: x["mood"])
        worst_day = min(mood_data, key=lambda x: x["mood"])

        # Calculate min and max for range display
        min_mood = min(moods)
        max_mood = max(moods)

        return {
            "period_days": days,
            "total_checkins": len(mood_data),
            "average_mood": round(avg_mood, 2),
            "min_mood": min_mood,
            "max_mood": max_mood,
            "mood_volatility": round(mood_std, 2),
            "trend": trend,
            "best_day": {
                # ISO date should come from the date object
                "date": best_day["date"].isoformat(),
                "mood": best_day["mood"],
            },
            "worst_day": {
                "date": worst_day["date"].isoformat(),
                "mood": worst_day["mood"],
            },
            "mood_distribution": self._get_mood_distribution(moods),
            "recent_data": mood_data[:7],  # Last 7 days
        }

    @handle_errors(
        "analyzing energy trends", default_return={"error": "Analysis failed"}
    )
    def get_energy_trends(self, user_id: str, days: int = 30) -> dict:
        """Analyze energy trends over the specified period"""
        checkins = get_checkins_by_days(user_id, days)
        if not checkins:
            return {"error": "No check-in data available"}

        # Extract energy data with timestamps
        energy_data = []
        for checkin in checkins:
            if "energy" in checkin and "timestamp" in checkin:
                try:
                    timestamp = datetime.strptime(checkin["timestamp"], TIMESTAMP_FULL)
                    energy_data.append(
                        {
                            "date": timestamp.date(),
                            "energy": checkin["energy"],
                            "timestamp": checkin["timestamp"],
                        }
                    )
                except (ValueError, TypeError):
                    continue

        if not energy_data:
            return {"error": "No valid energy data found"}

        energies = [d["energy"] for d in energy_data]
        avg_energy = statistics.mean(energies)
        energy_std = statistics.stdev(energies) if len(energies) > 1 else 0

        # Identify trends
        recent_energies = energies[:7] if len(energies) >= 7 else energies
        older_energies = energies[7:14] if len(energies) >= 14 else []

        trend = "stable"
        if len(older_energies) > 0:
            recent_avg = statistics.mean(recent_energies)
            older_avg = statistics.mean(older_energies)
            if recent_avg > older_avg + 0.5:
                trend = "improving"
            elif recent_avg < older_avg + 0.5:
                trend = "declining"

        # Find best and worst days
        best_day = max(energy_data, key=lambda x: x["energy"])
        worst_day = min(energy_data, key=lambda x: x["energy"])

        # Calculate min and max for range display
        min_energy = min(energies)
        max_energy = max(energies)

        return {
            "period_days": days,
            "total_checkins": len(energy_data),
            "average_energy": round(avg_energy, 2),
            "min_energy": min_energy,
            "max_energy": max_energy,
            "energy_volatility": round(energy_std, 2),
            "trend": trend,
            "best_day": {
                "date": best_day["date"].isoformat(),
                "energy": best_day["energy"],
            },
            "worst_day": {
                "date": worst_day["date"].isoformat(),
                "energy": worst_day["energy"],
            },
            "energy_distribution": self._get_energy_distribution(energies),
            "recent_data": energy_data[:7],  # Last 7 days
        }

    @handle_errors("analyzing habits", default_return={"error": "Analysis failed"})
    def get_habit_analysis(self, user_id: str, days: int = 30) -> dict:
        """Analyze habit patterns from check-in data"""
        checkins = get_checkins_by_days(user_id, days)
        if not checkins:
            return {"error": "No check-in data available"}

        # Define habits to track
        habits = {
            "ate_breakfast": "Breakfast",
            "brushed_teeth": "Teeth Brushing",
            "medication_taken": "Medication",
            "exercise": "Exercise",
            "hydration": "Hydration",
            "social_interaction": "Social Interaction",
            "treatment_adherence": "Treatment Adherence",
        }

        habit_stats = {}
        for habit_key, habit_name in habits.items():
            habit_data = []
            for checkin in checkins:
                if habit_key in checkin:
                    habit_data.append(checkin[habit_key])

            if habit_data:
                completion_rate = sum(habit_data) / len(habit_data) * 100
                streak_info = self._calculate_streak(checkins, habit_key)

                habit_stats[habit_key] = {
                    "name": habit_name,
                    "completion_rate": round(completion_rate, 1),
                    "total_days": len(habit_data),
                    "completed_days": sum(habit_data),
                    "current_streak": streak_info["current"],
                    "best_streak": streak_info["best"],
                    "status": self._get_habit_status(completion_rate),
                }

        return {
            "period_days": days,
            "habits": habit_stats,
            "overall_completion": self._calculate_overall_completion(habit_stats),
        }

    @handle_errors("analyzing sleep", default_return={"error": "Analysis failed"})
    def get_sleep_analysis(self, user_id: str, days: int = 30) -> dict:
        """Analyze sleep patterns from check-in data"""
        checkins = get_checkins_by_days(user_id, days)
        if not checkins:
            return {"error": "No check-in data available"}

        sleep_data = []
        for checkin in checkins:
            # Check for any sleep-related data (quality or schedule)
            has_sleep_data = "sleep_quality" in checkin or "sleep_schedule" in checkin
            if has_sleep_data:
                try:
                    timestamp = datetime.strptime(checkin["timestamp"], TIMESTAMP_FULL)
                    sleep_entry = {
                        "date": timestamp.date(),
                        "timestamp": checkin["timestamp"],
                    }

                    # Add available sleep data
                    if "sleep_quality" in checkin:
                        sleep_entry["quality"] = checkin["sleep_quality"]
                    if "sleep_schedule" in checkin:
                        schedule = checkin["sleep_schedule"]
                        if (
                            isinstance(schedule, dict)
                            and "sleep_time" in schedule
                            and "wake_time" in schedule
                        ):
                            sleep_duration = self._calculate_sleep_duration(
                                schedule["sleep_time"], schedule["wake_time"]
                            )
                            if sleep_duration is not None:
                                sleep_entry["hours"] = sleep_duration

                    sleep_data.append(sleep_entry)
                except (ValueError, TypeError):
                    continue

        if not sleep_data:
            return {"error": "No valid sleep data found"}

        hours = [d["hours"] for d in sleep_data if "hours" in d]
        quality = [d["quality"] for d in sleep_data if "quality" in d]

        avg_hours = statistics.mean(hours) if hours else None
        avg_quality = statistics.mean(quality) if quality else None

        # Identify sleep patterns
        good_sleep_days = []
        poor_sleep_days = []

        for d in sleep_data:
            is_good = True
            is_poor = True

            if "hours" in d and "quality" in d:
                is_good = d["hours"] >= 7 and d["quality"] >= 4
                is_poor = d["hours"] < 6 or d["quality"] <= 2
            elif "quality" in d:
                is_good = d["quality"] >= 4
                is_poor = d["quality"] <= 2
            elif "hours" in d:
                is_good = d["hours"] >= 7
                is_poor = d["hours"] < 6

            if is_good:
                good_sleep_days.append(d)
            if is_poor:
                poor_sleep_days.append(d)

        return {
            "period_days": days,
            "total_sleep_records": len(sleep_data),
            "average_hours": round(avg_hours, 1) if avg_hours is not None else None,
            "average_quality": (
                round(avg_quality, 1) if avg_quality is not None else None
            ),
            "good_sleep_days": len(good_sleep_days),
            "poor_sleep_days": len(poor_sleep_days),
            "sleep_consistency": (
                self._calculate_sleep_consistency(hours) if hours else None
            ),
            "recommendations": self._get_sleep_recommendations(
                avg_hours, avg_quality, len(poor_sleep_days)
            ),
            "recent_data": sleep_data[:7],  # Last 7 days
        }

    @handle_errors(
        "calculating wellness score", default_return={"error": "Calculation failed"}
    )
    def get_wellness_score(self, user_id: str, days: int = 7) -> dict:
        """Calculate overall wellness score from check-in data"""
        checkins = get_checkins_by_days(user_id, days)
        if not checkins:
            return {
                "error": "No check-in data available",
                "total_checkins": 0,
                "data_completeness": 0.0,
            }

        # Additional validation: check if we have meaningful data
        if len(checkins) < 3:  # Need at least 3 check-ins for meaningful analysis
            return {
                "error": "Insufficient data for analysis",
                "total_checkins": len(checkins),
                "data_completeness": (len(checkins) / days) * 100,
            }

        mood_score = self._calculate_mood_score(checkins)
        energy_score = self._calculate_energy_score(checkins)
        habit_score = self._calculate_habit_score(checkins)
        sleep_score = self._calculate_sleep_score(checkins)

        # Weighted average: mood 30%, energy 20%, habits 30%, sleep 20%
        overall_score = (
            (mood_score * 0.3)
            + (energy_score * 0.2)
            + (habit_score * 0.3)
            + (sleep_score * 0.2)
        )

        return {
            "score": round(overall_score, 1),
            "level": self._get_score_level(overall_score),
            "components": {
                "mood_score": round(mood_score, 1),
                "energy_score": round(energy_score, 1),
                "habit_score": round(habit_score, 1),
                "sleep_score": round(sleep_score, 1),
            },
            "period_days": days,
            "recommendations": self._get_wellness_recommendations(
                mood_score, energy_score, habit_score, sleep_score
            ),
        }

    @handle_errors(
        "getting check-in history", default_return={"error": "History retrieval failed"}
    )
    def get_checkin_history(self, user_id: str, days: int = 30) -> list[dict]:
        """Get check-in history with proper date formatting"""
        checkins = get_checkins_by_days(user_id, days)
        if not checkins:
            return []

        formatted_history = []
        for checkin in checkins:
            if "timestamp" in checkin:
                try:
                    timestamp = datetime.strptime(checkin["timestamp"], TIMESTAMP_FULL)

                    formatted_checkin = {
                        # ISO date should come from the date object
                        "date": timestamp.date().isoformat(),
                        "mood": checkin.get("mood", "No mood recorded"),
                        "energy": checkin.get("energy", "No energy recorded"),
                        "timestamp": checkin["timestamp"],
                    }

                    # Add habit information if available
                    habits = [
                        "ate_breakfast",
                        "brushed_teeth",
                        "medication_taken",
                        "exercise",
                        "hydration",
                        "social_interaction",
                    ]
                    for habit in habits:
                        if habit in checkin:
                            formatted_checkin[habit] = checkin[habit]

                    formatted_history.append(formatted_checkin)
                except (ValueError, TypeError):
                    continue

        return formatted_history

    @handle_errors(
        "detecting available data types", default_return={"error": "Detection failed"}
    )
    def get_available_data_types(self, user_id: str, days: int = 30) -> dict:
        """Detect what types of data are available for analytics"""
        checkins = get_checkins_by_days(user_id, days)
        if not checkins:
            return {"error": "No check-in data available"}

        # Analyze what data is actually present
        data_types = {
            "mood": False,
            "energy": False,
            "sleep": False,
            "habits": False,
            "quantitative": False,
        }

        # Check for mood data
        mood_data = [c for c in checkins if "mood" in c]
        if mood_data:
            data_types["mood"] = True
            data_types["quantitative"] = True

        # Check for energy data
        energy_data = [c for c in checkins if "energy" in c]
        if energy_data:
            data_types["quantitative"] = True

        # Check for sleep data
        sleep_data = [
            c for c in checkins if "sleep_quality" in c or "sleep_schedule" in c
        ]
        if sleep_data:
            data_types["sleep"] = True
            data_types["quantitative"] = True

        # Check for habit data
        habit_fields = [
            "ate_breakfast",
            "brushed_teeth",
            "medication_taken",
            "exercise",
            "hydration",
            "social_interaction",
        ]
        habit_data = [c for c in checkins if any(field in c for field in habit_fields)]
        if habit_data:
            data_types["habits"] = True
            data_types["quantitative"] = True

        return {
            "data_types": data_types,
            "total_checkins": len(checkins),
            "analysis_period": days,
        }

    @handle_errors(
        "computing quantitative summaries", default_return={"error": "Analysis failed"}
    )
    def get_quantitative_summaries(
        self, user_id: str, days: int = 30, enabled_fields: list[str] | None = None
    ) -> dict[str, dict[str, float]]:
        """Compute per-field averages and ranges for opted-in quantitative fields.

        Parameters:
            user_id: target user
            days: number of recent check-ins to analyze
            enabled_fields: list of fields to include (e.g., ['mood','energy','stress','sleep_quality','anxiety'])

        Returns mapping: { field: { 'average': float, 'min': float, 'max': float, 'count': int } }
        Only includes fields that appear in the data and are in enabled_fields if provided.
        """
        checkins = get_checkins_by_days(user_id, days)
        if not checkins:
            return {"error": "No check-in data"}

        # Candidate fields available directly on checkin dicts
        # Include all quantitative fields from questions.json
        candidate_fields = [
            # Scale 1-5 questions
            "mood",
            "energy",
            "stress_level",
            "sleep_quality",
            "anxiety_level",
            "focus_level",
            "hopelessness_level",
            "irritability_level",
            "motivation_level",
            # Number questions
            "sleep_schedule",
            # Yes/No questions (converted to 0/1 for analytics)
            "ate_breakfast",
            "brushed_teeth",
            "medication_taken",
            "exercise",
            "hydration",
            "social_interaction",
            "treatment_adherence",
        ]

        # If enabled_fields is not provided, check user preferences first, then fall back to auto-detection
        if enabled_fields is None:
            try:
                from core.user_data_handlers import get_user_data

                prefs = get_user_data(user_id, "preferences") or {}
                checkin_settings = (prefs.get("preferences") or {}).get(
                    "checkin_settings"
                ) or {}

                # Check for new questions format
                if "questions" in checkin_settings:
                    questions = checkin_settings["questions"]
                    enabled_fields = []
                    for field, config in questions.items():
                        if isinstance(config, dict) and config.get("enabled", False):
                            if field in candidate_fields:
                                enabled_fields.append(field)
                    logger.debug(
                        f"Using questions format enabled fields: {enabled_fields}"
                    )
                else:
                    # Fall back to auto-detection from data
                    available_fields = set()
                    for checkin in checkins:
                        for field in candidate_fields:
                            if field in checkin and checkin[field] is not None:
                                available_fields.add(field)
                    enabled_fields = list(available_fields)
                    logger.debug(f"Auto-detected available fields: {enabled_fields}")
            except Exception as e:
                logger.warning(f"Error checking user preferences: {e}")
                # Fall back to auto-detection
                available_fields = set()
                for checkin in checkins:
                    for field in candidate_fields:
                        if field in checkin and checkin[field] is not None:
                            available_fields.add(field)
                enabled_fields = list(available_fields)
                logger.debug(f"Auto-detected available fields: {enabled_fields}")

        if enabled_fields is not None:
            # Only include fields that are in candidate_fields
            fields = [f for f in candidate_fields if f in enabled_fields]
            logger.debug(f"Filtered fields: {fields}")
        else:
            fields = candidate_fields

        summaries: dict[str, dict[str, float]] = {}
        for field in fields:
            values: list[float] = []
            for c in checkins:
                if field in c:
                    try:
                        v_raw = c[field]
                        # Skip 'SKIPPED' responses to avoid analytics inaccuracies
                        if v_raw == "SKIPPED":
                            continue
                        # Handle sleep_schedule specially (convert to hours)
                        if field == "sleep_schedule" and isinstance(v_raw, dict):
                            if "sleep_time" in v_raw and "wake_time" in v_raw:
                                duration = self._calculate_sleep_duration(
                                    v_raw["sleep_time"], v_raw["wake_time"]
                                )
                                if duration is not None:
                                    values.append(duration)
                            continue
                        # Handle yes/no questions by converting to 0/1
                        if isinstance(v_raw, bool):
                            # Boolean values from validation (True/False)
                            v = 1.0 if v_raw else 0.0
                        elif isinstance(v_raw, str):
                            v_raw_lower = v_raw.lower().strip()
                            if v_raw_lower in [
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
                            ]:
                                v = 1.0
                            elif v_raw_lower in [
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
                            ]:
                                v = 0.0
                            else:
                                v = float(v_raw)
                        else:
                            v = float(v_raw)
                        values.append(v)
                    except Exception:
                        continue
                # Also support responses dict with numeric answers
                elif isinstance(c.get("responses"), dict) and field in c["responses"]:
                    try:
                        v_raw = c["responses"][field]
                        # Skip 'SKIPPED' responses to avoid analytics inaccuracies
                        if v_raw == "SKIPPED":
                            continue
                        # Handle yes/no questions by converting to 0/1
                        if isinstance(v_raw, bool):
                            # Boolean values from validation (True/False)
                            v = 1.0 if v_raw else 0.0
                        elif isinstance(v_raw, str):
                            v_raw_lower = v_raw.lower().strip()
                            if v_raw_lower in [
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
                            ]:
                                v = 1.0
                            elif v_raw_lower in [
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
                            ]:
                                v = 0.0
                            else:
                                v = float(v_raw)
                        else:
                            v = float(v_raw)
                        values.append(v)
                    except Exception:
                        continue
            if values:
                summaries[field] = {
                    "average": round(statistics.mean(values), 2),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }
        return summaries if summaries else {"error": "No quantitative fields present"}

    @handle_errors(
        "calculating completion rate", default_return={"error": "Calculation failed"}
    )
    def get_completion_rate(self, user_id: str, days: int = 30) -> dict:
        """Calculate overall completion rate for check-ins"""
        checkins = get_checkins_by_days(user_id, days)
        if not checkins:
            return {"error": "No check-in data available"}

        total_days = len(checkins)
        completed_days = sum(
            1 for checkin in checkins if checkin.get("completed", False)
        )
        missed_days = total_days - completed_days

        completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0

        return {
            "rate": round(completion_rate, 1),
            "days_completed": completed_days,
            "days_missed": missed_days,
            "total_days": total_days,
            "period_days": days,
        }

    @handle_errors(
        "calculating task weekly stats", default_return={"error": "Calculation failed"}
    )
    def get_task_weekly_stats(self, user_id: str, days: int = 7) -> dict:
        """Calculate weekly statistics for tasks"""
        checkins = get_checkins_by_days(user_id, days)
        if not checkins:
            return {"error": "No check-in data available"}

        # Define tasks to track
        tasks = {
            "ate_breakfast": "Breakfast",
            "brushed_teeth": "Teeth Brushing",
            "medication_taken": "Medication",
            "exercise": "Exercise",
            "hydration": "Hydration",
            "social_interaction": "Social Interaction",
        }

        task_stats = {}
        for task_key, task_name in tasks.items():
            completed_days = sum(
                1 for checkin in checkins if checkin.get(task_key, False)
            )
            missed_days = len(checkins) - completed_days

            task_stats[task_name] = {
                "completed_days": completed_days,
                "missed_days": missed_days,
                "total_days": len(checkins),
                "completion_rate": round(
                    (completed_days / len(checkins) * 100) if len(checkins) > 0 else 0,
                    1,
                ),
            }

        return task_stats

    @handle_errors(
        "calculating mood distribution", default_return={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    )
    def _get_mood_distribution(self, moods: list[int]) -> dict:
        """Calculate distribution of mood scores"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for mood in moods:
            if mood in distribution:
                distribution[mood] += 1
        return distribution

    @handle_errors(
        "calculating energy distribution", default_return={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    )
    def _get_energy_distribution(self, energies: list[int]) -> dict:
        """Calculate distribution of energy scores"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for energy in energies:
            if energy in distribution:
                distribution[energy] += 1
        return distribution

    @handle_errors("calculating habit streak", default_return={"current": 0, "best": 0})
    def _calculate_streak(self, checkins: list[dict], habit_key: str) -> dict:
        """Calculate current and best streaks for a habit"""
        current_streak = 0
        best_streak = 0
        temp_streak = 0

        for checkin in checkins:
            if habit_key in checkin and checkin[habit_key]:
                temp_streak += 1
                if temp_streak == 1:  # First day of streak
                    current_streak = temp_streak
            else:
                if temp_streak > best_streak:
                    best_streak = temp_streak
                temp_streak = 0

        # Check if current streak is the best
        if temp_streak > best_streak:
            best_streak = temp_streak

        return {"current": current_streak, "best": best_streak}

    @handle_errors("determining habit status", default_return="unknown")
    def _get_habit_status(self, completion_rate: float) -> str:
        """Get status description for habit completion rate"""
        if completion_rate >= 90:
            return "Excellent"
        elif completion_rate >= 75:
            return "Good"
        elif completion_rate >= 50:
            return "Fair"
        else:
            return "Needs Improvement"

    @handle_errors("calculating overall completion", default_return=0.0)
    def _calculate_overall_completion(self, habit_stats: dict) -> float:
        """Calculate overall habit completion rate"""
        if not habit_stats:
            return 0

        total_rate = sum(habit["completion_rate"] for habit in habit_stats.values())
        return round(total_rate / len(habit_stats), 1)

    @handle_errors("calculating sleep consistency", default_return=0.0)
    def _calculate_sleep_consistency(self, hours: list[float]) -> float:
        """Calculate sleep consistency (lower variance = more consistent)"""
        if len(hours) < 2:
            return 100

        variance = statistics.variance(hours)
        # Convert variance to consistency score (0-100)
        consistency = max(0, 100 - (variance * 10))
        return round(consistency, 1)

    @handle_errors("generating sleep recommendations", default_return=[])
    def _get_sleep_recommendations(
        self, avg_hours: float, avg_quality: float, poor_days: int
    ) -> list[str]:
        """Generate sleep recommendations"""
        recommendations = []

        # Handle None values for missing data
        if avg_hours is not None:
            if avg_hours < 7:
                recommendations.append(
                    "Try to get at least 7-8 hours of sleep per night"
                )
            elif avg_hours > 9:
                recommendations.append("Consider if you're getting too much sleep")

        if avg_quality is not None:
            if avg_quality < 3:
                recommendations.append(
                    "Work on improving sleep quality with a bedtime routine"
                )

        if poor_days > 3:
            recommendations.append(
                "Consider consulting a sleep specialist if poor sleep persists"
            )

        if not recommendations:
            recommendations.append("Your sleep patterns look good! Keep it up!")

        return recommendations

    @staticmethod
    @handle_errors("converting score from 0-100 to 1-5 scale", default_return=0.0)
    def convert_score_100_to_5(score_100: float) -> float:
        """
        Convert a score from 0-100 scale to 1-5 scale for display.

        Args:
            score_100: Score on 0-100 scale

        Returns:
            Score on 1-5 scale, rounded to 1 decimal place
        """
        if score_100 <= 0:
            return 0.0
        return round((score_100 / 25) + 1, 1)

    @staticmethod
    @handle_errors("converting score from 1-5 to 0-100 scale", default_return=0.0)
    def convert_score_5_to_100(score_5: float) -> float:
        """
        Convert a score from 1-5 scale to 0-100 scale for calculations.

        Args:
            score_5: Score on 1-5 scale

        Returns:
            Score on 0-100 scale
        """
        if score_5 <= 0:
            return 0.0
        return (score_5 - 1) * 25

    @handle_errors("calculating mood score", default_return=50.0)
    def _calculate_mood_score(self, checkins: list[dict]) -> float:
        """Calculate mood score (0-100)"""
        moods = [c.get("mood", 3) for c in checkins if "mood" in c]
        if not moods:
            return 50

        # Convert 1-5 scale to 0-100
        avg_mood = statistics.mean(moods)
        return self.convert_score_5_to_100(avg_mood)

    @handle_errors("calculating energy score", default_return=50.0)
    def _calculate_energy_score(self, checkins: list[dict]) -> float:
        """Calculate energy score (0-100)"""
        energies = [c.get("energy", 3) for c in checkins if "energy" in c]
        if not energies:
            return 50

        # Convert 1-5 scale to 0-100
        avg_energy = statistics.mean(energies)
        return self.convert_score_5_to_100(avg_energy)

    @handle_errors("calculating habit score", default_return=50.0)
    def _calculate_habit_score(self, checkins: list[dict]) -> float:
        """Calculate habit score (0-100)"""
        habits = [
            "ate_breakfast",
            "brushed_teeth",
            "medication_taken",
            "exercise",
            "hydration",
        ]
        total_completion = 0
        total_possible = 0

        for checkin in checkins:
            for habit in habits:
                if habit in checkin:
                    total_possible += 1
                    if checkin[habit]:
                        total_completion += 1

        if total_possible == 0:
            return 50

        return (total_completion / total_possible) * 100

    @handle_errors("calculating sleep duration", default_return=None)
    def _calculate_sleep_duration(
        self, sleep_time: str, wake_time: str
    ) -> float | None:
        """Calculate sleep duration in hours from sleep_time and wake_time (HH:MM format)."""
        try:
            from datetime import datetime, timedelta

            # Parse times
            sleep_dt = datetime.strptime(sleep_time, TIME_ONLY_MINUTE)
            wake_dt = datetime.strptime(wake_time, TIME_ONLY_MINUTE)

            # Calculate duration (handle overnight sleep)
            if wake_dt < sleep_dt:
                # Sleep spans midnight
                duration = (
                    wake_dt + timedelta(days=1) - sleep_dt
                ).total_seconds() / 3600
            else:
                duration = (wake_dt - sleep_dt).total_seconds() / 3600

            return round(duration, 1)
        except (ValueError, TypeError):
            return None

    @handle_errors("calculating sleep score", default_return=50.0)
    def _calculate_sleep_score(self, checkins: list[dict]) -> float:
        """Calculate sleep score (0-100)"""
        sleep_records = []
        for checkin in checkins:
            hours = None
            quality = None

            # Get sleep quality
            if "sleep_quality" in checkin:
                quality = checkin["sleep_quality"]

            # Get sleep hours from sleep_schedule
            if "sleep_schedule" in checkin:
                schedule = checkin["sleep_schedule"]
                if (
                    isinstance(schedule, dict)
                    and "sleep_time" in schedule
                    and "wake_time" in schedule
                ):
                    hours = self._calculate_sleep_duration(
                        schedule["sleep_time"], schedule["wake_time"]
                    )

            # Need both hours and quality to calculate score
            if hours is not None and quality is not None:
                # Score based on hours (optimal: 7-9 hours)
                if 7 <= hours <= 9:
                    hour_score = 100
                elif 6 <= hours <= 10:
                    hour_score = 80
                else:
                    hour_score = 40

                # Score based on quality (1-5 scale)
                quality_score = (quality - 1) * 25

                # Average the scores
                sleep_records.append((hour_score + quality_score) / 2)

        if not sleep_records:
            return 50

        return statistics.mean(sleep_records)

    @handle_errors("determining score level", default_return="unknown")
    def _get_score_level(self, score: float) -> str:
        """Get wellness score level description"""
        if score >= 80:
            return "Excellent"
        elif score >= 65:
            return "Good"
        elif score >= 50:
            return "Fair"
        else:
            return "Needs Attention"

    @handle_errors("generating wellness recommendations", default_return=[])
    def _get_wellness_recommendations(
        self,
        mood_score: float,
        energy_score: float,
        habit_score: float,
        sleep_score: float,
    ) -> list[str]:
        """Generate wellness recommendations based on component scores"""
        recommendations = []

        if mood_score < 60:
            recommendations.append("Focus on activities that boost your mood")

        if energy_score < 60:
            recommendations.append(
                "Consider rest, nutrition, and gentle movement to boost energy"
            )

        if habit_score < 60:
            recommendations.append("Work on building consistent daily habits")

        if sleep_score < 60:
            recommendations.append("Prioritize improving your sleep routine")

        if not recommendations:
            recommendations.append(
                "Your wellness is looking good! Keep up the great work!"
            )

        return recommendations


# Create a global instance for convenience
checkin_analytics = CheckinAnalytics()
