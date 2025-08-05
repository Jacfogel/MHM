"""
Behavior tests for checkin_analytics module.

Tests real behavior and side effects for check-in analytics functionality.
Focuses on data analysis, trend detection, and wellness scoring.
"""

import pytest
import json
import statistics
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

from core.checkin_analytics import CheckinAnalytics

class TestCheckinAnalyticsInitializationBehavior:
    """Test CheckinAnalytics initialization with real behavior verification."""
    
    @pytest.mark.behavior
    def test_analytics_initialization_real_behavior(self):
        """REAL BEHAVIOR TEST: Test CheckinAnalytics can be initialized."""
        # ✅ VERIFY REAL BEHAVIOR: Analytics can be created
        analytics = CheckinAnalytics()
        assert analytics is not None, "CheckinAnalytics should be created successfully"
        assert isinstance(analytics, CheckinAnalytics), "Should be correct type"

class TestCheckinAnalyticsMoodTrendsBehavior:
    """Test mood trends analysis with real behavior verification."""
    
    @pytest.fixture
    def analytics(self):
        """Create CheckinAnalytics instance for testing."""
        return CheckinAnalytics()
    
    @pytest.fixture
    def mock_checkins_with_mood(self):
        """Create mock check-in data with mood information."""
        base_date = datetime.now() - timedelta(days=30)
        checkins = []
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            checkins.append({
                'timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
                'mood': 3 + (i % 3),  # Alternating moods: 3, 4, 5
                'user_id': 'test_user'
            })
        
        return checkins
    
    @pytest.mark.behavior
    def test_mood_trends_no_data_real_behavior(self, analytics):
        """REAL BEHAVIOR TEST: Test mood trends with no check-in data."""
        # ✅ VERIFY REAL BEHAVIOR: No data returns error
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=[]):
            result = analytics.get_mood_trends('test_user', days=30)
        
        assert 'error' in result, "Should return error when no data available"
        assert result['error'] == 'No check-in data available', "Should have correct error message"
    
    @pytest.mark.behavior
    def test_mood_trends_with_data_real_behavior(self, analytics, mock_checkins_with_mood):
        """REAL BEHAVIOR TEST: Test mood trends analysis with valid data."""
        # ✅ VERIFY REAL BEHAVIOR: Analysis works with valid data
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=mock_checkins_with_mood):
            result = analytics.get_mood_trends('test_user', days=30)
        
        # ✅ VERIFY REAL BEHAVIOR: Result has expected structure
        assert 'error' not in result, "Should not have error with valid data"
        assert 'period_days' in result, "Should have period_days"
        assert 'total_checkins' in result, "Should have total_checkins"
        assert 'average_mood' in result, "Should have average_mood"
        assert 'trend' in result, "Should have trend"
        assert 'best_day' in result, "Should have best_day"
        assert 'worst_day' in result, "Should have worst_day"
        
        # ✅ VERIFY REAL BEHAVIOR: Values are reasonable
        assert result['period_days'] == 30, "Should have correct period"
        assert result['total_checkins'] == 30, "Should have correct total checkins"
        assert 3.0 <= result['average_mood'] <= 5.0, "Average mood should be in valid range"
        assert result['trend'] in ['stable', 'improving', 'declining'], "Trend should be valid"
    
    @pytest.mark.behavior
    def test_mood_trends_invalid_mood_data_real_behavior(self, analytics):
        """REAL BEHAVIOR TEST: Test mood trends with invalid mood data."""
        # ✅ VERIFY REAL BEHAVIOR: Invalid mood data returns error
        invalid_checkins = [
            {'timestamp': '2024-01-01 10:00:00', 'mood': 'invalid'},  # String instead of number
            {'timestamp': '2024-01-02 10:00:00'},  # Missing mood
            {'mood': 4},  # Missing timestamp
        ]
        
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=invalid_checkins):
            result = analytics.get_mood_trends('test_user', days=30)
        
        assert 'error' in result, "Should return error with invalid mood data"
        assert result['error'] == 'Analysis failed', "Should have correct error message"

class TestCheckinAnalyticsHabitAnalysisBehavior:
    """Test habit analysis with real behavior verification."""
    
    @pytest.fixture
    def analytics(self):
        """Create CheckinAnalytics instance for testing."""
        return CheckinAnalytics()
    
    @pytest.fixture
    def mock_checkins_with_habits(self):
        """Create mock check-in data with habit information."""
        base_date = datetime.now() - timedelta(days=30)
        checkins = []
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            checkins.append({
                'timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
                'ate_breakfast': i % 2,  # Every other day
                'brushed_teeth': 1,  # Every day
                'medication_taken': i % 3 == 0,  # Every third day
                'exercise': i % 4 == 0,  # Every fourth day
                'hydration': 1,  # Every day
                'social_interaction': i % 2,  # Every other day
                'user_id': 'test_user'
            })
        
        return checkins
    
    @pytest.mark.behavior
    def test_habit_analysis_no_data_real_behavior(self, analytics):
        """REAL BEHAVIOR TEST: Test habit analysis with no check-in data."""
        # ✅ VERIFY REAL BEHAVIOR: No data returns error
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=[]):
            result = analytics.get_habit_analysis('test_user', days=30)
        
        assert 'error' in result, "Should return error when no data available"
        assert result['error'] == 'No check-in data available', "Should have correct error message"
    
    @pytest.mark.behavior
    def test_habit_analysis_with_data_real_behavior(self, analytics, mock_checkins_with_habits):
        """REAL BEHAVIOR TEST: Test habit analysis with valid data."""
        # ✅ VERIFY REAL BEHAVIOR: Analysis works with valid data
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=mock_checkins_with_habits):
            result = analytics.get_habit_analysis('test_user', days=30)
        
        # ✅ VERIFY REAL BEHAVIOR: Result has expected structure
        assert 'error' not in result, "Should not have error with valid data"
        assert 'period_days' in result, "Should have period_days"
        assert 'habits' in result, "Should have habits"
        assert 'overall_completion' in result, "Should have overall_completion"
        
        # ✅ VERIFY REAL BEHAVIOR: Habits are analyzed correctly
        habits = result['habits']
        assert 'ate_breakfast' in habits, "Should analyze breakfast habit"
        assert 'brushed_teeth' in habits, "Should analyze teeth brushing habit"
        assert 'medication_taken' in habits, "Should analyze medication habit"
        
        # ✅ VERIFY REAL BEHAVIOR: Habit statistics are reasonable
        breakfast_stats = habits['ate_breakfast']
        assert 'completion_rate' in breakfast_stats, "Should have completion rate"
        assert 'total_days' in breakfast_stats, "Should have total days"
        assert 'completed_days' in breakfast_stats, "Should have completed days"
        assert 'current_streak' in breakfast_stats, "Should have current streak"
        assert 'best_streak' in breakfast_stats, "Should have best streak"
        assert 'status' in breakfast_stats, "Should have status"
        
        # ✅ VERIFY REAL BEHAVIOR: Values are reasonable
        assert 0 <= result['overall_completion'] <= 100, "Overall completion should be percentage"
        assert breakfast_stats['completion_rate'] == 50.0, "Breakfast should be 50% (every other day)"

class TestCheckinAnalyticsSleepAnalysisBehavior:
    """Test sleep analysis with real behavior verification."""
    
    @pytest.fixture
    def analytics(self):
        """Create CheckinAnalytics instance for testing."""
        return CheckinAnalytics()
    
    @pytest.fixture
    def mock_checkins_with_sleep(self):
        """Create mock check-in data with sleep information."""
        base_date = datetime.now() - timedelta(days=30)
        checkins = []
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            checkins.append({
                'timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
                'sleep_hours': 7.0 + (i % 3),  # 7, 8, 9 hours
                'sleep_quality': 3 + (i % 3),  # 3, 4, 5 quality
                'user_id': 'test_user'
            })
        
        return checkins
    
    @pytest.mark.behavior
    def test_sleep_analysis_no_data_real_behavior(self, analytics):
        """REAL BEHAVIOR TEST: Test sleep analysis with no check-in data."""
        # ✅ VERIFY REAL BEHAVIOR: No data returns error
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=[]):
            result = analytics.get_sleep_analysis('test_user', days=30)
        
        assert 'error' in result, "Should return error when no data available"
        assert result['error'] == 'No check-in data available', "Should have correct error message"
    
    @pytest.mark.behavior
    def test_sleep_analysis_with_data_real_behavior(self, analytics, mock_checkins_with_sleep):
        """REAL BEHAVIOR TEST: Test sleep analysis with valid data."""
        # ✅ VERIFY REAL BEHAVIOR: Analysis works with valid data
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=mock_checkins_with_sleep):
            result = analytics.get_sleep_analysis('test_user', days=30)
        
        # ✅ VERIFY REAL BEHAVIOR: Result has expected structure
        assert 'error' not in result, "Should not have error with valid data"
        assert 'period_days' in result, "Should have period_days"
        assert 'total_sleep_records' in result, "Should have total_sleep_records"
        assert 'average_hours' in result, "Should have average_hours"
        assert 'average_quality' in result, "Should have average_quality"
        assert 'good_sleep_days' in result, "Should have good_sleep_days"
        assert 'poor_sleep_days' in result, "Should have poor_sleep_days"
        assert 'sleep_consistency' in result, "Should have sleep_consistency"
        assert 'recommendations' in result, "Should have recommendations"
        
        # ✅ VERIFY REAL BEHAVIOR: Values are reasonable
        assert result['period_days'] == 30, "Should have correct period"
        assert result['total_sleep_records'] == 30, "Should have correct total records"
        assert 7.0 <= result['average_hours'] <= 9.0, "Average hours should be in valid range"
        assert 3.0 <= result['average_quality'] <= 5.0, "Average quality should be in valid range"
        assert isinstance(result['recommendations'], list), "Recommendations should be list"

class TestCheckinAnalyticsWellnessScoreBehavior:
    """Test wellness score calculation with real behavior verification."""
    
    @pytest.fixture
    def analytics(self):
        """Create CheckinAnalytics instance for testing."""
        return CheckinAnalytics()
    
    @pytest.fixture
    def mock_checkins_for_wellness(self):
        """Create mock check-in data for wellness scoring."""
        base_date = datetime.now() - timedelta(days=7)
        checkins = []
        
        for i in range(7):
            date = base_date + timedelta(days=i)
            checkins.append({
                'timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
                'mood': 4,  # Good mood
                'ate_breakfast': 1,  # Good habits
                'brushed_teeth': 1,
                'medication_taken': 1,
                'exercise': 1,
                'hydration': 1,
                'social_interaction': 1,
                'sleep_hours': 8.0,  # Good sleep
                'sleep_quality': 4,
                'user_id': 'test_user'
            })
        
        return checkins
    
    @pytest.mark.behavior
    def test_wellness_score_no_data_real_behavior(self, analytics):
        """REAL BEHAVIOR TEST: Test wellness score with no check-in data."""
        # ✅ VERIFY REAL BEHAVIOR: No data returns error
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=[]):
            result = analytics.get_wellness_score('test_user', days=7)
        
        assert 'error' in result, "Should return error when no data available"
        assert result['error'] == 'No check-in data available', "Should have correct error message"
    
    @pytest.mark.behavior
    def test_wellness_score_with_data_real_behavior(self, analytics, mock_checkins_for_wellness):
        """REAL BEHAVIOR TEST: Test wellness score calculation with valid data."""
        # ✅ VERIFY REAL BEHAVIOR: Score calculation works with valid data
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=mock_checkins_for_wellness):
            result = analytics.get_wellness_score('test_user', days=7)
        
        # ✅ VERIFY REAL BEHAVIOR: Result has expected structure
        assert 'error' not in result, "Should not have error with valid data"
        assert 'components' in result, "Should have components"
        assert 'level' in result, "Should have level"
        assert 'recommendations' in result, "Should have recommendations"
        
        # ✅ VERIFY REAL BEHAVIOR: Components are reasonable
        components = result['components']
        assert 'mood_score' in components, "Should have mood_score in components"
        assert 'habit_score' in components, "Should have habit_score in components"
        assert 'sleep_score' in components, "Should have sleep_score in components"
        
        # ✅ VERIFY REAL BEHAVIOR: Scores are reasonable
        assert 0 <= components['mood_score'] <= 100, "Mood score should be percentage"
        assert 0 <= components['habit_score'] <= 100, "Habit score should be percentage"
        assert 0 <= components['sleep_score'] <= 100, "Sleep score should be percentage"
        assert result['level'] in ['Excellent', 'Good', 'Fair', 'Poor'], "Level should be valid"
        assert isinstance(result['recommendations'], list), "Recommendations should be list"

class TestCheckinAnalyticsHistoryBehavior:
    """Test check-in history functionality with real behavior verification."""
    
    @pytest.fixture
    def analytics(self):
        """Create CheckinAnalytics instance for testing."""
        return CheckinAnalytics()
    
    @pytest.fixture
    def mock_checkins_for_history(self):
        """Create mock check-in data for history testing."""
        base_date = datetime.now() - timedelta(days=30)
        checkins = []
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            checkins.append({
                'timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
                'mood': 4,
                'notes': f'Check-in note for day {i}',
                'user_id': 'test_user'
            })
        
        return checkins
    
    @pytest.mark.behavior
    def test_checkin_history_no_data_real_behavior(self, analytics):
        """REAL BEHAVIOR TEST: Test check-in history with no data."""
        # ✅ VERIFY REAL BEHAVIOR: No data returns empty list
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=[]):
            result = analytics.get_checkin_history('test_user', days=30)
        
        assert isinstance(result, list), "Should return list when no data available"
        assert len(result) == 0, "Should return empty list when no data available"
    
    @pytest.mark.behavior
    def test_checkin_history_with_data_real_behavior(self, analytics, mock_checkins_for_history):
        """REAL BEHAVIOR TEST: Test check-in history with valid data."""
        # ✅ VERIFY REAL BEHAVIOR: History retrieval works with valid data
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=mock_checkins_for_history):
            result = analytics.get_checkin_history('test_user', days=30)
        
        # ✅ VERIFY REAL BEHAVIOR: Result is list of check-ins
        assert isinstance(result, list), "Should return list of check-ins"
        assert len(result) == 30, "Should return correct number of check-ins"
        
        # ✅ VERIFY REAL BEHAVIOR: Each check-in has expected structure
        for checkin in result:
            assert 'timestamp' in checkin, "Each check-in should have timestamp"
            assert 'mood' in checkin, "Each check-in should have mood"
            # Notes may not be present in all check-ins

class TestCheckinAnalyticsCompletionRateBehavior:
    """Test completion rate calculation with real behavior verification."""
    
    @pytest.fixture
    def analytics(self):
        """Create CheckinAnalytics instance for testing."""
        return CheckinAnalytics()
    
    @pytest.fixture
    def mock_checkins_for_completion(self):
        """Create mock check-in data for completion rate testing."""
        base_date = datetime.now() - timedelta(days=30)
        checkins = []
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            checkins.append({
                'timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
                'ate_breakfast': i % 2,  # 50% completion
                'brushed_teeth': 1,  # 100% completion
                'medication_taken': i % 3 == 0,  # 33% completion
                'user_id': 'test_user'
            })
        
        return checkins
    
    @pytest.mark.behavior
    def test_completion_rate_no_data_real_behavior(self, analytics):
        """REAL BEHAVIOR TEST: Test completion rate with no data."""
        # ✅ VERIFY REAL BEHAVIOR: No data returns error
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=[]):
            result = analytics.get_completion_rate('test_user', days=30)
        
        assert 'error' in result, "Should return error when no data available"
        assert result['error'] == 'No check-in data available', "Should have correct error message"
    
    @pytest.mark.behavior
    def test_completion_rate_with_data_real_behavior(self, analytics, mock_checkins_for_completion):
        """REAL BEHAVIOR TEST: Test completion rate calculation with valid data."""
        # ✅ VERIFY REAL BEHAVIOR: Completion rate calculation works with valid data
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=mock_checkins_for_completion):
            result = analytics.get_completion_rate('test_user', days=30)
        
        # ✅ VERIFY REAL BEHAVIOR: Result has expected structure
        assert 'error' not in result, "Should not have error with valid data"
        assert 'period_days' in result, "Should have period_days"
        assert 'rate' in result, "Should have rate"
        assert 'days_completed' in result, "Should have days_completed"
        assert 'days_missed' in result, "Should have days_missed"
        
        # ✅ VERIFY REAL BEHAVIOR: Values are reasonable
        assert result['period_days'] == 30, "Should have correct period"
        assert 0 <= result['rate'] <= 100, "Completion rate should be percentage"

class TestCheckinAnalyticsTaskStatsBehavior:
    """Test task weekly stats with real behavior verification."""
    
    @pytest.fixture
    def analytics(self):
        """Create CheckinAnalytics instance for testing."""
        return CheckinAnalytics()
    
    @pytest.fixture
    def mock_checkins_for_tasks(self):
        """Create mock check-in data for task stats testing."""
        base_date = datetime.now() - timedelta(days=7)
        checkins = []
        
        for i in range(7):
            date = base_date + timedelta(days=i)
            checkins.append({
                'timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
                'tasks_completed': i + 1,  # 1, 2, 3, 4, 5, 6, 7 tasks
                'tasks_total': 10,  # Always 10 total tasks
                'user_id': 'test_user'
            })
        
        return checkins
    
    @pytest.mark.behavior
    def test_task_weekly_stats_no_data_real_behavior(self, analytics):
        """REAL BEHAVIOR TEST: Test task weekly stats with no data."""
        # ✅ VERIFY REAL BEHAVIOR: No data returns error
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=[]):
            result = analytics.get_task_weekly_stats('test_user', days=7)
        
        assert 'error' in result, "Should return error when no data available"
        assert result['error'] == 'No check-in data available', "Should have correct error message"
    
    @pytest.mark.behavior
    def test_task_weekly_stats_with_data_real_behavior(self, analytics, mock_checkins_for_tasks):
        """REAL BEHAVIOR TEST: Test task weekly stats calculation with valid data."""
        # ✅ VERIFY REAL BEHAVIOR: Task stats calculation works with valid data
        with patch('core.checkin_analytics.get_recent_daily_checkins', return_value=mock_checkins_for_tasks):
            result = analytics.get_task_weekly_stats('test_user', days=7)
        
        # ✅ VERIFY REAL BEHAVIOR: Result has expected structure
        assert 'error' not in result, "Should not have error with valid data"
        # Task stats returns habit analysis format
        assert isinstance(result, dict), "Should return dictionary"
        assert len(result) > 0, "Should have habit data"
        
        # ✅ VERIFY REAL BEHAVIOR: Values are reasonable
        # Check that we have habit data for the expected habits
        for habit_name in ['Breakfast', 'Exercise', 'Hydration', 'Medication']:
            if habit_name in result:
                habit_data = result[habit_name]
                assert 'completion_rate' in habit_data, f"{habit_name} should have completion_rate"
                assert 'total_days' in habit_data, f"{habit_name} should have total_days" 