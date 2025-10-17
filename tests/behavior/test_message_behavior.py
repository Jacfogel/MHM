"""
Tests for the message management module - Message CRUD operations.

This module tests:
- Message category retrieval from environment
- Default message loading
- Message CRUD operations (add, edit, delete, update)
- Sent message tracking and retrieval
- Message file creation and management
- Message validation and error handling
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, mock_open

# Add the project root to the path
# Do not modify sys.path; rely on package imports

from core.message_management import (
    get_message_categories,
    load_default_messages,
    add_message,
    edit_message,
    update_message,
    delete_message,
    get_recent_messages,
    store_sent_message,
    create_message_file_from_defaults,
    ensure_user_message_files
)
from core.config import get_user_data_dir


class TestMessageCategories:
    """Test message category functionality."""
    
    @pytest.mark.messages
    @pytest.mark.critical
    def test_get_message_categories_success(self):
        """Test getting message categories successfully."""
        with patch.dict(os.environ, {'MESSAGE_CATEGORIES': 'motivational,health,fun_facts'}):
            categories = get_message_categories()
            # Use set for unordered comparison
            assert set(categories) == set(['motivational', 'health', 'fun_facts', 'quotes_to_ponder', 'word_of_the_day'])
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_get_message_categories_default(self):
        """Test getting default message categories."""
        with patch('os.getenv', return_value='motivational,health,fun_facts'):
            categories = get_message_categories()
            assert set(categories) == set(['motivational', 'health', 'fun_facts'])
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_get_message_categories_custom(self):
        """Test getting custom message categories."""
        with patch('os.getenv', return_value='custom1,custom2,custom3'):
            categories = get_message_categories()
            assert set(categories) == set(['custom1', 'custom2', 'custom3'])
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_get_message_categories_empty(self):
        """Test getting message categories when none are defined."""
        with patch('os.getenv', return_value=None):
            categories = get_message_categories()
            assert categories == []


class TestDefaultMessages:
    """Test default message loading functionality."""
    
    @pytest.mark.messages
    @pytest.mark.critical
    def test_load_default_messages_success(self, test_data_dir):
        """Test loading default messages successfully."""
        test_messages = [
            {
                'message': "Don't forget to be awesome today! Let's make some epic things happen!",
                'days': ['ALL'],
                'time_periods': ['ALL'],
                'message_id': 'motivational_001'
            },
            {
                'message': "Remember to stay hydrated and take care of yourself!",
                'days': ['ALL'],
                'time_periods': ['ALL'],
                'message_id': 'motivational_002'
            }
        ]
        
        # Mock the file reading to return the exact structure
        mock_file_data = {"messages": test_messages}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_file_data))):
            messages = load_default_messages('motivational')
            assert messages == test_messages
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_load_default_messages_file_not_found(self, test_data_dir, mock_config):
        """Test loading default messages when file doesn't exist."""
        category = "nonexistent"
        
        # Use the mock_config fixture which already patches DEFAULT_MESSAGES_DIR_PATH
        # The test directory structure is set up by mock_config
        messages = load_default_messages(category)
        assert messages == []
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_load_default_messages_invalid_json(self, test_data_dir, mock_config):
        """Test loading default messages with invalid JSON."""
        category = "invalid"
        
        # Create test default messages file with invalid JSON
        # Use the path that mock_config sets up
        from core.config import DEFAULT_MESSAGES_DIR_PATH
        os.makedirs(DEFAULT_MESSAGES_DIR_PATH, exist_ok=True)
        
        with open(os.path.join(DEFAULT_MESSAGES_DIR_PATH, f'{category}.json'), 'w') as f:
            f.write("invalid json content")
        
        # The mock_config fixture already patches DEFAULT_MESSAGES_DIR_PATH
        messages = load_default_messages(category)
        assert messages == []


class TestMessageCRUD:
    """Test message CRUD operations."""
    
    @pytest.mark.messages
    @pytest.mark.critical
    def test_add_message_success(self, test_data_dir):
        """Test adding a message successfully."""
        user_id = "test-user-add"
        category = "motivational"
        message_data = {
            "message": "Test message",
            "days": ["monday", "tuesday"],
            "time_periods": ["morning"]
        }
        
        # Create user directory structure under tests/data/users
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        os.makedirs(user_dir, exist_ok=True)
        # Don't create messages directory - let add_message create it
        messages_dir = os.path.join(user_dir, 'messages')

        # Ensure a clean slate for the category file
        message_file = os.path.join(messages_dir, f"{category}.json")
        if os.path.exists(message_file):
            os.remove(message_file)
        
        # Mock get_user_data_dir to return our test directory
        with patch('core.message_management.get_user_data_dir', return_value=user_dir):
            result = add_message(user_id, category, message_data)

            # Functions return None on success
            assert result is None

            # Verify the message file was created and contains the message
            # Add some debugging for parallel execution issues
            if not os.path.exists(message_file):
                # Check if the directory exists
                if not os.path.exists(messages_dir):
                    raise AssertionError(f"Messages directory was not created: {messages_dir}")
                # Check if any files were created
                files_in_dir = os.listdir(messages_dir) if os.path.exists(messages_dir) else []
                raise AssertionError(f"Message file was not created: {message_file}. Files in directory: {files_in_dir}")
            assert os.path.exists(message_file)
            
            with open(message_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert 'messages' in data
                assert len(data['messages']) == 1
                assert data['messages'][0]['message'] == "Test message"
                assert data['messages'][0]['days'] == ["monday", "tuesday"]
                assert data['messages'][0]['time_periods'] == ["morning"]
                assert 'message_id' in data['messages'][0]
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_edit_message_success(self, test_data_dir):
        """Test editing a message successfully."""
        user_id = "test-user-edit"
        category = "motivational"
        message_id = "test-msg-1"
        updated_data = {
            "message": "Updated message",
            "days": ["monday"],
            "time_periods": ["evening"]
        }
        
        # Create user directory structure and initial message file under tests/data/users
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        messages_dir = os.path.join(user_dir, 'messages')
        os.makedirs(messages_dir, exist_ok=True)
        
        # Create initial message file
        message_file = os.path.join(messages_dir, f"{category}.json")
        initial_data = {
            'messages': [
                {
                    "message_id": "test-msg-1",
                    "message": "Original message",
                    "days": ["monday", "tuesday"],
                    "time_periods": ["morning"]
                }
            ]
        }
        with open(message_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)
        
        # Mock get_user_data_dir to return our test directory
        with patch('core.message_management.get_user_data_dir', return_value=user_dir):
            result = edit_message(user_id, category, message_id, updated_data)
            
            # Functions return None on success
            assert result is None
            
            # Verify the message was updated in the file
            with open(message_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert len(data['messages']) == 1
                assert data['messages'][0]['message'] == "Updated message"
                assert data['messages'][0]['days'] == ["monday"]
                assert data['messages'][0]['time_periods'] == ["evening"]
                assert data['messages'][0]['message_id'] == "test-msg-1"
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_edit_message_not_found(self, test_data_dir):
        """Test editing a message that doesn't exist."""
        user_id = "test-user"
        category = "motivational"
        message_id = "nonexistent"
        updated_data = {"message": "Updated message"}
        
        existing_messages = {
            'messages': [
                {
                    "message_id": "test-msg-1",
                    "message": "Original message",
                    "days": ["monday"],
                    "time_periods": ["morning"]
                }
            ]
        }
        
        mock_load = Mock(return_value=existing_messages)
        
        with patch('core.message_management.load_json_data', mock_load):
            result = edit_message(user_id, category, message_id, updated_data)
            
            # Functions return None on failure (due to error handler)
            assert result is None
            mock_load.assert_called_once()
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_update_message_success(self, test_data_dir):
        """Test updating a message successfully."""
        user_id = "test-user"
        category = "motivational"
        message_id = "test-msg-1"
        updates = {
            "message": "Updated message",
            "days": ["monday"]
        }
        
        existing_messages = {
            'messages': [
                {
                    "message_id": "test-msg-1",
                    "message": "Original message",
                    "days": ["monday", "tuesday"],
                    "time_periods": ["morning"]
                }
            ]
        }
        
        mock_load = Mock(return_value=existing_messages)
        mock_save = Mock(return_value=True)
        
        with patch('core.message_management.load_json_data', mock_load), \
             patch('core.message_management.save_json_data', mock_save):
            
            result = update_message(user_id, category, message_id, updates)
            
            # Functions return None on success
            assert result is None
            mock_load.assert_called_once()
            mock_save.assert_called_once()
    
    @pytest.mark.messages
    @pytest.mark.critical
    def test_delete_message_success(self, test_data_dir):
        """Test deleting a message successfully."""
        user_id = "test-user-delete"
        category = "motivational"
        message_id = "test-msg-1"
        
        # Create user directory structure and initial message file under users
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        messages_dir = os.path.join(user_dir, 'messages')
        os.makedirs(messages_dir, exist_ok=True)
        
        # Create initial message file with two messages
        message_file = os.path.join(messages_dir, f"{category}.json")
        initial_data = {
            'messages': [
                {
                    "message_id": "test-msg-1",
                    "message": "Message to delete",
                    "days": ["monday"],
                    "time_periods": ["morning"]
                },
                {
                    "message_id": "test-msg-2",
                    "message": "Message to keep",
                    "days": ["tuesday"],
                    "time_periods": ["evening"]
                }
            ]
        }
        with open(message_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)
        
        # Mock get_user_data_dir to return our test directory
        with patch('core.message_management.get_user_data_dir', return_value=user_dir):
            result = delete_message(user_id, category, message_id)
            
            # Functions return None on success
            assert result is None
            
            # Verify the message was deleted from the file
            with open(message_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert len(data['messages']) == 1
                assert data['messages'][0]['message_id'] == "test-msg-2"
                assert data['messages'][0]['message'] == "Message to keep"
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_delete_message_not_found(self, test_data_dir):
        """Test deleting a message that doesn't exist."""
        user_id = "test-user"
        category = "motivational"
        message_id = "nonexistent"
        
        existing_messages = {
            'messages': [
                {
                    "message_id": "test-msg-1",
                    "message": "Existing message",
                    "days": ["monday"],
                    "time_periods": ["morning"]
                }
            ]
        }
        
        mock_load = Mock(return_value=existing_messages)
        
        with patch('core.message_management.load_json_data', mock_load):
            result = delete_message(user_id, category, message_id)
            
            # Functions return None on failure (due to error handler)
            assert result is None
            mock_load.assert_called_once()


class TestSentMessages:
    """Test sent message tracking functionality."""
    
    @pytest.mark.messages
    @pytest.mark.file_io
    def test_store_sent_message_success(self, test_data_dir):
        """Test storing a sent message successfully."""
        user_id = "test-user-sent"
        category = "motivational"
        message_id = "test_msg"
        message = "Test motivational message"
        
        # Mock file operations
        mock_load = Mock(return_value={})
        mock_save = Mock()
        
        with patch('core.message_management.load_json_data', mock_load), \
             patch('core.message_management.save_json_data', mock_save):
            
            result = store_sent_message(user_id, category, message_id, message)
            
            assert result is True or result is None
            mock_load.assert_called_once()
            mock_save.assert_called_once()
    
    @pytest.mark.messages
    @pytest.mark.file_io
    def test_get_recent_messages_success(self, test_data_dir):
        """Test getting last 10 sent messages successfully."""
        user_id = "test-user-last10"
        category = "motivational"
        
        # Create user directory structure and sent messages file under tests/data/users
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        messages_dir = os.path.join(user_dir, 'messages')
        os.makedirs(messages_dir, exist_ok=True)
        
        # Create sent messages file with test data (new chronological structure)
        sent_messages_file = os.path.join(messages_dir, 'sent_messages.json')
        test_sent_messages = {
            "metadata": {
                "version": "2.0",
                "total_messages": 3
            },
            "messages": [
                {"message_id": "msg1", "message": "Test message 1", "category": category, "timestamp": "2025-01-01 10:00:00", "delivery_status": "sent"},
                {"message_id": "msg2", "message": "Test message 2", "category": category, "timestamp": "2025-01-01 11:00:00", "delivery_status": "sent"},
                {"message_id": "msg3", "message": "Test message 3", "category": category, "timestamp": "2025-01-01 12:00:00", "delivery_status": "sent"}
            ]
        }
        with open(sent_messages_file, 'w', encoding='utf-8') as f:
            json.dump(test_sent_messages, f)
        
        # Mock determine_file_path to return our test file
        with patch('core.message_management.determine_file_path', return_value=sent_messages_file):
            messages = get_recent_messages(user_id, category=category, limit=10)
            
            assert len(messages) == 3
            # Messages are sorted by timestamp descending, so msg3 (latest) comes first
            assert messages[0]['message_id'] == 'msg3'
            assert messages[1]['message_id'] == 'msg2'
            assert messages[2]['message_id'] == 'msg1'
    
    @pytest.mark.messages
    @pytest.mark.file_io
    def test_get_recent_messages_empty(self, test_data_dir):
        """Test getting last 10 messages when none exist."""
        user_id = "test-user"
        category = "motivational"
        
        # Mock file operations
        mock_load = Mock(return_value={})
        
        with patch('core.message_management.load_json_data', mock_load):
            result = get_recent_messages(user_id, category=category, limit=10)
            
            assert result == []
            mock_load.assert_called_once()


class TestMessageFileManagement:
    """Test message file creation and management."""
    
    @pytest.mark.messages
    @pytest.mark.file_io
    def test_create_message_file_from_defaults_success(self, test_data_dir):
        """Test creating message file from defaults successfully."""
        user_id = "test-user"
        category = "motivational"
        
        default_messages = [
            {"message_id": "default1", "message": "Default message 1", "days": ["monday"], "time_periods": ["morning"]},
            {"message_id": "default2", "message": "Default message 2", "days": ["tuesday"], "time_periods": ["evening"]}
        ]
        
        # Mock file operations
        mock_load_defaults = Mock(return_value=default_messages)
        mock_save = Mock()
        
        with patch('core.message_management.load_default_messages', mock_load_defaults), \
             patch('core.message_management.save_json_data', mock_save):
            
            result = create_message_file_from_defaults(user_id, category)
            
            assert result is True
            mock_load_defaults.assert_called_once_with(category)
            mock_save.assert_called_once()
    
    @pytest.mark.messages
    @pytest.mark.file_io
    def test_ensure_user_message_files_success(self, test_data_dir):
        """Test ensuring user message files exist successfully."""
        user_id = "test-user"
        categories = ["motivational", "health"]
        
        # Mock file operations
        mock_file_exists = Mock(return_value=False)
        mock_create_file = Mock(return_value=True)
        
        with patch('core.message_management.Path.exists', mock_file_exists), \
             patch('core.message_management.create_message_file_from_defaults', mock_create_file):
            
            result = ensure_user_message_files(user_id, categories)
            
            assert result['success'] is True
            assert mock_file_exists.call_count >= 2
            assert mock_create_file.call_count == 2


class TestErrorHandling:
    """Test error handling in message management functions."""
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_add_message_file_error(self, test_data_dir):
        """Test add_message handles file errors gracefully."""
        user_id = "test-user"
        category = "motivational"
        message_data = {"message_id": "test_msg", "message": "Test message", "days": ["monday"], "time_periods": ["morning"]}
        
        # Mock file operations to raise exception
        mock_load = Mock(side_effect=Exception("File error"))
        
        with patch('core.message_management.load_json_data', mock_load):
            result = add_message(user_id, category, message_data)
            
            assert result is False or result is None
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_edit_message_file_error(self, test_data_dir):
        """Test edit_message handles file errors gracefully."""
        user_id = "test-user"
        category = "motivational"
        message_id = "test_msg"
        updated_data = {"message_id": "test_msg", "message": "Updated message", "days": ["monday"], "time_periods": ["morning"]}
        
        # Mock file operations to raise exception
        mock_load = Mock(side_effect=Exception("File error"))
        
        with patch('core.message_management.load_json_data', mock_load):
            result = edit_message(user_id, category, message_id, updated_data)
            
            assert result is False or result is None
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_delete_message_file_error(self, test_data_dir):
        """Test delete_message handles file errors gracefully."""
        user_id = "test-user"
        category = "motivational"
        message_id = "test_msg"
        
        # Mock file operations to raise exception
        mock_load = Mock(side_effect=Exception("File error"))
        
        with patch('core.message_management.load_json_data', mock_load):
            result = delete_message(user_id, category, message_id)
            
            assert result is False or result is None
    
    @pytest.mark.messages
    @pytest.mark.regression
    def test_store_sent_message_file_error(self, test_data_dir):
        """Test store_sent_message handles file errors gracefully."""
        user_id = "test-user"
        category = "motivational"
        message_id = "test_msg"
        message = "Test message"
        
        # Mock file operations to raise exception
        mock_load = Mock(side_effect=Exception("File error"))
        
        with patch('core.message_management.load_json_data', mock_load):
            result = store_sent_message(user_id, category, message_id, message)
            
            assert result is False or result is None


class TestIntegration:
    """Test integration between message management functions."""
    
    @pytest.mark.messages
    @pytest.mark.file_io
    def test_full_message_lifecycle(self, test_data_dir):
        """Test complete message lifecycle (add, edit, delete)."""
        import uuid
        user_id = f"test-user-lifecycle-{str(uuid.uuid4())[:8]}"  # Use unique user ID to avoid conflicts
        category = "motivational"
        
        # Create user directory structure under tests/data/users
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        messages_dir = os.path.join(user_dir, 'messages')
        os.makedirs(messages_dir, exist_ok=True)
        
        # Ensure no existing message file exists
        message_file = os.path.join(messages_dir, f"{category}.json")
        if os.path.exists(message_file):
            os.remove(message_file)
        
        # Message to add
        new_message = {
            "message": "Test message",
            "days": ["monday"],
            "time_periods": ["morning"]
        }
        
        # Updated message
        updated_message = {
            "message": "Updated test message",
            "days": ["monday", "tuesday"],
            "time_periods": ["morning", "evening"]
        }
        
        # Mock get_user_data_dir to return our test directory
        with patch('core.message_management.get_user_data_dir', return_value=user_dir):
            # 1. Add message
            result1 = add_message(user_id, category, new_message)
            assert result1 is None

            # Verify message was added
            # Add some debugging for parallel execution issues
            if not os.path.exists(message_file):
                # Check if the directory exists
                if not os.path.exists(messages_dir):
                    raise AssertionError(f"Messages directory was not created: {messages_dir}")
                # Check if any files were created
                files_in_dir = os.listdir(messages_dir) if os.path.exists(messages_dir) else []
                raise AssertionError(f"Message file was not created: {message_file}. Files in directory: {files_in_dir}")
            assert os.path.exists(message_file)
            with open(message_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert len(data['messages']) == 1
                assert data['messages'][0]['message'] == "Test message"
                message_id = data['messages'][0]['message_id']
            
            # 2. Edit message
            result2 = edit_message(user_id, category, message_id, updated_message)
            assert result2 is None
            
            # Verify message was updated - ensure file exists and is readable
            assert os.path.exists(message_file), f"Message file should exist after edit: {message_file}"
            with open(message_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert len(data['messages']) == 1
                assert data['messages'][0]['message'] == "Updated test message"
                assert data['messages'][0]['days'] == ["monday", "tuesday"]
            
            # 3. Delete message
            result3 = delete_message(user_id, category, message_id)
            assert result3 is None
            
            # Verify message was deleted - ensure file still exists but is empty
            assert os.path.exists(message_file), f"Message file should exist after delete: {message_file}"
            with open(message_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert len(data['messages']) == 0 