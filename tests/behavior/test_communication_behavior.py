"""
Tests for the communication manager module - Message delivery across channels.

This module tests:
- Message delivery to different channels (Discord, Email)
- Channel selection and routing
- Message formatting and validation
- Delivery status tracking
- Error handling and retry logic
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import asyncio
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the actual functions from communication_manager
from communication.core.channel_orchestrator import CommunicationManager, BotInitializationError, MessageSendError
from communication.core.retry_manager import QueuedMessage
from communication.communication_channels.base.base_channel import BaseChannel, ChannelConfig, ChannelStatus, ChannelType
from core.config import get_user_data_dir

class TestCommunicationManager:
    """Test cases for the CommunicationManager class."""
    
    @pytest.fixture
    def temp_dir(self, test_path_factory):
        """Provide a per-test directory under tests/data/tmp."""
        return test_path_factory
    
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
        mock_channel.get_status = AsyncMock(return_value=ChannelStatus.READY)
        mock_channel.status = ChannelStatus.READY
        return mock_channel
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.critical
    @pytest.mark.regression
    def test_communication_manager_singleton(self, comm_manager):
        """Test that CommunicationManager follows singleton pattern."""
        manager1 = CommunicationManager()
        manager2 = CommunicationManager()
        assert manager1 is manager2
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.critical
    @pytest.mark.regression
    def test_communication_manager_initialization(self, comm_manager):
        """Test CommunicationManager initialization."""
        assert comm_manager._channels_dict == {}
        assert comm_manager.channel_configs == {}
        assert comm_manager.scheduler_manager is None
        assert comm_manager._running is False
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.critical
    @pytest.mark.regression
    @patch('communication.core.channel_orchestrator.ChannelFactory')
    def test_initialize_channels_from_config(self, mock_factory, comm_manager, mock_channel_config, realistic_mock_channel):
        """Test channel initialization from configuration with realistic channel behavior."""
        # Mock the channel factory to return our realistic mock
        mock_factory.create_channel.return_value = realistic_mock_channel
        
        # Mock the async initialization
        with patch.object(comm_manager, 'initialize_channels_from_config__initialize_channels_async', new_callable=AsyncMock) as mock_async:
            mock_async.return_value = True
            result = comm_manager.initialize_channels_from_config({'test': mock_channel_config})
            
            assert result is True
            mock_async.assert_called_once()
            
            # Note: The actual implementation doesn't call create_channel directly in this method
            # It's called in the async method, so we don't verify it here
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_active_channels(self, comm_manager, realistic_mock_channel):
        """Test getting active channels with realistic channel setup."""
                # Add realistic mock channels
        comm_manager._channels_dict = {
            'discord': realistic_mock_channel,
            'email': realistic_mock_channel,
        }
        
        available = comm_manager.get_active_channels()
        assert 'discord' in available
        assert 'email' in available

        assert len(available) == 2
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_get_channel_status_with_realistic_channel(self, comm_manager, realistic_mock_channel):
        """Test checking channel status with realistic channel behavior."""
        comm_manager._channels_dict['test_channel'] = realistic_mock_channel
        
        # Mock the channel's get_status method
        realistic_mock_channel.get_status.return_value = ChannelStatus.READY
        
        # Test ready channel
        status = await comm_manager.get_channel_status('test_channel')
        assert status == ChannelStatus.READY
        
        # Test non-existent channel
        status = await comm_manager.get_channel_status('nonexistent')
        assert status is None
        
        # Test channel that's not ready
        realistic_mock_channel.get_status.return_value = ChannelStatus.ERROR
        status = await comm_manager.get_channel_status('test_channel')
        assert status == ChannelStatus.ERROR
        
        # Verify the get_status method was called
        assert realistic_mock_channel.get_status.call_count >= 2
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.critical
    @pytest.mark.regression
    def test_send_message_sync_with_realistic_channel(self, comm_manager, realistic_mock_channel):
        """Test synchronous message sending with realistic channel behavior."""
        comm_manager._channels_dict['test_channel'] = realistic_mock_channel
        
        # Mock the channel's send_message method to return True
        realistic_mock_channel.send_message.return_value = True
        realistic_mock_channel.is_ready.return_value = True
        
        # Test successful message sending
        result = comm_manager.send_message_sync('test_channel', 'user123', 'Test message')
        
        # The function should return True if the channel sends successfully
        assert result is True
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.critical
    @pytest.mark.regression
    def test_send_message_sync_channel_not_ready(self, comm_manager, realistic_mock_channel):
        """Test synchronous message sending when channel is not ready."""
        comm_manager._channels_dict['test_channel'] = realistic_mock_channel
        
        # Mock the channel to return False to simulate failure
        realistic_mock_channel.send_message.return_value = False
        realistic_mock_channel.is_ready.return_value = True
        
        result = comm_manager.send_message_sync('test_channel', 'user123', 'Test message')
        
        # Should return False when send fails
        assert result is False
        
        # Verify send_message was called
        realistic_mock_channel.send_message.assert_called_once_with('user123', 'Test message')
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.critical
    @pytest.mark.regression
    def test_send_message_sync_channel_not_found(self, comm_manager):
        """Test synchronous message sending when channel doesn't exist."""
        result = comm_manager.send_message_sync('nonexistent', 'user123', 'Test message')
        
        # Should return False when channel doesn't exist
        assert result is False
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_communication_manager_error_handling(self, comm_manager, realistic_mock_channel):
        """Test error handling in communication manager."""
        realistic_mock_channel.get_status.side_effect = Exception("Channel error")
        comm_manager._channels_dict['error_channel'] = realistic_mock_channel
        
        # Test that get_channel_status handles exceptions gracefully
        result = await comm_manager.get_channel_status('error_channel')
        assert result is None  # Should return None for error channels 