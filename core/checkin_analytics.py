# core/checkin_analytics.py

"""
Check-in Analytics Module

Provides insights and analysis from daily check-in data to help users
understand their patterns and progress over time.
"""

import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from core.logger import get_logger
from core.response_tracking import get_recent_daily_checkins
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_logger(__name__)

class CheckinAnalytics:
    def __init__(self):
        pass
    
    @handle_errors("analyzing mood trends", default_return={"error": "Analysis failed"})
    def get_mood_trends(self, user_id: str, days: int = 30) -> Dict:
        """Analyze mood trends over the specified period"""
        checkins = get_recent_daily_checkins(user_id, limit=days)
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
        checkins = get_recent_daily_checkins(user_id, limit=days)
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
        checkins = get_recent_daily_checkins(user_id, limit=days)
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
        """Calculate a comprehensive wellness score based on recent check-ins"""
        checkins = get_recent_daily_checkins(user_id, limit=days)
        if not checkins:
            return {"error": "No check-in data available"}
        
        # Calculate component scores
        mood_score = self._calculate_mood_score(checkins)
        habit_score = self._calculate_habit_score(checkins)
        sleep_score = self._calculate_sleep_score(checkins)
        
        # Weight the components
        overall_score = (mood_score * 0.4 + habit_score * 0.3 + sleep_score * 0.3)
        
        return {
            "overall_score": round(overall_score, 1),
            "mood_score": round(mood_score, 1),
            "habit_score": round(habit_score, 1),
            "sleep_score": round(sleep_score, 1),
            "period_days": days,
            "score_level": self._get_score_level(overall_score),
            "recommendations": self._get_wellness_recommendations(mood_score, habit_score, sleep_score)
        }
    
    def _get_mood_distribution(self, moods: List[int]) -> Dict:
        """Calculate distribution of mood scores"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for mood in moods:
            if mood in distribution:
                distribution[mood] += 1
        return distribution
    
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
    
    def _calculate_overall_completion(self, habit_stats: Dict) -> float:
        """Calculate overall habit completion rate"""
        if not habit_stats:
            return 0
        
        total_rate = sum(habit['completion_rate'] for habit in habit_stats.values())
        return round(total_rate / len(habit_stats), 1)
    
    def _calculate_sleep_consistency(self, hours: List[float]) -> float:
        """Calculate sleep consistency (lower variance = more consistent)"""
        if len(hours) < 2:
            return 100
        
        variance = statistics.variance(hours)
        # Convert variance to consistency score (0-100)
        consistency = max(0, 100 - (variance * 10))
        return round(consistency, 1)
    
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
    
    def _calculate_mood_score(self, checkins: List[Dict]) -> float:
        """Calculate mood score (0-100)"""
        moods = [c.get('mood', 3) for c in checkins if 'mood' in c]
        if not moods:
            return 50
        
        # Convert 1-5 scale to 0-100
        avg_mood = statistics.mean(moods)
        return (avg_mood - 1) * 25
    
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