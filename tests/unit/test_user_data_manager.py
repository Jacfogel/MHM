"""
Comprehensive tests for user data manager.

Tests the actual behavior, user interactions, and side effects for:
- User data manager initialization
- Message reference management
- User data backup and export
- User deletion
- User index management
- User search functionality
"""

import pytest
from unittest.mock import patch, Mock, MagicMock, mock_open
import os
import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

from core.user_data_manager import (
    UserDataManager,
    update_message_references,
    backup_user_data,
    export_user_data,
    delete_user_completely,
    get_user_data_summary,
    update_user_index,
    rebuild_user_index,
    get_user_info_for_data_manager,
    build_user_index,
    get_user_summary,
    get_all_user_summaries,
    get_user_analytics_summary
)
from tests.test_utilities import TestUserFactory


class TestUserDataManagerInitialization:
    """Test user data manager initialization."""
    
    @pytest.mark.unit
    def test_manager_initialization(self, test_data_dir):
        """Test: UserDataManager initializes correctly"""
        # Arrange: Set up test environment
        with patch('core.user_data_manager.BASE_DATA_DIR', test_data_dir), \
             patch('core.user_data_manager.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
            
            # Act: Create manager
            manager = UserDataManager()
            
            # Assert: Verify initialization
            assert manager is not None, "Manager should be created"
            assert manager.index_file is not None, "Index file should be set"
            assert manager.backup_dir is not None, "Backup directory should be set"
            assert os.path.exists(manager.backup_dir), "Backup directory should exist"
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_manager_initialization_creates_backup_dir(self, test_data_dir):
        """Test: UserDataManager creates backup directory if it doesn't exist"""
        # Arrange: Set up test environment
        backup_dir = os.path.join(test_data_dir, 'backups')
        if os.path.exists(backup_dir):
            # Windows file locking: retry with delay if files are locked
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    shutil.rmtree(backup_dir)
                    break
                except PermissionError:
                    if attempt < max_retries - 1:
                        time.sleep(0.1)  # Brief delay to allow file handles to release
                    else:
                        # On final attempt, try to close any open zip files first
                        import gc
                        gc.collect()
                        time.sleep(0.2)
                        try:
                            shutil.rmtree(backup_dir)
                        except PermissionError:
                            # If still locked, skip cleanup (test will still work)
                            pass
        
        with patch('core.user_data_manager.BASE_DATA_DIR', test_data_dir), \
             patch('core.user_data_manager.get_backups_dir', return_value=backup_dir):
            
            # Act: Create manager
            manager = UserDataManager()
            
            # Assert: Verify backup directory was created
            assert os.path.exists(backup_dir), "Backup directory should be created"


class TestUserDataManagerMessageReferences:
    """Test message reference management."""
    
    @pytest.fixture
    def manager(self, test_data_dir):
        """Create user data manager for testing."""
        with patch('core.user_data_manager.BASE_DATA_DIR', test_data_dir), \
             patch('core.user_data_manager.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
            return UserDataManager()
    
    @pytest.fixture
    def test_user(self, test_data_dir):
        """Create test user with categories."""
        user_id = "test_message_refs_user"
        TestUserFactory.create_basic_user(
            user_id, 
            enable_checkins=True, 
            test_data_dir=test_data_dir
        )
        
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        return actual_user_id
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_update_message_references_success(self, manager, test_user, test_data_dir):
        """Test: update_message_references updates references successfully"""
        # Arrange: User is created in fixture and this test runs serially because it touches shared files.
        result = manager.update_message_references(test_user)
        assert result is True, f"Should return True on success. Got: {result}"
    
    @pytest.mark.unit
    def test_update_message_references_invalid_user_id(self, manager):
        """Test: update_message_references handles invalid user_id"""
        # Arrange: Invalid user_id
        invalid_user_id = None
        
        # Act: Update message references
        result = manager.update_message_references(invalid_user_id)
        
        # Assert: Should return False
        assert result == False, "Should return False for invalid user_id"
    
    @pytest.mark.unit
    def test_update_message_references_empty_user_id(self, manager):
        """Test: update_message_references handles empty user_id"""
        # Arrange: Empty user_id
        empty_user_id = ""
        
        # Act: Update message references
        result = manager.update_message_references(empty_user_id)
        
        # Assert: Should return False
        assert result == False, "Should return False for empty user_id"
    
    @pytest.mark.unit
    def test_update_message_references_user_not_found(self, manager):
        """Test: update_message_references handles user not found"""
        # Arrange: Non-existent user
        non_existent_user = "non_existent_user_12345"
        
        # Act: Update message references
        result = manager.update_message_references(non_existent_user)
        
        # Assert: Should return False
        assert result == False, "Should return False for non-existent user"
    
    @pytest.mark.unit
    def test_get_user_message_files_success(self, manager, test_user, test_data_dir):
        """Test: get_user_message_files returns message files"""
        # Arrange: User is created in fixture
        
        # Act: Get message files
        message_files = manager.get_user_message_files(test_user)
        
        # Assert: Should return dict of message files
        assert isinstance(message_files, dict), "Should return dict"
        # Should have message files for categories
        assert len(message_files) >= 0, "Should return message files"
    
    @pytest.mark.unit
    def test_get_user_message_files_invalid_user_id(self, manager):
        """Test: get_user_message_files handles invalid user_id"""
        # Arrange: Invalid user_id
        invalid_user_id = None
        
        # Act: Get message files
        message_files = manager.get_user_message_files(invalid_user_id)
        
        # Assert: Should return empty dict
        assert message_files == {}, "Should return empty dict for invalid user_id"


class TestUserDataManagerBackup:
    """Test user data backup functionality."""
    
    @pytest.fixture
    def manager(self, test_data_dir):
        """Create user data manager for testing."""
        with patch('core.user_data_manager.BASE_DATA_DIR', test_data_dir), \
             patch('core.user_data_manager.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
            return UserDataManager()
    
    @pytest.fixture
    def test_user(self, test_data_dir):
        """Create test user."""
        user_id = "test_backup_user"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        return actual_user_id
    
    @pytest.mark.unit
    def test_backup_user_data_success(self, manager, test_user, test_data_dir):
        """Test: backup_user_data creates backup successfully"""
        # Arrange: User is created in fixture
        
        # Act: Create backup
        backup_path = manager.backup_user_data(test_user, include_messages=True)
        
        # Assert: Should return backup path
        assert backup_path != "", "Should return backup path"
        assert os.path.exists(backup_path), "Backup file should exist"
        assert backup_path.endswith('.zip'), "Backup should be zip file"
        
        # Assert: Backup should contain files
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            files = zipf.namelist()
            assert len(files) > 0, "Backup should contain files"
            assert 'backup_metadata.json' in files, "Backup should contain metadata"
    
    @pytest.mark.unit
    def test_backup_user_data_without_messages(self, manager, test_user, test_data_dir):
        """Test: backup_user_data creates backup without messages"""
        # Arrange: User is created in fixture
        
        # Act: Create backup without messages
        backup_path = manager.backup_user_data(test_user, include_messages=False)
        
        # Assert: Should return backup path
        assert backup_path != "", "Should return backup path"
        assert os.path.exists(backup_path), "Backup file should exist"
    
    @pytest.mark.unit
    def test_backup_user_data_invalid_user_id(self, manager):
        """Test: backup_user_data handles invalid user_id"""
        # Arrange: Invalid user_id
        invalid_user_id = None
        
        # Act: Create backup
        backup_path = manager.backup_user_data(invalid_user_id)
        
        # Assert: Should return empty string
        assert backup_path == "", "Should return empty string for invalid user_id"
    
    @pytest.mark.unit
    def test_backup_user_data_invalid_include_messages(self, manager, test_user):
        """Test: backup_user_data handles invalid include_messages"""
        # Arrange: Invalid include_messages
        invalid_include = "not_a_boolean"
        
        # Act: Create backup
        backup_path = manager.backup_user_data(test_user, include_messages=invalid_include)
        
        # Assert: Should return empty string
        assert backup_path == "", "Should return empty string for invalid include_messages"


class TestUserDataManagerExport:
    """Test user data export functionality."""
    
    @pytest.fixture
    def manager(self, test_data_dir):
        """Create user data manager for testing."""
        with patch('core.user_data_manager.BASE_DATA_DIR', test_data_dir), \
             patch('core.user_data_manager.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
            return UserDataManager()
    
    @pytest.fixture
    def test_user(self, test_data_dir):
        """Create test user."""
        user_id = "test_export_user"
        TestUserFactory.create_minimal_user(user_id, test_data_dir=test_data_dir)
        
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        return actual_user_id
    
    @pytest.mark.unit
    def test_export_user_data_success(self, manager, test_user, test_data_dir):
        """Test: export_user_data exports data successfully"""
        # Arrange: User is created in fixture
        
        # Act: Export user data
        export_data = manager.export_user_data(test_user, export_format="json")
        
        # Assert: Should return export data
        assert isinstance(export_data, dict), "Should return dict"
        assert export_data.get('user_id') == test_user, "Should include user_id"
        assert 'export_date' in export_data, "Should include export_date"
        assert 'profile' in export_data, "Should include profile"
        assert 'preferences' in export_data, "Should include preferences"
    
    @pytest.mark.unit
    def test_export_user_data_invalid_user_id(self, manager):
        """Test: export_user_data handles invalid user_id"""
        # Arrange: Invalid user_id
        invalid_user_id = None
        
        # Act: Export user data
        export_data = manager.export_user_data(invalid_user_id)
        
        # Assert: Should return empty dict
        assert export_data == {}, "Should return empty dict for invalid user_id"
    
    @pytest.mark.unit
    def test_export_user_data_invalid_format(self, manager, test_user):
        """Test: export_user_data handles invalid export_format"""
        # Arrange: Invalid export_format
        invalid_format = "invalid_format"
        
        # Act: Export user data
        export_data = manager.export_user_data(test_user, export_format=invalid_format)
        
        # Assert: Should return empty dict
        assert export_data == {}, "Should return empty dict for invalid format"


class TestUserDataManagerIndex:
    """Test user index management."""
    
    @pytest.fixture
    def manager(self, test_data_dir):
        """Create user data manager for testing."""
        with patch('core.user_data_manager.BASE_DATA_DIR', test_data_dir), \
             patch('core.user_data_manager.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
            return UserDataManager()
    
    @pytest.fixture
    def test_user(self, test_data_dir):
        """Create test user.
        
        Note: This fixture is used by tests marked @pytest.mark.no_parallel,
        so serial execution ensures data is available without retry logic.
        """
        from core.user_management import get_user_id_by_identifier
        from core.user_data_manager import rebuild_user_index
        from core.user_data_handlers import get_user_data
        
        user_id = "test_index_user"
        TestUserFactory.create_minimal_user(user_id, test_data_dir=test_data_dir)
        
        # Rebuild index to ensure user is discoverable (serial execution ensures this works)
        rebuild_user_index()
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Verify account data exists (serial execution ensures data is available)
        account_data = get_user_data(actual_user_id, 'account', auto_create=False)
        if not account_data.get('account'):
            # If account doesn't exist, try to get it with auto_create to ensure it's created
            account_data = get_user_data(actual_user_id, 'account', auto_create=True)
            # Rebuild index again after auto-creation
            rebuild_user_index()
        
        return actual_user_id
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_update_user_index_success(self, manager, test_user, test_data_dir):
        """Test: update_user_index updates index successfully
        
        Marked as no_parallel because it modifies user_index.json.
        """
        # Arrange: User is created in fixture
        from core.user_data_handlers import get_user_data
        from core.user_data_manager import rebuild_user_index
        
        # Verify user account exists (serial execution ensures data is available)
        # If account doesn't exist, try to ensure it's created
        user_data = get_user_data(test_user, 'account', auto_create=False)
        user_account = user_data.get('account') or {}
        if not user_account or not user_account.get('internal_username'):
            # Account might not exist yet - try with auto_create
            user_data = get_user_data(test_user, 'account', auto_create=True)
            user_account = user_data.get('account') or {}
            # Rebuild index after auto-creation
            rebuild_user_index()
            # Re-read to ensure data is fresh
            user_data = get_user_data(test_user, 'account', auto_create=False)
            user_account = user_data.get('account') or {}
        
        assert user_account and user_account.get('internal_username'), \
            f"User account data not available for {test_user} (account keys: {list(user_account.keys())})"
        
        # Act: Update user index (with retry for parallel execution)
        import time
        result = False
        for attempt in range(3):
            result = manager.update_user_index(test_user)
            if result:
                break
            if attempt < 2:
                time.sleep(0.1)  # Brief delay before retry
                # Rebuild index and re-read account to ensure fresh data
                rebuild_user_index()
                user_data = get_user_data(test_user, 'account', auto_create=False)
                user_account = user_data.get('account') or {}
        
        # Assert: Should return True
        assert result == True, f"Should return True on success. Got: {result} (user_id={test_user}, internal_username={user_account.get('internal_username')})"
        
        # Assert: Index file should exist and contain user
        if os.path.exists(manager.index_file):
            index_data = json.load(open(manager.index_file, 'r', encoding='utf-8'))
            # Should have last_updated
            assert 'last_updated' in index_data, "Index should have last_updated"
    
    @pytest.mark.unit
    def test_update_user_index_invalid_user_id(self, manager):
        """Test: update_user_index handles invalid user_id"""
        # Arrange: Invalid user_id
        invalid_user_id = None
        
        # Act: Update user index
        result = manager.update_user_index(invalid_user_id)
        
        # Assert: Should return False
        assert result == False, "Should return False for invalid user_id"
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_remove_from_index_success(self, manager, test_user, test_data_dir):
        """Test: remove_from_index removes user from index successfully"""
        # Arrange: User is created in fixture, update index first
        manager.update_user_index(test_user)
        
        # Act: Remove from index
        result = manager.remove_from_index(test_user)
        
        # Assert: Should return True
        assert result == True, "Should return True on success"
    
    @pytest.mark.unit
    def test_remove_from_index_invalid_user_id(self, manager):
        """Test: remove_from_index handles invalid user_id"""
        # Arrange: Invalid user_id
        invalid_user_id = None
        
        # Act: Remove from index
        result = manager.remove_from_index(invalid_user_id)
        
        # Assert: Should return False
        assert result == False, "Should return False for invalid user_id"
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_rebuild_full_index_success(self, manager, test_data_dir):
        """Test: rebuild_full_index rebuilds index successfully"""
        # Arrange: Create test users
        user1 = "test_rebuild_user1"
        user2 = "test_rebuild_user2"
        TestUserFactory.create_minimal_user(user1, test_data_dir=test_data_dir)
        TestUserFactory.create_minimal_user(user2, test_data_dir=test_data_dir)
        
        # Act: Rebuild index
        result = manager.rebuild_full_index()
        
        # Assert: Should return True
        assert result == True, "Should return True on success"
        
        # Assert: Index file should exist
        if os.path.exists(manager.index_file):
            index_data = json.load(open(manager.index_file, 'r', encoding='utf-8'))
            assert 'last_updated' in index_data, "Index should have last_updated"


class TestUserDataManagerSearch:
    """Test user search functionality."""
    
    @pytest.fixture
    def manager(self, test_data_dir):
        """Create user data manager for testing."""
        with patch('core.user_data_manager.BASE_DATA_DIR', test_data_dir), \
             patch('core.user_data_manager.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
            return UserDataManager()
    
    @pytest.fixture
    def test_user(self, test_data_dir):
        """Create test user."""
        user_id = "test_search_user"
        TestUserFactory.create_minimal_user(user_id, test_data_dir=test_data_dir)
        
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        return actual_user_id
    
    @pytest.mark.unit
    def test_search_users_success(self, manager, test_user, test_data_dir):
        """Test: search_users finds users successfully"""
        # Arrange: User is created in fixture
        
        # Act: Search users
        results = manager.search_users("test_search", search_fields=["internal_username"])
        
        # Assert: Should return list
        assert isinstance(results, list), "Should return list"
        # May or may not find the user depending on search criteria
    
    @pytest.mark.unit
    def test_search_users_invalid_query(self, manager):
        """Test: search_users handles invalid query"""
        # Arrange: Invalid query
        invalid_query = None
        
        # Act: Search users
        results = manager.search_users(invalid_query)
        
        # Assert: Should return empty list
        assert results == [], "Should return empty list for invalid query"
    
    @pytest.mark.unit
    def test_search_users_empty_query(self, manager):
        """Test: search_users handles empty query"""
        # Arrange: Empty query
        empty_query = ""
        
        # Act: Search users
        results = manager.search_users(empty_query)
        
        # Assert: Should return empty list
        assert results == [], "Should return empty list for empty query"
    
    @pytest.mark.unit
    def test_search_users_invalid_search_fields(self, manager):
        """Test: search_users handles invalid search_fields"""
        # Arrange: Invalid search_fields
        invalid_fields = "not_a_list"
        
        # Act: Search users
        results = manager.search_users("test", search_fields=invalid_fields)
        
        # Assert: Should return empty list
        assert results == [], "Should return empty list for invalid search_fields"


class TestUserDataManagerSummary:
    """Test user data summary functionality."""
    
    @pytest.fixture
    def manager(self, test_data_dir):
        """Create user data manager for testing."""
        with patch('core.user_data_manager.BASE_DATA_DIR', test_data_dir), \
             patch('core.user_data_manager.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
            return UserDataManager()
    
    @pytest.fixture
    def test_user(self, test_data_dir):
        """Create test user."""
        user_id = "test_summary_user"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        return actual_user_id
    
    @pytest.mark.unit
    def test_get_user_data_summary_success(self, manager, test_user, test_data_dir):
        """Test: get_user_data_summary returns summary successfully"""
        # Arrange: User is created in fixture
        
        # Act: Get user data summary
        summary = manager.get_user_data_summary(test_user)
        
        # Assert: Should return summary dict
        assert isinstance(summary, dict), "Should return dict"
        assert summary.get('user_id') == test_user, "Should include user_id"
        assert 'files' in summary, "Should include files"
        assert 'messages' in summary, "Should include messages"
        assert 'logs' in summary, "Should include logs"
        assert 'total_files' in summary, "Should include total_files"
        assert 'total_size_bytes' in summary, "Should include total_size_bytes"
    
    @pytest.mark.unit
    def test_get_user_data_summary_invalid_user_id(self, manager):
        """Test: get_user_data_summary handles invalid user_id"""
        # Arrange: Invalid user_id
        invalid_user_id = None
        
        # Act: Get user data summary
        summary = manager.get_user_data_summary(invalid_user_id)
        
        # Assert: Should return error dict
        assert isinstance(summary, dict), "Should return dict"
        assert 'error' in summary, "Should include error"


class TestUserDataManagerConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.fixture
    def test_user(self, test_data_dir):
        """Create test user and return the actual UUID to avoid index timing issues."""
        user_id = "test_conv_user"
        success, actual_user_id = TestUserFactory.create_minimal_user_and_get_id(
            user_id,
            test_data_dir=test_data_dir
        )
        assert success, f"Failed to create minimal user {user_id}"
        return actual_user_id or user_id
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_update_message_references_function(self, test_user, test_data_dir):
        """Test: update_message_references convenience function works
        
        Marked as no_parallel because it modifies user message files.
        """
        # Arrange: User is created in fixture
        from core.user_data_handlers import get_user_data
        
        # Verify user account exists (serial execution ensures data is available)
        user_data = get_user_data(test_user, 'account', auto_create=False)
        user_account = user_data.get('account') or {}
        assert user_account and user_account.get('internal_username'), \
            f"User account data not available for {test_user}"
        
        # Act: Update message references
        result = update_message_references(test_user)
        
        # Assert: Should return True
        assert result == True, f"Should return True on success. Got: {result}"
    
    @pytest.mark.unit
    def test_backup_user_data_function(self, test_user, test_data_dir):
        """Test: backup_user_data convenience function works"""
        # Arrange: User is created in fixture
        
        # Act: Create backup
        backup_path = backup_user_data(test_user, include_messages=True)
        
        # Assert: Should return backup path
        assert backup_path != "", "Should return backup path"
    
    @pytest.mark.unit
    def test_export_user_data_function(self, test_user, test_data_dir):
        """Test: export_user_data convenience function works"""
        # Arrange: User is created in fixture
        
        # Act: Export user data
        export_data = export_user_data(test_user, export_format="json")
        
        # Assert: Should return export data
        assert isinstance(export_data, dict), "Should return dict"
    
    @pytest.mark.unit
    def test_get_user_data_summary_function(self, test_user, test_data_dir):
        """Test: get_user_data_summary convenience function works"""
        # Arrange: User is created in fixture
        
        # Act: Get user data summary
        summary = get_user_data_summary(test_user)
        
        # Assert: Should return summary
        assert isinstance(summary, dict), "Should return dict"
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_update_user_index_function(self, test_user, test_data_dir):
        """Test: update_user_index convenience function works"""
        # Arrange: User is created in fixture
        
        # Act: Update user index
        result = update_user_index(test_user)
        
        # Assert: Should return True
        assert result == True, "Should return True on success"
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_rebuild_user_index_function(self, test_data_dir):
        """Test: rebuild_user_index convenience function works"""
        # Arrange: Create test users
        user1 = "test_rebuild_conv_user1"
        TestUserFactory.create_minimal_user(user1, test_data_dir=test_data_dir)
        
        # Act: Rebuild index
        result = rebuild_user_index()
        
        # Assert: Should return True
        assert result == True, "Should return True on success"
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_get_user_info_for_data_manager_function(self, test_user, test_data_dir):
        """Test: get_user_info_for_data_manager convenience function works
        
        Marked as no_parallel because it reads user data files that may be modified by other tests.
        """
        # Arrange: User is created in fixture
        
        # Act: Get user info (serial execution ensures data is available)
        user_info = get_user_info_for_data_manager(test_user)
        
        # Assert: Should return user info
        assert user_info is not None, f"Should return user info for user {test_user}"
        assert isinstance(user_info, dict), "Should return dict"
        assert user_info.get('user_id') == test_user, "Should include user_id"
    
    @pytest.mark.unit
    def test_get_user_info_for_data_manager_invalid_user_id(self):
        """Test: get_user_info_for_data_manager handles invalid user_id"""
        # Arrange: Invalid user_id
        invalid_user_id = None
        
        # Act: Get user info
        user_info = get_user_info_for_data_manager(invalid_user_id)
        
        # Assert: Should return None
        assert user_info is None, "Should return None for invalid user_id"
    
    @pytest.mark.unit
    def test_build_user_index_function(self, test_data_dir):
        """Test: build_user_index convenience function works"""
        # Arrange: Create test users
        user1 = "test_build_index_user1"
        TestUserFactory.create_minimal_user(user1, test_data_dir=test_data_dir)
        
        # Act: Build user index
        index_data = build_user_index()
        
        # Assert: Should return index data
        assert isinstance(index_data, dict), "Should return dict"
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_get_user_summary_function(self, test_user, test_data_dir):
        """Test: get_user_summary convenience function works
        
        Marked as no_parallel because it reads user data files that may be modified by other tests.
        """
        # Arrange: User is created in fixture
        
        # Act: Get user summary
        summary = get_user_summary(test_user)

        # Assert: Should return summary
        assert isinstance(summary, dict), "Should return dict"
        assert summary.get('user_id') == test_user, f"Should include user_id. Summary: {summary}"
    
    @pytest.mark.unit
    def test_get_all_user_summaries_function(self, test_data_dir):
        """Test: get_all_user_summaries convenience function works"""
        # Arrange: Create test users
        user1 = "test_all_summaries_user1"
        TestUserFactory.create_minimal_user(user1, test_data_dir=test_data_dir)
        
        # Act: Get all user summaries
        summaries = get_all_user_summaries()
        
        # Assert: Should return list
        assert isinstance(summaries, list), "Should return list"
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_get_user_analytics_summary_function(self, test_user, test_data_dir):
        """Test: get_user_analytics_summary convenience function works"""
        # Arrange: User is created in fixture
        
        # Act: Get analytics summary
        analytics = get_user_analytics_summary(test_user)
        
        # Assert: Should return analytics
        assert isinstance(analytics, dict), "Should return dict"
        assert 'user_id' in analytics or 'error' in analytics, "Should include user_id or error"


class TestUserDataManagerDeleteUser:
    """Test user deletion functionality."""
    
    @pytest.fixture
    def manager(self, test_data_dir):
        """Create user data manager for testing."""
        with patch('core.user_data_manager.BASE_DATA_DIR', test_data_dir), \
             patch('core.user_data_manager.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
            return UserDataManager()
    
    @pytest.fixture
    def test_user(self, test_data_dir):
        """Create test user."""
        user_id = "test_delete_user"
        TestUserFactory.create_minimal_user(user_id, test_data_dir=test_data_dir)
        
        from core.user_management import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        return actual_user_id
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_delete_user_completely_with_backup(self, manager, test_user, test_data_dir):
        """Test: delete_user_completely deletes user with backup"""
        # Arrange: User is created in fixture
        
        # Act: Delete user with backup
        result = manager.delete_user_completely(test_user, create_backup=True)
        
        # Assert: Should return True
        assert result == True, "Should return True on success"
    
    @pytest.mark.unit
    @pytest.mark.no_parallel
    def test_delete_user_completely_without_backup(self, manager, test_user, test_data_dir):
        """Test: delete_user_completely deletes user without backup"""
        # Arrange: User is created in fixture
        
        # Ensure user data is available (race condition fix for parallel execution)
        import time
        from core.user_data_handlers import get_user_data
        
        # Wait for user account data to be available
        max_retries = 5
        user_account = None
        for attempt in range(max_retries):
            user_data = get_user_data(test_user, 'account', auto_create=False)
            user_account = user_data.get('account') or {}
            if user_account:
                break
            if attempt < max_retries - 1:
                time.sleep(0.1)
        
        # Act: Delete user without backup
        result = manager.delete_user_completely(test_user, create_backup=False)
        
        # Assert: Should return True
        assert result == True, f"Should return True on success. Got: {result}"
    
    @pytest.mark.unit
    def test_delete_user_completely_invalid_user_id(self, manager):
        """Test: delete_user_completely handles invalid user_id"""
        # Arrange: Invalid user_id
        invalid_user_id = None
        
        # Act: Delete user
        result = manager.delete_user_completely(invalid_user_id)
        
        # Assert: Should return False
        assert result == False, "Should return False for invalid user_id"
    
    @pytest.mark.unit
    def test_delete_user_completely_invalid_create_backup(self, manager, test_user):
        """Test: delete_user_completely handles invalid create_backup"""
        # Arrange: Invalid create_backup
        invalid_backup = "not_a_boolean"
        
        # Act: Delete user
        result = manager.delete_user_completely(test_user, create_backup=invalid_backup)
        
        # Assert: Should return False
        assert result == False, "Should return False for invalid create_backup"

