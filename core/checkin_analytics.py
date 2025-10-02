# core/checkin_analytics.py

"""
Check-in Analytics Module

Provides insights and analysis from check-in data to help users
understand their patterns and progress over time.
"""

import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from core.logger import get_logger, get_component_logger
from core.response_tracking import get_recent_checkins
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_component_logger('analytics')
analytics_logger = get_component_logger('user_activity')

class CheckinAnalytics:
    def __init__(self):
        """
        Initialize the CheckinAnalytics instance.
        
        This class provides analytics and insights from check-in data.
        """
        pass
    
    @handle_errors("analyzing mood trends", default_return={"error": "Analysis failed"})
    def get_mood_trends(self, user_id: str, days: int = 30) -> Dict:
        """Analyze mood trends over the specified period"""
        checkins = get_recent_checkins(user_id, limit=days)
        if not checkins:
            return {"error": "No check-in data available"}
        
        # Extract mood data with timestamps
        mood_data = []
        for checkin in checkins:
            if 'mood' in checkin and 'timestamp' in checkin:
                try:
                    timestamp = datetime.strptime(checkin['timestamp'], '%Y-%m-%d %H:%M:%S')
                    mood_data.append({
                        'date': timestamp.date(),
                        'mood': checkin['mood'],
                        'timestamp': checkin['timestamp']
                    })
                except (ValueError, TypeError):
                    continue
        
        if not mood_data:
            return {"error": "No valid mood data found"}
        
        # Calculate statistics
        moods = [d['mood'] for d in mood_data]
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
        best_day = max(mood_data, key=lambda x: x['mood'])
        worst_day = min(mood_data, key=lambda x: x['mood'])
        
        return {
            "period_days": days,
            "total_checkins": len(mood_data),
            "average_mood": round(avg_mood, 2),
            "mood_volatility": round(mood_std, 2),
            "trend": trend,
            "best_day": {
                "date": best_day['date'].strftime('%Y-%m-%d'),
                "mood": best_day['mood']
            },
            "worst_day": {
                "date": worst_day['date'].strftime('%Y-%m-%d'),
                "mood": worst_day['mood']
            },
            "mood_distribution": self._get_mood_distribution(moods),
            "recent_data": mood_data[:7]  # Last 7 days
        }
    
    @handle_errors("analyzing habits", default_return={"error": "Analysis failed"})
    def get_habit_analysis(self, user_id: str, days: int = 30) -> Dict:
        """Analyze habit patterns from check-in data"""
        checkins = get_recent_checkins(user_id, limit=days)
        if not checkins:
            return {"error": "No check-in data available"}
        
        # Define habits to track
        habits = {
            'ate_breakfast': 'Breakfast',
            'brushed_teeth': 'Teeth Brushing',
            'medication_taken': 'Medication',
            'exercise': 'Exercise',
            'hydration': 'Hydration',
            'social_interaction': 'Social Interaction'
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
                    "current_streak": streak_info['current'],
                    "best_streak": streak_info['best'],
                    "status": self._get_habit_status(completion_rate)
                }
        
        return {
            "period_days": days,
            "habits": habit_stats,
            "overall_completion": self._calculate_overall_completion(habit_stats)
        }
    
    @handle_errors("analyzing sleep", default_return={"error": "Analysis failed"})
    def get_sleep_analysis(self, user_id: str, days: int = 30) -> Dict:
        """Analyze sleep patterns from check-in data"""
        checkins = get_recent_checkins(user_id, limit=days)
        if not checkins:
            return {"error": "No check-in data available"}
        
        sleep_data = []
        for checkin in checkins:
            if 'sleep_hours' in checkin and 'sleep_quality' in checkin:
                try:
                    timestamp = datetime.strptime(checkin['timestamp'], '%Y-%m-%d %H:%M:%S')
                    sleep_data.append({
                        'date': timestamp.date(),
                        'hours': checkin['sleep_hours'],
                        'quality': checkin['sleep_quality'],
                        'timestamp': checkin['timestamp']
                    })
                except (ValueError, TypeError):
                    continue
        
        if not sleep_data:
            return {"error": "No valid sleep data found"}
        
        # Calculate sleep statistics
        hours = [d['hours'] for d in sleep_data]
        quality = [d['quality'] for d in sleep_data]
        
        avg_hours = statistics.mean(hours)
        avg_quality = statistics.mean(quality)
        
        # Identify sleep patterns
        good_sleep_days = [d for d in sleep_data if d['hours'] >= 7 and d['quality'] >= 4]
        poor_sleep_days = [d for d in sleep_data if d['hours'] < 6 or d['quality'] <= 2]
        
        return {
            "period_days": days,
            "total_sleep_records": len(sleep_data),
            "average_hours": round(avg_hours, 1),
            "average_quality": round(avg_quality, 1),
            "good_sleep_days": len(good_sleep_days),
            "poor_sleep_days": len(poor_sleep_days),
            "sleep_consistency": self._calculate_sleep_consistency(hours),
            "recommendations": self._get_sleep_recommendations(avg_hours, avg_quality, len(poor_sleep_days)),
            "recent_data": sleep_data[:7]  # Last 7 days
        }
    
    @handle_errors("calculating wellness score", default_return={"error": "Calculation failed"})
    def get_wellness_score(self, user_id: str, days: int = 7) -> Dict:
        """Calculate overall wellness score from check-in data"""
        checkins = get_recent_checkins(user_id, limit=days)
        if not checkins:
            return {"error": "No check-in data available"}
        
        # Calculate component scores
        mood_score = self._calculate_mood_score(checkins)
        habit_score = self._calculate_habit_score(checkins)
        sleep_score = self._calculate_sleep_score(checkins)
        
        # Calculate overall score (weighted average)
        overall_score = (mood_score * 0.4) + (habit_score * 0.4) + (sleep_score * 0.2)
        
        return {
            "score": round(overall_score, 1),
            "level": self._get_score_level(overall_score),
            "components": {
                "mood_score": round(mood_score, 1),
                "habit_score": round(habit_score, 1),
                "sleep_score": round(sleep_score, 1)
            },
            "period_days": days,
            "recommendations": self._get_wellness_recommendations(mood_score, habit_score, sleep_score)
        }
    
    @handle_errors("getting check-in history", default_return={"error": "History retrieval failed"})
    def get_checkin_history(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get check-in history with proper date formatting"""
        checkins = get_recent_checkins(user_id, limit=days)
        if not checkins:
            return []
        
        formatted_history = []
        for checkin in checkins:
            if 'timestamp' in checkin:
                try:
                    timestamp = datetime.strptime(checkin['timestamp'], '%Y-%m-%d %H:%M:%S')
                    formatted_date = timestamp.strftime('%Y-%m-%d')
                    
                    formatted_checkin = {
                        'date': formatted_date,
                        'mood': checkin.get('mood', 'No mood recorded'),
                        'timestamp': checkin['timestamp']
                    }
                    
                    # Add habit information if available
                    habits = ['ate_breakfast', 'brushed_teeth', 'medication_taken', 'exercise', 'hydration', 'social_interaction']
                    for habit in habits:
                        if habit in checkin:
                            formatted_checkin[habit] = checkin[habit]
                    
                    formatted_history.append(formatted_checkin)
                except (ValueError, TypeError):
                    continue
        
        return formatted_history

    @handle_errors("computing quantitative summaries", default_return={"error": "Analysis failed"})
    def get_quantitative_summaries(self, user_id: str, days: int = 30, enabled_fields: Optional[List[str]] = None) -> Dict[str, Dict[str, float]]:
        """Compute per-field averages and ranges for opted-in quantitative fields.

        Parameters:
            user_id: target user
            days: number of recent check-ins to analyze
            enabled_fields: list of fields to include (e.g., ['mood','energy','stress','sleep_quality','anxiety'])

        Returns mapping: { field: { 'average': float, 'min': float, 'max': float, 'count': int } }
        Only includes fields that appear in the data and are in enabled_fields if provided.
        """
        checkins = get_recent_checkins(user_id, limit=days)
        if not checkins:
            return {"error": "No check-in data"}

        # If enabled_fields is not provided, get it from user preferences
        if enabled_fields is None:
            try:
                from core.user_data_handlers import get_user_data
                prefs = get_user_data(user_id, 'preferences') or {}
                checkin_settings = (prefs.get('preferences') or {}).get('checkin_settings') or {}
                if isinstance(checkin_settings, dict):
                    # LEGACY COMPATIBILITY: Support old enabled_fields format
                    if 'enabled_fields' in checkin_settings:
                        logger.warning(f"LEGACY COMPATIBILITY: User {user_id} using old enabled_fields format - consider migrating to questions format")
                        enabled_fields = checkin_settings.get('enabled_fields', [])
                        logger.debug(f"LEGACY: Found enabled_fields: {enabled_fields}")
                    else:
                        # Get enabled fields from new questions configuration
                        questions = checkin_settings.get('questions', {})
                        enabled_fields = [key for key, config in questions.items() 
                                        if config.get('enabled', False) and 
                                        config.get('type') in ['scale_1_5', 'number', 'yes_no']]
            except Exception:
                enabled_fields = None

        # Candidate fields available directly on checkin dicts
        # Include all quantitative fields from questions.json
        candidate_fields = [
            # Scale 1-5 questions
            'mood', 'energy', 'stress_level', 'sleep_quality', 'anxiety_level', 
            'focus_level',
            # Number questions  
            'sleep_hours',
            # Yes/No questions (converted to 0/1 for analytics)
            'ate_breakfast', 'brushed_teeth', 'medication_taken', 'exercise', 
            'hydration', 'social_interaction'
        ]

        if enabled_fields is not None:
            # LEGACY COMPATIBILITY: For legacy enabled_fields, include any field that's in the data
            # For new questions format, only include fields that are in candidate_fields
            try:
                from core.user_data_handlers import get_user_data
                prefs = get_user_data(user_id, 'preferences') or {}
                checkin_settings = (prefs.get('preferences') or {}).get('checkin_settings') or {}
                is_legacy_format = isinstance(checkin_settings, dict) and 'enabled_fields' in checkin_settings
            except Exception:
                is_legacy_format = False
                
            if is_legacy_format:
                # Legacy format: include any field that's in enabled_fields and has data
                fields = enabled_fields
                logger.debug(f"LEGACY: Using fields directly: {fields}")
            else:
                # New format: only include fields that are in candidate_fields
                fields = [f for f in candidate_fields if f in enabled_fields]
                logger.debug(f"NEW: Filtered fields: {fields}")
        else:
            fields = candidate_fields

        summaries: Dict[str, Dict[str, float]] = {}
        for field in fields:
            values: List[float] = []
            for c in checkins:
                if field in c:
                    try:
                        v_raw = c[field]
                        # Handle yes/no questions by converting to 0/1
                        if isinstance(v_raw, str):
                            v_raw_lower = v_raw.lower().strip()
                            if v_raw_lower in ['yes', 'y', 'true', '1']:
                                v = 1.0
                            elif v_raw_lower in ['no', 'n', 'false', '0']:
                                v = 0.0
                            else:
                                v = float(v_raw)
                        else:
                            v = float(v_raw)
                        values.append(v)
                    except Exception:
                        continue
                # Also support responses dict with numeric answers
                elif isinstance(c.get('responses'), dict) and field in c['responses']:
                    try:
                        v_raw = c['responses'][field]
                        # Handle yes/no questions by converting to 0/1
                        if isinstance(v_raw, str):
                            v_raw_lower = v_raw.lower().strip()
                            if v_raw_lower in ['yes', 'y', 'true', '1']:
                                v = 1.0
                            elif v_raw_lower in ['no', 'n', 'false', '0']:
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
                    'average': round(statistics.mean(values), 2),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values),
                }
        return summaries if summaries else {"error": "No quantitative fields present"}
    
    @handle_errors("calculating completion rate", default_return={"error": "Calculation failed"})
    def get_completion_rate(self, user_id: str, days: int = 30) -> Dict:
        """Calculate overall completion rate for check-ins"""
        checkins = get_recent_checkins(user_id, limit=days)
        if not checkins:
            return {"error": "No check-in data available"}
        
        total_days = len(checkins)
        completed_days = sum(1 for checkin in checkins if checkin.get('completed', False))
        missed_days = total_days - completed_days
        
        completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
        
        return {
            "rate": round(completion_rate, 1),
            "days_completed": completed_days,
            "days_missed": missed_days,
            "total_days": total_days,
            "period_days": days
        }
    
    @handle_errors("calculating task weekly stats", default_return={"error": "Calculation failed"})
    def get_task_weekly_stats(self, user_id: str, days: int = 7) -> Dict:
        """Calculate weekly statistics for tasks"""
        checkins = get_recent_checkins(user_id, limit=days)
        if not checkins:
            return {"error": "No check-in data available"}
        
        # Define tasks to track
        tasks = {
            'ate_breakfast': 'Breakfast',
            'brushed_teeth': 'Teeth Brushing', 
            'medication_taken': 'Medication',
            'exercise': 'Exercise',
            'hydration': 'Hydration',
            'social_interaction': 'Social Interaction'
        }
        
        task_stats = {}
        for task_key, task_name in tasks.items():
            completed_days = sum(1 for checkin in checkins if checkin.get(task_key, False))
            missed_days = len(checkins) - completed_days
            
            task_stats[task_name] = {
                "completed_days": completed_days,
                "missed_days": missed_days,
                "total_days": len(checkins),
                "completion_rate": round((completed_days / len(checkins) * 100) if len(checkins) > 0 else 0, 1)
            }
        
        return task_stats
    
    @handle_errors("calculating mood distribution", default_return={1: 0, 2: 0, 3: 0, 4: 0, 5: 0})
    def _get_mood_distribution(self, moods: List[int]) -> Dict:
        """Calculate distribution of mood scores"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for mood in moods:
            if mood in distribution:
                distribution[mood] += 1
        return distribution
    
    @handle_errors("calculating habit streak", default_return={"current": 0, "best": 0})
    def _calculate_streak(self, checkins: List[Dict], habit_key: str) -> Dict:
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
        
        return {
            "current": current_streak,
            "best": best_streak
        }
    
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
    def _calculate_overall_completion(self, habit_stats: Dict) -> float:
        """Calculate overall habit completion rate"""
        if not habit_stats:
            return 0
        
        total_rate = sum(habit['completion_rate'] for habit in habit_stats.values())
        return round(total_rate / len(habit_stats), 1)
    
    @handle_errors("calculating sleep consistency", default_return=0.0)
    def _calculate_sleep_consistency(self, hours: List[float]) -> float:
        """Calculate sleep consistency (lower variance = more consistent)"""
        if len(hours) < 2:
            return 100
        
        variance = statistics.variance(hours)
        # Convert variance to consistency score (0-100)
        consistency = max(0, 100 - (variance * 10))
        return round(consistency, 1)
    
    @handle_errors("generating sleep recommendations", default_return=[])
    def _get_sleep_recommendations(self, avg_hours: float, avg_quality: float, poor_days: int) -> List[str]:
        """Generate sleep recommendations"""
        recommendations = []
        
        if avg_hours < 7:
            recommendations.append("Try to get at least 7-8 hours of sleep per night")
        elif avg_hours > 9:
            recommendations.append("Consider if you're getting too much sleep")
        
        if avg_quality < 3:
            recommendations.append("Work on improving sleep quality with a bedtime routine")
        
        if poor_days > 3:
            recommendations.append("Consider consulting a sleep specialist if poor sleep persists")
        
        if not recommendations:
            recommendations.append("Your sleep patterns look good! Keep it up!")
        
        return recommendations
    
    @handle_errors("calculating mood score", default_return=50.0)
    def _calculate_mood_score(self, checkins: List[Dict]) -> float:
        """Calculate mood score (0-100)"""
        moods = [c.get('mood', 3) for c in checkins if 'mood' in c]
        if not moods:
            return 50
        
        # Convert 1-5 scale to 0-100
        avg_mood = statistics.mean(moods)
        return (avg_mood - 1) * 25
    
    @handle_errors("calculating habit score", default_return=50.0)
    def _calculate_habit_score(self, checkins: List[Dict]) -> float:
        """Calculate habit score (0-100)"""
        habits = ['ate_breakfast', 'brushed_teeth', 'medication_taken', 'exercise', 'hydration']
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
    
    @handle_errors("calculating sleep score", default_return=50.0)
    def _calculate_sleep_score(self, checkins: List[Dict]) -> float:
        """Calculate sleep score (0-100)"""
        sleep_records = []
        for checkin in checkins:
            if 'sleep_hours' in checkin and 'sleep_quality' in checkin:
                hours = checkin['sleep_hours']
                quality = checkin['sleep_quality']
                
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
    def _get_wellness_recommendations(self, mood_score: float, habit_score: float, sleep_score: float) -> List[str]:
        """Generate wellness recommendations based on component scores"""
        recommendations = []
        
        if mood_score < 60:
            recommendations.append("Focus on activities that boost your mood")
        
        if habit_score < 60:
            recommendations.append("Work on building consistent daily habits")
        
        if sleep_score < 60:
            recommendations.append("Prioritize improving your sleep routine")
        
        if not recommendations:
            recommendations.append("Your wellness is looking good! Keep up the great work!")
        
        return recommendations

# Create a global instance for convenience
checkin_analytics = CheckinAnalytics() 
