"""
Analytics Handler Behavior Tests

Tests for communication/command_handlers/analytics_handler.py focusing on real behavior and side effects.
These tests verify that the analytics handler actually works and produces expected
side effects rather than just returning values.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import the modules we're testing
from communication.command_handlers.analytics_handler import AnalyticsHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from tests.test_utilities import TestUserFactory


class TestAnalyticsHandlerBehavior:
    """Test analytics handler real behavior and side effects."""
    
    def _create_test_user(self, user_id: str, enable_checkins: bool = True, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, enable_checkins=enable_checkins, test_data_dir=test_data_dir)
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    def test_analytics_handler_can_handle_intents(self):
        """Test that AnalyticsHandler can handle all expected intents."""
        handler = AnalyticsHandler()
        
        expected_intents = [
            'show_analytics', 'mood_trends', 'habit_analysis', 'sleep_analysis', 
            'wellness_score', 'checkin_history', 'checkin_analysis', 
            'completion_rate', 'task_analytics', 'task_stats', 'quant_summary'
        ]
        for intent in expected_intents:
            assert handler.can_handle(intent), f"AnalyticsHandler should handle {intent}"
        
        # Test that it doesn't handle other intents
        assert not handler.can_handle('create_task'), "AnalyticsHandler should not handle create_task"
        assert not handler.can_handle('start_checkin'), "AnalyticsHandler should not handle start_checkin"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    def test_analytics_handler_get_help(self):
        """Test that AnalyticsHandler returns help text."""
        handler = AnalyticsHandler()
        help_text = handler.get_help()
        
        assert isinstance(help_text, str), "Should return help text as string"
        assert len(help_text) > 0, "Help text should not be empty"
        assert "analytics" in help_text.lower(), "Help text should mention analytics"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    def test_analytics_handler_get_examples(self):
        """Test that AnalyticsHandler returns example commands."""
        handler = AnalyticsHandler()
        examples = handler.get_examples()
        
        assert isinstance(examples, list), "Should return examples as list"
        assert len(examples) > 0, "Should have at least one example"
        for example in examples:
            assert isinstance(example, str), "Each example should be a string"
            assert len(example) > 0, "Each example should not be empty"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    def test_analytics_handler_show_analytics_success(self, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler shows analytics successfully."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_show"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock analytics instance
        mock_analytics = MagicMock()
        mock_analytics_class.return_value = mock_analytics
        
        # Mock wellness score
        mock_analytics.get_wellness_score.return_value = {
            'score': 75,
            'level': 'Good',
            'recommendations': ['Get more sleep', 'Exercise regularly']
        }
        
        # Mock mood trends
        mock_analytics.get_mood_trends.return_value = {
            'average_mood': 4.0,
            'min_mood': 3,
            'max_mood': 5,
            'trend': 'Stable'
        }
        
        # Mock habit analysis
        mock_analytics.get_habit_analysis.return_value = {
            'overall_completion': 80,
            'current_streak': 5,
            'best_streak': 10
        }
        
        # Create a parsed command for showing analytics
        parsed_command = ParsedCommand(
            intent="show_analytics",
            entities={'days': 30},
            confidence=0.9,
            original_message="show analytics"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "analytics" in response.message.lower() or "wellness" in response.message.lower(), "Should mention analytics or wellness"
        assert "75" in response.message or "score" in response.message.lower(), "Should include wellness score"
        
        # Verify actual system changes: Check that analytics methods were called with correct parameters
        mock_analytics.get_wellness_score.assert_called_once()
        call_args = mock_analytics.get_wellness_score.call_args
        # Verify days parameter (default 30 if not specified)
        assert call_args[0][0] == user_id, "Should call get_wellness_score with correct user_id"
        assert call_args[0][1] == 30 if len(call_args[0]) > 1 else True, "Should use default 30 days or specified days"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    def test_analytics_handler_show_analytics_no_data(self, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler handles case with no data."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_no_data"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock analytics instance
        mock_analytics = MagicMock()
        mock_analytics_class.return_value = mock_analytics
        
        # Mock wellness score to return error
        mock_analytics.get_wellness_score.return_value = {'error': 'Not enough data'}
        
        # Create a parsed command for showing analytics
        parsed_command = ParsedCommand(
            intent="show_analytics",
            entities={'days': 30},
            confidence=0.9,
            original_message="show analytics"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "not enough" in response.message.lower() or "data" in response.message.lower() or "check-in" in response.message.lower(), "Should indicate insufficient data"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    def test_analytics_handler_mood_trends_success(self, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler shows mood trends successfully."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_mood"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock analytics instance
        mock_analytics = MagicMock()
        mock_analytics_class.return_value = mock_analytics
        
        # Mock mood trends
        mock_analytics.get_mood_trends.return_value = {
            'average_mood': 4.0,
            'min_mood': 3,
            'max_mood': 5,
            'trend': 'Improving',
            'mood_distribution': {'3': 5, '4': 10, '5': 15},
            'insights': ['Mood is improving', 'Consistent patterns']
        }
        
        # Create a parsed command for mood trends
        parsed_command = ParsedCommand(
            intent="mood_trends",
            entities={'days': 30},
            confidence=0.9,
            original_message="mood trends"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "mood" in response.message.lower(), "Should mention mood"
        assert "4.0" in response.message or "average" in response.message.lower(), "Should include average mood"
        
        # Verify actual system changes: Check that get_mood_trends was called with correct parameters
        mock_analytics.get_mood_trends.assert_called_once()
        call_args = mock_analytics.get_mood_trends.call_args
        assert call_args[0][0] == user_id, "Should call get_mood_trends with correct user_id"
        assert call_args[0][1] == 30 if len(call_args[0]) > 1 else True, "Should use specified days parameter"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    def test_analytics_handler_wellness_score_success(self, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler shows wellness score successfully."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_wellness"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock analytics instance
        mock_analytics = MagicMock()
        mock_analytics_class.return_value = mock_analytics
        
        # Mock wellness score
        mock_analytics.get_wellness_score.return_value = {
            'score': 80,
            'level': 'Excellent',
            'components': {
                'mood_score': 85,
                'habit_score': 75,
                'sleep_score': 80
            },
            'recommendations': ['Keep up the good work', 'Maintain consistency']
        }
        
        # Create a parsed command for wellness score
        parsed_command = ParsedCommand(
            intent="wellness_score",
            entities={'days': 30},
            confidence=0.9,
            original_message="wellness score"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "wellness" in response.message.lower() or "score" in response.message.lower(), "Should mention wellness score"
        assert "80" in response.message or "score" in response.message.lower(), "Should include score"
        
        # Verify actual system changes: Check that get_wellness_score was called with correct parameters
        mock_analytics.get_wellness_score.assert_called_once()
        call_args = mock_analytics.get_wellness_score.call_args
        assert call_args[0][0] == user_id, "Should call get_wellness_score with correct user_id"
        assert call_args[0][1] == 30 if len(call_args[0]) > 1 else True, "Should use specified days parameter"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    def test_analytics_handler_checkin_history_success(self, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler shows check-in history successfully."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_history"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create mock analytics instance
        mock_analytics_instance = mock_analytics_class.return_value
        
        # Mock check-in history (formatted as returned by get_checkin_history)
        mock_analytics_instance.get_checkin_history.return_value = [
            {
                'date': '2025-01-01',
                'mood': 4,
                'energy': 3,
                'timestamp': '2025-01-01 10:00:00'
            },
            {
                'date': '2025-01-02',
                'mood': 5,
                'energy': 4,
                'timestamp': '2025-01-02 10:00:00'
            }
        ]
        
        # Create a parsed command for check-in history
        parsed_command = ParsedCommand(
            intent="checkin_history",
            entities={'days': 30},
            confidence=0.9,
            original_message="checkin history"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "history" in response.message.lower() or "check-in" in response.message.lower(), "Should mention check-in history"
        assert "mood" in response.message.lower(), "Should include mood information"
        
        # Verify that CheckinAnalytics was instantiated and get_checkin_history was called
        mock_analytics_class.assert_called_once()
        mock_analytics_instance.get_checkin_history.assert_called_once_with(user_id, 30)
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    def test_analytics_handler_checkin_history_no_checkins(self, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler handles case with no check-ins."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_history_none"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create mock analytics instance
        mock_analytics_instance = mock_analytics_class.return_value
        
        # Mock check-ins to return empty list
        mock_analytics_instance.get_checkin_history.return_value = []
        
        # Create a parsed command for check-in history
        parsed_command = ParsedCommand(
            intent="checkin_history",
            entities={'days': 30},
            confidence=0.9,
            original_message="checkin history"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "haven't" in response.message.lower() or "no" in response.message.lower() or "check-in" in response.message.lower(), "Should indicate no check-ins"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    @patch('core.response_tracking.get_recent_checkins')
    def test_analytics_handler_checkin_analysis_success(self, mock_get_checkins, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler shows check-in analysis successfully."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_analysis"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock check-ins
        mock_get_checkins.return_value = [
            {'timestamp': '2025-01-01 10:00:00', 'mood': 4, 'responses': {'How are you?': 'Good'}},
            {'timestamp': '2025-01-02 10:00:00', 'mood': 5, 'responses': {'How are you?': 'Great'}}
        ]
        
        # Mock analytics instance
        mock_analytics = MagicMock()
        mock_analytics_class.return_value = mock_analytics
        
        # Mock mood trends
        mock_analytics.get_mood_trends.return_value = {
            'average_mood': 4.5,
            'min_mood': 4,
            'max_mood': 5,
            'trend': 'Stable'
        }
        
        # Create a parsed command for check-in analysis
        parsed_command = ParsedCommand(
            intent="checkin_analysis",
            entities={'days': 30},
            confidence=0.9,
            original_message="checkin analysis"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "analysis" in response.message.lower() or "check-in" in response.message.lower(), "Should mention check-in analysis"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    def test_analytics_handler_habit_analysis_success(self, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler shows habit analysis successfully."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_habit"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock analytics instance
        mock_analytics = MagicMock()
        mock_analytics_class.return_value = mock_analytics
        
        # Mock habit analysis
        mock_analytics.get_habit_analysis.return_value = {
            'overall_completion': 75,
            'current_streak': 5,
            'best_streak': 10,
            'habits': {
                'Exercise': {'completion_rate': 80, 'status': 'Good'},
                'Meditation': {'completion_rate': 70, 'status': 'Fair'}
            },
            'recommendations': ['Keep it up', 'Focus on consistency']
        }
        
        # Create a parsed command for habit analysis
        parsed_command = ParsedCommand(
            intent="habit_analysis",
            entities={'days': 30},
            confidence=0.9,
            original_message="habit analysis"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "habit" in response.message.lower() or "completion" in response.message.lower(), "Should mention habit analysis"
        assert "75" in response.message or "completion" in response.message.lower(), "Should include completion rate"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    def test_analytics_handler_sleep_analysis_success(self, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler shows sleep analysis successfully."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_sleep"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock analytics instance
        mock_analytics = MagicMock()
        mock_analytics_class.return_value = mock_analytics
        
        # Mock sleep analysis
        mock_analytics.get_sleep_analysis.return_value = {
            'average_hours': 7.5,
            'average_quality': 4,
            'good_sleep_days': 20,
            'poor_sleep_days': 5,
            'sleep_consistency': 0.8,
            'recommendations': ['Maintain sleep schedule', 'Reduce screen time']
        }
        
        # Create a parsed command for sleep analysis
        parsed_command = ParsedCommand(
            intent="sleep_analysis",
            entities={'days': 30},
            confidence=0.9,
            original_message="sleep analysis"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "sleep" in response.message.lower(), "Should mention sleep"
        assert "7.5" in response.message or "hours" in response.message.lower(), "Should include sleep hours"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    def test_analytics_handler_completion_rate_success(self, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler shows completion rate successfully."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_completion"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock analytics instance
        mock_analytics = MagicMock()
        mock_analytics_class.return_value = mock_analytics
        
        # Mock completion rate
        mock_analytics.get_completion_rate.return_value = {
            'rate': 85,
            'days_completed': 25,
            'days_missed': 5,
            'total_days': 30
        }
        
        # Create a parsed command for completion rate
        parsed_command = ParsedCommand(
            intent="completion_rate",
            entities={'days': 30},
            confidence=0.9,
            original_message="completion rate"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "completion" in response.message.lower() or "rate" in response.message.lower(), "Should mention completion rate"
        assert "85" in response.message or "rate" in response.message.lower(), "Should include completion rate"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    @patch('tasks.task_management.get_user_task_stats')
    @patch('tasks.task_management.load_active_tasks')
    @patch('tasks.task_management.load_completed_tasks')
    def test_analytics_handler_task_analytics_success(self, mock_load_completed, mock_load_active, mock_get_stats, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler shows task analytics successfully."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_task"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock task statistics
        mock_get_stats.return_value = {
            'active_count': 5,
            'completed_count': 10,
            'total_count': 15
        }
        
        mock_load_active.return_value = [
            {'title': 'Task 1', 'priority': 'high'},
            {'title': 'Task 2', 'priority': 'medium'}
        ]
        
        mock_load_completed.return_value = [
            {'title': 'Completed Task 1'},
            {'title': 'Completed Task 2'}
        ]
        
        # Mock analytics instance
        mock_analytics = MagicMock()
        mock_analytics_class.return_value = mock_analytics
        
        # Mock task weekly stats
        mock_analytics.get_task_weekly_stats.return_value = {
            'Task 1': {'completion_rate': 80, 'completed_days': 8, 'total_days': 10},
            'Task 2': {'completion_rate': 90, 'completed_days': 9, 'total_days': 10}
        }
        
        # Create a parsed command for task analytics
        parsed_command = ParsedCommand(
            intent="task_analytics",
            entities={'days': 30},
            confidence=0.9,
            original_message="task analytics"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "task" in response.message.lower() or "analytics" in response.message.lower(), "Should mention task analytics"
        assert "active" in response.message.lower() or "completed" in response.message.lower(), "Should include task statistics"
        
        # Verify actual system changes: Check that all functions were called with correct parameters
        mock_get_stats.assert_called_once_with(user_id)
        mock_load_active.assert_called_once_with(user_id)
        mock_load_completed.assert_called_once_with(user_id)
        mock_analytics.get_task_weekly_stats.assert_called_once()
        call_args = mock_analytics.get_task_weekly_stats.call_args
        assert call_args[0][0] == user_id, "Should call get_task_weekly_stats with correct user_id"
        assert call_args[0][1] == 30 if len(call_args[0]) > 1 else True, "Should use specified days parameter (30)"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    @pytest.mark.file_io
    @patch('core.checkin_analytics.CheckinAnalytics')
    @patch('core.user_data_handlers.get_user_data')
    def test_analytics_handler_quant_summary_success(self, mock_get_user_data, mock_analytics_class, test_data_dir):
        """Test that AnalyticsHandler shows quantitative summary successfully."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_quant"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Mock user data
        mock_get_user_data.return_value = {
            'preferences': {
                'checkin_settings': {
                    'questions': {
                        'mood': {'enabled': True, 'type': 'scale_1_5'},
                        'energy': {'enabled': True, 'type': 'scale_1_5'}
                    }
                }
            }
        }
        
        # Mock analytics instance
        mock_analytics = MagicMock()
        mock_analytics_class.return_value = mock_analytics
        
        # Mock quantitative summaries
        mock_analytics.get_quantitative_summaries.return_value = {
            'mood': {'average': 4.0, 'min': 3, 'max': 5, 'count': 30},
            'energy': {'average': 3.5, 'min': 2, 'max': 5, 'count': 30}
        }
        
        # Create a parsed command for quantitative summary
        parsed_command = ParsedCommand(
            intent="quant_summary",
            entities={'days': 30},
            confidence=0.9,
            original_message="quant summary"
        )
        
        # Handle the command
        response = handler.handle(user_id, parsed_command)
        
        # Verify response
        assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
        assert response.completed, "Response should be completed"
        assert "summary" in response.message.lower() or "quantitative" in response.message.lower(), "Should mention quantitative summary"
        assert "mood" in response.message.lower() or "average" in response.message.lower(), "Should include field summaries"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    def test_analytics_handler_truncate_response(self):
        """Test that AnalyticsHandler truncates long responses."""
        handler = AnalyticsHandler()
        
        # Create a very long response
        long_response = "A" * 2000  # 2000 characters
        
        # Truncate it
        truncated = handler._truncate_response(long_response, max_length=1900)
        
        # Verify truncation
        assert len(truncated) <= 1900, "Should truncate to max length"
        assert "..." in truncated or "truncated" in truncated.lower(), "Should indicate truncation"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    def test_analytics_handler_truncate_response_short(self):
        """Test that AnalyticsHandler doesn't truncate short responses."""
        handler = AnalyticsHandler()
        
        # Create a short response
        short_response = "This is a short response."
        
        # Truncate it
        truncated = handler._truncate_response(short_response, max_length=1900)
        
        # Verify no truncation
        assert truncated == short_response, "Should not truncate short responses"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.analytics
    def test_analytics_handler_unknown_intent(self, test_data_dir):
        """Test that AnalyticsHandler handles unknown intents appropriately."""
        handler = AnalyticsHandler()
        user_id = "test_user_analytics_unknown"
        
        # Create test user
        assert self._create_test_user(user_id, enable_checkins=True, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a parsed command with unknown intent
        parsed_command = ParsedCommand(
            intent="unknown_analytics_intent",
            entities={},
            confidence=0.9,
            original_message="unknown analytics command"
        )
        
        # Since can_handle returns False for this, we need to test the handle method directly
        with patch.object(handler, 'can_handle', return_value=True):
            response = handler.handle(user_id, parsed_command)
            
            # Verify response
            assert isinstance(response, InteractionResponse), "Should return InteractionResponse"
            assert response.completed, "Response should be completed"
            assert "don't understand" in response.message.lower() or "try" in response.message.lower(), "Should indicate command not understood"

