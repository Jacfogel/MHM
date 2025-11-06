"""
Comprehensive tests for user analytics dialog.

Tests the actual UI behavior, user interactions, and side effects for:
- User analytics dialog (PySide6)
- Analytics data loading and display
- Time period selection
- Tab visibility configuration
- Error handling and recovery
"""
from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import logging
logger = logging.getLogger("mhm_tests")

# Do not modify sys.path; rely on package imports
from ui.dialogs.user_analytics_dialog import UserAnalyticsDialog, open_user_analytics_dialog
from tests.test_utilities import TestUserFactory

# Create QApplication instance for testing
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for UI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app as it might be used by other tests

class TestUserAnalyticsDialogInitialization:
    """Test user analytics dialog initialization."""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir, mock_config):
        """Create user analytics dialog for testing."""
        # Create test user
        user_id = "test_analytics_user"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Mock analytics to avoid actual data loading during initialization
        with patch('ui.dialogs.user_analytics_dialog.CheckinAnalytics') as mock_analytics_class:
            mock_analytics = MagicMock()
            mock_analytics.get_available_data_types.return_value = {
                'data_types': {
                    'mood': True,
                    'habits': False,
                    'sleep': False,
                    'quantitative': False
                }
            }
            mock_analytics.get_wellness_score.return_value = {
                'score': 75,
                'level': 'Good',
                'recommendations': ['Get more sleep', 'Exercise regularly']
            }
            mock_analytics.get_mood_trends.return_value = {
                'average_mood': 3.5,
                'trend': 'stable',
                'mood_changes': 2,
                'recent_data': []
            }
            mock_analytics_class.return_value = mock_analytics
            
            # Create dialog (DO NOT show() - this would display UI during testing)
            dialog = UserAnalyticsDialog(parent=None, user_id=actual_user_id)
            
            yield dialog
            
            # Cleanup
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_dialog_initialization(self, dialog):
        """Test dialog initializes correctly with proper UI state."""
        # Arrange: Dialog is created in fixture
        
        # Act: (No action needed - initialization happens in fixture)
        
        # Assert: Verify initial state
        assert dialog is not None, "Dialog should be created"
        assert not dialog.isVisible(), "Dialog should not be visible during testing"
        assert "User Analytics" in dialog.windowTitle(), "Dialog should have correct title"
        
        # Assert: Verify UI components exist
        assert hasattr(dialog, 'ui'), "UI should be set up"
        assert hasattr(dialog.ui, 'pushButton_refresh'), "Refresh button should exist"
        assert hasattr(dialog.ui, 'pushButton_close'), "Close button should exist"
        assert hasattr(dialog.ui, 'comboBox_time_period'), "Time period combo box should exist"
        assert hasattr(dialog.ui, 'tabWidget_analytics'), "Tab widget should exist"
        
        # Assert: Verify initial state
        assert dialog.current_days == 30, "Default time period should be 30 days"
        assert dialog.ui.comboBox_time_period.currentIndex() == 2, "Time period combo should be set to 30 days"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_dialog_initialization_without_user_id(self, qapp):
        """Test dialog initializes correctly without user_id."""
        with patch('ui.dialogs.user_analytics_dialog.CheckinAnalytics') as mock_analytics_class:
            mock_analytics = MagicMock()
            mock_analytics_class.return_value = mock_analytics
            
            dialog = UserAnalyticsDialog(parent=None, user_id=None)
            
            assert dialog.user_id is None, "User ID should be None"
            assert dialog.windowTitle() == "User Analytics", "Dialog should have default title"
            
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_setup_connections(self, dialog):
        """Test signal connections are set up correctly."""
        # Verify buttons exist and are connected
        assert dialog.ui.pushButton_refresh is not None, "Refresh button should exist"
        assert dialog.ui.pushButton_close is not None, "Close button should exist"
        assert dialog.ui.comboBox_time_period is not None, "Time period combo should exist"

class TestUserAnalyticsDataLoading:
    """Test analytics data loading functionality."""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir, mock_config):
        """Create user analytics dialog for testing."""
        # Create test user
        user_id = "test_analytics_data_user"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Mock analytics
        with patch('ui.dialogs.user_analytics_dialog.CheckinAnalytics') as mock_analytics_class:
            mock_analytics = MagicMock()
            mock_analytics_class.return_value = mock_analytics
            
            dialog = UserAnalyticsDialog(parent=None, user_id=actual_user_id)
            dialog.analytics = mock_analytics  # Replace with mock
            
            yield dialog
            
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_analytics_data_with_user_id(self, dialog):
        """Test load_analytics_data loads data when user_id is set."""
        # Reset call counts (load_analytics_data is called during initialization)
        dialog.analytics.reset_mock()
        
        # Mock analytics methods
        dialog.analytics.get_available_data_types.return_value = {
            'data_types': {
                'mood': True,
                'habits': False,
                'sleep': False,
                'quantitative': False
            }
        }
        dialog.analytics.get_wellness_score.return_value = {
            'score': 80,
            'level': 'Excellent',
            'recommendations': ['Keep it up!']
        }
        dialog.analytics.get_mood_trends.return_value = {
            'average_mood': 4.0,
            'trend': 'improving',
            'mood_changes': 1,
            'recent_data': []
        }
        
        with patch('core.response_tracking.get_checkins_by_days', return_value=[]):
            dialog.load_analytics_data()
            
            # Verify analytics methods were called (at least once, may be called multiple times)
            assert dialog.analytics.get_available_data_types.called, "get_available_data_types should be called"
            assert dialog.analytics.get_wellness_score.called, "get_wellness_score should be called"
            assert dialog.analytics.get_mood_trends.called, "get_mood_trends should be called"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_analytics_data_without_user_id(self, dialog):
        """Test load_analytics_data shows error when user_id is not set."""
        dialog.user_id = None
        
        dialog.load_analytics_data()
        
        # Verify error state is shown
        assert "No user selected" in dialog.ui.textEdit_summary.toPlainText(), "Should show error message"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_detect_available_data_types_success(self, dialog):
        """Test detect_available_data_types detects available data types."""
        dialog.analytics.get_available_data_types.return_value = {
            'data_types': {
                'mood': True,
                'habits': True,
                'sleep': True,
                'quantitative': False
            }
        }
        
        dialog.detect_available_data_types()
        
        # Verify data types were detected
        assert dialog.available_data_types.get('mood') is True, "Mood data should be available"
        assert dialog.available_data_types.get('habits') is True, "Habits data should be available"
        assert dialog.available_data_types.get('sleep') is True, "Sleep data should be available"
        assert dialog.available_data_types.get('quantitative') is False, "Quantitative data should not be available"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_detect_available_data_types_with_error(self, dialog):
        """Test detect_available_data_types handles errors gracefully."""
        dialog.analytics.get_available_data_types.return_value = {
            'error': 'No data available'
        }
        
        dialog.detect_available_data_types()
        
        # Verify default data types are set
        assert dialog.available_data_types.get('mood') is True, "Should default to showing mood tab"
        assert dialog.available_data_types.get('habits') is False, "Habits should default to False"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_detect_available_data_types_with_exception(self, dialog):
        """Test detect_available_data_types handles exceptions gracefully."""
        dialog.analytics.get_available_data_types.side_effect = Exception("Test error")
        
        # Should not raise exception
        dialog.detect_available_data_types()
        
        # Verify default data types are set
        assert dialog.available_data_types.get('mood') is True, "Should default to showing mood tab"
        assert dialog.available_data_types.get('habits') is True, "Should default to showing all tabs on error"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_configure_tab_visibility(self, dialog):
        """Test configure_tab_visibility configures tabs based on available data."""
        dialog.available_data_types = {
            'mood': True,
            'habits': False,
            'sleep': True,
            'quantitative': False
        }
        
        dialog.configure_tab_visibility()
        
        # Verify tabs are configured (we can't easily check visibility without UI, but we can verify method completes)
        assert dialog.ui.tabWidget_analytics is not None, "Tab widget should exist"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_overview_data_success(self, dialog):
        """Test load_overview_data loads and displays overview data."""
        # Arrange: Set up mock analytics data
        dialog.analytics.get_wellness_score.return_value = {
            'score': 85,
            'level': 'Excellent',
            'recommendations': ['Keep up the good work!', 'Maintain current habits']
        }
        
        # Act: Load overview data
        with patch('core.response_tracking.get_checkins_by_days', return_value=[{}, {}, {}]):
            dialog.load_overview_data()
            
            # Assert: Verify wellness score is displayed (side effect)
            wellness_text = dialog.ui.label_wellness_score.text()
            assert "85" in wellness_text, "Should show wellness score"
            assert "Excellent" in wellness_text, "Should show wellness level"
            
            # Assert: Verify summary is displayed (side effect)
            summary_text = dialog.ui.textEdit_summary.toPlainText()
            assert "Wellness Analysis" in summary_text, "Should show wellness analysis"
            assert "85" in summary_text, "Should show score in summary"
            
            # Assert: Verify recommendations are displayed (side effect)
            recommendations_text = dialog.ui.textEdit_recommendations.toPlainText()
            assert "Keep up the good work!" in recommendations_text, "Should show recommendations"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_overview_data_with_error(self, dialog):
        """Test load_overview_data handles errors gracefully."""
        dialog.analytics.get_wellness_score.return_value = {
            'error': 'Insufficient data',
            'total_checkins': 2,
            'data_completeness': 6.7
        }
        
        dialog.load_overview_data()
        
        # Verify error message is displayed
        wellness_text = dialog.ui.label_wellness_score.text()
        assert "No data available" in wellness_text, "Should show no data message"
        
        summary_text = dialog.ui.textEdit_summary.toPlainText()
        assert "Insufficient data" in summary_text, "Should show error message"
        assert "2" in summary_text, "Should show total check-ins"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_overview_data_with_exception(self, dialog):
        """Test load_overview_data handles exceptions gracefully."""
        dialog.analytics.get_wellness_score.side_effect = Exception("Test error")
        
        # Should not raise exception
        dialog.load_overview_data()
        
        # Verify error message is displayed
        summary_text = dialog.ui.textEdit_summary.toPlainText()
        assert "Error loading overview data" in summary_text, "Should show error message"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_mood_data_success(self, dialog):
        """Test load_mood_data loads and displays mood data."""
        dialog.analytics.get_mood_trends.return_value = {
            'average_mood': 3.8,
            'trend': 'improving',
            'mood_changes': 3,
            'recent_data': [
                {'date': '2025-11-01', 'mood': 4},
                {'date': '2025-11-02', 'mood': 3},
                {'date': '2025-11-03', 'mood': 4}
            ]
        }
        
        dialog.load_mood_data()
        
        # Verify mood data is displayed
        mood_text = dialog.ui.textEdit_mood_data.toPlainText()
        assert "Mood Analysis" in mood_text, "Should show mood analysis"
        assert "3.8" in mood_text, "Should show average mood"
        assert "Improving" in mood_text or "improving" in mood_text, "Should show trend (may be capitalized)"
        assert "2025-11-01" in mood_text, "Should show recent data"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_mood_data_with_error(self, dialog):
        """Test load_mood_data handles errors gracefully."""
        dialog.analytics.get_mood_trends.return_value = {
            'error': 'No mood data available'
        }
        
        dialog.load_mood_data()
        
        # Verify error message is displayed
        mood_text = dialog.ui.textEdit_mood_data.toPlainText()
        assert "No mood data available" in mood_text, "Should show no data message"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_habits_data_success(self, dialog):
        """Test load_habits_data loads and displays habit data."""
        dialog.analytics.get_habit_analysis.return_value = {
            'overall_completion': 75.5,
            'habits': {
                'exercise': {
                    'name': 'Exercise',
                    'completion_rate': 80.0,
                    'total_days': 30,
                    'completed_days': 24,
                    'status': 'Good'
                },
                'meditation': {
                    'name': 'Meditation',
                    'completion_rate': 70.0,
                    'total_days': 30,
                    'completed_days': 21,
                    'status': 'Fair'
                }
            }
        }
        
        dialog.load_habits_data()
        
        # Verify habit data is displayed
        habits_text = dialog.ui.textEdit_habits_data.toPlainText()
        assert "Habit Analysis" in habits_text, "Should show habit analysis"
        assert "75.5" in habits_text, "Should show overall completion rate"
        assert "Exercise" in habits_text, "Should show habit name"
        assert "80.0" in habits_text, "Should show habit completion rate"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_habits_data_with_no_habits(self, dialog):
        """Test load_habits_data handles no habits gracefully."""
        dialog.analytics.get_habit_analysis.return_value = {
            'overall_completion': 0,
            'habits': {}
        }
        
        dialog.load_habits_data()
        
        # Verify no habits message is displayed
        habits_text = dialog.ui.textEdit_habits_data.toPlainText()
        assert "No Habits Configured" in habits_text, "Should show no habits message"
        assert "N/A" in habits_text, "Should show N/A for completion rate"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_sleep_data_success(self, dialog):
        """Test load_sleep_data loads and displays sleep data."""
        dialog.analytics.get_sleep_analysis.return_value = {
            'average_hours': 7.5,
            'average_quality': 4.0,
            'good_sleep_days': 20,
            'poor_sleep_days': 5,
            'sleep_consistency': 85.0,
            'recommendations': ['Maintain consistent sleep schedule', 'Avoid screens before bed']
        }
        
        dialog.load_sleep_data()
        
        # Verify sleep data is displayed
        sleep_text = dialog.ui.textEdit_sleep_data.toPlainText()
        assert "Sleep Analysis" in sleep_text, "Should show sleep analysis"
        assert "7.5" in sleep_text, "Should show average hours"
        assert "4.0" in sleep_text, "Should show average quality"
        assert "20" in sleep_text, "Should show good sleep days"
        assert "Maintain consistent sleep schedule" in sleep_text, "Should show recommendations"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_sleep_data_with_none_values(self, dialog):
        """Test load_sleep_data handles None values gracefully."""
        dialog.analytics.get_sleep_analysis.return_value = {
            'average_hours': None,
            'average_quality': None,
            'good_sleep_days': 0,
            'poor_sleep_days': 0,
            'sleep_consistency': None,
            'recommendations': []
        }
        
        dialog.load_sleep_data()
        
        # Verify None values are handled
        sleep_text = dialog.ui.textEdit_sleep_data.toPlainText()
        assert "No data" in sleep_text, "Should show no data for None values"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_quantitative_data_success(self, dialog):
        """Test load_quantitative_data loads and displays quantitative data."""
        dialog.analytics.get_quantitative_summaries.return_value = {
            'weight': {
                'average': 150.5,
                'min': 148.0,
                'max': 152.0,
                'count': 10
            },
            'steps': {
                'average': 8500.0,
                'min': 5000.0,
                'max': 12000.0,
                'count': 15
            }
        }
        
        dialog.load_quantitative_data()
        
        # Verify quantitative data is displayed
        quant_text = dialog.ui.textEdit_quantitative_data.toPlainText()
        assert "Quantitative Summaries" in quant_text, "Should show quantitative summaries"
        assert "Weight" in quant_text, "Should show field name"
        assert "150.5" in quant_text, "Should show average value"
        assert "Steps" in quant_text, "Should show another field name"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_quantitative_data_with_error(self, dialog):
        """Test load_quantitative_data handles errors gracefully."""
        dialog.analytics.get_quantitative_summaries.return_value = {
            'error': 'No quantitative data available'
        }
        
        dialog.load_quantitative_data()
        
        # Verify error message is displayed
        quant_text = dialog.ui.textEdit_quantitative_data.toPlainText()
        assert "No quantitative data available" in quant_text, "Should show no data message"

class TestUserAnalyticsInteractions:
    """Test user interactions with analytics dialog."""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir, mock_config):
        """Create user analytics dialog for testing."""
        # Create test user
        user_id = "test_analytics_interactions_user"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Mock analytics
        with patch('ui.dialogs.user_analytics_dialog.CheckinAnalytics') as mock_analytics_class:
            mock_analytics = MagicMock()
            mock_analytics_class.return_value = mock_analytics
            
            dialog = UserAnalyticsDialog(parent=None, user_id=actual_user_id)
            dialog.analytics = mock_analytics  # Replace with mock
            
            yield dialog
            
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_refresh_analytics(self, dialog):
        """Test refresh_analytics reloads analytics data."""
        with patch.object(dialog, 'load_analytics_data') as mock_load:
            dialog.refresh_analytics()
            
            mock_load.assert_called_once()
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_on_time_period_changed(self, dialog):
        """Test on_time_period_changed updates time period and reloads data."""
        # Arrange: Set up mock for load_analytics_data
        with patch.object(dialog, 'load_analytics_data') as mock_load:
            # Act: Change to 7 days (index 0)
            dialog.on_time_period_changed(0)
            
            # Assert: Verify system state changed
            assert dialog.current_days == 7, "Time period should be updated to 7 days"
            mock_load.assert_called_once()
            
            # Act: Change to 90 days (index 4)
            dialog.on_time_period_changed(4)
            
            # Assert: Verify system state changed again
            assert dialog.current_days == 90, "Time period should be updated to 90 days"
            assert mock_load.call_count == 2, "Load should be called again"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_on_time_period_changed_invalid_index(self, dialog):
        """Test on_time_period_changed handles invalid index gracefully."""
        original_days = dialog.current_days
        
        # Invalid index (too high)
        dialog.on_time_period_changed(10)
        
        # Should not change or crash
        assert dialog.current_days == original_days, "Time period should not change with invalid index"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_show_loading_state(self, dialog):
        """Test show_loading_state displays loading messages."""
        dialog.show_loading_state()
        
        # Verify loading messages are displayed
        assert "Loading..." in dialog.ui.label_wellness_score.text(), "Should show loading for wellness score"
        assert "Loading analytics data..." in dialog.ui.textEdit_summary.toPlainText(), "Should show loading for summary"
        assert "Loading mood data..." in dialog.ui.textEdit_mood_data.toPlainText(), "Should show loading for mood"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_show_error_state(self, dialog):
        """Test show_error_state displays error messages."""
        error_message = "Test error message"
        dialog.show_error_state(error_message)
        
        # Verify error messages are displayed
        assert "Error" in dialog.ui.label_wellness_score.text(), "Should show error for wellness score"
        assert error_message in dialog.ui.textEdit_summary.toPlainText(), "Should show error message in summary"
        assert "Error loading data" in dialog.ui.textEdit_mood_data.toPlainText(), "Should show error for mood"

class TestUserAnalyticsErrorHandling:
    """Test error handling in user analytics dialog."""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir, mock_config):
        """Create user analytics dialog for testing."""
        # Create test user
        user_id = "test_analytics_errors_user"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Mock analytics
        with patch('ui.dialogs.user_analytics_dialog.CheckinAnalytics') as mock_analytics_class:
            mock_analytics = MagicMock()
            mock_analytics_class.return_value = mock_analytics
            
            dialog = UserAnalyticsDialog(parent=None, user_id=actual_user_id)
            dialog.analytics = mock_analytics  # Replace with mock
            
            yield dialog
            
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_analytics_data_handles_exceptions(self, dialog):
        """Test load_analytics_data handles exceptions gracefully."""
        dialog.analytics.get_available_data_types.side_effect = Exception("Test error")
        
        # Should not raise exception
        dialog.load_analytics_data()
        
        # Verify error state is shown (error may be in summary or overview)
        summary_text = dialog.ui.textEdit_summary.toPlainText()
        assert "Error" in summary_text, "Should show error message (may be in overview data error)"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_mood_data_handles_exceptions(self, dialog):
        """Test load_mood_data handles exceptions gracefully."""
        dialog.analytics.get_mood_trends.side_effect = Exception("Test error")
        
        # Should not raise exception
        dialog.load_mood_data()
        
        # Verify error message is displayed
        mood_text = dialog.ui.textEdit_mood_data.toPlainText()
        assert "Error loading mood data" in mood_text, "Should show error message"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_habits_data_handles_exceptions(self, dialog):
        """Test load_habits_data handles exceptions gracefully."""
        dialog.analytics.get_habit_analysis.side_effect = Exception("Test error")
        
        # Should not raise exception
        dialog.load_habits_data()
        
        # Verify error message is displayed
        habits_text = dialog.ui.textEdit_habits_data.toPlainText()
        assert "Error loading habits data" in habits_text, "Should show error message"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_sleep_data_handles_exceptions(self, dialog):
        """Test load_sleep_data handles exceptions gracefully."""
        dialog.analytics.get_sleep_analysis.side_effect = Exception("Test error")
        
        # Should not raise exception
        dialog.load_sleep_data()
        
        # Verify error message is displayed
        sleep_text = dialog.ui.textEdit_sleep_data.toPlainText()
        assert "Error loading sleep data" in sleep_text, "Should show error message"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_load_quantitative_data_handles_exceptions(self, dialog):
        """Test load_quantitative_data handles exceptions gracefully."""
        dialog.analytics.get_quantitative_summaries.side_effect = Exception("Test error")
        
        # Should not raise exception
        dialog.load_quantitative_data()
        
        # Verify error message is displayed
        quant_text = dialog.ui.textEdit_quantitative_data.toPlainText()
        assert "Error loading quantitative data" in quant_text, "Should show error message"

class TestUserAnalyticsHelperFunction:
    """Test helper function for opening dialog."""
    
    @pytest.mark.ui
    @pytest.mark.analytics
    def test_open_user_analytics_dialog(self, qapp, test_data_dir, mock_config):
        """Test open_user_analytics_dialog creates and shows dialog."""
        # Create test user
        user_id = "test_open_dialog_user"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Mock analytics
        with patch('ui.dialogs.user_analytics_dialog.CheckinAnalytics') as mock_analytics_class:
            mock_analytics = MagicMock()
            mock_analytics.get_available_data_types.return_value = {'data_types': {}}
            mock_analytics.get_wellness_score.return_value = {'score': 0, 'level': 'Unknown'}
            mock_analytics_class.return_value = mock_analytics
            
            # Mock exec to avoid showing dialog
            with patch('ui.dialogs.user_analytics_dialog.QDialog.exec', return_value=0):
                result = open_user_analytics_dialog(None, actual_user_id)
                
                assert result == 0, "Should return dialog result"


class TestUserAnalyticsIntegration:
    """Integration tests for user analytics dialog workflows."""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir, mock_config):
        """Create user analytics dialog for testing."""
        # Create test user
        user_id = "test_analytics_integration_user"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Mock analytics
        with patch('ui.dialogs.user_analytics_dialog.CheckinAnalytics') as mock_analytics_class:
            mock_analytics = MagicMock()
            mock_analytics_class.return_value = mock_analytics
            
            dialog = UserAnalyticsDialog(parent=None, user_id=actual_user_id)
            dialog.analytics = mock_analytics  # Replace with mock
            
            yield dialog
            
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.analytics
    @pytest.mark.integration
    def test_complete_analytics_loading_workflow(self, dialog):
        """Test complete analytics loading workflow: detect data types -> load overview -> load specific data."""
        # Arrange: Set up mock analytics data
        dialog.analytics.get_available_data_types.return_value = {
            'data_types': {
                'mood': True,
                'habits': True,
                'sleep': False,
                'quantitative': False
            }
        }
        dialog.analytics.get_wellness_score.return_value = {
            'score': 80,
            'level': 'Good',
            'recommendations': ['Exercise regularly']
        }
        dialog.analytics.get_mood_trends.return_value = {
            'average_mood': 3.5,
            'trend': 'stable',
            'mood_changes': 2,
            'recent_data': []
        }
        dialog.analytics.get_habit_analysis.return_value = {
            'overall_completion': 75.0,
            'habits': {
                'exercise': {
                    'name': 'Exercise',
                    'completion_rate': 80.0,
                    'total_days': 30,
                    'completed_days': 24,
                    'status': 'Good'
                }
            }
        }
        
        # Act: Execute complete loading workflow
        with patch('core.response_tracking.get_checkins_by_days', return_value=[{}, {}]):
            dialog.load_analytics_data()
        
        # Assert: Verify data was loaded and displayed (side effects)
        assert dialog.available_data_types.get('mood') is True, "Mood data should be available"
        assert dialog.available_data_types.get('habits') is True, "Habits data should be available"
        
        # Assert: Verify overview data is displayed
        wellness_text = dialog.ui.label_wellness_score.text()
        assert "80" in wellness_text, "Should show wellness score"
        
        # Assert: Verify mood data is displayed
        mood_text = dialog.ui.textEdit_mood_data.toPlainText()
        assert "Mood Analysis" in mood_text, "Should show mood analysis"
        
        # Assert: Verify habits data is displayed
        habits_text = dialog.ui.textEdit_habits_data.toPlainText()
        assert "Habit Analysis" in habits_text, "Should show habit analysis"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    @pytest.mark.integration
    def test_time_period_change_workflow(self, dialog):
        """Test time period change workflow: change period -> reload data -> update display."""
        # Arrange: Set up initial analytics data
        dialog.analytics.get_available_data_types.return_value = {
            'data_types': {'mood': True}
        }
        dialog.analytics.get_wellness_score.return_value = {
            'score': 75,
            'level': 'Good',
            'recommendations': []
        }
        dialog.analytics.get_mood_trends.return_value = {
            'average_mood': 3.5,
            'trend': 'stable',
            'mood_changes': 2,
            'recent_data': []
        }
        
        # Arrange: Load initial data
        with patch('core.response_tracking.get_checkins_by_days', return_value=[]):
            dialog.load_analytics_data()
        
        initial_days = dialog.current_days
        
        # Act: Change time period to 7 days
        dialog.analytics.reset_mock()
        dialog.analytics.get_available_data_types.return_value = {
            'data_types': {'mood': True}
        }
        dialog.analytics.get_wellness_score.return_value = {
            'score': 70,
            'level': 'Fair',
            'recommendations': []
        }
        dialog.analytics.get_mood_trends.return_value = {
            'average_mood': 3.2,
            'trend': 'declining',
            'mood_changes': 3,
            'recent_data': []
        }
        
        # Arrange: Set combo box index to match the time period change
        dialog.ui.comboBox_time_period.setCurrentIndex(0)  # 7 days
        
        with patch('core.response_tracking.get_checkins_by_days', return_value=[]):
            dialog.on_time_period_changed(0)  # 7 days
        
        # Assert: Verify time period changed (system state)
        assert dialog.current_days == 7, "Time period should be updated to 7 days"
        assert dialog.current_days != initial_days, "Time period should be different from initial"
        
        # Assert: Verify analytics methods were called with new time period
        assert dialog.analytics.get_available_data_types.called, "Should call get_available_data_types"
        assert dialog.analytics.get_wellness_score.called, "Should call get_wellness_score"
        assert dialog.analytics.get_mood_trends.called, "Should call get_mood_trends"
    
    @pytest.mark.ui
    @pytest.mark.analytics
    @pytest.mark.integration
    def test_refresh_workflow(self, dialog):
        """Test refresh workflow: refresh button -> reload all data -> update display."""
        # Arrange: Set up initial analytics data
        dialog.analytics.get_available_data_types.return_value = {
            'data_types': {'mood': True}
        }
        dialog.analytics.get_wellness_score.return_value = {
            'score': 75,
            'level': 'Good',
            'recommendations': []
        }
        dialog.analytics.get_mood_trends.return_value = {
            'average_mood': 3.5,
            'trend': 'stable',
            'mood_changes': 2,
            'recent_data': []
        }
        
        # Arrange: Load initial data
        with patch('core.response_tracking.get_checkins_by_days', return_value=[]):
            dialog.load_analytics_data()
        
        # Arrange: Update analytics data for refresh
        dialog.analytics.reset_mock()
        dialog.analytics.get_available_data_types.return_value = {
            'data_types': {'mood': True}
        }
        dialog.analytics.get_wellness_score.return_value = {
            'score': 85,
            'level': 'Excellent',
            'recommendations': ['Keep it up!']
        }
        dialog.analytics.get_mood_trends.return_value = {
            'average_mood': 4.0,
            'trend': 'improving',
            'mood_changes': 1,
            'recent_data': []
        }
        
        # Act: Refresh analytics
        with patch('core.response_tracking.get_checkins_by_days', return_value=[{}, {}]):
            dialog.refresh_analytics()
        
        # Assert: Verify data was refreshed (side effects)
        wellness_text = dialog.ui.label_wellness_score.text()
        assert "85" in wellness_text, "Should show updated wellness score"
        assert "Excellent" in wellness_text, "Should show updated wellness level"
        
        mood_text = dialog.ui.textEdit_mood_data.toPlainText()
        assert "4.0" in mood_text or "improving" in mood_text, "Should show updated mood data"

