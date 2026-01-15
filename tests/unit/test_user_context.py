"""
User Context Tests

Tests for user/user_context.py:
- UserContext singleton pattern
- Thread safety
- Load/save user data
- Set/get user_id
- Set/get internal_username
- Set/get preferred_name
- get_instance_context
"""

import pytest
import threading
from unittest.mock import patch, Mock, MagicMock

from user.user_context import UserContext
from tests.test_utilities import TestUserFactory


class TestUserContextSingleton:
    """Test UserContext singleton pattern"""
    
    @pytest.mark.unit
    def test_singleton_returns_same_instance(self):
        """Test: UserContext returns same instance on multiple calls"""
        # Act
        instance1 = UserContext()
        instance2 = UserContext()
        
        # Assert
        assert instance1 is instance2, "Should return same instance (singleton)"
    
    @pytest.mark.unit
    def test_singleton_thread_safe(self):
        """Test: UserContext singleton is thread-safe"""
        # Arrange
        instances = []
        
        def create_instance():
            instances.append(UserContext())
        
        # Act
        threads = [threading.Thread(target=create_instance) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Assert
        assert len(instances) == 5, "Should create 5 instances"
        # All instances should be the same
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance, "Should return same instance from all threads"
    
    @pytest.mark.unit
    def test_singleton_initializes_user_data(self):
        """Test: UserContext initializes user_data dictionary"""
        # Act
        instance = UserContext()
        
        # Assert
        assert hasattr(instance, 'user_data'), "Should have user_data attribute"
        assert isinstance(instance.user_data, dict), "Should initialize user_data as dict"


class TestUserContextUserID:
    """Test UserContext user_id methods"""
    
    @pytest.fixture
    def context(self):
        """Create UserContext instance for testing"""
        # Reset singleton for clean test
        UserContext._instance = None
        return UserContext()
    
    @pytest.mark.unit
    def test_set_user_id(self, context):
        """Test: set_user_id sets user_id in user_data"""
        # Arrange
        user_id = "test_user_123"
        
        # Act
        context.set_user_id(user_id)
        
        # Assert
        assert context.user_data['user_id'] == user_id, "Should set user_id in user_data"
    
    @pytest.mark.unit
    def test_set_user_id_none_clears_user_id(self, context):
        """Test: set_user_id with None clears user_id"""
        # Arrange
        user_id = "test_user_123"
        context.set_user_id(user_id)
        
        # Act
        context.set_user_id(None)
        
        # Assert
        assert context.user_data['user_id'] is None, "Should clear user_id"
    
    @pytest.mark.unit
    def test_get_user_id_returns_user_id(self, context):
        """Test: get_user_id returns user_id from user_data"""
        # Arrange
        user_id = "test_user_123"
        context.set_user_id(user_id)
        
        # Act
        result = context.get_user_id()
        
        # Assert
        assert result == user_id, "Should return user_id"
    
    @pytest.mark.unit
    def test_get_user_id_returns_none_when_not_set(self, context):
        """Test: get_user_id returns None when not set"""
        # Act
        result = context.get_user_id()
        
        # Assert
        assert result is None, "Should return None when not set"


class TestUserContextInternalUsername:
    """Test UserContext internal_username methods"""
    
    @pytest.fixture
    def context(self):
        """Create UserContext instance for testing"""
        UserContext._instance = None
        return UserContext()
    
    @pytest.mark.unit
    def test_set_internal_username(self, context):
        """Test: set_internal_username sets internal_username in user_data"""
        # Arrange
        username = "test_username"
        
        # Act
        context.set_internal_username(username)
        
        # Assert
        assert context.user_data['internal_username'] == username, "Should set internal_username"
    
    @pytest.mark.unit
    def test_set_internal_username_none_clears(self, context):
        """Test: set_internal_username with None clears value"""
        # Arrange
        username = "test_username"
        context.set_internal_username(username)
        
        # Act
        context.set_internal_username(None)
        
        # Assert
        assert context.user_data['internal_username'] is None, "Should clear internal_username"
    
    @pytest.mark.unit
    def test_get_internal_username_returns_username(self, context):
        """Test: get_internal_username returns internal_username"""
        # Arrange
        username = "test_username"
        context.set_internal_username(username)
        
        # Act
        result = context.get_internal_username()
        
        # Assert
        assert result == username, "Should return internal_username"
    
    @pytest.mark.unit
    def test_get_internal_username_returns_none_when_not_set(self, context):
        """Test: get_internal_username returns None when not set"""
        # Act
        result = context.get_internal_username()
        
        # Assert
        assert result is None, "Should return None when not set"


class TestUserContextPreferredName:
    """Test UserContext preferred_name methods"""
    
    @pytest.fixture
    def context(self):
        """Create UserContext instance for testing"""
        UserContext._instance = None
        return UserContext()
    
    @pytest.mark.unit
    def test_set_preferred_name(self, context):
        """Test: set_preferred_name sets preferred_name in user_data"""
        # Arrange
        name = "Test User"
        
        # Act
        context.set_preferred_name(name)
        
        # Assert
        assert context.user_data['preferred_name'] == name, "Should set preferred_name"
    
    @pytest.mark.unit
    def test_get_preferred_name_returns_name(self, context):
        """Test: get_preferred_name returns preferred_name"""
        # Arrange
        name = "Test User"
        context.set_preferred_name(name)
        
        # Act
        result = context.get_preferred_name()
        
        # Assert
        assert result == name, "Should return preferred_name"
    
    @pytest.mark.unit
    def test_get_preferred_name_returns_none_when_not_set(self, context):
        """Test: get_preferred_name returns None when not set"""
        # Act
        result = context.get_preferred_name()
        
        # Assert
        assert result is None, "Should return None when not set"


class TestUserContextLoadSave:
    """Test UserContext load/save user data"""
    
    @pytest.fixture
    def context(self):
        """Create UserContext instance for testing"""
        UserContext._instance = None
        return UserContext()
    
    @pytest.mark.unit
    def test_load_user_data_without_user_id(self, context):
        """Test: load_user_data returns early without user_id"""
        # Act
        context.load_user_data(None)
        
        # Assert
        # Should return early without error
        assert True, "Should return early without error"
    
    @pytest.mark.unit
    def test_load_user_data_loads_account_data(self, context, test_data_dir, mock_config):
        """Test: load_user_data loads account data"""
        # Arrange
        user_id = "test_context_load"
        TestUserFactory.create_minimal_user(user_id, test_data_dir=test_data_dir)
        
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Act
        context.load_user_data(actual_user_id)
        
        # Assert
        assert context.user_data['user_id'] == actual_user_id, "Should load user_id"
        assert 'preferences' in context.user_data, "Should load preferences"
    
    @pytest.mark.unit
    def test_save_user_data_without_user_id(self, context):
        """Test: save_user_data returns early without user_id"""
        # Act
        context.save_user_data(None)
        
        # Assert
        # Should return early without error
        assert True, "Should return early without error"
    
    @pytest.mark.unit
    def test_save_user_data_saves_data(self, context, test_data_dir, mock_config):
        """Test: save_user_data saves user data"""
        # Arrange
        user_id = "test_context_save"
        TestUserFactory.create_minimal_user(user_id, test_data_dir=test_data_dir)
        
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        context.load_user_data(actual_user_id)
        context.user_data['preferred_name'] = "Updated Name"
        
        with patch('core.user_data_handlers.save_user_data') as mock_save:
            # Act
            context.save_user_data(actual_user_id)
            
            # Assert
            # Should call save_user_data multiple times (account, preferences, context)
            assert mock_save.call_count >= 3, "Should save account, preferences, and context"


class TestUserContextGetInstanceContext:
    """Test UserContext get_instance_context method"""
    
    @pytest.fixture
    def context(self):
        """Create UserContext instance for testing"""
        UserContext._instance = None
        return UserContext()
    
    @pytest.mark.unit
    def test_get_instance_context_without_user_id(self, context):
        """Test: get_instance_context returns empty dict without user_id"""
        # Act
        result = context.get_instance_context()
        
        # Assert
        assert result == {}, "Should return empty dict without user_id"
    
    @pytest.mark.unit
    def test_get_instance_context_with_user_id(self, context, test_data_dir, mock_config):
        """Test: get_instance_context returns context with user_id"""
        # Arrange
        user_id = "test_context_instance"
        TestUserFactory.create_minimal_user(user_id, test_data_dir=test_data_dir)
        
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        context.set_user_id(actual_user_id)
        
        # Act
        result = context.get_instance_context()
        
        # Assert
        assert result is not None, "Should return context"
        assert result['user_id'] == actual_user_id, "Should include user_id"
        assert 'preferences' in result, "Should include preferences"
        assert 'active_schedules' in result, "Should include active_schedules"
    
    @pytest.mark.unit
    def test_get_instance_context_includes_account_status(self, context, test_data_dir, mock_config):
        """Test: get_instance_context includes account_status"""
        # Arrange
        user_id = "test_context_status"
        TestUserFactory.create_minimal_user(user_id, test_data_dir=test_data_dir)
        
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        context.set_user_id(actual_user_id)
        
        # Act
        result = context.get_instance_context()
        
        # Assert
        assert 'account_status' in result, "Should include account_status"
    
    @pytest.mark.unit
    def test_get_instance_context_includes_preferred_name(self, context, test_data_dir, mock_config):
        """Test: get_instance_context includes preferred_name"""
        # Arrange
        user_id = "test_context_name"
        TestUserFactory.create_minimal_user(user_id, test_data_dir=test_data_dir)
        
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        context.set_user_id(actual_user_id)
        context.set_preferred_name("Test Name")
        
        # Act
        result = context.get_instance_context()
        
        # Assert
        assert 'preferred_name' in result, "Should include preferred_name"

