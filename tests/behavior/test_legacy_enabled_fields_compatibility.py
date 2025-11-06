"""
Test legacy enabled_fields format compatibility for quantitative analytics.

This test ensures that users with the old enabled_fields format continue to work
while we transition to the new questions format.
"""

import pytest
import json
import os
from unittest.mock import patch
from core.checkin_analytics import CheckinAnalytics
from core.config import get_user_file_path
from core.user_management import get_user_id_by_identifier
# Removed unused imports: get_user_data, save_user_data
from tests.test_utilities import TestUserFactory


class TestLegacyEnabledFieldsCompatibility:
    """Test that legacy enabled_fields format still works."""

    @pytest.mark.behavior
    @pytest.mark.analytics
    def test_legacy_enabled_fields_format_still_works(self, test_data_dir, fix_user_data_loaders):
        """Test that old enabled_fields format continues to work for backward compatibility."""
        user_id = "test-user-legacy-enabled-fields"
        test_user = TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        # Get the actual UUID for the user
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be created and resolvable"

        # Create sample check-in data (use recent dates)
        from datetime import datetime, timedelta
        now = datetime.now()
        sample_checkins = [
            {
                "timestamp": (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                "mood": 4, "energy": 3, "sleep_hours": 7.5
            },
            {
                "timestamp": now.strftime('%Y-%m-%d %H:%M:%S'), 
                "mood": 5, "energy": 4, "sleep_hours": 8.0
            }
        ]

        # Store check-in data in the correct UUID directory
        checkin_file = get_user_file_path(actual_user_id, 'checkins')
        os.makedirs(os.path.dirname(checkin_file), exist_ok=True)
        with open(checkin_file, 'w', encoding='utf-8') as f:
            json.dump(sample_checkins, f, indent=2)

        # Test legacy format by directly passing enabled_fields (use actual_user_id)
        analytics = CheckinAnalytics()
        summaries = analytics.get_quantitative_summaries(actual_user_id, days=30, enabled_fields=["mood", "energy", "sleep_hours"])

        assert "error" not in summaries, f"Should not have error: {summaries}"
        
        # Should include the fields specified in enabled_fields
        assert 'mood' in summaries
        assert 'energy' in summaries  
        assert 'sleep_hours' in summaries
        
        # Should have correct averages
        assert summaries['mood']['average'] == 4.5
        assert summaries['energy']['average'] == 3.5
        assert summaries['sleep_hours']['average'] == 7.75

    @pytest.mark.behavior
    @pytest.mark.analytics
    def test_legacy_format_works_with_mocked_data(self, test_data_dir, fix_user_data_loaders):
        """Test that legacy format works when user data is properly mocked."""
        user_id = "test-user-legacy-mocked"
        test_user = TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        # Get the actual UUID for the user
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be created and resolvable"

        # Create minimal check-in data (use recent date)
        from datetime import datetime, timedelta
        now = datetime.now()
        sample_checkins = [
            {"timestamp": (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), "mood": 4, "energy": 3}
        ]

        # Store check-in data in the correct UUID directory
        checkin_file = get_user_file_path(actual_user_id, 'checkins')
        os.makedirs(os.path.dirname(checkin_file), exist_ok=True)
        with open(checkin_file, 'w', encoding='utf-8') as f:
            json.dump(sample_checkins, f, indent=2)

        # Mock the user data to return legacy format
        with patch('core.user_data_handlers.get_user_data') as mock_get_user_data:
            mock_get_user_data.return_value = {
                'preferences': {
                    'checkin_settings': {
                        'enabled_fields': ['mood', 'energy']
                    }
                }
            }
            
            analytics = CheckinAnalytics()
            summaries = analytics.get_quantitative_summaries(actual_user_id, days=30)

        # Should work with legacy format
        assert "error" not in summaries, f"Should not have error: {summaries}"
        assert 'mood' in summaries
        assert 'energy' in summaries

    @pytest.mark.behavior
    @pytest.mark.analytics
    def test_new_questions_format_takes_precedence(self, test_data_dir, fix_user_data_loaders):
        """Test that new questions format takes precedence over legacy enabled_fields."""
        user_id = "test-user-mixed-formats"
        test_user = TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        # Get the actual UUID for the user
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be created and resolvable"

        # Create sample check-in data (use recent date)
        from datetime import datetime, timedelta
        now = datetime.now()
        sample_checkins = [
            {
                "timestamp": (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                "mood": 4, "energy": 3, "sleep_hours": 7.5
            }
        ]

        # Store check-in data in the correct UUID directory
        checkin_file = get_user_file_path(actual_user_id, 'checkins')
        os.makedirs(os.path.dirname(checkin_file), exist_ok=True)
        with open(checkin_file, 'w', encoding='utf-8') as f:
            json.dump(sample_checkins, f, indent=2)

        # Mock the user data to return new questions format
        with patch('core.user_data_handlers.get_user_data') as mock_get_user_data:
            mock_get_user_data.return_value = {
                'preferences': {
                    'checkin_settings': {
                        'questions': {
                            'mood': {'enabled': True, 'type': 'scale_1_5'},
                            'sleep_hours': {'enabled': True, 'type': 'number'},
                            'energy': {'enabled': False, 'type': 'scale_1_5'}  # Disabled in new format
                        }
                    }
                }
            }
            
            analytics = CheckinAnalytics()
            summaries = analytics.get_quantitative_summaries(actual_user_id, days=30)

        assert "error" not in summaries, f"Should not have error: {summaries}"
        
        # Should use NEW format (questions), not legacy enabled_fields
        # mood should be included (enabled in questions)
        # energy should NOT be included (disabled in questions) 
        # sleep_hours should be included (enabled in questions)
        assert 'mood' in summaries
        assert 'sleep_hours' in summaries
        assert 'energy' not in summaries, "Energy should be excluded because it's disabled in questions format"


class TestLegacyPreferencesBlockRemoval:
    """Test that preferences blocks are preserved even when features are disabled."""
    
    @pytest.mark.behavior
    def test_preferences_block_preserved_on_full_update_when_feature_disabled(self, test_data_dir, fix_user_data_loaders):
        """Test that preferences blocks are preserved on full updates even when features are disabled."""
        user_id = "test-user-prefs-block-preserved"
        test_user = TestUserFactory.create_basic_user(user_id, enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        
        # Get the actual UUID for the user
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be created and resolvable"
        
        # Set up initial state: user has task_settings and checkin_settings blocks
        from core.user_data_handlers import update_user_preferences, get_user_data
        from core.user_data_handlers import update_user_account
        
        # Initial preferences with blocks
        initial_prefs = {
            "categories": ["motivational"],
            "channel": {"type": "email"},
            "task_settings": {"enabled": True, "reminder_frequency": "daily"},
            "checkin_settings": {"enabled": True, "frequency": "daily"}
        }
        update_user_preferences(actual_user_id, initial_prefs)
        
        # Verify blocks exist
        prefs_data = get_user_data(actual_user_id, 'preferences')
        assert 'task_settings' in prefs_data.get('preferences', {}), "Task settings should exist initially"
        assert 'checkin_settings' in prefs_data.get('preferences', {}), "Check-in settings should exist initially"
        
        # Disable features in account
        account_data = get_user_data(actual_user_id, 'account')
        account_data['account']['features']['task_management'] = 'disabled'
        account_data['account']['features']['checkins'] = 'disabled'
        update_user_account(actual_user_id, account_data['account'])
        
        # Full update without providing blocks (categories presence indicates full update)
        full_update = {
            "categories": ["motivational", "health"],
            "channel": {"type": "email"}
            # Note: task_settings and checkin_settings NOT provided
        }
        update_user_preferences(actual_user_id, full_update)
        
        # Verify blocks are preserved after full update (even though features are disabled)
        updated_prefs = get_user_data(actual_user_id, 'preferences')
        assert 'task_settings' in updated_prefs.get('preferences', {}), "Task settings should be preserved even when feature disabled"
        assert 'checkin_settings' in updated_prefs.get('preferences', {}), "Check-in settings should be preserved even when feature disabled"
        assert updated_prefs.get('preferences', {}).get('categories') == ["motivational", "health"], "Categories should be updated"
        # Verify settings values are preserved
        assert updated_prefs.get('preferences', {}).get('task_settings', {}).get('reminder_frequency') == "daily", "Task settings values should be preserved"
        assert updated_prefs.get('preferences', {}).get('checkin_settings', {}).get('frequency') == "daily", "Check-in settings values should be preserved"
    
    @pytest.mark.behavior
    def test_preferences_block_preserved_on_partial_update_when_feature_disabled(self, test_data_dir, fix_user_data_loaders):
        """Test that preferences blocks are preserved on partial updates even when features are disabled."""
        user_id = "test-user-prefs-block-partial"
        test_user = TestUserFactory.create_basic_user(user_id, enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        
        # Get the actual UUID for the user
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be created and resolvable"
        
        # Set up initial state: user has task_settings and checkin_settings blocks
        from core.user_data_handlers import update_user_preferences, get_user_data
        from core.user_data_handlers import update_user_account
        
        # Initial preferences with blocks
        initial_prefs = {
            "categories": ["motivational"],
            "channel": {"type": "email"},
            "task_settings": {"enabled": True, "reminder_frequency": "daily"},
            "checkin_settings": {"enabled": True, "frequency": "daily"}
        }
        update_user_preferences(actual_user_id, initial_prefs)
        
        # Disable features in account
        account_data = get_user_data(actual_user_id, 'account')
        account_data['account']['features']['task_management'] = 'disabled'
        account_data['account']['features']['checkins'] = 'disabled'
        update_user_account(actual_user_id, account_data['account'])
        
        # Partial update (no categories = not a full update)
        partial_update = {
            "channel": {"type": "discord"}
            # Note: task_settings and checkin_settings NOT provided, but this is a partial update
        }
        update_user_preferences(actual_user_id, partial_update)
        
        # Verify blocks are preserved on partial update
        updated_prefs = get_user_data(actual_user_id, 'preferences')
        assert 'task_settings' in updated_prefs.get('preferences', {}), "Task settings should be preserved on partial update"
        assert 'checkin_settings' in updated_prefs.get('preferences', {}), "Check-in settings should be preserved on partial update"
        assert updated_prefs.get('preferences', {}).get('channel', {}).get('type') == "discord", "Channel should be updated"
    
    @pytest.mark.behavior
    def test_preferences_block_preserved_when_provided_in_full_update(self, test_data_dir, fix_user_data_loaders):
        """Test that preferences blocks are preserved when provided in full update even when features are disabled."""
        user_id = "test-user-prefs-block-provided"
        test_user = TestUserFactory.create_basic_user(user_id, enable_checkins=True, enable_tasks=True, test_data_dir=test_data_dir)
        
        # Get the actual UUID for the user
        actual_user_id = get_user_id_by_identifier(user_id)
        assert actual_user_id is not None, "User should be created and resolvable"
        
        # Set up initial state: user has task_settings and checkin_settings blocks
        from core.user_data_handlers import update_user_preferences, get_user_data
        from core.user_data_handlers import update_user_account
        
        # Initial preferences with blocks
        initial_prefs = {
            "categories": ["motivational"],
            "channel": {"type": "email"},
            "task_settings": {"enabled": True, "reminder_frequency": "daily"},
            "checkin_settings": {"enabled": True, "frequency": "daily"}
        }
        update_user_preferences(actual_user_id, initial_prefs)
        
        # Disable features in account
        account_data = get_user_data(actual_user_id, 'account')
        account_data['account']['features']['task_management'] = 'disabled'
        account_data['account']['features']['checkins'] = 'disabled'
        update_user_account(actual_user_id, account_data['account'])
        
        # Full update WITH blocks provided (categories presence indicates full update)
        full_update_with_blocks = {
            "categories": ["motivational", "health"],
            "channel": {"type": "email"},
            "task_settings": {"enabled": False, "reminder_frequency": "weekly"},  # Block provided
            "checkin_settings": {"enabled": False, "frequency": "weekly"}  # Block provided
        }
        update_user_preferences(actual_user_id, full_update_with_blocks)
        
        # Verify blocks are preserved when provided in full update
        updated_prefs = get_user_data(actual_user_id, 'preferences')
        assert 'task_settings' in updated_prefs.get('preferences', {}), "Task settings should be preserved when provided in full update"
        assert 'checkin_settings' in updated_prefs.get('preferences', {}), "Check-in settings should be preserved when provided in full update"
        assert updated_prefs.get('preferences', {}).get('task_settings', {}).get('reminder_frequency') == "weekly", "Task settings should be updated"
        assert updated_prefs.get('preferences', {}).get('checkin_settings', {}).get('frequency') == "weekly", "Check-in settings should be updated"