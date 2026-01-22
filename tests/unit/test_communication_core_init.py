"""
Tests for communication.core.__init__ module.

Tests lazy imports, __getattr__ functionality, and package-level exports:
- Direct imports (RetryManager, QueuedMessage)
- Lazy imports via __getattr__ (ChannelFactory, ChannelMonitor)
- Error handling for invalid attribute access
- Circular dependency handling
"""

import pytest
from unittest.mock import patch, MagicMock
import sys


from core.time_utilities import now_datetime_full


class TestCommunicationCoreInitDirectImports:
    """Test direct imports from communication.core.__init__."""

    @pytest.mark.unit
    @pytest.mark.communication
    def test_retry_manager_direct_import(self):
        """Test that RetryManager can be imported directly."""
        # Arrange & Act
        from communication.core import RetryManager

        # Assert
        assert RetryManager is not None, "RetryManager should be importable"
        assert hasattr(RetryManager, "__init__"), "RetryManager should be a class"

    @pytest.mark.unit
    @pytest.mark.communication
    def test_queued_message_direct_import(self):
        """Test that QueuedMessage can be imported directly."""
        # Arrange & Act
        from communication.core import QueuedMessage

        # Assert
        assert QueuedMessage is not None, "QueuedMessage should be importable"
        assert hasattr(QueuedMessage, "__init__"), "QueuedMessage should be a class"

    @pytest.mark.unit
    @pytest.mark.communication
    def test_retry_manager_usage(self):
        """Test that RetryManager can be instantiated and used."""
        # Arrange & Act
        from communication.core import RetryManager

        manager = RetryManager(send_callback=None)

        # Assert
        assert manager is not None, "RetryManager should be instantiable"
        assert hasattr(
            manager, "queue_failed_message"
        ), "RetryManager should have queue_failed_message method"
        assert hasattr(
            manager, "get_queue_size"
        ), "RetryManager should have get_queue_size method"

    @pytest.mark.unit
    @pytest.mark.communication
    def test_queued_message_usage(self):
        """Test that QueuedMessage can be instantiated and used."""
        # Arrange & Act
        from communication.core import QueuedMessage
        from datetime import datetime

        message = QueuedMessage(
            user_id="test_user",
            category="motivational",
            message="test message",
            recipient="test_recipient",
            channel_name="discord",
            timestamp=now_datetime_full(),
        )

        # Assert
        assert message is not None, "QueuedMessage should be instantiable"
        assert (
            message.channel_name == "discord"
        ), "QueuedMessage should store channel_name"
        assert message.user_id == "test_user", "QueuedMessage should store user_id"
        assert message.message == "test message", "QueuedMessage should store message"
        assert message.category == "motivational", "QueuedMessage should store category"


class TestCommunicationCoreInitLazyImports:
    """Test lazy imports via __getattr__."""

    @pytest.mark.unit
    @pytest.mark.communication
    def test_channel_factory_lazy_import(self):
        """Test that ChannelFactory can be imported lazily via __getattr__."""
        # Arrange - Clear any existing imports
        if "communication.core" in sys.modules:
            # Remove the module to test fresh import
            del sys.modules["communication.core"]

        # Act
        from communication.core import ChannelFactory

        # Assert
        assert ChannelFactory is not None, "ChannelFactory should be importable"
        assert hasattr(ChannelFactory, "__init__"), "ChannelFactory should be a class"

    @pytest.mark.unit
    @pytest.mark.communication
    def test_channel_monitor_lazy_import(self):
        """Test that ChannelMonitor can be imported lazily via __getattr__."""
        # Arrange - Clear any existing imports
        if "communication.core" in sys.modules:
            # Remove the module to test fresh import
            del sys.modules["communication.core"]

        # Act
        from communication.core import ChannelMonitor

        # Assert
        assert ChannelMonitor is not None, "ChannelMonitor should be importable"
        assert hasattr(ChannelMonitor, "__init__"), "ChannelMonitor should be a class"

    @pytest.mark.unit
    @pytest.mark.communication
    def test_lazy_import_caching(self):
        """Test that lazy imports are cached after first access."""
        # Arrange - Clear any existing imports
        if "communication.core" in sys.modules:
            del sys.modules["communication.core"]

        # Act - Import twice
        from communication.core import ChannelFactory

        first_import = ChannelFactory

        from communication.core import ChannelFactory

        second_import = ChannelFactory

        # Assert - Should be the same object (cached)
        assert first_import is second_import, "Lazy imports should be cached"

    @pytest.mark.unit
    @pytest.mark.communication
    def test_lazy_import_handles_import_errors(self):
        """Test that lazy imports handle import errors gracefully."""
        # Arrange - Clear any existing imports
        if "communication.core" in sys.modules:
            del sys.modules["communication.core"]

        # Act & Assert - Should raise ImportError for invalid attribute during import
        with pytest.raises((ImportError, AttributeError)):
            from communication.core import InvalidAttribute

    @pytest.mark.unit
    @pytest.mark.communication
    def test_getattr_raises_attribute_error_for_invalid(self):
        """Test that __getattr__ raises AttributeError for invalid attributes."""
        # Arrange
        import communication.core as core_module

        # Act & Assert
        with pytest.raises(
            AttributeError,
            match="module 'communication.core' has no attribute 'invalid_attr'",
        ):
            _ = core_module.invalid_attr


class TestCommunicationCoreInitExports:
    """Test __all__ exports."""

    @pytest.mark.unit
    @pytest.mark.communication
    def test_all_exports_are_defined(self):
        """Test that all exports in __all__ are accessible."""
        # Arrange
        from communication.core import (
            ChannelFactory,
            RetryManager,
            QueuedMessage,
            ChannelMonitor,
        )

        # Assert - All should be importable
        assert ChannelFactory is not None
        assert RetryManager is not None
        assert QueuedMessage is not None
        assert ChannelMonitor is not None

    @pytest.mark.unit
    @pytest.mark.communication
    def test_all_exports_match_available(self):
        """Test that __all__ matches available exports."""
        # Arrange
        import communication.core as core_module

        # Act
        all_exports = getattr(core_module, "__all__", [])

        # Assert - Should have expected exports
        assert "ChannelFactory" in all_exports, "ChannelFactory should be in __all__"
        assert "RetryManager" in all_exports, "RetryManager should be in __all__"
        assert "QueuedMessage" in all_exports, "QueuedMessage should be in __all__"
        assert "ChannelMonitor" in all_exports, "ChannelMonitor should be in __all__"


class TestCommunicationCoreInitCircularDependencyHandling:
    """Test circular dependency handling via lazy imports."""

    @pytest.mark.unit
    @pytest.mark.communication
    def test_lazy_import_prevents_circular_dependency(self):
        """Test that lazy imports prevent circular dependency issues."""
        # Arrange - Clear any existing imports
        if "communication.core" in sys.modules:
            del sys.modules["communication.core"]

        # Act - Import should not cause circular dependency
        from communication.core import ChannelFactory, ChannelMonitor

        # Assert - Should import successfully
        assert ChannelFactory is not None
        assert ChannelMonitor is not None

    @pytest.mark.unit
    @pytest.mark.communication
    def test_getattr_does_not_use_error_handling_decorator(self):
        """Test that __getattr__ intentionally does not use @handle_errors decorator."""
        # This test verifies the design decision documented in the code
        # The __getattr__ function should not use @handle_errors to avoid circular dependencies
        import communication.core as core_module
        import inspect

        # Act - Get the __getattr__ function
        getattr_func = core_module.__getattr__
        source = inspect.getsource(getattr_func)

        # Assert - Should not have @handle_errors decorator on the function definition
        # Check that the decorator is not on the function line (it may appear in comments)
        lines = source.split("\n")
        func_line = None
        for i, line in enumerate(lines):
            if line.strip().startswith("def __getattr__"):
                func_line = i
                break

        if func_line is not None and func_line > 0:
            # Check the line before the function definition
            decorator_line = lines[func_line - 1].strip()
            assert not decorator_line.startswith(
                "@handle_errors"
            ), "__getattr__ should not use @handle_errors decorator to avoid circular dependencies"


class TestCommunicationCoreInitRealBehavior:
    """Test real behavior of communication.core module."""

    @pytest.mark.unit
    @pytest.mark.communication
    @pytest.mark.behavior
    def test_retry_manager_creates_proper_structure(self):
        """Test that RetryManager creates proper internal structure."""
        # Arrange & Act
        from communication.core import RetryManager

        manager = RetryManager(send_callback=None)

        # Assert - Verify internal structure
        assert hasattr(
            manager, "_failed_message_queue"
        ), "RetryManager should have _failed_message_queue"
        assert hasattr(
            manager, "_send_callback"
        ), "RetryManager should have _send_callback"
        assert manager._send_callback is None, "RetryManager should store send_callback"
        assert hasattr(
            manager, "queue_failed_message"
        ), "RetryManager should have queue_failed_message method"
        assert hasattr(
            manager, "get_queue_size"
        ), "RetryManager should have get_queue_size method"

    @pytest.mark.unit
    @pytest.mark.communication
    @pytest.mark.behavior
    def test_queued_message_stores_data(self):
        """Test that QueuedMessage stores data correctly."""
        # Arrange & Act
        from communication.core import QueuedMessage
        from datetime import datetime

        message = QueuedMessage(
            user_id="test_user_001",
            category="reminder",
            message="test content",
            recipient="test_recipient",
            channel_name="email",
            timestamp=now_datetime_full(),
            retry_count=0,
            max_retries=3,
            retry_delay=300,
        )

        # Assert - Verify data persistence
        assert (
            message.channel_name == "email"
        ), "QueuedMessage should persist channel_name"
        assert (
            message.user_id == "test_user_001"
        ), "QueuedMessage should persist user_id"
        assert message.message == "test content", "QueuedMessage should persist message"
        assert message.category == "reminder", "QueuedMessage should persist category"
        assert message.max_retries == 3, "QueuedMessage should persist max_retries"
        assert message.retry_delay == 300, "QueuedMessage should persist retry_delay"

    @pytest.mark.unit
    @pytest.mark.communication
    @pytest.mark.behavior
    def test_channel_factory_can_be_instantiated(self):
        """Test that ChannelFactory can be instantiated after lazy import."""
        # Arrange
        from communication.core import ChannelFactory

        # Act
        factory = ChannelFactory()

        # Assert
        assert factory is not None, "ChannelFactory should be instantiable"

    @pytest.mark.unit
    @pytest.mark.communication
    @pytest.mark.behavior
    def test_channel_monitor_can_be_instantiated(self):
        """Test that ChannelMonitor can be instantiated after lazy import."""
        # Arrange
        from communication.core import ChannelMonitor

        # Act
        monitor = ChannelMonitor()

        # Assert
        assert monitor is not None, "ChannelMonitor should be instantiable"
