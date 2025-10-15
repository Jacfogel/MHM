"""
Comprehensive tests for AI ContextBuilder coverage expansion.

Tests focus on covering the uncovered lines in the ContextBuilder module.
"""

import pytest
import os
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta

from ai.context_builder import ContextBuilder, ContextData, ContextAnalysis, get_context_builder
from tests.test_utilities import TestUserFactory, TestDataFactory


class TestContextBuilderCoverageExpansion:
    """Test coverage expansion for ContextBuilder module."""

    def test_analyze_context_with_empty_checkins(self, test_data_dir):
        """Test analyze_context with empty recent checkins."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        context_data = ContextData()
        context_data.recent_checkins = []
        
        # Act
        analysis = context_builder.analyze_context(context_data)
        
        # Assert
        assert isinstance(analysis, ContextAnalysis), "Should return ContextAnalysis"
        assert analysis.breakfast_rate == 0, "Breakfast rate should be 0"
        assert analysis.avg_mood is None, "Average mood should be None"
        assert analysis.avg_energy is None, "Average energy should be None"
        assert analysis.teeth_brushing_rate == 0, "Teeth brushing rate should be 0"
        assert analysis.overall_wellness_score == 0.0, "Wellness score should be 0"

    def test_analyze_context_with_checkin_data(self, test_data_dir):
        """Test analyze_context with actual checkin data."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        context_data = ContextData()
        context_data.recent_checkins = [
            {'ate_breakfast': True, 'mood': 4, 'energy': 3, 'brushed_teeth': True},
            {'ate_breakfast': False, 'mood': 3, 'energy': 4, 'brushed_teeth': True},
            {'ate_breakfast': True, 'mood': 5, 'energy': 5, 'brushed_teeth': False}
        ]
        
        # Act
        analysis = context_builder.analyze_context(context_data)
        
        # Assert
        assert abs(analysis.breakfast_rate - 66.67) < 0.1, "Breakfast rate should be calculated correctly"
        assert analysis.avg_mood == 4.0, "Average mood should be calculated correctly"
        assert analysis.avg_energy == 4.0, "Average energy should be calculated correctly"
        assert abs(analysis.teeth_brushing_rate - 66.67) < 0.1, "Teeth brushing rate should be calculated correctly"
        assert analysis.overall_wellness_score > 0, "Wellness score should be calculated"

    def test_analyze_context_with_missing_data(self, test_data_dir):
        """Test analyze_context with missing data fields."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        context_data = ContextData()
        context_data.recent_checkins = [
            {'ate_breakfast': True},  # Missing mood, energy, teeth
            {'mood': 3},  # Missing other fields
            {'energy': 4}  # Missing other fields
        ]
        
        # Act
        analysis = context_builder.analyze_context(context_data)
        
        # Assert
        assert abs(analysis.breakfast_rate - 33.33) < 0.1, "Breakfast rate should handle missing data"
        assert analysis.avg_mood == 3.0, "Average mood should handle missing data"
        assert analysis.avg_energy == 4.0, "Average energy should handle missing data"
        assert analysis.teeth_brushing_rate == 0, "Teeth brushing rate should handle missing data"

    def test_determine_trend_improving(self, test_data_dir):
        """Test _determine_trend with improving values."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]  # Clearly improving
        
        # Act
        trend = context_builder._determine_trend(values)
        
        # Assert
        assert trend == "improving", "Should detect improving trend"

    def test_determine_trend_declining(self, test_data_dir):
        """Test _determine_trend with declining values."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        values = [5.0, 4.0, 3.0, 2.0, 1.0]  # Clearly declining
        
        # Act
        trend = context_builder._determine_trend(values)
        
        # Assert
        assert trend == "declining", "Should detect declining trend"

    def test_determine_trend_stable(self, test_data_dir):
        """Test _determine_trend with stable values."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        values = [3.0, 3.0, 3.0, 3.0, 3.0]  # Stable
        
        # Act
        trend = context_builder._determine_trend(values)
        
        # Assert
        assert trend == "stable", "Should detect stable trend"

    def test_determine_trend_insufficient_data(self, test_data_dir):
        """Test _determine_trend with insufficient data."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        values = [1.0, 2.0]  # Less than 3 values
        
        # Act
        trend = context_builder._determine_trend(values)
        
        # Assert
        assert trend == "stable", "Should return stable for insufficient data"

    def test_calculate_wellness_score_all_factors(self, test_data_dir):
        """Test _calculate_wellness_score with all factors present."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        score = context_builder._calculate_wellness_score(
            breakfast_rate=80.0,
            avg_mood=4.0,
            avg_energy=4.0,
            teeth_brushing_rate=90.0
        )
        
        # Assert
        assert score > 0, "Score should be calculated"
        assert score <= 100, "Score should not exceed 100"

    def test_calculate_wellness_score_no_factors(self, test_data_dir):
        """Test _calculate_wellness_score with no factors present."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        score = context_builder._calculate_wellness_score(
            breakfast_rate=0.0,
            avg_mood=None,
            avg_energy=None,
            teeth_brushing_rate=0.0
        )
        
        # Assert
        assert score == 0.0, "Score should be 0 when no factors present"

    def test_generate_insights_excellent_breakfast(self, test_data_dir):
        """Test _generate_insights with excellent breakfast rate."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        insights = context_builder._generate_insights(
            breakfast_rate=85.0,
            avg_mood=4.0,
            avg_energy=4.0,
            teeth_brushing_rate=90.0,
            mood_trend="stable",
            energy_trend="stable"
        )
        
        # Assert
        assert "excellent breakfast habits" in insights, "Should include excellent breakfast insight"

    def test_generate_insights_poor_breakfast(self, test_data_dir):
        """Test _generate_insights with poor breakfast rate."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        insights = context_builder._generate_insights(
            breakfast_rate=25.0,
            avg_mood=4.0,
            avg_energy=4.0,
            teeth_brushing_rate=90.0,
            mood_trend="stable",
            energy_trend="stable"
        )
        
        # Assert
        assert "room for improvement in breakfast habits" in insights, "Should include improvement insight"

    def test_generate_insights_positive_mood(self, test_data_dir):
        """Test _generate_insights with positive mood."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        insights = context_builder._generate_insights(
            breakfast_rate=80.0,
            avg_mood=4.5,
            avg_energy=4.0,
            teeth_brushing_rate=90.0,
            mood_trend="improving",
            energy_trend="stable"
        )
        
        # Assert
        assert "generally positive mood" in insights, "Should include positive mood insight"
        assert "mood is trending upward" in insights, "Should include mood trend insight"

    def test_generate_insights_low_mood(self, test_data_dir):
        """Test _generate_insights with low mood."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act
        insights = context_builder._generate_insights(
            breakfast_rate=80.0,
            avg_mood=1.5,
            avg_energy=4.0,
            teeth_brushing_rate=90.0,
            mood_trend="declining",
            energy_trend="stable"
        )
        
        # Assert
        assert "challenging mood patterns" in insights, "Should include challenging mood insight"
        assert "mood is trending downward" in insights, "Should include mood decline insight"

    def test_generate_insights_energy_patterns(self, test_data_dir):
        """Test _generate_insights with energy patterns."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act - High energy
        insights_high = context_builder._generate_insights(
            breakfast_rate=80.0,
            avg_mood=4.0,
            avg_energy=4.5,
            teeth_brushing_rate=90.0,
            mood_trend="stable",
            energy_trend="improving"
        )
        
        # Act - Low energy
        insights_low = context_builder._generate_insights(
            breakfast_rate=80.0,
            avg_mood=4.0,
            avg_energy=1.5,
            teeth_brushing_rate=90.0,
            mood_trend="stable",
            energy_trend="declining"
        )
        
        # Assert
        assert "good energy levels" in insights_high, "Should include good energy insight"
        assert "energy is trending upward" in insights_high, "Should include energy improvement insight"
        assert "low energy patterns" in insights_low, "Should include low energy insight"
        assert "energy is trending downward" in insights_low, "Should include energy decline insight"

    def test_generate_insights_dental_hygiene(self, test_data_dir):
        """Test _generate_insights with dental hygiene patterns."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        
        # Act - Excellent dental hygiene
        insights_excellent = context_builder._generate_insights(
            breakfast_rate=80.0,
            avg_mood=4.0,
            avg_energy=4.0,
            teeth_brushing_rate=95.0,
            mood_trend="stable",
            energy_trend="stable"
        )
        
        # Act - Poor dental hygiene
        insights_poor = context_builder._generate_insights(
            breakfast_rate=80.0,
            avg_mood=4.0,
            avg_energy=4.0,
            teeth_brushing_rate=30.0,
            mood_trend="stable",
            energy_trend="stable"
        )
        
        # Assert
        assert "excellent dental hygiene" in insights_excellent, "Should include excellent dental insight"
        assert "room for improvement in dental hygiene" in insights_poor, "Should include dental improvement insight"

    def test_create_context_prompt_with_profile(self, test_data_dir):
        """Test create_context_prompt with user profile data."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        context_data = ContextData()
        context_data.user_profile = {
            'preferred_name': 'Test User',
            'active_categories': ['health', 'productivity']
        }
        context_data.recent_checkins = [
            {'ate_breakfast': True, 'mood': 4, 'energy': 3, 'brushed_teeth': True}
        ]
        
        # Act
        prompt = context_builder.create_context_prompt(context_data)
        
        # Assert
        assert "Test User" in prompt, "Should include user name"
        assert "health, productivity" in prompt, "Should include active categories"
        assert "Recent check-in data" in prompt, "Should include check-in data"

    def test_create_context_prompt_with_user_context(self, test_data_dir):
        """Test create_context_prompt with user context data."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        context_data = ContextData()
        context_data.user_context = {
            'custom_fields': {
                'health_conditions': ['ADHD', 'Depression']
            },
            'notes_for_ai': ['I prefer gentle reminders'],
            'activities_for_encouragement': ['exercise', 'meditation'],
            'goals': ['Improve sleep', 'Exercise regularly']
        }
        
        # Act
        prompt = context_builder.create_context_prompt(context_data)
        
        # Assert
        assert "ADHD, Depression" in prompt, "Should include health conditions"
        assert "I prefer gentle reminders" in prompt, "Should include notes for AI"
        assert "exercise, meditation" in prompt, "Should include encouraging activities"
        assert "Improve sleep, Exercise regularly" in prompt, "Should include goals"

    def test_create_context_prompt_with_analysis(self, test_data_dir):
        """Test create_context_prompt with pre-computed analysis."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        context_data = ContextData()
        context_data.recent_checkins = [
            {'ate_breakfast': True, 'mood': 4, 'energy': 3, 'brushed_teeth': True}
        ]
        analysis = ContextAnalysis(
            breakfast_rate=100.0,
            avg_mood=4.0,
            avg_energy=3.0,
            teeth_brushing_rate=100.0,
            mood_trend="stable",
            energy_trend="stable",
            overall_wellness_score=85.0,
            insights=["excellent breakfast habits", "generally positive mood"]
        )
        
        # Act
        prompt = context_builder.create_context_prompt(context_data, analysis)
        
        # Assert
        assert "100%" in prompt, "Should include breakfast rate"
        assert "4.0/5" in prompt, "Should include mood score"
        assert "3.0/5" in prompt, "Should include energy score"
        assert "85.0/100" in prompt, "Should include wellness score"
        assert "excellent breakfast habits" in prompt, "Should include insights"

    def test_create_task_context(self, test_data_dir):
        """Test create_task_context method."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        task_description = "Complete project report"
        
        # Act
        context = context_builder.create_task_context(user_id, task_description)
        
        # Assert
        assert "Task: Complete project report" in context, "Should include task description"
        assert "Check-in Type" not in context, "Should not include check-in specific content"

    def test_create_checkin_context(self, test_data_dir):
        """Test create_checkin_context method."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        checkin_type = "weekly"
        
        # Act
        context = context_builder.create_checkin_context(user_id, checkin_type)
        
        # Assert
        assert "Check-in Type: weekly" in context, "Should include check-in type"
        # Note: "Areas to focus on" may not appear if there are no insights

    def test_get_context_builder_singleton(self, test_data_dir):
        """Test get_context_builder singleton behavior."""
        # Act
        builder1 = get_context_builder()
        builder2 = get_context_builder()
        
        # Assert
        assert builder1 is builder2, "Should return same instance"
        assert isinstance(builder1, ContextBuilder), "Should return ContextBuilder instance"

    def test_analyze_context_error_handling(self, test_data_dir):
        """Test analyze_context error handling."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        context_data = ContextData()
        context_data.recent_checkins = [{'invalid': 'data'}]  # Invalid data
        
        # Act
        analysis = context_builder.analyze_context(context_data)
        
        # Assert
        assert isinstance(analysis, ContextAnalysis), "Should return ContextAnalysis even on error"

    def test_create_context_prompt_error_handling(self, test_data_dir):
        """Test create_context_prompt error handling."""
        # Arrange
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        context_builder = ContextBuilder()
        context_data = None  # Invalid data
        
        # Act
        prompt = context_builder.create_context_prompt(context_data)
        
        # Assert
        assert prompt == "", "Should return empty string on error"

    def test_create_task_context_error_handling(self, test_data_dir):
        """Test create_task_context error handling."""
        # Arrange
        user_id = "invalid-user"
        context_builder = ContextBuilder()
        task_description = "Test task"
        
        # Act
        context = context_builder.create_task_context(user_id, task_description)
        
        # Assert
        assert "Task: Test task" in context, "Should return task description even on error"

    def test_create_checkin_context_error_handling(self, test_data_dir):
        """Test create_checkin_context error handling."""
        # Arrange
        user_id = "invalid-user"
        context_builder = ContextBuilder()
        checkin_type = "daily"
        
        # Act
        context = context_builder.create_checkin_context(user_id, checkin_type)
        
        # Assert
        assert "Check-in Type: daily" in context, "Should return check-in type even on error"
