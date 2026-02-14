"""
Comprehensive tests for Communication Factory coverage expansion.

Tests focus on covering the uncovered lines in the ChannelFactory module.
"""

from unittest.mock import patch, Mock
import core

from communication.core.factory import ChannelFactory
import pytest

from communication.communication_channels.base.base_channel import BaseChannel, ChannelConfig


@pytest.mark.behavior
class TestCommunicationFactoryCoverageExpansion:
    """Test coverage expansion for Communication Factory module."""

    def test_initialize_registry_already_initialized(self, test_data_dir):
        """Test _initialize_registry when already initialized."""
        # Arrange
        ChannelFactory._initialized = True
        original_registry = ChannelFactory._channel_registry.copy()
        
        # Act
        ChannelFactory._initialize_registry()
        
        # Assert
        assert ChannelFactory._channel_registry == original_registry, "Registry should not change when already initialized"
        
        # Cleanup
        ChannelFactory._initialized = False

    def test_initialize_registry_with_import_error(self, test_data_dir):
        """Test _initialize_registry with import error."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        with patch('communication.core.factory.get_available_channels') as mock_channels, patch(
            'communication.core.factory.get_channel_class_mapping'
        ) as mock_mapping:
            mock_channels.return_value = ['test_channel']
            mock_mapping.return_value = {'test_channel': 'invalid.module.Class'}

            # Act
            ChannelFactory._initialize_registry()

            # Assert
            assert 'test_channel' not in ChannelFactory._channel_registry, "Should not register channel with import error"

    def test_initialize_registry_with_attribute_error(self, test_data_dir):
        """Test _initialize_registry with attribute error."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        with patch('communication.core.factory.get_available_channels') as mock_channels, patch(
            'communication.core.factory.get_channel_class_mapping'
        ) as mock_mapping, patch('importlib.import_module') as mock_import:
            mock_channels.return_value = ['test_channel']
            mock_mapping.return_value = {'test_channel': 'tests.test_utilities.TestUserFactory'}
            mock_import.return_value = Mock()
            # Use a different approach to simulate attribute error
            mock_import.return_value.TestUserFactory = None

            # Act
            ChannelFactory._initialize_registry()

            # Assert
            assert 'test_channel' not in ChannelFactory._channel_registry, "Should not register channel with attribute error"

    def test_initialize_registry_successful_registration(self, test_data_dir):
        """Test _initialize_registry with successful channel registration."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        with patch.object(core.config, 'get_available_channels') as mock_channels, patch.object(
            core.config, 'get_channel_class_mapping'
        ) as mock_mapping, patch('importlib.import_module') as mock_import:
            mock_channels.return_value = ['test_channel']
            mock_mapping.return_value = {'test_channel': 'tests.test_utilities.TestUserFactory'}
            mock_module = Mock()
            mock_module.TestUserFactory = Mock
            mock_import.return_value = mock_module

            # Act
            ChannelFactory._initialize_registry()

            # Assert - Check that the registry was initialized and contains our test channel
            assert ChannelFactory._initialized, "Should be marked as initialized"
            assert 'test_channel' in ChannelFactory._channel_registry, "Should register channel successfully"
            assert ChannelFactory._channel_registry['test_channel'] == Mock, "Should register correct class"

    def test_create_channel_unknown_type(self, test_data_dir):
        """Test create_channel with unknown channel type."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        with patch('communication.core.factory.get_available_channels') as mock_channels, patch(
            'communication.core.factory.get_channel_class_mapping'
        ) as mock_mapping:
            mock_channels.return_value = ['known_channel']
            mock_mapping.return_value = {'known_channel': 'tests.test_utilities.TestUserFactory'}

            # Initialize registry
            ChannelFactory._initialize_registry()

            # Act
            config = ChannelConfig(name="test_channel")
            result = ChannelFactory.create_channel('unknown_channel', config)

            # Assert
            assert result is None, "Should return None for unknown channel type"

    def test_create_channel_successful_creation(self, test_data_dir):
        """Test create_channel with successful channel creation."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        # Create a mock channel class
        class MockChannel(BaseChannel):
            def __init__(self, config):
                super().__init__(config)
                self.initialized = True
            
            @property
            def channel_type(self):
                from communication.communication_channels.base.base_channel import ChannelType
                return ChannelType.SYNC
            
            async def initialize(self):
                return True
            
            async def shutdown(self):
                return True
            
            async def send_message(self, recipient, message, **kwargs):
                return True
            
            async def receive_messages(self):
                return []
            
            async def health_check(self):
                return True
        
        with patch.object(core.config, 'get_available_channels') as mock_channels, patch.object(
            core.config, 'get_channel_class_mapping'
        ) as mock_mapping, patch('importlib.import_module') as mock_import:
            mock_channels.return_value = ['test_channel']
            mock_mapping.return_value = {'test_channel': 'tests.test_utilities.TestUserFactory'}
            mock_module = Mock()
            mock_module.TestUserFactory = MockChannel
            mock_import.return_value = mock_module

            # Initialize registry
            ChannelFactory._initialize_registry()

            # Act
            config = ChannelConfig(name="test_channel")
            result = ChannelFactory.create_channel('test_channel', config)

            # Assert
            assert result is not None, "Should create channel successfully"
            assert isinstance(result, MockChannel), "Should return correct channel type"
            assert result.initialized, "Channel should be properly initialized"

    def test_get_registered_channels_empty_registry(self, test_data_dir):
        """Test get_registered_channels with empty registry."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        with patch.object(core.config, 'get_available_channels') as mock_channels, patch.object(
            core.config, 'get_channel_class_mapping'
        ) as mock_mapping:
            mock_channels.return_value = []
            mock_mapping.return_value = {}

            # Act
            channels = ChannelFactory.get_registered_channels()

            # Assert
            assert channels == [], "Should return empty list for empty registry"

    def test_get_registered_channels_with_channels(self, test_data_dir):
        """Test get_registered_channels with registered channels."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        with patch.object(core.config, 'get_available_channels') as mock_channels, patch.object(
            core.config, 'get_channel_class_mapping'
        ) as mock_mapping, patch('importlib.import_module') as mock_import:
            mock_channels.return_value = ['channel1', 'channel2']
            mock_mapping.return_value = {
                'channel1': 'tests.test_utilities.TestUserFactory',
                'channel2': 'tests.test_utilities.TestDataFactory'
            }
            mock_module = Mock()
            mock_module.TestUserFactory = Mock
            mock_module.TestDataFactory = Mock
            mock_import.return_value = mock_module

            # Act
            channels = ChannelFactory.get_registered_channels()

            # Assert
            assert 'channel1' in channels, "Should include channel1"
            assert 'channel2' in channels, "Should include channel2"
            assert len(channels) == 2, "Should return correct number of channels"

    def test_factory_error_handling_initialization(self, test_data_dir):
        """Test factory error handling during initialization."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        with patch('communication.core.factory.get_available_channels', side_effect=Exception("Config error")):
            # Act
            ChannelFactory._initialize_registry()
            
            # Assert
            assert ChannelFactory._initialized, "Should handle errors gracefully"

    def test_factory_error_handling_create_channel(self, test_data_dir):
        """Test factory error handling during channel creation."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        # Create a channel class that raises an exception
        class ErrorChannel(BaseChannel):
            def __init__(self, config):
                raise Exception("Channel creation error")
            
            @property
            def channel_type(self):
                from communication.communication_channels.base.base_channel import ChannelType
                return ChannelType.SYNC
            
            async def initialize(self):
                return True
            
            async def shutdown(self):
                return True
            
            async def send_message(self, recipient, message, **kwargs):
                return True
            
            async def receive_messages(self):
                return []
            
            async def health_check(self):
                return True
        
        with patch('communication.core.factory.get_available_channels') as mock_channels, patch(
            'communication.core.factory.get_channel_class_mapping'
        ) as mock_mapping, patch('importlib.import_module') as mock_import:
            mock_channels.return_value = ['error_channel']
            mock_mapping.return_value = {'error_channel': 'tests.test_utilities.TestUserFactory'}
            mock_module = Mock()
            mock_module.TestUserFactory = ErrorChannel
            mock_import.return_value = mock_module

            # Initialize registry
            ChannelFactory._initialize_registry()

            # Act
            config = ChannelConfig(name="error_channel")
            result = ChannelFactory.create_channel('error_channel', config)

            # Assert
            assert result is None, "Should return None on channel creation error"

    def test_factory_error_handling_get_channels(self, test_data_dir):
        """Test factory error handling during get_registered_channels."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        with patch.object(core.config, 'get_available_channels', side_effect=Exception("Config error")):
            # Act
            channels = ChannelFactory.get_registered_channels()
            
            # Assert
            assert channels == [], "Should return empty list on error"

    def test_factory_registry_persistence(self, test_data_dir):
        """Test that registry persists between calls."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        with patch.object(core.config, 'get_available_channels') as mock_channels, patch.object(
            core.config, 'get_channel_class_mapping'
        ) as mock_mapping, patch('importlib.import_module') as mock_import:
            mock_channels.return_value = ['persistent_channel']
            mock_mapping.return_value = {'persistent_channel': 'tests.test_utilities.TestUserFactory'}
            mock_module = Mock()
            mock_module.TestUserFactory = Mock
            mock_import.return_value = mock_module

            # Act - First call
            channels1 = ChannelFactory.get_registered_channels()

            # Act - Second call (should use cached registry)
            channels2 = ChannelFactory.get_registered_channels()

            # Assert
            assert channels1 == channels2, "Should return same results"
            assert 'persistent_channel' in channels1, "Should include registered channel"

    def test_factory_dynamic_import_handling(self, test_data_dir):
        """Test factory handling of dynamic imports."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        with patch('communication.core.factory.get_available_channels') as mock_channels, patch(
            'communication.core.factory.get_channel_class_mapping'
        ) as mock_mapping:
            mock_channels.return_value = ['dynamic_channel']
            mock_mapping.return_value = {'dynamic_channel': 'communication.communication_channels.discord.bot.DiscordBot'}

            # Act
            ChannelFactory._initialize_registry()

            # Assert
            # Should handle the import attempt gracefully, even if DiscordBot isn't available in test environment
            assert ChannelFactory._initialized, "Should complete initialization"

    def test_factory_config_integration(self, test_data_dir):
        """Test factory integration with configuration system."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        # Test with real config functions (mocked)
        with patch.object(core.config, 'get_available_channels') as mock_channels, patch.object(
            core.config, 'get_channel_class_mapping'
        ) as mock_mapping:
            mock_channels.return_value = ['config_channel']
            mock_mapping.return_value = {'config_channel': 'tests.test_utilities.TestUserFactory'}

            # Act
            ChannelFactory._initialize_registry()

            # Assert
            assert mock_channels.called, "Should call get_available_channels"
            assert mock_mapping.called, "Should call get_channel_class_mapping"

    def test_factory_logging_behavior(self, test_data_dir):
        """Test factory logging behavior."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        with patch('communication.core.factory.logger') as mock_logger, patch(
            'communication.core.factory.get_available_channels'
        ) as mock_channels, patch(
            'communication.core.factory.get_channel_class_mapping'
        ) as mock_mapping:
            mock_channels.return_value = ['logging_channel']
            mock_mapping.return_value = {'logging_channel': 'tests.test_utilities.TestUserFactory'}

            # Act
            ChannelFactory._initialize_registry()

            # Assert
            mock_logger.info.assert_called()
            mock_logger.debug.assert_called()

    def test_factory_singleton_behavior(self, test_data_dir):
        """Test factory singleton-like behavior."""
        # Arrange
        ChannelFactory._initialized = False
        ChannelFactory._channel_registry.clear()
        
        # Act - Multiple calls should use same registry
        channels1 = ChannelFactory.get_registered_channels()
        channels2 = ChannelFactory.get_registered_channels()
        
        # Assert
        assert channels1 is not channels2, "Should return new list each time"
        assert channels1 == channels2, "Should return same content"
