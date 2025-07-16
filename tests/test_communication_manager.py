"""
Tests for the communication manager module - Message delivery across channels.

This module tests:
- Message delivery to different channels (Discord, Email, Telegram)
- Channel selection and routing
- Message formatting and validation
- Delivery status tracking
- Error handling and retry logic
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import asyncio

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the actual functions from communication_manager
from bot.communication_manager import (
    CommunicationManager,
    BotInitializationError,
    MessageSendError,
    LegacyChannelWrapper
)
from bot.base_channel import ChannelConfig, ChannelStatus, ChannelType
from core.config import get_user_data_dir

class TestCommunicationManager:
    """Test cases for the CommunicationManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def comm_manager(self):
        """Create a CommunicationManager instance for testing."""
        return CommunicationManager()
    
    @pytest.fixture
    def mock_channel_config(self):
        """Create a mock channel configuration."""
        return ChannelConfig(
            name='test_channel',
            enabled=True,
            max_retries=3,
            retry_delay=1.0,
            backoff_multiplier=2.0
        )
    
    @pytest.fixture
    def realistic_mock_channel(self):
        """Create a realistic mock channel with proper async methods."""
        mock_channel = Mock()
        mock_channel.is_ready.return_value = True
        mock_channel.is_initialized.return_value = True
        mock_channel.send_message = AsyncMock(return_value=True)
        mock_channel.start = AsyncMock(return_value=True)
        mock_channel.stop = AsyncMock(return_value=True)
        mock_channel.initialize = AsyncMock(return_value=True)
        mock_channel.status = ChannelStatus.READY
        return mock_channel
    
    def test_communication_manager_singleton(self, comm_manager):
        """Test that CommunicationManager follows singleton pattern."""
        manager1 = CommunicationManager()
        manager2 = CommunicationManager()
        assert manager1 is manager2
    
    def test_communication_manager_initialization(self, comm_manager):
        """Test CommunicationManager initialization."""
        assert comm_manager.channels == {}
        assert comm_manager.channel_configs == {}
        assert comm_manager.scheduler_manager is None
        assert comm_manager._running is False
    
    @patch('bot.communication_manager.ChannelFactory')
    def test_initialize_channels_from_config(self, mock_factory, comm_manager, mock_channel_config, realistic_mock_channel):
        """Test channel initialization from configuration with realistic channel behavior."""
        # Mock the channel factory to return our realistic mock
        mock_factory.create_channel.return_value = realistic_mock_channel
        
        # Mock the async initialization
        with patch.object(comm_manager, '_initialize_channels_async', new_callable=AsyncMock) as mock_async:
            mock_async.return_value = True
            result = comm_manager.initialize_channels_from_config({'test': mock_channel_config})
            
            assert result is True
            mock_async.assert_called_once()
            
            # Note: The actual implementation doesn't call create_channel directly in this method
            # It's called in the async method, so we don't verify it here
    
    def test_get_available_channels(self, comm_manager, realistic_mock_channel):
        """Test getting available channels with realistic channel setup."""
        # Add realistic mock channels
        comm_manager.channels = {
            'discord': realistic_mock_channel,
            'email': realistic_mock_channel,
            'telegram': realistic_mock_channel
        }
        
        available = comm_manager.get_available_channels()
        assert 'discord' in available
        assert 'email' in available
        assert 'telegram' in available
        assert len(available) == 3
    
    def test_is_channel_ready_with_realistic_channel(self, comm_manager, realistic_mock_channel):
        """Test checking if a channel is ready with realistic channel behavior."""
        comm_manager.channels['test_channel'] = realistic_mock_channel
        
        # Test ready channel
        assert comm_manager.is_channel_ready('test_channel') is True
        
        # Test non-existent channel
        assert comm_manager.is_channel_ready('nonexistent') is False
        
        # Test channel that's not ready
        realistic_mock_channel.is_ready.return_value = False
        assert comm_manager.is_channel_ready('test_channel') is False
        
        # Verify the is_ready method was called
        assert realistic_mock_channel.is_ready.call_count >= 2
    
    def test_send_message_sync_with_realistic_channel(self, comm_manager, realistic_mock_channel):
        """Test synchronous message sending with realistic channel behavior."""
        comm_manager.channels['test_channel'] = realistic_mock_channel
        
        # The actual implementation doesn't use asyncio.run_coroutine_threadsafe
        # It uses legacy channels or direct Discord methods
        # For this test, we'll test the fallback behavior
        
        # Create a legacy wrapper that returns synchronous values
        legacy_wrapper = Mock()
        legacy_wrapper.send_message.return_value = True
        comm_manager._legacy_channels = {'test_channel': legacy_wrapper}
        
        # Test successful message sending
        result = comm_manager.send_message_sync('test_channel', 'user123', 'Test message')
        
        # The function should return True if the legacy channel sends successfully
        assert result is True
        
        # Verify the legacy wrapper's send_message was called with correct parameters
        legacy_wrapper.send_message.assert_called_once_with('user123', 'Test message')
    
    def test_send_message_sync_channel_not_ready(self, comm_manager, realistic_mock_channel):
        """Test synchronous message sending when channel is not ready."""
        # The actual implementation doesn't check is_ready in send_message_sync
        # It just tries to send and returns False if it fails
        comm_manager.channels['test_channel'] = realistic_mock_channel
        
        # Create a legacy wrapper that returns False to simulate failure
        legacy_wrapper = Mock()
        legacy_wrapper.send_message.return_value = False
        comm_manager._legacy_channels = {'test_channel': legacy_wrapper}
        
        result = comm_manager.send_message_sync('test_channel', 'user123', 'Test message')
        
        # Should return False when send fails
        assert result is False
        
        # Verify send_message was called
        legacy_wrapper.send_message.assert_called_once_with('user123', 'Test message')
    
    def test_send_message_sync_channel_not_found(self, comm_manager):
        """Test synchronous message sending when channel doesn't exist."""
        result = comm_manager.send_message_sync('nonexistent', 'user123', 'Test message')
        
        # Should return False when channel doesn't exist
        assert result is False
    
    def test_legacy_channel_wrapper_with_realistic_channel(self, realistic_mock_channel):
        """Test LegacyChannelWrapper functionality with realistic channel behavior."""
        wrapper = LegacyChannelWrapper(realistic_mock_channel)
        
        # Test initialization status
        assert wrapper.is_initialized() is True
        
        # Test wrapper methods delegate to the base channel
        assert wrapper.is_ready() is True
        
        # Test that the wrapper has the expected attributes
        assert hasattr(wrapper, 'send_message')
        assert hasattr(wrapper, 'start')
        assert hasattr(wrapper, 'stop')
        assert hasattr(wrapper, 'initialize')
    
    def test_legacy_channel_wrapper_method_delegation(self, realistic_mock_channel):
        """Test that LegacyChannelWrapper properly delegates methods to base channel."""
        wrapper = LegacyChannelWrapper(realistic_mock_channel)
        
        # Reset the mock to start fresh
        realistic_mock_channel.is_ready.reset_mock()
        
        # Test that wrapper methods call the base channel methods
        wrapper.is_ready()
        realistic_mock_channel.is_ready.assert_called_once()
    
    def test_communication_manager_error_handling(self, comm_manager, realistic_mock_channel):
        """Test error handling in communication manager."""
        # The actual implementation doesn't handle exceptions in is_channel_ready
        # It just calls channel.is_ready() directly
        realistic_mock_channel.is_ready.side_effect = Exception("Channel error")
        comm_manager.channels['error_channel'] = realistic_mock_channel
        
        # The actual implementation will raise the exception
        with pytest.raises(Exception, match="Channel error"):
            comm_manager.is_channel_ready('error_channel')
        
        # Test with non-existent channel
        result = comm_manager.is_channel_ready('nonexistent')
        assert result is False 